from fastapi import APIRouter, status, Request
from fastapi.responses import HTMLResponse
from typing import Optional
import weaviate
from ..dependencies import WeaviateRequest, get_embedding, TANA_NAMESPACE, TANA_TYPE
from logging import getLogger
from ratelimit import limits, RateLimitException, sleep_and_retry
from functools import lru_cache
import asyncio
import time

logger = getLogger()

router = APIRouter()

@lru_cache() # reuse connection to chromadb to avoid connection rate limiting on parallel requests
def get_weaviate(environment:str):
  # TODO: let environment specify file name?
  client = weaviate.Client(
    embedded_options=weaviate.embedded.EmbeddedOptions(),
  )
  logger.info("Connected to weaviate")

  create_schema(client)

  return client

#TODO: fix debugger so it doesn't always trip on this exception
def create_schema(client):
  schema = {
    "classes": [{
        "class": "TanaNode",
        "description": "Tana nodes",
        "vectorizer": "none",
        "properties": [
            {
                "name": "nodeId",
                "dataType": ["text"],
            },
            {
                "name": "supertags",
                "dataType": ["text"],
            },
            {
                "name": "content",
                "dataType": ["text"],
            }]
    }]
  }
  #TODO: figure out how to avoid this exception. Check schema exists first?
  try:
    client.schema.create(schema)
  except weaviate.exceptions.UnexpectedStatusCodeException:
    logger.info("Schema already exists")


def find_by_node_id(client, node_id):
  # first, look for the node already in the DB
  node_filter = {
    'path': ['nodeId'],
    'operator': 'Equal',
    'valueString': node_id
  }
  result = client.query.get("TanaNode", ["nodeId"]) \
    .with_additional('id') \
    .with_where(node_filter) \
    .do()

  node_ids = result.get('data').get('Get').get('TanaNode')
  return node_ids

# attempt to paralleize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()

@router.post("/weaviate/upsert", status_code=status.HTTP_204_NO_CONTENT)
async def weaviate_upsert(request: Request, req: WeaviateRequest):
  async with lock:
    start_time = time.time()
    logger.info(f'DO txid={request.headers["x-request-id"]}')
    embedding = get_embedding(req)
    vector = embedding[0]['embedding']

    client = get_weaviate(req.environment)

    metadata = {'nodeId': req.nodeId,
                'supertags': req.tags,
                'content': req.context}
    
    # @sleep_and_retry
    # @limits(calls=5, period=10)

    #TODO: ensure we don't double-add the same Tana Node. How?
    def do_upsert():
      node_ids = find_by_node_id(client, req.nodeId)

      if len(node_ids) > 1:
        # uh oh. dupes!
        logger.info(f"DUPLICATES Found {len(node_ids)} nodes with nodeId={req.nodeId}")
      
      if len(node_ids) > 0:
        # we have at least one node already. update one of them
        uuid = node_ids[0]['_additional']['id']
        client.data_object.update(uuid=uuid, data_object=metadata, class_name="TanaNode", vector=vector)
      else:
        # no node yet. create it
        client.data_object.create(data_object=metadata, class_name="TanaNode", vector=vector)

    do_upsert()
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f'DONE txid={request.headers["x-request-id"]} time={formatted_process_time}')
    return None

@router.post("/weaviate/delete", status_code=status.HTTP_204_NO_CONTENT)
def weaviate_delete(req: WeaviateRequest):  
  client = get_weaviate(req.environment)
  nodes = find_by_node_id(client, req.nodeId)
  for node in nodes:
    client.data_object.delete(uuid=node['_additional']['id'], class_name="TanaNode")
  return None


def get_tana_nodes_for_query(req: WeaviateRequest, send_text: Optional[bool] = False):  
  embedding = get_embedding(req)

  vector = {'vector': embedding[0]['embedding'] }

  supertags = str(req.tags).split()
  tag_filter = None
  if len(supertags) > 0:
    tag_filter = {
        'path': ['supertags'],
        'operator': 'ContainsAll',
        'valueStringArray': supertags
    }
    
  client = get_weaviate(req.environment)
  
  query = client.query.get("TanaNode", ["nodeId", "content", "supertags"]) \
    .with_near_vector(vector) \
    .with_additional('certainty') \
    .with_additional('distance') \
    .with_limit(req.top)
  
  if tag_filter:
    query = query.with_where(tag_filter) \
  
  result = query.do()
  
  closest = result.get('data').get('Get').get('TanaNode')

  def threshold_function(match):
    return match['_additional']['certainty'] > req.score
  
  best = filter(threshold_function, closest)
  ids = ["[[^"+match['nodeId']+"]]" for match in best]
  
  if not send_text:
    return ids
  else:
    # iterator exhausted. do it again
    best = filter(threshold_function, closest)
    docs = [ {'sources': '[[^'+match['nodeId']+']]', 'answer': match['content']} for match in best]
    return docs

@router.post("/weaviate/query", response_class=HTMLResponse)
def weaviate_query(req: WeaviateRequest, send_text: Optional[bool] = False):  
  ids = get_tana_nodes_for_query(req)
  if len(ids) == 0:
    tana_result = "No sufficiently well-scored results"
  else:
    tana_result = ''.join(["- "+str(id)+"\n" for id in ids])
  return tana_result


@router.post("/weaviate/purge", status_code=status.HTTP_204_NO_CONTENT)
def weaviate_purge(req: WeaviateRequest):
  client = get_weaviate(req.environment)
  client.schema.delete_class("TanaNode")
  create_schema(client)
  return None