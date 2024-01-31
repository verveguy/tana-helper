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

