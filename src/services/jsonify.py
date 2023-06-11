from fastapi import APIRouter, status, Body, HTTPException
from fastapi.responses import HTMLResponse
from ..dependencies import tana_to_json
from starlette.requests import Request
from logging import getLogger
from ..dependencies import settings
import json
import os

router = APIRouter()

logger = getLogger()

@router.post("/jsonify")
async def jsonify(req:Request, 
                     body:str=Body(...)):
  
  tana_format = bytes(body, "utf-8").decode("unicode_escape")  
  logger.debug(tana_format)
  object_graph = tana_to_json(tana_format)
  logger.debug(object_graph)
  return object_graph

@router.post("/export/{filename}", response_class=HTMLResponse)
async def export_to_file(req:Request, filename:str,
                     body:str=Body(...)):

  object_graph = await jsonify(req, body)
  # sanitize filename first
  if '..' in filename:
    raise HTTPException(detail = 'Invalid filename', status_code=status.HTTP_403_FORBIDDEN)
  
  path = settings.export_path
  filepath = f'{path}/{filename}.json'

  # write to file name
  try:
    if not os.path.exists(path):
      os.makedirs(path, exist_ok=True)
    
    json_format = json.dumps(object_graph)
    with open(filepath, 'w') as output_file:
      print(json_format, file=output_file)
      logger.debug(f'Saved output to {filepath}')
  except IOError as e:
    raise HTTPException(detail = e.strerror, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

  return f'{filepath}'