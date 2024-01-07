import asyncio
import json
import os
import tempfile
import time
from functools import lru_cache
from logging import getLogger
from pathlib import Path

from fastapi import APIRouter, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from pydantic.json import pydantic_encoder
from typing import Optional

# This is here to satisfy runtime import needs 
# that pyinstaller appears to miss
from transformers import AutoModel, AutoTokenizer
import tqdm

from llama_index import (
    StorageContext,
    VectorStoreIndex,
    ServiceContext,
    download_loader,
)
from llama_index.llms import Ollama
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from snowflake import SnowflakeGenerator

from service.dependencies import (
    TANA_TYPE,
    MistralAsk,
    MistralRequest,
    get_embedding,
)
from service.endpoints.topics import TanaDocument, extract_topics
from service.tana_types import TanaDump

logger = getLogger()
snowflakes = SnowflakeGenerator(42)

router = APIRouter()

minutes = 1000 * 60

# TODO: Add header support throughout so we can pass Tana API key and OpenAPI Key as headers
# NOTE: we already have this in the main.py middleware wrapper, but it would be better
# to do it here for OpenAPI purposes.
# x_tana_api_token: Annotated[str | None, Header()] = None
# x_openai_api_key: Annotated[str | None, Header()] = None

db_path = os.path.join(Path.home(), '.qdrant.db')
@lru_cache() # reuse connection to qdrant
def get_qdrant():
  # re-initialize the vector store
  client = QdrantClient(
      path=db_path
  )
  vector_store = QdrantVectorStore(client=client, collection_name="tana")
  logger.info("Mistral (qdrant) vector store ready")
  return vector_store
  
@lru_cache() # reuse connection to ollama
def get_mistral():
  vector_store = get_qdrant()
  service_context = get_llm()

  # load the index from the vector store
  index = VectorStoreIndex.from_vector_store(vector_store=vector_store, service_context=service_context) # type: ignore
  logger.info("Connected to Mistral")
  return index

# get the LLM 
@lru_cache() # reuse connection to ollama
def get_llm():
  llm = Ollama(model="mistral", request_timeout=(5 * minutes))
  service_context = ServiceContext.from_defaults(llm=llm,embed_model="local")
  logger.info("Mistral (ollama) service context ready")
  return service_context

def load_topic_index(filename:str):
  # load the JSON off disk
  json_reader = download_loader("JSONReader")
  loader = json_reader()
  documents = loader.load_data(Path(filename))

  vector_store = get_qdrant()

  storage_context = StorageContext.from_defaults(vector_store=vector_store)
  logger.info("Mistral (qdrant) storage context ready")

  # initialize the LLM
  service_context = get_llm()

  # create the index; this will embed the documents and store them in the vector store
  #TODO: ensure we are upserting by topic id, otherwise we will have duplicates
  # and will have to drop the index first
  index = VectorStoreIndex.from_documents(documents, service_context=service_context, storage_context=storage_context)
  logger.info("Mistral index populated and ready")
  return index
 
 
# attempt to paralleize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()

@router.post("/mistral/preload", status_code=status.HTTP_204_NO_CONTENT, tags=["Mistral"])
async def mistral_preload(request: Request,tana_dump:TanaDump):
  async with lock:
    start_time = time.time()
    logger.info(f'DO txid={request.headers["x-request-id"]}')

    result = await extract_topics(tana_dump) # type: ignore
    logger.info('Extracted topics from Tana dump')

    # save output to a temporary file
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'topics.json')
        # use path
        with open(path, "w") as f:
            json_result = jsonable_encoder(result)
            f.write(json.dumps(json_result))
        
        load_topic_index(path)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f'DONE txid={request.headers["x-request-id"]} time={formatted_process_time}')
    #TODO: consider returning some kind of completion confirmation payload with statidtics
    return None


@router.post("/mistral/ask", response_class=HTMLResponse, tags=["Mistral"])
def mistral_ask(req: MistralAsk):
  index = get_mistral()
  query_engine = index.as_query_engine(similarity_top_k=20, stream=False, timeout=1000*60*5)
  logger.info(f'Querying Mistral with {req.query}')
  response = query_engine.query(req.query)
  return str(response)


# @router.post("/mistral/upsert", status_code=status.HTTP_204_NO_CONTENT, tags=["Mistral"])
# async def mistral_upsert(request: Request, req: MistralRequest):
#   async with lock:
#     start_time = time.time()
#     logger.info(f'DO txid={request.headers["x-request-id"]}')

#     metadata = {'category': TANA_TYPE,
#                   'supertag': req.tags,
#                   'title': req.name,
#                   'text': req.context}
    
#     # TODO: implement qrant upsert
#     # @sleep_and_retry
#     # @limits(calls=5, period=10)
#     def do_upsert():
#       pass
      
#     do_upsert()
#     process_time = (time.time() - start_time) * 1000
#     formatted_process_time = '{0:.2f}'.format(process_time)
#     logger.info(f'DONE txid={request.headers["x-request-id"]} time={formatted_process_time}')
#     return None

# @router.post("/mistral/delete", status_code=status.HTTP_204_NO_CONTENT, tags=["Mistral"])
# def mistral_delete(req: MistralRequest):  
#   index = get_mistral()
#   index.delete(ids=[req.nodeId])
#   return None


# def get_tana_nodes_for_query(req: MistralRequest):  
#   embedding = get_embedding(req)

#   vector = embedding[0]['embedding']

#   supertags = str(req.tags).split()
#   tag_filter = None
#   if len(supertags) > 0:
#     tag_filter = {
#       'supertag': { "$in": supertags }    
#     }

#   index = get_mistral()

#   query_response = index.query(query_embeddings=vector,
#     n_results=req.top, # type: ignore
#     where=tag_filter
#   )

#   # the result from ChromaDB is kinda strange. Instead of an array of objects
#   # # it's four distinct arrays of object properties. Very odd interface.
#   best = []
#   texts = []
#   index = 0
#   for node_id in query_response['ids'][0]:
#     distance = (1.0 - query_response['distances'][0][index])
#     metadata = query_response['metadatas'][0][index]
#     if 'title' in metadata:
#       first_line = metadata['title']
#     else:
#       first_line = metadata['text'].partition('\n')[0]
#     if node_id != req.nodeId:
#       logger.info(f"Found node {node_id} with score {distance}. Title is {first_line}")
#       if distance > req.score: # type: ignore
#         best.append(node_id)
#         texts.append(metadata['text'])
#     index += 1


#   ids = ["[[^"+match+"]]" for match in best]  
#   return ids, texts

# @router.post("/mistral/query", response_class=HTMLResponse, tags=["Mistral"])
# def mistral_query(req: MistralRequest, send_text: Optional[bool] = False):  
#   ids, texts = get_tana_nodes_for_query(req)
#   if len(ids) == 0:
#     tana_result = "No sufficiently well-scored results"
#   else:
#     if send_text:
#       tana_result = ''.join([str(text)+"\n" for text in texts])
#     else:
#       tana_result = ''.join(["- "+str(id)+"\n" for id in ids])
#   return tana_result

# @router.post("/mistral/query_text", response_class=HTMLResponse, tags=["Mistral"])
# def mistral_query_text(req: MistralRequest):  
#   return mistral_query(req, True)


# @router.post("/mistral/purge", status_code=status.HTTP_204_NO_CONTENT, tags=["Mistral"])
# def mistral_purge(req: MistralRequest):
#   index = get_mistral()
#   index.delete()
#   return None

