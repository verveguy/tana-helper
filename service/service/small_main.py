from logging import getLogger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from service.logconfig import setup_rich_logger
from service.endpoints.api_docs import get_api_metadata

log_filename = None

def get_app() -> FastAPI:
  global log_filename
  app = FastAPI(
    **get_api_metadata(),
    )
  log_filename = setup_rich_logger()
  return app

app = get_app()

logger = getLogger()

logger.info(f"Log file is {log_filename}")

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



@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def new_app_ui():
  # return a completely generic index.html that assumes the app is
  # available on App_file.js (note initial cap)
  return """
<html>
  <head>
    <title>Tana Helper</title>
  </head>
  <body>
    <h1>Welcome to Tana Helper</h1>
  </body>
  </html>
  """

# TODO: find out the actual configured port at runtime
logger.info("Tana Helper running on port 8000")
logger.info("Try opening http://localhost:8000/")
