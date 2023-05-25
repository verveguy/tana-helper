import pinecone
import openai
from pydantic import BaseModel, BaseSettings
from typing import Union, Optional
from datetime import datetime
import pytz

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
