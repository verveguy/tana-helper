from fastapi import APIRouter, Body, Header
from fastapi.responses import HTMLResponse
from service.settings import settings, set_settings, Settings
from service.json2tana import tana_to_json
from starlette.requests import Request
from logging import getLogger

router = APIRouter()

logger = getLogger()

# expose our configuration Webapp on /configure
@router.get("/configuration", tags=["Configuration"])
def configure():
  global settings
  return settings


@router.post("/configuration", tags=["Configuration"])
def set_configuration(new_settings:Settings):
  global settings
  settings = set_settings(new_settings)
  return settings

