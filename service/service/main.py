import os
import platform
import time
from logging import getLogger

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from service.dependencies import settings
from service.endpoints import (calendar, chroma, class_diagram, configure, exec_code, graph_view, 
                 inlinerefs, jsonify, preload, cleanups, proxy, research, topics, weaviate, webhooks)
from service.logconfig import setup_rich_logger
from snowflake import SnowflakeGenerator

def get_app() -> FastAPI:
  app = FastAPI(
    description="Tana Helper", version="0.0.2",
    # TODO: get servers from passed in cmd line / env var
    servers=[
      {"url": "https://verveguy.ngrok.app", "description": "Personal laptop"},
    ])
  setup_rich_logger()
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

app.include_router(weaviate.router)
# TODO: uprgade pinecone code
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


@app.get("/usage", response_class=HTMLResponse)
async def usage():
  return """<html>
  Tana-helper service is running.
  See the Tana Template at <a href="https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A">https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A</a>
  </html>
  """

# fiddle with the CWD to satsify double-clickable .app
# context
basedir = os.path.dirname(__file__)
logger.info(f"Install dir = {basedir}")
cwd = os.getcwd()
logger.info(f"Current working dir = {cwd}")
os.chdir(basedir)
cwd = os.getcwd()
logger.info(f"Setting cwd = {cwd}")

app.mount("/static", StaticFiles(directory="dist"), name="static")

favicon_path = os.path.join(basedir,'dist','assets','favicon.ico')

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
  return FileResponse(favicon_path)


@app.get("/", response_class=HTMLResponse, tags=["Usage"])
async def root():
  return """
<div>
<h1>About Tana Helper</h1>
<p>
Simple API service that provides a variety useful API services to complement your daily use of Tana.

Most payloads are in JSON. Most results are in Tana paste format.

See the <a href="https://tana.pub/EufhKV4ZMH/tana-helper">Tana Publish page</a> for more usage information and examples.

There's also a <a href="https://app.tana.inc/?bundle=cVYW2gX8nY.EufhKV4ZMH">Tana template</a> that you can load into your Tana workspace with all the Tana commands preconfigured, demo nodes, etc.

<h2>UI Apps</h2>
<ul>
<li><a href="/redoc">Tana Helper API Documentation</a></li>
<li><a href="/ui/graph">Workspace Visualizer</a></li>
<li><a href="/ui/classdiagram">Tana Tag Hierarchy Diagram</a></li>
</ul>
</p>
</div>
"""

# expose our various Webapps on /ui/{app_name}
@app.get("/ui/{app_file}", response_class=HTMLResponse, tags=["Visualizer"])
async def app_ui(app_file:str):
  # return a completely generic index.html that assumes the app is
  # available on App_file.js (note initial cap)
  return f"""<!doctype html>
<html lang="en">

<head>
  <title>Tana Graph Viewer</title>
  <script defer="defer" src="/static/{app_file.capitalize()}.js" ></script>
</head>

<body>
  <noscript>You need to enable JavaScript to run this app.</noscript>
  <div id="root"></div>
</body>

</html>
  """