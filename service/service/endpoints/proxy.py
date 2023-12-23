from enum import Enum
from starlette.requests import Request
from starlette.background import BackgroundTask
from starlette.datastructures import Headers
from fastapi import APIRouter, Response, status, Body, HTTPException
from fastapi.responses import HTMLResponse
from service.dependencies import tana_to_json, json_to_tana
from starlette.requests import Request
from logging import getLogger
import json
import httpx

router = APIRouter()

logger = getLogger()

client = httpx.AsyncClient()

class BodyVerb(str, Enum):
  POST = "POST"
  PUT = "PUT"
  PATCH = "PATCH"

def strip_header(headers, key):
  if key in headers:
    del headers[key]

async def make_proxy_request(method:str, path: str, req:Request, body=None):
  target_url=httpx.URL(path)

  headers = req.headers.raw
  new_headers = dict(headers)

  strip_header(new_headers, b'content-type')
  strip_header(new_headers, b'content-length')
  strip_header(new_headers, b'host')
  strip_header(new_headers, b'accept-encoding')

  new_headers[b'accept-encoding'] = b'identity'

  # TODO: follow redirects, etc ...
  # rp_resp:httpx.Response = None
  if method == 'POST':
    # build a request and pass on all headers
    rp_resp = await client.post(url=target_url,
                                  headers=new_headers,
                                  json=body)
  elif method == 'PUT':
    rp_resp = await client.put(url=target_url,
                                  headers=new_headers,
                                  json=body)
  elif method == 'PATCH':
    rp_resp = await client.patch(url=target_url,
                                  headers=new_headers,
                                  json=body)
  elif method == 'GET':
    rp_resp = await client.get(url=target_url,
                                  headers=new_headers)
  elif method == 'DELETE':
    rp_resp = await client.delete(url=target_url,
                                  headers=new_headers)
  else:
    rp_resp = None

  # now convert the response back to Tana paste format
  tana_format = None
  if rp_resp is not None:
    try:
      rp_body = rp_resp.content.decode("unicode_escape")
      json_format = json.loads(rp_body)
      tana_format = json_to_tana(json_format)
    except Exception as e:
      logger.error(f'Exception converting response to Tana format: {e}')
      tana_format = f"Exception converting response to Tana format. Response was {rp_resp.content}"
  return (tana_format, rp_resp.status_code)


# Make a GET request to a JSON endpoint and return result in Tana format
@router.get("/proxy/GET/{path:path}", response_class=HTMLResponse, tags=["Proxy"])
async def proxy_get(req:Request, path, response:Response):
  # NO BODY
  (tana_format, status) = await make_proxy_request('GET', path, req)
  response.status_code = status
  return tana_format

@router.post("/proxy/DELETE/{path:path}", response_class=HTMLResponse, tags=["Proxy"])
async def proxy_delete(req:Request, path:str, response:Response):
  # NO BODY
  (tana_format, status) = await make_proxy_request('DELETE', path, req)
  response.status_code = status
  return tana_format

# For HTTP methods that accept bodies, take input in Tana format, and return 
# result in Tana format, but call intermediate service in between with JSON format
@router.post("/proxy/{verb}/{path:path}", response_class=HTMLResponse, tags=["Proxy"])
async def proxy_bodyverb(req:Request, path:str, verb:BodyVerb, response:Response):
  # convert the body to JSON
  body = await req.body()
  tana_format = body.decode("unicode_escape")  
  object_graph = tana_to_json(tana_format)
  # extract object within the wrapped array
  object_graph = object_graph[0]
  (tana_format, status) = await make_proxy_request(verb, path, req, object_graph)
  response.status_code = status
  return tana_format
