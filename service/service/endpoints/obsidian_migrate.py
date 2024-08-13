import asyncio
import json
import os
import re
import tempfile
from logging import getLogger

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from typing import List, Tuple
from openai import OpenAI


from service.dependencies import capture_logs
from service.endpoints.chroma import EmbeddableNode, chroma_upsert, get_collection, prepare_node_for_embedding
from service.endpoints.topics import TanaTopicNode, extract_topics
from service.tana_types import TanaDump
from service.json2tana import json_to_tana

logger = getLogger()

router = APIRouter()


def simple_name(name:str) -> str:
  '''Convert a Tana node name to a simple string for a file name.
  Replaces references of form [[text^id]] with text.

  e.g. the string 'Meeting with [[Brett Adam^124]] and John' becomes 'Meeting with Brett Adam and John'
  '''
  simple_name = re.sub(r'\[\[(.*)\^.*\]\]', r'\1', name)
  return simple_name

async def export_topics_to_obsidian(topics:List[TanaTopicNode]):
  '''Dump all the topics to markdown files for obsidian'''

  logger.info('Building obsidian vault')

  references = {}

  index_nodes = []

  # create a temporary directoy for the vault
  with tempfile.TemporaryDirectory() as tmpdirname:
    os.chdir(tmpdirname)
    logger.info(f'Created temporary directory {tmpdirname}')

    # create a directory for the vault
    os.mkdir('vault')
    os.chdir('vault')

    basedir = os.path.join(tmpdirname, 'vault')
    # loop through all the topics and create a markdown file for each
    for topic in topics:
      filename = simple_name(topic.name) + '.md'
      os.makedirs(os.path.dirname(os.path.join(basedir, filename)), exist_ok=True)
      # write the topic content to the file
      with open(filename, 'w') as f:
        f.write('---\n')
        # first, write all the fields to the properties section of the markdown file
        for content in topic.content[1:]:
          if content.is_field:
            f.write(content.content + '\n')
        
        f.write('---\n')
        # then the name of the topic
        f.write(topic.name + '\n')

        # next write all the tags to this file
        tags = ' '.join(topic.tags)
        f.write(tags + '\n')

        # now all the child nodes
        for content in topic.content[1:]:
          if content.is_field:
            continue
          else:
            if content.is_reference:
              f.write(f'[[{content.content}]]\n')
            else:
              f.write(content.content + '\n')

    
  logger.info("Obsidian vault populated and ready")
  return index_nodes


# attempt to parallelize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()

# Note: accepts ?model= query param
@router.post("/migrate/obsidian", tags=["migrate"])
async def migrate_to_obsidian(request: Request, tana_dump:TanaDump):
  '''Accepts a Tana dump JSON payload and builds an Obsidian vault from it.
  
  Returns a list of log messages from the process.
  '''
  async with lock:
    messages = []
    async with capture_logs(logger) as logs:
      topics = await extract_topics(tana_dump, 'TANA') # type: ignore
      logger.info('Extracted topics from Tana dump')

      # make a vault from the topics
      await export_topics_to_obsidian(topics)
    
      messages = logs.getvalue()
    return messages

