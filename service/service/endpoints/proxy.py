from starlette.requests import Request
from starlette.background import BackgroundTask
from starlette.datastructures import Headers
from fastapi import APIRouter, status, Body, HTTPException
from fastapi.responses import HTMLResponse
from service.dependencies import tana_to_json, json_to_tana
from starlette.requests import Request
from logging import getLogger
import json
import httpx

router = APIRouter()

logger = getLogger()

client = httpx.AsyncClient()

async def make_proxy_request(method:str, req:Request, body=None):
  # strip /proxy/ off the front
  path=req.url.path[7:]
  # build up valid request
  query=req.url.query
  if query != '':
    new = path+'?'+query
  else:
    new = path

  target_url=httpx.URL(new)

  headers = req.headers.raw
  new_headers = dict(headers)
  del new_headers[b'content-type']
  del new_headers[b'content-length']
  del new_headers[b'host']
  del new_headers[b'accept-encoding']
  new_headers[b'accept-encoding'] = b'identity'

  rp_resp:httpx.Response = None
  if method == 'POST':
    # build a request and pass on all headers
    rp_resp = await client.post(url=target_url,
                                  headers=new_headers,
                                  json=body)
  elif method == 'GET':
    rp_resp = await client.get(url=target_url,
                                  headers=new_headers)
  elif method == 'DELETE':
    pass
  elif method == 'PUT':
    pass
  elif method == 'PATCH':
    pass
  
  # now convert the response back to Tana paste format
  tana_format = None
  if rp_resp is not None:
    rp_body = rp_resp.content.decode("unicode_escape")
    json_format = json.loads(rp_body)
    tana_format = json_to_tana(json_format)
  
  return (tana_format, rp_resp.status_code)

# take input in Tana format, and return result in Tana format, but call intermediate
# service in between with JSON format
@router.post("/proxy/{path:path}", response_class=HTMLResponse, tags=["Proxy"])
async def proxy_post(req:Request, body:str=Body(...)):
  # convert the body to JSON
  tana_format = bytes(body, "utf-8").decode("unicode_escape")  
  object_graph = tana_to_json(tana_format)
  # extract object within the wrapped array
  object_graph = object_graph[0]
  (tana_format, status) = await make_proxy_request('POST', req, object_graph)

  return tana_format

# Make a GET request to a JSON endpoint and return result in Tana format
@router.get("/proxy/{path:path}", response_class=HTMLResponse, tags=["Proxy"])
async def proxy_get(req:Request, body:str=Body(...)):

  (tana_format, status) = await make_proxy_request('GET', req)

  return tana_format

