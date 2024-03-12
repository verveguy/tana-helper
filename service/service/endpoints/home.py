from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.background import BackgroundTasks

import httpx

# for serving home page content
# app.mount("/EufhKV4ZMH/tana-helper", StaticFiles(directory="dist/assets/tana-helper"), name="static")

router = APIRouter()

@router.get("/EufhKV4ZMH/tana-helper/{path:path}", response_class=HTMLResponse)
async def get_home(path:str, request:Request):
  response = httpx.get(f'https://tana.pub/EufhKV4ZMH/tana-helper/{path}', follow_redirects=True)
  return response.text

@router.get("/_next/{path:path}", response_class=HTMLResponse)
async def get_next(path:str, request:Request):

  headers = request.headers.raw
  # headers.append((b'x-requested-for', b'tana.pub'))

  response = httpx.get(f'https://tana.pub/_next/{path}',
                       follow_redirects=True,
                       headers=headers)
  return response.text

async def _reverse_proxy(request: Request):
  url = httpx.URL(path=request.url.path,
                  query=request.url.query.encode("utf-8"))

  client = httpx.Client(base_url="http:/tana.pub/")

  rp_req = client.build_request(request.method, url,
                                headers=request.headers.raw,
                                content=await request.body(),
                                timeout=60.0)
  rp_resp = client.send(rp_req)
  return Response(
      rp_resp.aiter_raw(),
      status_code=rp_resp.status_code,
      headers=rp_resp.headers,
  )
# async def _reverse_proxy(request: Request):
#   url = httpx.URL(path=request.url.path,
#                   query=request.url.query.encode("utf-8"))

#   client = httpx.AsyncClient(base_url="http:/tana.pub/")

#   rp_req = client.build_request(request.method, url,
#                                 headers=request.headers.raw,
#                                 content=request.stream(),
#                                 timeout=60.0)
#   rp_resp = await client.send(rp_req, stream=True)
#   return StreamingResponse(
#       rp_resp.aiter_raw(),
#       status_code=rp_resp.status_code,
#       headers=rp_resp.headers,
#       background=BackgroundTasks(rp_resp.aclose),
#   )


# # for local file serving (favicon, etc)
# app.mount("/EufhKV4ZMH/tana-helper", StaticFiles(directory="dist/assets/tana-helper"), name="static")
