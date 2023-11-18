from fastapi import APIRouter, status, Request
from fastapi.responses import HTMLResponse
from typing import Optional
from service.dependencies import ChromaRequest, get_embedding, TANA_NAMESPACE, TANA_TYPE
from logging import getLogger
from ratelimit import limits, RateLimitException, sleep_and_retry
from functools import lru_cache
import asyncio
import time
import chromadb
import chromadb.api.segment
from pathlib import Path
import os

logger = getLogger()

router = APIRouter()

db_path = os.path.join(Path.home(), '.chroma.db')
@lru_cache() # reuse connection to chromadb to avoid connection rate limiting on parallel requests
def get_chroma(environment:str):
  # pinecone.init(api_key=api_key, environment=environment)
  # TODO: let environment specify file name?

  chroma_client = chromadb.PersistentClient(path=db_path)

  logger.info("Connected to chromadb")
  return chroma_client

def get_collection(req:ChromaRequest):
  chroma = get_chroma(req.environment)
  # use cosine rather than l2 (should test this)
  collection = chroma.get_or_create_collection(name=req.index, metadata={"hnsw:space": "cosine"})
  return collection

# attempt to paralleize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()

@router.post("/chroma/upsert", status_code=status.HTTP_204_NO_CONTENT)
async def chroma_upsert(request: Request, req: ChromaRequest):
  async with lock:
    start_time = time.time()
    logger.info(f'DO txid={request.headers["x-request-id"]}')
    embedding = get_embedding(req)
    vector = embedding[0]['embedding']

    collection = get_collection(req)

    metadata = {'category': TANA_TYPE,
                  'supertag': req.tags,
                  'text': req.context}
    
    # @sleep_and_retry
    # @limits(calls=5, period=10)
    def do_upsert():
      collection.upsert(
        ids=req.nodeId,
        embeddings=vector,
        metadatas=metadata
      )
      
    do_upsert()
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f'DONE txid={request.headers["x-request-id"]} time={formatted_process_time}')
    return None

@router.post("/chroma/delete", status_code=status.HTTP_204_NO_CONTENT)
def chroma_delete(req: ChromaRequest):  
  collection = get_collection(req)
  collection.delete(ids=[req.nodeId])
  return None


def get_tana_nodes_for_query(req: ChromaRequest, send_text: Optional[bool] = False):  
  embedding = get_embedding(req)

  vector = embedding[0]['embedding']

  supertags = str(req.tags).split()
  tag_filter = None
  if len(supertags) > 0:
    tag_filter = {
      'supertag': { "$in": supertags }    
    }

  collection = get_collection(req)

  query_response = collection.query(query_embeddings=vector,
    n_results=req.top, # type: ignore
    where=tag_filter
  )

  # the result from ChromaDB is kinda strange. Instead of an array of objects
  # # it's four distinct arrays of object properties. Very odd interface.
  best = []
  index = 0
  for node_id in query_response['ids'][0]:
    logger.info(f"Found node {node_id}")
    if query_response['distances'][0][index] < (1.0 - req.score): # type: ignore
      best.append(node_id)
    index += 1


  ids = ["[[^"+match+"]]" for match in best]
  
  return ids

  # ids = query_response.ids

  # if not send_text:
  #   return ids
  # else:
  #   # iterator exhausted. do it again
  #   best = filter(threshold_function, query_response.matches)
  #   docs = [ {'sources': '[[^'+match.id+']]', 'answer': match.metadata['text']} for match in best]
  #   return docs

@router.post("/chroma/query", response_class=HTMLResponse)
def chroma_query(req: ChromaRequest, send_text: Optional[bool] = False):  
  ids = get_tana_nodes_for_query(req)
  if len(ids) == 0:
    tana_result = "No sufficiently well-scored results"
  else:
    tana_result = ''.join(["- "+str(id)+"\n" for id in ids])
  return tana_result


@router.post("/chroma/purge", status_code=status.HTTP_204_NO_CONTENT)
def chroma_purge(req: ChromaRequest):
  collection = get_collection(req)
  collection.delete()
  return None