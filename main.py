from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from pydantic import BaseModel
import pinecone
import openai


app = FastAPI()

origins = [
    "http://localhost",
    "https://lolalhost",
    "http://app.tana.inc",
    "https://app.tana.inc",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PineconeRequest(BaseModel):
  score: float | None = 0.80
  top: int | None = 10
  context: str | None = ""
  tags: str | None = ""
  nodeId: str
  openai: str
  pinecone: str
  model: str | None = "text-embedding-ada-002"
  environment: str | None = "asia-southeast1-gcp"
  index: str | None = "tana-helper"


# Pinecone keys that are not configured
TANA_NAMESPACE = "tana-namespace"
TANA_TYPE = "tana_node"

@app.get("/")
async def root():
  return {"message": "Hello World"}

def get_pincone(req:PineconeRequest):
  pinecone.init(api_key=req.pinecone, environment=req.environment)
  return pinecone

def get_embedding(req:PineconeRequest):
  openai.api_key = req.openai
  embedding = openai.Embedding.create(input=req.context, model=req.model)
  return embedding.data

@app.post("/pinecone/upsert", status_code=status.HTTP_204_NO_CONTENT)
async def upsert(req: PineconeRequest):
  embedding = get_embedding(req)
  vectors = [(req.nodeId, embedding[0]['embedding'],
              {
              'category': TANA_TYPE,
              'supertag': req.tags,
              'text': req.context
              })
            ]
  
  pinecone = get_pincone(req)
  index = pinecone.Index(req.index)

  upsert_response = index.upsert(vectors=vectors, namespace=TANA_NAMESPACE)
  return None

@app.post("/pinecone/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete(req: PineconeRequest):  
  pinecone = get_pincone(req)
  index = pinecone.Index(req.index)

  delete_response = index.delete(ids=[req.nodeId], namespace=TANA_NAMESPACE)
  return None

@app.post("/pinecone/query")
async def delete(req: PineconeRequest, res: Response):  
  embedding = get_embedding(req)

  vector = embedding[0]['embedding']

  supertags = req.tags.split()
  tag_filter = None
  if len(supertags) > 0:
    tag_filter = {
      'category': TANA_TYPE,
      'supertag': { "$in": supertags }    
    }

  pinecone = get_pincone(req)
  index = pinecone.Index(req.index)

  query_response = index.query(
    namespace=TANA_NAMESPACE,
    top_k=req.top,
    include_values=True,
    include_metadata=True,
    vector = vector,
    filter=tag_filter
  )

  def threshold_function(match):
    return match.score > req.score

  best = filter(threshold_function, query_response.matches)
  ids = [match.id for match in best]

  tana_result = ""
  if len(ids) == 0:
    tana_result = "No sufficiently well-scored results"
  else:
    tana_result += ''.join(["- [[^"+id+"]]\n" for id in ids])

  # res.headers['Content-Type'] = "text/plain"
  return tana_result


@app.post("/pinecone/purge", status_code=status.HTTP_204_NO_CONTENT)
async def delete(req: PineconeRequest):  
  pinecone = get_pincone(req)
  index = pinecone.Index(req.index)

  return "Not yet implemented"

