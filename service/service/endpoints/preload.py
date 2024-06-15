import asyncio
import json
import os
import tempfile
from logging import getLogger

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from typing import List, Tuple
from openai import OpenAI

# This is here to satisfy runtime import needs 
# that pyinstaller appears to miss


from service.dependencies import (
    OPENAI_EMBEDDING_MODEL,
    ChromaRequest,
    capture_logs,
    get_embeddings,
    nextflake,
)

from service.endpoints.chroma import EmbeddableNode, chroma_upsert, get_collection, prepare_node_for_embedding
from service.endpoints.topics import TanaTopicNode, extract_topics
from service.tana_types import TanaDump
from service.json2tana import json_to_tana

logger = getLogger()

router = APIRouter()

minutes = 1000 * 60

BATCH_SIZE = 500

# TODO: Add header support throughout so we can pass Tana API key and OpenAPI Key as headers
# NOTE: we already have this in the main.py middleware wrapper, but it would be better
# to do it here for OpenAPI spec purposes.
# x_tana_api_token: Annotated[str | None, Header()] = None
# x_openai_api_key: Annotated[str | None, Header()] = None


# reduce our list of nodes to embed by testing hashes of the nodes
def reduce_embeddings(nodes:List[EmbeddableNode]) -> Tuple[List[EmbeddableNode], dict]:  
  
  collection = get_collection()
  lookup = {node.id: node for node in nodes}
  removes = {}
  deletes = {}
  
  # TODO: narrow this query to nodes from the given workspace 
  # (requires we track workspace root node somehow in metadata or collection name)
  query_response = collection.get()

  if query_response:
    # the result from ChromaDB is kinda strange. Instead of an array of objects
    # # it's four distinct arrays of object properties. Very odd interface.

    for node_id, metadata in zip(
            query_response["ids"],
            query_response["metadatas"], # type: ignore
        ):
      
      # is this node in the new set?
      if node_id in lookup:
        the_node = lookup[node_id]
        if metadata and the_node.hash == metadata["hash"]:
          # remove this node from the results
          removes[node_id] = the_node
      else:
        deletes[node_id] = True

  # remove the nodes that are already in the DB
  results = [node for node in nodes if node.id not in removes]
  return results, deletes

async def load_chromadb_from_topics(topics:List[TanaTopicNode], model:str, observe=False):
  '''Load the topic index from the topic array directly.'''

  logger.info('Building ChromaDB vectors from nodes')

  references = {}

  index_nodes = []
  # loop through all the topics and create an EmbeddableNode for each
  for topic in topics:
    tags = ' '.join(topic.tags)
    text = topic.content[0].content + ' ' + tags + '\n'

    # find all of the fields and make them part of the topic context
    field_text=''
    for content in topic.content[1:]:
      if content.is_field:
        # TODO HACK if content starts with Attendees:: we want to skip it
        if content.field_name == 'Attendees':
          continue

        field_text += content.content + '\n'

    text += field_text
    index_nodes.append(prepare_node_for_embedding(node_id=topic.id,
                                                  content_id=topic.id,
                                                  topic_id=topic.id, 
                                                  name=topic.name,
                                                  tags=tags,
                                                  context=text))
    
    # now embed all the child content nodes, pointing back at the parent topic
    for content in topic.content[1:]:
      if content.is_field:
        continue

      # build a more detailed tree of nodes
      # references are .. hard. We make a new synthetic node here
      # since references will be embedded themselves as topics
      # and we just want to know that the content of the reference node
      # is relevant to the current topic we are embedding.
      topic_id = topic.id
      content_id = content.id
      if content.is_reference:
        #node_id = nextflake() # this means we will leak fake reference nodes over time...
        node_id = content.id + '__' + topic.id # type: ignore
        if node_id in references:
          # we already created this node_topic ref, so skip
          continue
        references[node_id] = content
      else:
        node_id = content.id

      new_node = prepare_node_for_embedding(node_id=node_id,
                                            content_id=content_id,
                                            topic_id= topic_id, 
                                            name=content.content,
                                            tags='', # TODO: add tags to content nodes
                                            context=content.content + '\n')
      index_nodes.append(new_node)

  logger.info(f'Gathered {len(index_nodes)} nodes for embedding')

  index_nodes, deletes = reduce_embeddings(index_nodes)

  logger.info(f'Reduced to {len(index_nodes)} nodes for embedding')
  # TODO: delete dead nodes, but NOT until we have properly implemented multi-workspace support
  logger.info(f'Identified {len(deletes)} nodes for removal')

  collection = get_collection()

  counter = 0
  # batch process the nodes, generating embeddings
  for i in range(0, len(index_nodes), BATCH_SIZE):
    batch = index_nodes[i:i+BATCH_SIZE]
    nodes = [node.text for node in batch]

    counter = counter + 1
    # somewhere in this batch, we have a very long text that will cause the OpenAI API to fail
    biggest=0
    for node in batch:
      if len(node.text) > biggest:
        biggest = len(node.text)
        big_node = node

    logger.info(f'Batch {counter} Node {big_node.id} has {len(big_node.text)} characters')

    embeddings = get_embeddings(nodes, model=model)
    for j, node in enumerate(batch):    
      node.embedding = embeddings[j].embedding

    # upsert the batch into ChromaDB
    # @sleep_and_retry
    # @limits(calls=5, period=10)
    def do_upsert():
      collection.upsert(
        ids=[node.id for node in batch],
        embeddings=[node.embedding for node in batch], # type: ignore
        # we only embed the name of the node (primary content of the node)
        documents=[node.name for node in batch],
        metadatas=[node.metadata for node in batch], #type: ignore
      )
    
    do_upsert()
    
  logger.info("ChromaDB populated and ready")
  return index_nodes


# attempt to parallelize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()

# Note: accepts ?model= query param
@router.post("/chroma/preload", tags=["preload"])
async def chroma_preload(request: Request, tana_dump:TanaDump, model:str=OPENAI_EMBEDDING_MODEL):
  '''Accepts a Tana dump JSON payload and builds the index from it.
  Uses the topic extraction code from the topics endpoint to build
  an object tree in memory, then loads that into ChromaDB via LLamaIndex.
  
  Returns a list of log messages from the process.
  '''
  async with lock:
    messages = []
    async with capture_logs(logger) as logs:
      topics = await extract_topics(tana_dump, 'TANA') # type: ignore
      logger.info('Extracted topics from Tana dump')

      # DEBUG save output to a temporary file
      with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'topics.json')
        logger.info(f'Saving topics to {path}')
        # use path
        with open(path, "w") as f:
          json_result = jsonable_encoder(topics)
          f.write(json.dumps(json_result))
        
        logger.info('Loading index ...')
      # logger.info(f'Deleted temp file {path}')

      # load directly from in-memory representation

      # extract the tag schema from the dump
      # tags_schema = tag_schema_from_dump(tana_dump)

      # extract the field schema from the dump
      # fields_schema = field_schema_from_dump(tana_dump)

      # load the vector DB from the topics
      await load_chromadb_from_topics(topics, model=model)
    
      messages = logs.getvalue()
    return messages

