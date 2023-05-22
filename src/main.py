from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from .services import pinecone, inlinerefs, exec_code

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

@app.get("/", response_class=HTMLResponse)
@app.get("/usage", response_class=HTMLResponse)
async def usage():
  return """<html>
  Pinecone Experiments for use with Tana

  See the Tana Template at <a href="https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A">https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A</a>
  </html>
  """
