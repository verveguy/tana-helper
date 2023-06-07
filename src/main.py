from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from logging import getLogger
from .services import pinecone, inlinerefs, exec_code, webhooks, jsonify, graph_view
from .dependencies import settings
from .logging import setup_rich_logger
from snowflake import SnowflakeGenerator
import time

def get_app() -> FastAPI:
    app = FastAPI()
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
app.include_router(pinecone.router)
app.include_router(inlinerefs.router)
app.include_router(exec_code.router)
app.include_router(webhooks.router)
app.include_router(jsonify.router)
app.include_router(graph_view.router)

@app.middleware("http")
async def add_get_authorization_headers(request: Request, call_next):
    # find headers in request
    x_tana_api_token = request.headers.get('x-tana-api-token')
    x_openai_api_key = request.headers.get('x-openai-api-key')
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
  logger.info(f"txid={idem} start request path={request.url.path}")
  start_time = time.time()
    
  response = await call_next(request)

  process_time = (time.time() - start_time) * 1000
  formatted_process_time = '{0:.2f}'.format(process_time)
  logger.info(f"txid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")
  if not x_request_id:
     response.headers['x-request-id'] = str(idem)
  return response

@app.get("/", response_class=HTMLResponse)
@app.get("/usage", response_class=HTMLResponse)
async def usage():
  return """<html>
  Pinecone Experiments for use with Tana

  See the Tana Template at <a href="https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A">https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A</a>
  </html>
  """
