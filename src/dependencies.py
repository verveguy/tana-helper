import pinecone
import openai
from pydantic import BaseModel, BaseSettings
from typing import Union, Optional
from datetime import datetime
from logging import getLogger
import timeit
import pytz
import json

logger = getLogger()

class Settings(BaseSettings):
    openai_api_key: str = "OPENAI API KEY NOT SET"
    tana_api_token: str = "TANA API TOKEN NOT SET"
    production: bool = False
    logger_file: str = 'tana-handler.log'
    template_path: str = '/tmp/tana-helper'

    class Config:
        env_file = ".env"

# create global settings 
settings = Settings()

# Pinecone keys that are not configured
# put them in .env?
TANA_NAMESPACE = "tana-namespace"
TANA_TYPE = "tana_node"


class HelperRequest(BaseModel):
  context: Optional[str] = ''

class NodeRequest(HelperRequest):
  nodeId: str

class ExecRequest(BaseModel):
  code: Optional[str] = ''
  call: str 
  payload: dict

class OpenAIRequest(BaseModel):
  openai: Optional[str] = None
  model: Optional[str] = 'gpt-3.5-turbo'

class OpenAICompletion(OpenAIRequest):
  prompt: str
  max_tokens: Optional[int]
  temperature: Optional[int] = 0

class PineconeRequest(HelperRequest, OpenAIRequest):
  pinecone: str
  embedding_model: Optional[str] = "text-embedding-ada-002"
  environment: Optional[str] = "asia-southeast1-gcp"
  index: Optional[str] = "tana-helper"
  score: Optional[float] = 0.80
  top: Optional[int] = 10
  tags: Optional[str] = ''
  nodeId: str

class ChainsRequest(HelperRequest, OpenAIRequest):
  serpapi: Optional[str] = None
  wolfram: Optional[str] = None
  iterations: Optional[int] = 6


def get_pinecone(req:PineconeRequest):
  pinecone.init(api_key=req.pinecone, environment=req.environment)
  return pinecone

def get_embedding(req:PineconeRequest):
  openai.api_key = settings.openai_api_key if not req.openai else req.openai
  embedding = openai.Embedding.create(input=req.context, model=req.embedding_model)
  return embedding.data # type: ignore

def get_chatcompletion(req:OpenAICompletion) -> dict:
  openai.api_key = settings.openai_api_key if not req.openai else req.openai
  completion = openai.ChatCompletion.create(
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

class LineTimer:
    def __init__(self, name=None):
        self.name = " '"  + name + "'" if name else ''

    def __enter__(self):
        self.start = timeit.default_timer()

    def __exit__(self, exc_type, exc_value, traceback):
        self.took = (timeit.default_timer() - self.start) * 1000.0
        logger.info('Code block' + self.name + ' took: ' + str(self.took) + ' ms')



# RETHINK THIS

# Build an initial tree of nodes using 'children' arrays, marking those that are fields vs. those that are plain
# then, walk the tree again, hoisting up any children of field nodes to be the value of the node 
# instead of being 'children'

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
  for line in tana_format.split('\n'):
    
    line = line.rstrip()
    if line == '' or line == '-':
      continue

    # count leading spaces
    leader = line.split('-')[0]
    level = int(len(leader) / 2) + 1
    print(f'level: {level} line: {line}')

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
        raise Exception('Field with both value and children is not supported')
      if children:
        value = children
    parent[node['field']] = value

  def process_node(node):
    if 'is_field' in node and node['is_field']:
      newnode = {'field': node['field'], 'value': node['value']}
    else:
      newnode = { 'name': node['name']}
    if 'children' in node:
      for child in node['children']:
        newchild = process_node(child)
        if child['is_field']:
          hoist_field(newchild, newnode)
        else: 
          add_child(newnode, newchild)
    return newnode

  # now, reprocess tree, 'hoisting' children of fields and dropping is_field flags
  result = process_node(top)
  return result['children']
