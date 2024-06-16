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
from fastapi.concurrency import asynccontextmanager
from openai import OpenAI
from pydantic import BaseModel
from pathlib import Path

from service.tana_types import TANA_NODE


from .settings import settings

# Load environment variables from .env file
# load_dotenv()

app_name = "TanaHelper"

  # production: Annotated[bool, Field(title="Production", 
  #   description="Whether we are running in production mode")] \
  #     = False
  
  # templates:object = None




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

#OPENAI_EMBEDDING_MODEL = "text-embedding-3-large"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_EMBEDDING_THRESHOLD = 0.45

#OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
#OPENAI_EMBEDDING_THRESHOLD = 0.80


OPENAI_CHAT_MODEL = 'gpt-4o'

class OpenAIRequest(BaseModel):
  model: str = OPENAI_CHAT_MODEL
  embedding_model: str = OPENAI_EMBEDDING_MODEL

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
  score: Optional[float] = OPENAI_EMBEDDING_THRESHOLD
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
  score: Optional[float] = OPENAI_EMBEDDING_THRESHOLD
  top: Optional[int] = 10
  tags: Optional[str] = ''
  metadata: Optional[dict] = None
  nodeId: str
  returns: Optional[str] = 'topic'


class LlamaRequest(EmbeddingRequest):
  score: Optional[float] = OPENAI_EMBEDDING_THRESHOLD
  top: Optional[int] = 10
  tags: Optional[str] = ''
  nodeId: str

class LlamaindexAsk(BaseModel):
  query: str


class QueueRequest(HelperRequest):
  pass

class WeaviateRequest(EmbeddingRequest):
  environment: Optional[str] = settings.tana_environment
  index: Optional[str] = settings.tana_index
  score: Optional[float] = OPENAI_EMBEDDING_THRESHOLD
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

def get_embedding(req:EmbeddingRequest) -> List:
  # get shared client object
  api_key = settings.openai_api_key
  openai_client = OpenAI(api_key=api_key)
  content = req.context 
  embedding = openai_client.embeddings.create(input=content, model=req.embedding_model)
  return embedding.data # type: ignore


def get_embeddings(nodes:List, model:str):
  # get shared client object
  api_key = settings.openai_api_key
  openai_client = OpenAI(api_key=api_key)
  embedding = openai_client.embeddings.create(input=nodes, model=model)
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


from io import StringIO
from snowflake import SnowflakeGenerator

snowflakes = SnowflakeGenerator(42)

BASE66_ALPHABET = u"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_.~"
BASE = len(BASE66_ALPHABET)

def nextflake():
    n = next(snowflakes)
    if n == 0:
        return BASE66_ALPHABET[0].encode('ascii')

    r = StringIO()
    while n:
        n, t = divmod(n, BASE)
        r.write(BASE66_ALPHABET[t])
    return r.getvalue().encode('ascii')[::-1]