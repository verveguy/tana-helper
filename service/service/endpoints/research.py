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
from llama_index.indices.query.query_transform.base import DecomposeQueryTransform
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

  # THIS doesn't work at all well with GPT 3
  # and only works sometimes with GPT4. Problem is that it becomes fixated on the 
  # use of metadata to filter results, overly constraining relevance.
  # retriever = VectorIndexAutoRetriever(
  #     index, 
  #     vector_store_info=vector_store_info, 
  #     similarity_top_k=10
  # )

  retriever = VectorIndexRetriever(index=index, similarity_top_k=10)
  return retriever


@router.post("/llamaindex/ask", response_class=HTMLResponse, tags=["research"])
def llamaindex_ask(req: LlamaindexAsk, model:str):
  '''Ask a question of the Llamaindex and return the top results
  '''

  (index, service_context, vector_store, llm) = get_index(model=model)

  query_engine=index.as_query_engine(similarity_top_k=20, stream=False)

  logger.info(f'Querying LLamaindex with {req.query}')
  response = query_engine.query(req.query)
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
@router.post("/llamaindex/research", response_class=HTMLResponse, tags=["research"])
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

  p2 = QueryPipeline(chain=[prompt_tmpl, llm])
  response = p2.run(query=req.query, context='\n'.join(context))
  return response.message.content

# attempt to paralleize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()

