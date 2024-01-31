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
from typing import List, Dict, Any
from pydantic import Field, validator

# This is here to satisfy runtime import needs 
# that pyinstaller appears to miss

from llama_index.node_parser import SentenceSplitter
from llama_index.schema import TextNode, NodeRelationship, RelatedNodeInfo, MetadataMode
from llama_index.callbacks import CallbackManager, LlamaDebugHandler, OpenInferenceCallbackHandler
from llama_index.embeddings import OpenAIEmbedding, OllamaEmbedding
from llama_index.indices.query.query_transform import HyDEQueryTransform
from llama_index.query_pipeline import QueryPipeline
from llama_index.llms import OpenAI, Ollama
from llama_index.llms.base import BaseLLM
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index import LLMPredictor, PromptTemplate, VectorStoreIndex, Document, StorageContext, ServiceContext, download_loader
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from llama_index.embeddings import OpenAIEmbedding
from llama_index.llms import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index import VectorStoreIndex, Document, StorageContext, ServiceContext, download_loader
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from llama_index import ServiceContext
from llama_index.postprocessor import CohereRerank
from llama_index.response_synthesizers import TreeSummarize
from llama_index.postprocessor import PrevNextNodePostprocessor, LLMRerank
from llama_index.storage.docstore import SimpleDocumentStore
from llama_index.query_pipeline import CustomQueryComponent, InputKeys, OutputKeys
from llama_index.postprocessor.types import BaseNodePostprocessor
from llama_index.vector_stores.types import BasePydanticVectorStore

from llama_index.indices.vector_store.retrievers import VectorIndexAutoRetriever, VectorIndexRetriever

from llama_index.vector_stores.types import MetadataInfo, VectorStoreInfo

from snowflake import SnowflakeGenerator

from service.dependencies import (
    TANA_NODE,
    TANA_TEXT,
    LlamaindexAsk,
    TanaNodeMetadata,
)
from service.endpoints.chroma import get_collection, get_tana_nodes_by_id

from service.endpoints.topics import TanaDocument, extract_topics, is_reference_content, tana_node_ids_from_text
from service.llamaindex import DecomposeQueryWithNodeContext, WidenNodeWindowPostProcessor, create_index, get_index
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


# enrich our retriever with knowledge of our metadata
def get_auto_retriever(index:VectorStoreIndex):
  vector_store_info = VectorStoreInfo(
    content_info="My Tana Notebook. Comprises many Tana nodes with text and metadata fields.",
    metadata_info=[
        MetadataInfo(
            name="category",
            type="str",
            description=(
                "One of TANA_NODE or TANA_TEXT\n"
                "TANA_NODE means that this is a top-level topic in my Tana notebook\n"
                "TANA_TEXT means this is detailed information as part of a topic, identfied by topic_id metadata.\n"
                "Do NOT use category to query the index. Only use category to enrich your understanding of the result.\n"
                "DO NOT reference category in your responses.\n"
            ),
        ),
        MetadataInfo(
            name="topic_id",
            type="str",
            description=(
                "Identifies the Tana Notebook Node that this text is part of. Should be used as a reference to the notebook entry.\n"
                "Only use topic_id to query the index when you want a single specific node by reference.\n"
                "You can use topic_id when referencing a Tana Notebook Node in your responses.\n"
            ),
        ),
        MetadataInfo(
            name="tana_id",
            type="str",
            description=(
                "The Tana Notebook Node for this piece of text. Should be used a reference to the notebook entry.\n"
                "Only use topic_id to query the index when you want a single specific node by reference.\n"
                "You can use tana_id when referencing a Tana Notebook Node in your responses.\n"
            ),
        ),
        MetadataInfo(
            name="supertag",
            type="str",
            description=(
                "One or more optional GENERAL semantic ontology tags for this Tana Notebook Node.\n"
                "Delimited by spaces (NOT a LIST. Do not use IN operator to test membership)\n"
                "Example: \n"
                "{ supertag:  #task #topic #person #meeting }\n"
                "Do NOT use supertags to query the index. Only use supertags to enrich your understanding of the result.\n"
            ),
        ),
      ],
  )

  # THIS doesn't work at all well with GPT 2
  # retriever = VectorIndexAutoRetriever(
  #     index, 
  #     vector_store_info=vector_store_info, 
  #     similarity_top_k=10
  # )

  retriever = VectorIndexRetriever(index=index, similarity_top_k=10)
  return retriever



# TODO: migrate chroma query/ask feature over. This includes tag filtering
@router.post("/llamaindex/ask", response_class=HTMLResponse, tags=["LlamaIndex"])
def llama_ask(req: LlamaindexAsk, model:str):
  '''Ask a question of Llamaindex and return the top results.'''

  (index, service_context, storage_context, llm) = get_index(model, observe=True)

  vector_store = get_vector_store()

  response = index.as_query_engine().query(req.query)
  return str(response)


summary_tmpl = PromptTemplate(
    "You are an expert Q&A system that is trusted around the world.\n"
    "TASK\n"
    "Summarize the following CONTEXT in order to best answer the QUERY.\n"
    "Answer the QUERY using the provided CONTEXT information, and not prior knowledge.\n"
    "Some rules to follow:\n"
    "1. Avoid statements like 'Based on the context, ...' or 'The context information ...' or anything along those lines.\n"
    "2. The CONTEXT contais references to many Tana Notebook Nodes. Nodes have both metadata and text content\n"
    "3. Whenever your summary needs to reference Tana Notebook Nodes from the CONTEXT, use proper Tana node reference format as follows:\n"
    "  the characters '[[' + '^' + tana_id metadata and then the characters ']]'.\n"
    "  E.g. to reference the Tana context node titled 'Recipe for making icecream' with tana_id: xghysd76 use this format:\n"
    "    [[^xghysd76]]\n"
    "5. Try to avoid making many redundant references to the same Tana node in your summary. Use footnote style if you really need to do this.\n"
    "\n"
    "QUERY: {query_str}\n"
    "-----\n"
    "CONTEXT:\n"
    "{context_str}\n"
    "END_CONTEXT\n"
    "-----\n"
  )

#TODO: Move model out of POST body and into query params perhaps?
@router.post("/llamaindex/research", response_class=HTMLResponse, tags=["LlamaIndex"])
def llama_ask_custom_pipeline(req: LlamaindexAsk, model:str):
  '''Research a question using Llamaindex and return the top results.'''

  (index, service_context, storage_context, llm) = get_index(model, observe=True)

  logger.info(f'Researching LLamaindex with {req.query}')

  # first, build up a set of research questions
  decompose_transform = DecomposeQueryWithNodeContext(llm=llm)
  p1 = QueryPipeline(chain=[decompose_transform])
  questions = p1.run(query=req.query)
  
 
  retriever = get_auto_retriever(index)
  # and preprocess the result nodes to make use of next/previous
  prevnext = WidenNodeWindowPostProcessor(storage_context=storage_context, num_nodes=5, mode="both")
  summarizer = TreeSummarize(summary_template=summary_tmpl, service_context=service_context)

  # for each question, do a fetch against Chroma to find potentially relevant nodes
  results = []
  for question in questions:
    if question == '':
      continue

    logger.info(f'Question: {question}')
    # use our metadata aware auto-retriever to fetch from Chroma
    q1 = QueryPipeline(chain=[retriever, prevnext])
    nodes = q1.run(input=question)
    # nodes = retriever.retrieve(question)
    # logger.info(f'Nodes:\n{nodes}')
    research = '\n'.join([node.get_content(metadata_mode=MetadataMode.LLM) for node in nodes])
    logger.info(f'Nodes:\n{research}')

    # tailor the summarizer prompt
    sum_result = summarizer.as_query_component().run_component(nodes=nodes, query_str=question)
    summary = sum_result['output'].response
    logger.info(f'Summary:\n{summary}')

    result = {'question': question,
              'answers': nodes,
              'summary': summary}
    results.append(result)

  # now build up the context from the result nodes
  context = []
  for result in results:
    question = result['question']
    answer = result['answers']
    summary = result['summary']
    context.append(f'QUESTION: {question}\n')

    #context.append('RESEARCH:\n')
    # TODO: instead of dumping all nodes into the primary context
    # we should prepare an answer to each question and then use that
    # node:TextNode
    # for node in answer:
    #   context.append(node.get_content(metadata_mode=MetadataMode.LLM)+'\n')
    
    context.append('ANSWER:\n')
    context.append(summary+'\n')

    context.append('\n')

  # now combine all that research 
  prompt_tmpl = PromptTemplate(
    "You are an expert Q&A system that is trusted around the world.\n"
    "Always answer the question using the provided context information, and not prior knowledge.\n"
    "Some rules to follow:\n"
    "1. Avoid statements like 'Based on the context, ...' or 'The context information ...' or anything along those lines.\n"
    "2. You will be given CONTEXT information in the form of one or more related QUESTIONS and the ANSWERS to those questions.\n"
    "3. For each ANSWER, there may be many Tana Notebook Nodes. Nodes have both metadata and text content\n"
    "4. Whenever your response needs to reference Tana Notebook Nodes from the context, use proper Tana node reference format as follows:\n"
    "  the characters '[[' + '^' + tana_id metadata and then the characters ']]'.\n"
    "  E.g. to reference the Tana context node titled 'Recipe for making icecream' with tana_id: xghysd76 use this format:\n"
    "    [[^xghysd76]]\n"
    "5. Try to avoid making many redundant references to the same Tana node in your response. Use footnote style if you really need to do this.\n"
    "\n"
    "QUERY: {query}\n"
    "-----\n"
    "CONTEXT:\n"
    "{context}\n"
    "END_CONTEXT\n"
    "-----\n"
  )


  # TODO: this is broken - seems a vector store is not enough
  # and the persistent docstore isn't loading in parallel
  # (unclear why)
  # prevnext = PrevNextNodePostprocessor(
  #   docstore=storage_context.docstore, 
  #   num_nodes=5,  # number of nodes to fetch when looking forawrds or backwards
  #   mode="both",  # can be either 'next', 'previous', or 'both'
  # )

  p2 = QueryPipeline(chain=[prompt_tmpl, llm])
  response = p2.run(query=req.query, context='\n'.join(context))
  return response.message.content


def load_index_from_topics(topics:List[TanaDocument], model:str, observe=False):
  '''Load the topic index from the topic array directly.'''

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
    # TODO: use actual tana node id here perhaps?
    previous_text_node = None
    if len(topic.content) > 30:
      logger.warning(f'Large topic {topic.id} with {len(topic.content)} children')

    # process all the child content records...
    for (content_id, is_ref, tana_element) in topic.content[1:]:
    
      content_metadata = TanaNodeMetadata(
        category=TANA_TEXT,
        # use the parent doc's metadata...??
        title=topic.name,
        topic_id=topic.id,
        tana_id=content_id,
        # 'doc_id': document_node.node_id,
        # 'supertag': ' '.join(['#' + tag for tag in topic.tags]),
        # text gets added below...
      )
      
      # wire up the tana_node as an index_node
      index_tana_node = TextNode(text=tana_node)
      # we copy all the metadata to associate this strongly with the parent document
      # TODO: check if this is strictly required
      index_tana_node.metadata = document.metadata
      # reset the category since text nodes aren't actual Tana nodes (I mean, they are, but we don't link them that way)
      index_tana_node.metadata['category'] = TANA_TEXT
      index_tana_node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=document.node_id)

      current_text_node.metadata = content_metadata.model_dump()

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

  logger.info(f'Gathered {len(index_nodes)} tana nodes')
  logger.info("Preparing storage context")

  index = create_index(model, observe, index_nodes)
  logger.info("Llamaindex populated and ready")
  return index


# attempt to paralleize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()

# Note: accepts ?model= query param
@router.post("/llamaindex/preload", status_code=status.HTTP_204_NO_CONTENT, tags=["LlamaIndex"])
async def llama_preload(request: Request, tana_dump:TanaDump, model:str="openai"):
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
    load_index_from_topics(result, model=model)
  
    # logger.info(f'Deleted temp file {path}')

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

