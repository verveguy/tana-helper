import asyncio
import os
from pathlib import Path
import platform
import time
from logging import getLogger

from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from service.dependencies import settings
from service.endpoints import (calendar, chroma, class_diagram, configure, exec_code, graph_view, 
                 inlinerefs, jsonify, logmonitor, preload, cleanups, proxy, research, topics, weaviate, webhooks)
from service.logconfig import get_logger_config, setup_rich_logger
from snowflake import SnowflakeGenerator

log_filename = None

def get_app() -> FastAPI:
  global log_filename
  app = FastAPI(
    description="Tana Helper", version="0.2.0",
    # TODO: get servers from passed in cmd line / env var
    servers=[
      {"url": "http://localhost:8000", "description": "Local loopback"},
      {"url": "https://verveguy.ngrok.app", "description": "ngrok test"},
    ])
  log_filename = setup_rich_logger()
  return app

app = get_app()

logger = getLogger()

origins = [
  "http://localhost",
  "https://localhost",
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

# import our various service endpoints
# Comment out any service you don't want here
# and remove the import from above (line 4)

plat = platform.system()
if plat == 'Darwin':
  app.include_router(calendar.router)

app.include_router(inlinerefs.router)
app.include_router(exec_code.router)
app.include_router(webhooks.router)
app.include_router(jsonify.router)
app.include_router(graph_view.router)
app.include_router(class_diagram.router)
app.include_router(topics.router)
app.include_router(configure.router)
app.include_router(cleanups.router)
app.include_router(proxy.router)

app.include_router(chroma.router)
app.include_router(preload.router)
app.include_router(research.router)

app.include_router(logmonitor.router)

app.include_router(weaviate.router)
# TODO: upgrade pinecone code
# app.include_router(pinecone.router)


# async helpers to get the body during middleware evaluation
# useful for debugging in the layer _prior_ to pydantic validation
async def set_body(request: Request, body: bytes):
  async def receive():
    return {"type": "http.request", "body": body}
  request._receive = receive

async def get_body(request: Request) -> bytes:
  body = await request.body()
  await set_body(request, body)
  return body

@app.middleware("http")
async def add_get_authorization_headers(request: Request, call_next):
  # find headers in request
  x_tana_api_token = request.headers.get('x-tana-api-token')
  x_openai_api_key = request.headers.get('x-openai-api-key')
  # TODO: make settings per-request context, not gobal
  # use passed in header tokens if present, otherwise look for env vars
  settings.openai_api_key = settings.openai_api_key if not x_openai_api_key else x_openai_api_key
  settings.tana_api_token = settings.tana_api_token if not x_tana_api_token else x_tana_api_token
  response = await call_next(request)
  return response

snowflakes = SnowflakeGenerator(42)

@app.middleware("http")
async def log_entry_exit(request: Request, call_next):
  x_request_id = request.headers.get('x-request-id')
  idem = next(snowflakes) if not x_request_id else x_request_id
  if not x_request_id:
    id_header = (b'x-request-id', bytes(str(idem), 'utf-8'))
    request.headers.__dict__["_list"].append(id_header)
     
  logger.info(f"txid={idem} start request path={request.url.path}")
  start_time = time.time()

  # await set_body(request, await request.body())
  # body = await get_body(request)
  # logger.info(f"txid={idem} body={body}")
  response:Response = await call_next(request)

  process_time = (time.time() - start_time) * 1000
  formatted_process_time = '{0:.2f}'.format(process_time)
  logger.info(f"txid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")
  if not x_request_id:
     response.headers['x-request-id'] = str(idem)
  return response


# fiddle with the CWD to satsify double-clickable .app
# context
basedir = os.path.dirname(__file__)
# logger.info(f"Install dir = {basedir}")
cwd = os.getcwd()
# logger.info(f"Current working dir = {cwd}")
os.chdir(basedir)
cwd = os.getcwd()
# logger.info(f"Setting cwd = {cwd}")


# for local file serving (favicon, etc)
app.mount("/static", StaticFiles(directory="dist"), name="static")

# for HTML template responses
settings.templates = Jinja2Templates(directory=os.path.join(basedir,'dist','templates'))

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
  favicon_path = os.path.join(basedir,'dist','assets','favicon.ico')
  return FileResponse(favicon_path)


# expose our various Webapps on /ui/{app_name}
@app.get("/testui/{app_file}", response_class=HTMLResponse, tags=["UI"])
async def app_ui(app_file:str):
  # return a completely generic index.html that assumes the app is
  # available on App_file.js (note initial cap)
  return f"""<!doctype html>
<html lang="en">

<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link href="/static/{app_file.capitalize()}.css" rel="stylesheet">
  <script defer="defer" src="/static/{app_file.capitalize()}.js" ></script>
</head>

<body>
  <noscript>You need to enable JavaScript to run this app.</noscript>
  <div id="root" />
</body>

</html>
  """

@app.get("/", response_class=HTMLResponse, tags=["UI"])
@app.get("/ui", response_class=HTMLResponse, tags=["UI"])
async def new_app_ui():
  # return a completely generic index.html that assumes the app is
  # available on App_file.js (note initial cap)
  return await app_ui('root')

# TODO: find out the actual configured port at runtime
logger.info("Tana Helper running on port 8000")
logger.info("Try opening http://localhost:8000/")
