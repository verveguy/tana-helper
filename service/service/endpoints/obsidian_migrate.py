import asyncio
import json
import os
import re
import tempfile
from logging import getLogger
from pathlib import Path

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

def obsidian_reference(name:str) -> str:
  '''Convert a Tana node name to a simple string for a file name.
  Replaces references of form [[text^id]] with [[id|text]].

  e.g. the string 'Meeting with [[Brett Adam^124]] and John' becomes 'Meeting with Brett Adam and John'
  '''
  obs_link = re.sub(r'\[\[([^\[\^]*)\^([^\]]+)\]\]', r'[[\2|\1]]', name)
  return obs_link

def convert_links(content:str) -> str:
  '''Convert all the Tana references in the content to Obsidian references'''
  obs = re.sub(r'\[\[([^\[\^]*)\^([^\]]+)\]\]', r'[[\2|\1]]', content)
  return obs

def strip_links(content:str) -> str:
  '''Convert all the Tana references in the content to Obsidian references'''
  obs = re.sub(r'\[\[([^\[\^]*)\^([^\]]+)\]\]', r'\1', content)
  return obs

def unwrap_reference(content:str):
  '''Convert all the Tana references in the content to Obsidian references'''
  obs = re.search(r'([ -]*)\[\[(.+)\^([^\]]+)\]\](.*)', content)
  if obs:
    return obs.groups()
  else:
    return '', content, '', ''

def obsidian_frontmatter_field(content:str) -> str:
  '''Convert all the Tana references in the content to Obsidian references'''
  obs = re.search(r'([ -]*)([^:]+)::(.*)', content)
  if obs:
    result = obs.groups()[1] + ': ' + strip_links(obs.groups()[2])
  else:
    result = content
  return result

def obsidian_field(content:str) -> str:
  '''Convert all the Tana references in the content to Obsidian references'''
  if content.find(':') > 0:
    obs = re.search(r'([ -]*)([^:]+):?:?(.*)', content)
    if obs:
      grps = obs.groups()
      result = f'{grps[0]}{grps[1]}:{convert_links(grps[2])}'
    else:
      result = content
  else:
    result = convert_links(content)
  return result

async def export_topics_to_obsidian(topics:List[TanaTopicNode]):
  '''Dump all the topics to markdown files for obsidian'''

  logger.info('Building obsidian vault')

  index_nodes = []

  # create a temporary directory for the vault
  tmpdirname = os.path.join('/', 'tmp')
  #with tempfile.TemporaryDirectory() as tmpdirname:
  if tmpdirname:
    os.chdir(tmpdirname)

    # create a directory for the vault
    basedir = os.path.join(tmpdirname, 'vault')
    Path(basedir).mkdir(parents=True, exist_ok=True)
    os.chdir(basedir)

    logger.info(f'Created temporary directory {basedir}')

    # loop through all the topics and create a markdown file for each
    for topic in topics:
      filename = simple_name(topic.id) + '.md'
      os.makedirs(os.path.dirname(os.path.join(basedir, filename)), exist_ok=True)
      # write the topic content to the file
      with open(filename, 'w') as f:
        f.write('---\n')
        f.write(f'title: {strip_links(topic.name)}\n')
        f.write(f'id: {topic.id}\n')        
        f.write('---\n')
        f.write('Fields:\n')

        # first, write all the fields to the properties section of the markdown file
        for content in topic.content[1:]:
          if content.is_field:
            f.write(f'  {obsidian_field(content.content)}\n')

        # then the name of the topic
        f.write(convert_links(topic.name) + '\n')

        # next write all the tags to this file
        tags = ' '.join(topic.tags)
        f.write(tags + '\n')

        # now all the child nodes
        for content in topic.content[1:]:
          if content.is_field:
            continue
          else:
            if content.is_reference:
              indent, name, id, tags = unwrap_reference(content.content)
              f.write(f'{indent}{convert_links(name)} {tags} ([[{content.id}|link]])\n')
            else:
              f.write(convert_links(content.content) + '\n')

    # keep the resulting temp directory
    #os.chdir(tmpdirname)
    #os.rename('vault', '/tmp/vault')

    logger.info(f'Obsidian vault populated and ready at {basedir}')

    
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

