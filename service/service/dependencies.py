import io
import os
import logging
import httpx
import pytz
import json

from datetime import datetime
from logging import getLogger
from timeit import timeit
from typing import ForwardRef, List, Optional
from typing_extensions import Annotated
from fastapi.concurrency import asynccontextmanager
from openai import OpenAI
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


# Load environment variables from .env file
# load_dotenv()

app_name = "TanaHelper"

# TODO: figure out how to make settings more modular, based on endpoints configured
class Settings(BaseSettings):
  """
  Settings for Tana Helper
  """
  # Read from .env for development/debug only
  # otherwise, see below for get_settings() function
  model_config = SettingsConfigDict( title="Settings", env_file='.env', env_file_encoding='utf-8')

  openai_api_key: Annotated[str, Field(title="OpenAI API Key", 
    description="API Key for OpenAI. You can also pass this as the header x-openai-api-key on each request.")] \
      = "OPENAI_API_KEY NOT SET"
  
  tana_api_token: Annotated[str, Field(title="Tana API Token", 
    description="API Token for Tana access. You can also pass this as the header x-tana-api-token on each request.")] \
      = "TANA_API_TOKEN NOT SET"
  
  webhook_template_path: Annotated[str, Field(title="Webhook Template Path", 
      description="Path to store webhook templates")] \
        = os.path.join(Path.home(), '.tana_helper', 'webhooks')
  
  temp_files: Annotated[str, Field(title="Temporary Files Path", 
    description="Path to store temporary files")] \
      = os.path.join('/', 'tmp','tana_helper', 'tmp')
  
  export_path: Annotated[str, Field(title="Export Path", 
    description="Path to store exported files")] \
      = os.path.join('/', 'tmp','tana_helper', 'export')
  
  tana_environment: Annotated[str, Field(title="Tana Pinecone Environment",
    description="Pinecone environment for Tana vector storage")] \
      = "us-west4-gcp-free" 
  
  tana_namespace: Annotated[str, Field(title="Tana VectorDB Namespace", 
    description="VectorDB namespace for Tana vector storage")] \
      = "tana-namespace" 
  
  tana_index: Annotated[str, Field(title="Tana VectorDB Index", 
    description="VectorDB index for Tana vector storage")] \
      = "tana-helper"
                          
  # production: Annotated[bool, Field(title="Production", 
  #   description="Whether we are running in production mode")] \
  #     = False
  
  # templates:object = None

# create global settings 
# TODO: make settings per-request context, not gobal
global settings

tana_helper_config_dir = os.path.join(Path.home(), '.tana_helper')
settings_path = os.path.join(tana_helper_config_dir, 'settings.json')

def get_settings():
  global settings
  try:
    with open(settings_path, 'r') as f:
      settings_dict = json.load(f)
      settings = Settings.model_validate(settings_dict)
  except Exception:
    # any exception, reset to defaults
    settings = Settings()
  return settings

def set_settings(new_settings:Settings):
  global settings
  settings = new_settings
  # write new settings to .env file
  if not os.path.exists(tana_helper_config_dir):
      os.makedirs(tana_helper_config_dir, exist_ok=True)
  with open(settings_path, 'w') as f:
    f.write(settings.model_dump_json())
  return settings

# read from file to start with
settings = get_settings()


# Types for our APIs to use

TANA_TEXT = "tana-text"
TANA_NODE = "tana-node"

class CalendarRequest(BaseModel):
  me: Optional[str] = None
  one2one: Optional[str] = None
  meeting: Optional[str] = None
  person: Optional[str] = None
  solo: Optional[bool] = None
  calendar: Optional[str] = None
  offset: Optional[str] = None
  range: Optional[str] = None
  date: Optional[str] = None
  # model_config = ConfigDict(extra='forbid')

class HelperRequest(BaseModel):
  context: str = ''
  name: str = ''

class NodeRequest(HelperRequest):
  nodeId: str

class ExecRequest(BaseModel):
  code: Optional[str] = ''
  call: str 
  payload: dict

class OpenAIRequest(BaseModel):
  model: str = 'gpt-3.5-turbo'
  embedding_model: str = "text-embedding-ada-002"

class OpenAICompletion(OpenAIRequest):
  prompt: str
  max_tokens: Optional[int]
  temperature: Optional[int] = 0

class EmbeddingRequest(HelperRequest, OpenAIRequest):
  # union type, nothing to add
  pass

class PineconeRequest(EmbeddingRequest):
  pinecone: str
  environment: Optional[str] = settings.tana_environment
  index: Optional[str] = settings.tana_index
  score: Optional[float] = 0.80
  top: Optional[int] = 10
  tags: Optional[str] = ''
  nodeId: str

class PineconeNode(BaseModel):
  category: str = TANA_NODE
  supertag: Optional[List[str]] = []
  text: str


class ChromaStoreRequest(BaseModel):
  environment: Optional[str] = "local"

class ChromaRequest(EmbeddingRequest, ChromaStoreRequest):
  score: Optional[float] = 0.80
  top: Optional[int] = 10
  tags: Optional[str] = ''
  nodeId: str


class LlamaRequest(EmbeddingRequest):
  score: Optional[float] = 0.80
  top: Optional[int] = 10
  tags: Optional[str] = ''
  nodeId: str

class LlamaindexAsk(BaseModel):
  query: str

class TanaNodeMetadata(BaseModel):
  category: str = TANA_NODE
  title: str
  supertag: Optional[str] = None
  topic_id: str
  tana_id: Optional[str] = None
  text: Optional[str] = None

class QueueRequest(HelperRequest):
  pass

class WeaviateRequest(EmbeddingRequest):
  environment: Optional[str] = settings.tana_environment
  index: Optional[str] = settings.tana_index
  score: Optional[float] = 0.80
  top: Optional[int] = 10
  tags: Optional[str] = ''
  nodeId: Optional[str] = None


class ChainsRequest(HelperRequest, OpenAIRequest):
  serpapi: Optional[str] = None
  wolfram: Optional[str] = None
  iterations: Optional[int] = 6


# Tana Input API 

class SuperTag(BaseModel):
  id: str

Node = ForwardRef('Node') # type: ignore

class Node(BaseModel):
  name: str
  description: Optional[str] = None
  supertags: Optional[List[SuperTag]] = None
  children: Optional[List[Node]] = None

# Pydantic models can be nested, this is how you reference the same model
#Node.update_forward_refs()
#Node.model_rebuild()

class AddToNodeRequest(BaseModel):
  nodes: List[Node]
  targetNodeId: Optional[str] = None


# Utility classes

logger = getLogger()

class TanaInputAPIClient:
  def __init__(self, base_url: str = "https://europe-west1-tagr-prod.cloudfunctions.net", auth_token: Optional[str] = None):
    self.base_url = base_url
    self.client = httpx.Client(verify=True)
    self.headers = {'Content-Type': 'application/json'}
    if auth_token:
      self.headers['Authorization'] = f'Bearer {auth_token}'

  def add_to_inbox(self, request_data: AddToNodeRequest):
    url = f"{self.base_url}/addToNodeV2"
    response = self.client.post(url, json=request_data.model_dump(exclude_unset=True), headers=self.headers)
    return response

# OpenAI helper functions

def get_embedding(req:EmbeddingRequest):
  # get shared client object
  api_key = settings.openai_api_key
  openai_client = OpenAI(api_key=api_key)
  content = req.name + req.context 
  embedding = openai_client.embeddings.create(input=content, model=req.embedding_model)
  return embedding.data # type: ignore

def get_chatcompletion(req:OpenAICompletion) -> dict:
  api_key = settings.openai_api_key
  openai_client = OpenAI(api_key=api_key)
  completion = openai_client.chat.completions.create(
                  messages=[{ 'role': 'user', 'content': req.prompt }],
                  model=req.model, 
                  max_tokens=req.max_tokens, 
                  temperature=req.temperature)
  
  return completion # type: ignore

def get_date():

  # Set the desired timezone (EST)
  est_timezone = pytz.timezone('US/Eastern')
  
  # Get the current date and time in UTC
  current_date_time_utc = datetime.now(pytz.utc)
  
  # Convert the UTC time to the desired timezone (EST)
  current_date_time_est = current_date_time_utc.astimezone(est_timezone)
  
  # Format and print the current date and time in EST
  formatted_date_time = current_date_time_est.strftime("%Y-%m-%d %H:%M:%S")
      
  return formatted_date_time


# helper function for timing exeuction of various calls
class LineTimer:
  def __init__(self, name=None):
    self.name = " '"  + name + "'" if name else ''

  def __enter__(self):
    self.start = timeit.default_timer()

  def __exit__(self, exc_type, exc_value, traceback):
    self.took = (timeit.default_timer() - self.start) * 1000.0
    logger.info('Code block' + self.name + ' took: ' + str(self.took) + ' ms')


# tana to JSON conversion. Takes Tana API payload in "native" format
# and turns into logically equivalent JSON object tree.
# Child nodes are represented as 'children': [child, child, child]

# Strategy: 
# Build an initial tree of nodes using 'children' arrays, marking those that are fields vs. those that are plain
# then, walk the tree again, hoisting up any children of field nodes to be the value of the node 
# instead of being 'children'

# TODO: pull this out into sep file
def tana_to_json(tana_format):

  def add_child(obj, child):
    if 'children' not in obj:
      obj['children'] = []
    obj['children'].append(child)
    
  stack = []
  top = { 'name': 'ROOT', 'is_field': False}
  current = top
  stack.append(top)
  current_level = 1
  in_code_block = False
  code_block = ""

  for line in tana_format.split('\n'):
    
    line = line.rstrip()
    if line == '' or line == '-':
      continue

    if in_code_block:
      code_block += line +'\n'
      if '```' in line and line[0:3] == '```':
        in_code_block = False
        if current['is_field']:
          current['value'] = code_block
        else:
          # code block is sibling
          newobj = { 'name': code_block, 'is_field': False, 'field': None, 'value': None  }
          add_child(stack[-1], newobj)
          current = newobj
      continue

    if '-' not in line:
      # this could be a code block or other multi-line value
      if '```' in line:
        code_block = line + '\n'
        in_code_block = True
        continue

    # count leading spaces
    leader = line.split('-')[0]
    level = int(len(leader) / 2) + 1

    line = line.lstrip(' -')

    field = None
    value = None
    
    is_field = '::' in line

    if is_field:
      fields = line.split('::')
      field = fields[0].strip()
      if fields[1].strip() != '':
        value = fields[1].strip()
    
    newobj = { 'name': line, 'is_field': is_field, 'field': field, 'value': value  }
    if level < current_level:  #exdent
      # pop off as many as needed
      stack = stack[0:level - current_level]
      add_child(stack[-1], newobj)
      current = newobj
      current_level = level

    elif level > current_level:
      # indent, means child of current
      add_child(current, newobj)
      stack.append(current)
      current = newobj
      current_level = level
    else:
      # same level, means add as child to same parent
      add_child(stack[-1], newobj)
      current = newobj

  def hoist_field(node, parent):
    value = node['value']
    if 'children' in node:
      children = node['children']
      # if value is non-null and children is non-null, we have a problem
      if value and children:
        raise TypeError('Field with both value and children is not supported')
      if children:
        value = children
    parent[node['field']] = value

  def process_node(node):
    is_field = False
    if 'is_field' in node and node['is_field']:
      is_field = True
      newnode = {'field': node['field'], 'value': node['value']}
    else:
      newnode = { 'name': node['name']}
    
    if 'children' in node:
      value_node = newnode
      # fields with fields are special...
      if is_field:
        if node['value'] is None:
          node['value'] = {}
        value_node = node['value']
        newnode['value'] = value_node
      
      for child in node['children']:
        newchild = process_node(child)
        if child['is_field']:
          hoist_field(newchild, value_node)
        else: 
          add_child(newnode, newchild)
    return newnode

  # now, reprocess tree, 'hoisting' children of fields and dropping is_field flags
  # print(top)
  result = process_node(top)
  # print(result)
  return result['children']


def code_to_tana(value, indent):
  line = ''
  splits = value.split('<br>')
  for split in splits:
    if len(split) == 0:
      # skip the blank entry on the end...
      continue
    # count spaces
    strip = split.lstrip(' ')
    spaces = len(split) - len(strip)
    line += ' '*(indent + spaces) + '- ' + strip + '\n'
  indent -= 2
  return line

def children_to_tana(objects, initial_indent):
  tana_format = ''
  
  for obj in objects:
    indent = initial_indent
    children = [] # assume no children initially
    # do name first. If empty, we're a field with fields...
    if 'name' in obj and obj['name'] is not None:
      name = obj['name']

      if '```' in name:
        # name is in fact code block
        tana_format += code_to_tana(name, indent)
      else:
        tana_format += ' '*indent + '- ' + name +'\n'
      
      indent += 2

    for key in obj.keys():
      line = ''
      value = obj[key]
      if key == 'name':
        continue
      elif key == 'children':
        children = value
        # skip for now
      else:
        # do all the fields first
        if '```' in value:
          # code block needs special handling
          line = ' '*indent + '- ' + key + '::\n'
          line += code_to_tana(value, indent+2)
          tana_format += line
        elif type(value) is list:
          # multi-valued fields need special handling
          tana_format += ' '*indent + '- ' + key + '::\n'
          chunk = children_to_tana(value, indent+2)
          tana_format += chunk
        elif type(value) is str:
          # just a plain valued field
          tana_format += ' '*indent + '- ' + key + ':: ' + value + '\n'
        else:
          # must be an object type, recurse
          tana_format += ' '*indent + '- ' + key + '::\n'
          chunk = children_to_tana([value], indent+2)
          tana_format += chunk
 
    # now do children recursively
    if len(children) > 0:
      chunk = children_to_tana(children, indent)
      if chunk != '':
        tana_format += chunk

  return tana_format

def json_to_tana(json_format):
  tana_format = ''
  indent = 0
  if type(json_format) is not list:
    json_format = [json_format]
  
  chunk = children_to_tana(json_format, indent) 
  tana_format += chunk

  return tana_format

# essentially, context managers are aspect-oriented constructs for python
@asynccontextmanager
async def capture_logs(logger):
  # add a local capture to our logger
  logs = io.StringIO('')
  eh = logging.StreamHandler(logs)
  formatter = logging.Formatter('%(asctime)s - %(module)s.%(funcName)s() - %(levelname)s - %(message)s',"%Y-%m-%d %H:%M:%S")
  eh.setFormatter(formatter)
  logger.addHandler(eh)
  yield logs
  logger.removeHandler(eh)