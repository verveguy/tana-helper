import pinecone
import openai
from pydantic import BaseModel
from datetime import datetime
import pytz

# TODO: import these from common file
# Pinecone keys that are not configured
TANA_NAMESPACE = "tana-namespace"
TANA_TYPE = "tana_node"


class HelperRequest(BaseModel):
  context: str | None = ""

class NodeRequest(HelperRequest):
  nodeId: str

class OpenAIRequest(BaseModel):
  openai: str
  model: str | None = 'gpt-3.5-turbo'

class PineconeRequest(HelperRequest, OpenAIRequest):
  pinecone: str
  embedding_model: str | None = "text-embedding-ada-002"
  environment: str | None = "asia-southeast1-gcp"
  index: str | None = "tana-helper"
  score: float | None = 0.80
  top: int | None = 10
  tags: str | None = ""
  nodeId: str

class ChainsRequest(HelperRequest, OpenAIRequest):
  serpapi: str | None = None
  wolfram: str | None = None
  iterations: int | None = 6


#TODO: Move thse to shared file
def get_pincone(req:HelperRequest):
  pinecone.init(api_key=req.pinecone, environment=req.environment)
  return pinecone

def get_embedding(req:HelperRequest):
  openai.api_key = req.openai
  embedding = openai.Embedding.create(input=req.context, model=req.embedding_model)
  return embedding.data

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
