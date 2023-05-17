from fastapi import APIRouter, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Annotated
from pydantic import BaseModel
import pinecone
import openai
from ..dependencies import *


router = APIRouter()

@router.post("/pinecone/upsert", status_code=status.HTTP_204_NO_CONTENT)
def upsert(req: PineconeRequest):
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

@router.post("/pinecone/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete(req: PineconeRequest):  
  pinecone = get_pincone(req)
  index = pinecone.Index(req.index)

  delete_response = index.delete(ids=[req.nodeId], namespace=TANA_NAMESPACE)
  return None

@router.post("/pinecone/query", response_class=HTMLResponse)
def query_pinecone(req: PineconeRequest, send_text: bool | None = False):  
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
  text_stuff = [match.metadata['text'] for match in best]
  ids = [match.id for match in best]
  
  if send_text:
    text_result = ''.join(text_stuff)

  tana_result = ""
  if len(ids) == 0:
    tana_result = "No sufficiently well-scored results"
  else:
    tana_result += ''.join(["- [[^"+id+"]]\n" for id in ids])

  if send_text:
    return tana_result, text_result
  else:
    return tana_result


@router.post("/pinecone/purge", status_code=status.HTTP_204_NO_CONTENT)
def purge(req: PineconeRequest):  
  pinecone = get_pincone(req)
  index = pinecone.Index(req.index)

  return "Not yet implemented"