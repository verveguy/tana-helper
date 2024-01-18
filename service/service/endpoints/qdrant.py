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
from typing import List

# This is here to satisfy runtime import needs 
# that pyinstaller appears to miss

from llama_index.node_parser import SentenceSplitter
from llama_index.schema import TextNode, NodeRelationship, RelatedNodeInfo
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from llama_index.embeddings import OpenAIEmbedding
from llama_index.llms import Ollama, OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index import VectorStoreIndex, Document, StorageContext, ServiceContext, download_loader
from llama_index.tools import QueryEngineTool, ToolMetadata
from llama_index.query_engine import SubQuestionQueryEngine
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from llama_index import ServiceContext

from qdrant_client import QdrantClient

from snowflake import SnowflakeGenerator

from service.dependencies import TANA_NODE, TANA_TEXT
from service.endpoints.chroma import get_collection

from service.endpoints.topics import TanaDocument, extract_topics
from service.tana_types import TanaDump

logger = getLogger()
snowflakes = SnowflakeGenerator(42)

router = APIRouter()

minutes = 1000 * 60

# TODO: finish this work on qdrant vector store in the fashion of chroma store

# TODO: Add header support throughout so we can pass Tana API key and OpenAPI Key as headers
# NOTE: we already have this in the main.py middleware wrapper, but it would be better
# to do it here for OpenAPI spec purposes.
# x_tana_api_token: Annotated[str | None, Header()] = None
# x_openai_api_key: Annotated[str | None, Header()] = None


db_path = os.path.join(Path.home(), '.qdrant.db')
@lru_cache() # reuse connection to qdrant
def get_qdrant_vector_store():
  # re-initialize the vector store
  client = QdrantClient(
      path=db_path
  )
  vector_store = QdrantVectorStore(client=client, collection_name="tana")
  logger.info("Mistral (qdrant) vector store ready")
  return vector_store

# use this to ease switching backends
def get_vector_store():
  return get_qdrant_vector_store()

# get the LLM 
@lru_cache() # reuse connection to ollama
def get_llm(debug=True):
  #llm = Ollama(model="mistral", request_timeout=(5 * minutes))
  llm = OpenAI(model="gpt-4-1106-preview", request_timeout=(5 * minutes))
  embed_model = OpenAIEmbedding(embed_batch_size=500)
  callback_manager = None
  if debug:
    llama_debug = LlamaDebugHandler(print_trace_on_end=True)
    callback_manager = CallbackManager([llama_debug])
  service_context = ServiceContext.from_defaults(llm=llm,
                                                 embed_model=embed_model, # or 'local'
                                                 callback_manager=callback_manager
                                                )
  logger.info("Mistral (ollama) service context ready")
  return service_context, llm

@lru_cache() # reuse connection to llama_index
def get_index():
  vector_store = get_vector_store()
  service_context, llm = get_llm()

  # load the index from the vector store
  index = VectorStoreIndex.from_vector_store(vector_store=vector_store, service_context=service_context) # type: ignore
  logger.info("Connected to Mistral")
  return index, service_context, vector_store, llm


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

