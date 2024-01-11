from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from logging import getLogger
# note pinecone is not included - problems with PyInstaller and google API depedencies...
from service.endpoints import calendar, chroma, weaviate, inlinerefs, exec_code, webhooks, jsonify, graph_view, class_diagram, configure, proxy, topics
from service.logconfig import setup_rich_logger
from snowflake import SnowflakeGenerator
import time
import os
import platform
from service.dependencies import settings

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

app.include_router(chroma.router)
app.include_router(weaviate.router)
#app.include_router(pinecone.router)
app.include_router(inlinerefs.router)
app.include_router(exec_code.router)
app.include_router(webhooks.router)
app.include_router(jsonify.router)
app.include_router(graph_view.router)
app.include_router(class_diagram.router)
app.include_router(topics.router)
app.include_router(configure.router)
app.include_router(proxy.router)

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
    
  response:Response = await call_next(request)

  process_time = (time.time() - start_time) * 1000
  formatted_process_time = '{0:.2f}'.format(process_time)
  logger.info(f"txid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")
  if not x_request_id:
     response.headers['x-request-id'] = str(idem)
  return response


@app.get("/", response_class=HTMLResponse, tags=["Usage"])
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
print(f"Install dir = {basedir}")
cwd = os.getcwd()
print(f"Current working dir = {cwd}")
os.chdir(basedir)
cwd = os.getcwd()
print(f"Setting cwd = {cwd}")

app.mount("/static", StaticFiles(directory="dist"), name="static")

favicon_path = os.path.join(basedir,'dist','assets','favicon.ico')

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
  return FileResponse(favicon_path)


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