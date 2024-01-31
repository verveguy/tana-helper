from fastapi import APIRouter, status, Request
from fastapi.responses import HTMLResponse
from typing import Dict, List, Optional
from service.dependencies import TANA_INDEX, ChromaStoreRequest, TanaNodeMetadata, settings, QueueRequest, ChromaRequest, get_embedding, TANA_NAMESPACE, TANA_NODE, TanaInputAPIClient, SuperTag, Node, AddToNodeRequest
from logging import getLogger
from ratelimit import limits, RateLimitException, sleep_and_retry
from functools import lru_cache
import asyncio
import time
from chromadb import EmbeddingFunction, Documents, Embeddings, Where
import chromadb
import chromadb.api.segment
from chromadb.config import Settings
from pathlib import Path
import os
import re
from snowflake import SnowflakeGenerator

from service.tanaparser import prune_reference_nodes

logger = getLogger()
snowflakes = SnowflakeGenerator(42)

router = APIRouter()

INBOX_QUEUE = "queue"

# TODO: Add header support throughout so we can pass Tana API key and OpenAPI Key as headers
# NOTE: we already have this in the main.py middleware wrapper, but it would be better
# to do it here for OpenAPI purposes.
# x_tana_api_token: Annotated[str | None, Header()] = None
# x_openai_api_key: Annotated[str | None, Header()] = None

db_path = os.path.join(Path.home(), '.chroma.db')
@lru_cache() # reuse connection to chromadb to avoid connection rate limiting on parallel requests
def get_chroma():
  chroma_client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))

  logger.info("Connected to chromadb")
  return chroma_client


def get_collection():
  chroma = get_chroma()
  # use cosine rather than l2 (should test this)
  collection = chroma.get_or_create_collection(name=TANA_INDEX, metadata={"hnsw:space": "cosine"})
  return collection

def get_queue_collection():
  chroma = get_chroma()
  # use cosine rather than l2 (should test this)
  collection = chroma.get_or_create_collection(name=INBOX_QUEUE)
  return collection

# attempt to parallelize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()

@router.post("/chroma/upsert", status_code=status.HTTP_204_NO_CONTENT, tags=["Chroma"])
async def chroma_upsert(request: Request, req: ChromaRequest):
  async with lock:
    start_time = time.time()
    logger.info(f'DO txid={request.headers["x-request-id"]}')
    
    # we only want the direct children of the node as context
    # so we prune the context before embedding
    pruned_content = prune_reference_nodes(req.context)
    req.context = pruned_content
    
    embedding = get_embedding(req)
    vector = embedding[0].embedding

    collection = get_collection()

    metadata = TanaNodeMetadata(
                category=TANA_NODE,
                supertag=req.tags,
                title=req.name,
                # we put the pruned node context into the metadata
                text=req.context,
                tana_id=req.nodeId,
                topic_id=req.nodeId,
    )
    
    if req.context is None:
      logger.warning(f"Empty context for {req.nodeId}")

    # @sleep_and_retry
    # @limits(calls=5, period=10)
    def do_upsert():
      collection.upsert(
        ids=req.nodeId,
        embeddings=vector,
        # we only embed the name of the node (primary content of the node)
        documents=req.name,
        metadatas=metadata.model_dump(),
      )
      
    do_upsert()
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f'DONE txid={request.headers["x-request-id"]} time={formatted_process_time}')
    return None

@router.post("/chroma/delete", status_code=status.HTTP_204_NO_CONTENT, tags=["Chroma"])
def chroma_delete(req: ChromaRequest):  
  collection = get_collection()
  collection.delete(ids=[req.nodeId])
  return None


def get_nodes_by_id(node_ids: List[str]):  

  if len(node_ids) == 0:
    return []
  
  collection = get_collection()

  query_response = collection.get(ids=node_ids)

  texts = []

  if query_response:
    # the result from ChromaDB is kinda strange. Instead of an array of objects
    # # it's four distinct arrays of object properties. Very odd interface.

    for node_id, text, metadata in zip(
            query_response["ids"],
            query_response["documents"], # type: ignore
            query_response["metadatas"], # type: ignore
        ):
      
      # strip out llama_index metadata
      # TODO: figure out how to turn this whole thing into a customretriever of whole nodes
      metadata.pop('_node_type', None)
      metadata.pop('_node_content', None)
      metadata.pop('title', None)

      content = text+'\n'
      content += '\n'.join([f'  - {key}:: {value}' for key, value in metadata.items()])

      texts.append(content)

  return texts

def get_tana_nodes_for_query(req: ChromaRequest):  
  embedding = get_embedding(req)

  vector = embedding[0].embedding

  supertags = str(req.tags).split()
  tag_filter:Where = { 'category': TANA_NODE }
  if len(supertags) > 0:
      tag_filter = { '$and': [
                      {'category': { '$eq': TANA_NODE }},
                      {'supertag': { '$in': supertags }} # type: ignore
                    ]}

  collection = get_collection()

  query_response = collection.query(query_embeddings=vector,
    n_results=req.top, # type: ignore
    where=tag_filter
  )

  best = []
  texts = []

  if query_response:
    # the result from ChromaDB is kinda strange. Instead of an array of objects
    # # it's four distinct arrays of object properties. Very odd interface.

    for node_id, text, metadata, distance in zip(
            query_response["ids"][0],
            query_response["documents"][0], # type: ignore
            query_response["metadatas"][0], # type: ignore
            query_response["distances"][0], # type: ignore
        ):
      
      distance = (1.0 - distance)
      if 'title' in metadata:
        first_line = metadata['title']
      elif 'text' in metadata:
        first_line = metadata['text'].partition('\n')[0] # type: ignore
      else:
        first_line = "<<No title>>"

      if node_id != req.nodeId:
        logger.info(f"Found node {node_id} with score {distance}. Title is {first_line}")
        if distance > req.score: # type: ignore
          best.append(node_id)
          if 'text' in metadata:
            texts.append(metadata['text'])


  ids = ["[[^"+match+"]]" for match in best]  
  return ids, texts

  # ids = query_response.ids

  # if not send_text:
  #   return ids
  # else:
  #   # iterator exhausted. do it again
  #   best = filter(threshold_function, query_response.matches)
  #   docs = [ {'sources': '[[^'+match.id+']]', 'answer': match.metadata['text']} for match in best]
  #   return docs

@router.post("/chroma/query", response_class=HTMLResponse, tags=["Chroma"])
def chroma_query(req: ChromaRequest, send_text: Optional[bool] = False):  
  ids, texts = get_tana_nodes_for_query(req)
  if len(ids) == 0:
    tana_result = "No sufficiently well-scored results"
  else:
    if send_text:
      tana_result = ''.join([str(text)+"\n" for text in texts])
    else:
      tana_result = ''.join(["- "+str(id)+"\n" for id in ids])
  return tana_result

@router.post("/chroma/query_text", response_class=HTMLResponse, tags=["Chroma"])
def chroma_query_text(req: ChromaRequest):  
  return chroma_query(req, True)


@router.post("/chroma/purge", status_code=status.HTTP_204_NO_CONTENT, tags=["Chroma"])
def chroma_purge(req: ChromaRequest):
  collection = get_collection()
  collection.delete()
  return None

# Support for "delayed Tana Paste" capability

# enqueue is like upsert, BUT we don't yet have a nodeID from Tana
# so we create a temporary nodeID and we also shove a placeholder
# into the Tana INBOX
@router.post("/chroma/enqueue", status_code=status.HTTP_204_NO_CONTENT, tags=["Queue"])
async def chroma_enqueue(request: Request, req: QueueRequest):
  async with lock:
    start_time = time.time()
    logger.info(f'DO txid={request.headers["x-request-id"]}')
    #embedding = get_embedding(req)
    vector = [0]
    #embedding[0]['embedding']

    collection = get_queue_collection()

    # generate a temporary nodeID
    node_id = str(next(snowflakes))

    metadata = {'category': TANA_NODE,
                  'text': req.context}
    
    # @sleep_and_retry
    # @limits(calls=5, period=10)
    def do_upsert():
      collection.upsert(
        ids=node_id,
        embeddings=vector,
        metadatas=metadata
      )
      
    do_upsert()

    tana_api_token = settings.tana_api_token
    print(f"Using Tana API token {tana_api_token}")

    # now push into Tana Inbox via inbox API call
    # Replace 'your_auth_token' with your actual auth token
    client = TanaInputAPIClient(auth_token=tana_api_token)

    line_one = req.context.partition('\n')[0]
    # Create nodes, supertags, and children
    supertag = SuperTag(id="qf0MJpvP7liP")  # BRETT HARDCOIDEX FIXME
    main_node = Node(name=f'{node_id}', description=f'{line_one} ...', supertags=[supertag])

    # Prepare request data
    request_data = AddToNodeRequest(nodes=[main_node], targetNodeId="INBOX")

    # Add node to Tana
    response = client.add_to_inbox(request_data=request_data)
    print(response.text)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f'DONE txid={request.headers["x-request-id"]} time={formatted_process_time}')
    return None


# dequeue is like query, but gets the node by ID strictly
@router.post("/chroma/dequeue", response_class=HTMLResponse, tags=["Queue"])
def chroma_dequeue(request: Request, req: QueueRequest):
  best = []
  texts = []
  
  collection = get_queue_collection()

  extracted_group = re.search(r'\b\d+\b', req.context)
  if extracted_group:
    queue_id = extracted_group.group()

    query_response = collection.get(ids=queue_id, limit=1)

    # regex to extract number from this string '- 7135316624697106432 #[[tana paste buffer]] - This is an enqueued Tana Paste\n  - Could not find enqueued content\n'

    # the result from ChromaDB is kinda strange. Instead of an array of objects
    # # it's four distinct arrays of object properties. Very odd interface.
    index = 0
    for node_id in query_response['ids']:
      logger.info(f"Found node {node_id}")
      best.append(node_id)
      metadatas = query_response['metadatas']
      if metadatas is not None:
        texts.append(metadatas[index]['text'])

      # TODO: and delete the node from the queue to keep things clean
      index += 1

  ids = ["[[^"+match+"]]" for match in best]

  if len(ids) == 0:
    tana_result = "Could not find enqueued content"
  else:
    tana_result = ''.join([str(text)+"\n" for text in texts])

  return tana_result

