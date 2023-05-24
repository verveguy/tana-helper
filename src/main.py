from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from .services import pinecone, inlinerefs, exec_code, webhooks
from .dependencies import settings

app = FastAPI()

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


@app.get("/", response_class=HTMLResponse)
@app.get("/usage", response_class=HTMLResponse)
async def usage():
  return """<html>
  Pinecone Experiments for use with Tana

  See the Tana Template at <a href="https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A">https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A</a>
  </html>
  """
