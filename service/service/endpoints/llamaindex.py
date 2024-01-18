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
from llama_index.llms import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index import VectorStoreIndex, Document, StorageContext, ServiceContext, download_loader
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from llama_index import ServiceContext

from snowflake import SnowflakeGenerator

from service.dependencies import (
    TANA_NODE,
    TANA_TEXT,
    ChromaStoreRequest,
    MistralAsk,
)
from service.endpoints.chroma import get_collection

from service.endpoints.topics import TanaDocument, extract_topics
from service.tana_types import TanaDump

logger = getLogger()
snowflakes = SnowflakeGenerator(42)

router = APIRouter()

minutes = 1000 * 60

# TODO: Add header support throughout so we can pass Tana API key and OpenAPI Key as headers
# NOTE: we already have this in the main.py middleware wrapper, but it would be better
# to do it here for OpenAPI spec purposes.
# x_tana_api_token: Annotated[str | None, Header()] = None
# x_openai_api_key: Annotated[str | None, Header()] = None


@lru_cache() # reuse connection to chroma
def get_chroma_vector_store():
  chroma_collection = get_collection(ChromaStoreRequest())
  vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
  logger.info("Llamaindex (chroma) vector store ready")
  return vector_store

# use this to ease switching backends
def get_vector_store():
  return get_chroma_vector_store()

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
  logger.info("Llamaindex (openai) service context ready")
  return service_context, llm

@lru_cache() # reuse connection to llama_index
def get_index():
  vector_store = get_vector_store()
  service_context, llm = get_llm()

  # load the index from the vector store
  index = VectorStoreIndex.from_vector_store(vector_store=vector_store, service_context=service_context) # type: ignore
  logger.info("Connected to Llamaindex")
  return index, service_context, vector_store, llm



def load_index_from_file(filename:str):
  '''Load the topic index from a temporary JSON file

  The topic index is built from walking the Tana dump and extracting
  all of the topics. This is a very expensive operation, so we only
  want to do it once. This function loads the index from a temporary
  file that was created by the preload endpoint.
  '''

  # load the JSON off disk as a set of documents
  # TODO: change this to load topic fragments with 
  # parent nodes as discrete chunks and also do sentence level embedding
  json_reader = download_loader("JSONReader")
  loader = json_reader()
  documents = loader.load_data(Path(filename))

  vector_store = get_vector_store()

  # create a storage context in order to create a new index
  storage_context = StorageContext.from_defaults(vector_store=vector_store)
  logger.info("Mistral storage context ready")

  # initialize the LLM
  (service_context, llm) = get_llm()

  # create the index; this will embed the documents and store them in the vector store
  #TODO: ensure we are upserting by topic id, otherwise we will have duplicates
  # and will have to drop the index first
  index = VectorStoreIndex.from_documents(documents, service_context=service_context, storage_context=storage_context)
  logger.info("Mistral index populated and ready")
  return index
 

def load_index_from_topics(topics:List[TanaDocument]):
  '''Load the topic index from the topic array directly.
  '''

  # TODO: change this to load topic fragments with 
  # parent nodes as discrete chunks and also do sentence level embedding

  vector_store = get_vector_store()

  # create a storage context in order to create a new index
  storage_context = StorageContext.from_defaults(vector_store=vector_store)
  logger.info("Mistral storage context ready")

  # initialize the LLM
  (service_context, llm) = get_llm()

  parser = SentenceSplitter()

  index_nodes = []
  # loop through all the topics and create a Document for each
  for topic in topics:
    metadata = {'category': TANA_NODE,
                'supertag': ' '.join(topic.tags),
                'title': topic.name,
                'text': topic.content[0], # first line only
                'tana_id': topic.id,
      }

    # what other props do we need to create?
    document = Document(id_=topic.id, text=topic.name) # type: ignore
    document.metadata = metadata

    # make a note of the document in our nodes list
    index_nodes.append(document)

    # now iterate all the remaining topic.content and create a node for each
    # TODO: make these tana_nodes richer structurally
    # TODO: use actual tana node id here
    for tana_node in topic.content:
      
      # wire up the tana_node as an index_node
      index_tana_node = TextNode(text=tana_node)
      # we copy all the metadata to associate this strongly with the parent document
      # TODO: check if this is strictly required
      index_tana_node.metadata = document.metadata
      # reset the category since text nodes aren't actual Tana nodes (I mean, they are, but we don't link them that way)
      index_tana_node.metadata['category'] = TANA_TEXT
      index_tana_node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=document.node_id)

      index_nodes.append(index_tana_node)

      # now split the sentences as make them children of the index_tana_node
      # sentences = parser.split_text(tana_node)
      # last_sentence = None
      # for sentence in sentences:
      #   sentence_node = TextNode(text=sentence)
      #   sentence_node.metadata = document.metadata

      #   # wire up all the relationships (useful?)
      #   sentence_node.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(node_id=index_tana_node.node_id)
      #   sentence_node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=document.node_id)
      #   if last_sentence:
      #     sentence_node.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(node_id=last_sentence.node_id)
      #     last_sentence.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id=sentence_node.node_id)
          
      #   last_sentence = sentence_node
      #   # replicate metadata (seems excessive...?)                         

      #   # TODO: what else can we add to the sentence node?
      #   index_nodes.append(sentence_node)

  # create the index; this will embed the documents and nodes and store them in the vector store
  #TODO: ensure we are upserting by topic id, otherwise we will have duplicates
  # and will have to drop the index first
  index = VectorStoreIndex(index_nodes, service_context=service_context, storage_context=storage_context)
  logger.info("Mistral index populated and ready")
  return index


# attempt to paralleize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()

@router.post("/llamaindex/preload", status_code=status.HTTP_204_NO_CONTENT, tags=["LlamaIndex"])
async def mistral_preload(request: Request,tana_dump:TanaDump):
  '''Accepts a Tana dump JSON payload and builds the Mistral index from it
  Uses the topic extraction code from the topics endpoint to build
  a temporary JSON file, then loads that into the index.
  '''
  async with lock:
    start_time = time.time()
    logger.info(f'DO txid={request.headers["x-request-id"]}')

    result = await extract_topics(tana_dump) # type: ignore
    logger.info('Extracted topics from Tana dump')

    # save output to a temporary file
    with tempfile.TemporaryDirectory() as tmp:
      path = os.path.join(tmp, 'topics.json')
      logger.info(f'Saving topics to {path}')
      # use path
      with open(path, "w") as f:
          json_result = jsonable_encoder(result)
          f.write(json.dumps(json_result))
      
      logger.info('Loading index ...')
      # don't use file anymore...
      # load_index_from_file(path)
      # load directly from in-memory representation
      load_index_from_topics(result)
    
    logger.info(f'Deleted temp file {path}')

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f'DONE txid={request.headers["x-request-id"]} time={formatted_process_time}')
    #TODO: consider returning some kind of completion confirmation payload with statidtics
    return None


@router.post("/llamaindex/ask", response_class=HTMLResponse, tags=["LlamaIndex"])
def mistral_ask(req: MistralAsk):
  '''Ask a question of the Mistral index and return the top results
  '''

  (index, service_context, vector_store, llm) = get_index()

  query_engine=index.as_query_engine(similarity_top_k=20, stream=False)

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

