from fastapi import APIRouter, status, Body, HTTPException
from fastapi.responses import HTMLResponse
from ..dependencies import tana_to_json, json_to_tana
from starlette.requests import Request
from logging import getLogger
from ..dependencies import settings
import json
import os
import csv

router = APIRouter()

logger = getLogger()

@router.post("/jsonify")
async def jsonify(req:Request, body:str=Body(...)):
  tana_format = bytes(body, "utf-8").decode("unicode_escape")  
  logger.debug(tana_format)
  object_graph = tana_to_json(tana_format)
  logger.debug(object_graph)
  return object_graph

@router.post("/tanify", response_class=HTMLResponse)
async def tanify(body:str=Body(...)):
  raw_body = bytes(body, "utf-8").decode("unicode_escape")
  json_format = json.loads(raw_body)
  tana_format = json_to_tana(json_format)
  return tana_format

@router.post("/tana-to-code", response_class=HTMLResponse)
async def tana_to_code(body:str=Body(...)):
  tana_format = bytes(body, "utf-8").decode("unicode_escape")  
  object_graph = tana_to_json(tana_format)
  json_format = json.dumps(object_graph, indent=2)
  result_format = '```json\n'+json_format+'\n```\n'
  return result_format


@router.post("/export/{filename}", response_class=HTMLResponse)
async def export_to_file(req:Request, filename:str, format='json',
                     body:str=Body(...)):

  # sanitize filename
  if '..' in filename:
    raise HTTPException(detail = 'Invalid filename', status_code=status.HTTP_403_FORBIDDEN)

  # first build an object graph from input Tana data
  object_graph = await jsonify(req, body)

  path = settings.export_path
  filepath = f'{path}/{filename}.{format}'

  # write to file name
  try:
    if not os.path.exists(path):
      os.makedirs(path, exist_ok=True)
   
    with open(filepath, 'w') as output_file:
       
      if format == 'json':
        json_format = json.dumps(object_graph, indent=2)
        print(json_format, file=output_file)
      elif format == 'csv':
        # assume root is a single object, given the way Tana works
        root = object_graph[0]
        if 'children' in root:
          rows = object_graph[0]['children']
        else:
          # just one lone object...spit it out
          rows = [root]
        writer = csv.DictWriter(output_file, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
          # TODO: handle code blocks - multiline values
          # need to escape any \n chars
          writer.writerow(row)

      logger.debug(f'Saved output to {filepath}')
  except IOError as e:
    raise HTTPException(detail = e.strerror, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

  return f'{filepath}'