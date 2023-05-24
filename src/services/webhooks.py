from fastapi import APIRouter, status, Response, Body, Header, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from typing import Union, Annotated
from ..dependencies import OpenAICompletion, get_chatcompletion, settings
from starlette.requests import Request
from logging import getLogger
import httpx
import openai
from openai.error import AuthenticationError
import json
import re
import os

router = APIRouter()

logger = getLogger()

path = settings.template_path

environment = Environment(loader=FileSystemLoader(path))
# pattern to strip URLs out of incoming 
pattern = re.compile(r'\(?"?http[^\t ")]*"?\)?')

# Schema upload handlers

# Add a new OpenAI Prompt template by POST to /template/<typename>
# Allows for customized prompts
@router.post("/template/{schema}", status_code=status.HTTP_204_NO_CONTENT)
async def add_template(schema:str, body:str=Body(...)):
  # create file from body
  try:
    if not os.path.exists(path):
      os.mkdir(path)
    with open(f'{path}/{schema}.jn2', 'w') as template_file:
      print(body, file=template_file)
      logger.debug(f'Saved template {path}/{schema}.jn2')
  except IOError as e:
    raise HTTPException(detail = e.strerror, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

  return None

# GET the template for a schema_name
@router.get("/template/{schema}", response_class=HTMLResponse)
async def get_template(schema:str):
  try:
      with open(f'{path}/{schema}.jn2', 'r') as template_file:
        body = template_file.read()
      return body
  except IOError as e:
    logger.warning(f'Failed to read file {path}/{schema}.jn2')
    raise HTTPException(detail = e.strerror, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Add a new Tana schema by POST of Tana schema to /schema/<typename>
# generates a standard OpenAI prompt from the schema
@router.post("/schema/{schema}", status_code=status.HTTP_204_NO_CONTENT)
async def add_schema(schema:str, body:str=Body(...)):
  # create template from standard prompt + body (schema def)
  template = '''TASK: Extract information from CONTEXT 

OUTPUT FORMAT: as a JSON structure following the TYPESCRIPT DEFINITION. Output only a valid JSON structure.

''' + body + '''

CONTEXT: {{ context }}

OUTPUT: 
{'''
  return await add_template(schema, template)


# workhorse function for processing webhooks
async def do_webhook(schema: str, body: str):
  try:
    # strip all URLs and take first 6000 chars
    body = re.sub(pattern, '', body)
    body = body[0:6000]
    
    # stuff the body into the OpenAI prompt template
    try:
      temp = environment.get_template(schema+".jn2")
      prompt = temp.render({"context": body})
    except TemplateNotFound:
      logger.warning(f'Failed to find template {path}/{schema}.jn2')
      raise HTTPException(detail=f'Schema {schema} not found. Upload first', status_code=status.HTTP_400_BAD_REQUEST)
    
    # ask OpenAI to turn trash into gold
    completion_request = OpenAICompletion(prompt=prompt, max_tokens=1000, temperature=0)
    completion = get_chatcompletion(completion_request)
    logger.debug(f'Result from OpenAI: {completion}')

    jsonstring = '{' + completion['choices'][0].message.content
    tana_payload = json.loads(jsonstring)

    callback_url = "https://europe-west1-tagr-prod.cloudfunctions.net/addToNodeV2"
    headers = {'Authorization': 'Bearer ' + settings.tana_api_token}
    tana_result = httpx.post(callback_url, json={ 'nodes': [tana_payload]}, headers=headers)
    
    if tana_result.is_error:
      raise HTTPException(status_code=tana_result.status_code, detail=tana_result.content)

    return tana_result.content
  
  except AuthenticationError as e:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OpenAI Authentication Error. Did you pass your OpenAI API Key in X-OpenAI-API-Key header or set your service env variable?")
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=''.join(e.args))


# Webhook request handlers

# Accept query params /webhook?schema=<schema_name>
@router.post("/webhook")
async def webhook(schema:str, body:str=Body(...)):
  return await do_webhook(schema, body)
   
# Accept path parm /webhook/<schema>
@router.post("/webhook/{schema}")
async def webhook_alt(schema:str, body:str=Body(...)):
  return await do_webhook(schema, body)