from fastapi import APIRouter, status, Request
from fastapi.responses import HTMLResponse
from typing import Optional
import pinecone
from service.dependencies import PineconeRequest, PineconeNode, get_embedding, TANA_NAMESPACE, TANA_TYPE
from logging import getLogger
from ratelimit import limits, RateLimitException, sleep_and_retry
from functools import lru_cache
import asyncio
import time

logger = getLogger()

router = APIRouter()

@lru_cache() # reuse connection to pinecone to avoid connection rate limiting on parallel requests
def get_pinecone(api_key:str, environment:str):
  pinecone.init(api_key=api_key, environment=environment)
  logger.info("Connected to pinecone")
  return pinecone

@router.on_event("startup")
def startup_pinecone():
  # TODO: how to do this? Index might be variable per API call...
  # create_index_if_needed()
  pass

def create_index_if_needed(req:PineconeRequest):
  pinecone = get_pinecone(req.pinecone, req.environment)
  index = None
  # Check if the index name is specified and exists in Pinecone
  if req.index and req.index not in pinecone.list_indexes():
    fields_to_index = list(PineconeNode.__fields__.keys())

    # Create a new index with the specified name, dimension, and metadata configuration
    # TODO: ignore metadata narrowing  - not supported on free plan anyhow
    try:
        logger.info(
            f"Creating index {req.index} with metadata config {fields_to_index}"
        )
        pinecone.create_index(
            req.index,
            dimension=1536,  # dimensionality of OpenAI ada v2 embeddings
            metadata_config={"indexed": fields_to_index},
        )
        index = pinecone.Index(req.index)
        logger.info(f"Index {req.index} created successfully")
    except Exception as e:
        logger.error(f"Error creating index {req.index}: {e}")
        raise e
    
  return index

def get_index(req:PineconeRequest):
  pinecone = get_pinecone(req.pinecone, req.environment)

  # too slow to do this check every time
  # TODO: Put this in an initialization function
  # create_index_if_needed(req)

  index = pinecone.Index(req.index) # type: ignore
  return index

# attempt to paralleize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()

@router.post("/pinecone/upsert", status_code=status.HTTP_204_NO_CONTENT, tags=["Pinecone"])
async def upsert(request: Request, req: PineconeRequest):
  async with lock:
    start_time = time.time()
    logger.info(f'DO txid={request.headers["x-request-id"]}')
    embedding = get_embedding(req)
    vectors = [(req.nodeId, embedding[0]['embedding'],
                {
                'category': TANA_TYPE,
                'supertag': req.tags,
                'text': req.context
                })
              ]
    
    index = get_index(req)

    # @sleep_and_retry
    # @limits(calls=5, period=10)
    def do_upsert():
      index.upsert(vectors=vectors, namespace=TANA_NAMESPACE)
    
    do_upsert()
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f'DONE txid={request.headers["x-request-id"]} time={formatted_process_time}')
    return None

@router.post("/pinecone/delete", status_code=status.HTTP_204_NO_CONTENT, tags=["Pinecone"])
def delete(req: PineconeRequest):  
  index = get_index(req)

  index.delete(ids=[req.nodeId], namespace=TANA_NAMESPACE)
  return None


def get_tana_nodes_for_query(req: PineconeRequest, send_text: Optional[bool] = False):  
  embedding = get_embedding(req)

  vector = embedding[0]['embedding']

  supertags = str(req.tags).split()
  tag_filter = None
  if len(supertags) > 0:
    tag_filter = {
      'category': TANA_TYPE,
      'supertag': { "$in": supertags }    
    }

  index = get_index(req)

  query_response = index.query(
    namespace=TANA_NAMESPACE,
    top_k=req.top,
    include_values=True,
    include_metadata=True,
    vector = vector,
    filter=tag_filter
  )

  def threshold_function(match):
    return match.score > req.score

  best = filter(threshold_function, query_response.matches)
  ids = ["[[^"+match.id+"]]" for match in best]
  
  if not send_text:
    return ids
  else:
    # iterator exhausted. do it again
    best = filter(threshold_function, query_response.matches)
    docs = [ {'sources': '[[^'+match.id+']]', 'answer': match.metadata['text']} for match in best]
    return docs

@router.post("/pinecone/query", response_class=HTMLResponse, tags=["Pinecone"])
def query_pinecone(req: PineconeRequest, send_text: Optional[bool] = False):  
  ids = get_tana_nodes_for_query(req)
  if len(ids) == 0:
    tana_result = "No sufficiently well-scored results"
  else:
    tana_result = ''.join(["- "+str(id)+"\n" for id in ids])
  return tana_result


@router.post("/pinecone/purge", status_code=status.HTTP_204_NO_CONTENT, tags=["Pinecone"])
def purge(req: PineconeRequest):  
  return "Not yet implemented"