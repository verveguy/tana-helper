from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from logging import getLogger

logger = getLogger()

router = APIRouter()

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