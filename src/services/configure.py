from fastapi import APIRouter, Body, Header
from fastapi.responses import HTMLResponse
from ..dependencies import tana_to_json
from starlette.requests import Request
from logging import getLogger

router = APIRouter()

logger = getLogger()


# expose our configuration Webapp on /configure
@router.get("/ui/configure", response_class=HTMLResponse)
async def configure():
  return """<!doctype html>
<html lang="en">

<head>
  <title>Tana Helper Configuration</title>
  <script defer="defer" src="/static/webapp.js"></script>
</head>

<img src="/static/assets/clip2tana-512.png">
<body><noscript>You need to enable JavaScript to run this app.</noscript>
  <div id="root" style="width: 550px;" ></div>
</body>

</html>
  """
