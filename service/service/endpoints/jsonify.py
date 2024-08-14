from fastapi import APIRouter, status, Body, HTTPException
from fastapi.responses import HTMLResponse
from service.json2tana import json_to_tana, tana_to_json
from service.settings import settings
from starlette.requests import Request
from logging import getLogger
import json
import os
import csv

router = APIRouter()

logger = getLogger()

def extract_json_from_code_node(payload):
  # this is a code node full of json
  left = payload.find('```json\n')+8
  right = payload.rfind('```\n')
  return payload[left:right]

@router.post("/jsonify", tags=["Conversions"])
async def jsonify(req:Request, body:str=Body(...)):
  tana_format = bytes(body, "utf-8").decode("unicode_escape")  
  object_graph = tana_to_json(tana_format)
  return object_graph

@router.post("/tanify", response_class=HTMLResponse, tags=["Conversions"])
async def tanify(body:str=Body(...)):
  raw_body = bytes(body, "utf-8").decode("unicode_escape")
  if raw_body.startswith('```json'):
    # this is a code node full of json
    raw_body = extract_json_from_code_node(raw_body)
  json_format = json.loads(raw_body)
  tana_format = json_to_tana(json_format)
  return tana_format

@router.post("/tana-to-code", response_class=HTMLResponse, tags=["Conversions"])
async def tana_to_code(body:str=Body(...)):
  tana_format = bytes(body, "utf-8").decode("unicode_escape")  
  object_graph = tana_to_json(tana_format)
  json_format = json.dumps(object_graph, indent=2)
  result_format = '```json\n'+json_format+'\n```\n'
  return result_format

@router.post("/code-to-json", tags=["Conversions"])
async def code_to_json(body:str=Body(...)):
  tana_format = bytes(body, "utf-8").decode("unicode_escape").rstrip()
  code_content = extract_json_from_code_node(tana_format)
  object_graph = json.loads(code_content)
  return object_graph

@router.post("/export/{filename}", response_class=HTMLResponse, tags=["Export"])
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

@router.post("/echo", response_class=HTMLResponse, tags=["Echo"])
async def echo(body:str=Body(...)):
  result = bytes(body, "utf-8").decode("unicode_escape")  
  return result

@router.post("/childless", response_class=HTMLResponse, tags=["Conversions"])
async def childless(req:Request, body:str=Body(...)):
  tana_format = bytes(body, "utf-8").decode("unicode_escape")  
  object_graph = tana_to_json(tana_format)
  empty_nodes = []
  # start with the root node of the context
  root_list = object_graph[0]['children']
  for each in root_list:
    if not 'children' in each or len(each['children']) == 0:
        # only append a reference to the node if it has NO children
        empty_nodes.append(each['name'])
  
  tana_paste = f'- Childless nodes within {object_graph[0]["name"]}\n'
  for ref in empty_nodes:
    tana_paste += f'  - {ref}\n'
    
  return tana_paste

