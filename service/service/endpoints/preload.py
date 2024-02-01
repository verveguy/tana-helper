import asyncio
import json
import os
import tempfile
import time
from logging import getLogger

from fastapi import APIRouter, Request, status
from fastapi.encoders import jsonable_encoder
from typing import List

# This is here to satisfy runtime import needs 
# that pyinstaller appears to miss

from llama_index.schema import TextNode, NodeRelationship, RelatedNodeInfo
from llama_index import Document
from llama_index import Document

from snowflake import SnowflakeGenerator

from service.dependencies import (
    TANA_NODE,
    TANA_TEXT,
    TanaNodeMetadata,
)

from service.endpoints.topics import TanaDocument, extract_topics
from service.llamaindex import create_index
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

def load_index_from_topics(topics:List[TanaDocument], model:str, observe=False):
  '''Load the topic index from the topic array directly.'''

  logger.info('Building llama_index nodes')

  index_nodes = []
  # loop through all the topics and create a Document for each
  for topic in topics:
    metadata = {
      'category': TANA_NODE,
      'supertag': ' '.join(['#' + tag for tag in topic.tags]),
      'title': topic.name,
      'tana_id': topic.id,
      # text gets added below...
      # TODO: check that this matches at the embedding layer
      }
    
    if topic.fields:
      # get all the fields as metdata as well
      fields = set([field.name for field in topic.fields])
      for field_name in fields:
        metadata[field_name] = ' '.join([field.value for field in topic.fields if field.name == field_name])

    # what other props do we need to create?
    # document = Document(id_=topic.id, text=topic.name) # type: ignore
    # we only add the ffirst line and fields to the document payload
    # anything else and we blow out the token limits (and cost a lot!)
    text = topic.content[0][2]
    document_node = Document(doc_id=topic.id, text=text) # first line only
    document_node.metadata = metadata

    # make a note of the document in our nodes list
    index_nodes.append(document_node)

    # now iterate all the remaining topic.content and create a node for each
    # each of these is simply a string, being the name of a tana child node
    # but with [[]name^id]] reference syntax used for references
    # TODO: make these tana_nodes richer structurally
    # TODO: use actual tana node id here perhaps?
    previous_text_node = None
    if len(topic.content) > 30:
      logger.warning(f'Large topic {topic.id} with {len(topic.content)} children')

    # process all the child content records...
    for (content_id, is_ref, tana_element) in topic.content[1:]:
    
      content_metadata = TanaNodeMetadata(
        category=TANA_TEXT,
        title=topic.name,
        topic_id=topic.id,
        tana_id=content_id,
        # TODO: ? 'supertag': ' '.join(['#' + tag for tag in topic.tags]),
        # text gets added below...
      )
      
      # wire up the tana_node as an index_node with the text as the payload
      if is_ref:
        current_text_node = TextNode(text=tana_element)
        current_text_node.metadata['tana_ref_id'] = content_id
      else:
        current_text_node = TextNode(id_=content_id, text=tana_element)

      current_text_node.metadata = content_metadata.model_dump()

      # check if this is a reference node and add additional metadata
      # TODO: backport this to chroma upsert...?

      current_text_node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=document_node.node_id)
      # wire up next/previous
      if previous_text_node:
        current_text_node.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(node_id=previous_text_node.node_id)
        previous_text_node.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id=current_text_node.node_id)

      index_nodes.append(current_text_node)
      previous_text_node = current_text_node

  logger.info(f'Gathered {len(index_nodes)} tana nodes')
  logger.info("Preparing storage context")

  index = create_index(model, observe, index_nodes)
  logger.info("Llamaindex populated and ready")
  return index


# attempt to paralleize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()

# Note: accepts ?model= query param
@router.post("/llamaindex/preload", status_code=status.HTTP_204_NO_CONTENT, tags=["preload"])
async def llama_preload(request: Request, tana_dump:TanaDump, model:str="openai"):
  '''Accepts a Tana dump JSON payload and builds the Mistral index from it
  Uses the topic extraction code from the topics endpoint to build
  a temporary JSON file, then loads that into the index.
  '''
  async with lock:
    start_time = time.time()
    logger.info(f'DO txid={request.headers["x-request-id"]}')

    result = await extract_topics(tana_dump, 'JSON') # type: ignore
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

