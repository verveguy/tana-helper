from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from logging import getLogger

logger = getLogger()

router = APIRouter()

def get_api_metadata():
  return {
    'title':"Tana Helper",
    'version':"0.2.0", # TODO: make this configured at build time somehow
    'description':"""
Tana Helper API helps you do awesome stuff. 🚀

Most of this API is intended to be called from the `Make API request` command in Tana.
As a result, most API calls return data in "Tana paste" format.

See the [Tana Helper GitHub](https://www.github.com/verveguy/tana-helper) for more information.
Also see 

""",
    'summary':"API for the Tana Helper service that augments Tana.",
    # TODO: get servers from passed in cmd line / env var
    'servers':[
      {"url": "http://localhost:8000", "description": "Local loopback"},
      {"url": "https://verveguy.ngrok.app", "description": "ngrok test"},
    ],
    
    'terms_of_service':"https://www.github.com/verveguy/tana-helper",
    'contact':{
      "name": "Verveguy https://tanacommunity.slack.com/team/U04H7HN2AE7",
      # "url": "https://tanacommunity.slack.com/team/U04H7HN2AE7",
      },
    'license_info':{
      "identifier": "MIT",
      "name": "MIT"
      },
    'openapi_tags': [
      {
        "name": "Calendar",
        "description": "Get your calendar events in Tana Paste format.",
      },
      {
        "name": "items",
        "description": "Manage items. So _fancy_ they have their own docs.",
        "externalDocs": {
          "description": "Items external docs",
          "url": "https://fastapi.tiangolo.com/",
        },
      },
    ],
  }



async def get_openapi_url_in_route(req: Request):
    return req.app.openapi_url

@router.get("/rapidoc", response_class=HTMLResponse, include_in_schema=False)
async def rapidoc(req:Request):
    openapi_url = await get_openapi_url_in_route(req)
    return f"""
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8">
                <script 
                    type="module" 
                    src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"
                ></script>
            </head>
            <body>
                <rapi-doc spec-url="{openapi_url}"></rapi-doc>
            </body> 
        </html>
    """