from fastapi import APIRouter, Body, Header
from ..dependencies import tana_to_json
from starlette.requests import Request
from logging import getLogger

router = APIRouter()

logger = getLogger()

@router.post("/jsonify")
async def jsonify(req:Request, 
                     body:str=Body(...)):
  tana_format = bytes(body, "utf-8").decode("unicode_escape")  
  logger.debug(tana_format)
  json_format = tana_to_json(tana_format)
  logger.debug(json_format)
  return json_format

