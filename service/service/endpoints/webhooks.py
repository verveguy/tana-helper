from fastapi.responses import HTMLResponse
from fastapi import APIRouter, status, Body, HTTPException
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from service.dependencies import OpenAICompletion, get_chatcompletion, settings, LineTimer
from starlette.requests import Request
from logging import getLogger
import httpx
import json
import re
import os

router = APIRouter()

logger = getLogger()

path = settings.webhook_template_path

environment = Environment(loader=FileSystemLoader(path))
# pattern to strip URLs out of incoming 
pattern = re.compile(r'\(?"?http[^\t ")]*"?\)?')

# Schema upload handlers

@router.post("/template/{schema}", response_class=HTMLResponse, tags=["Webhooks"])
async def add_template(req:Request,
                       schema:str,
                       body:str=Body(...)):
  '''
  Add a new OpenAI Prompt template for a Tana schema and creates a webhook endpoint.
  Allows for fully customized prompts.
  '''
  # create file from body
  try:
    if not os.path.exists(path):
      os.makedirs(path, exist_ok=True)
    with open(f'{path}/{schema}.jn2', 'w') as template_file:
      print(body, file=template_file)
      logger.debug(f'Saved template {path}/{schema}.jn2')
  except IOError as e:
    raise HTTPException(detail = e.strerror, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

  return f'{req.base_url}webhook/{schema}'

@router.get("/schema", tags=["Webhooks"])
async def get_schemas():
  '''
  Retrieve a list of all existing webhook schemas (for configuration)
  '''
  try:
      directory = os.listdir(path)
      files = [f for f in directory if os.path.isfile(path+'/'+f)] #Filtering only the files.
      schemas = [s.split('.jn2')[0] for s in files if '.jn2' in s]
      return schemas
  except IOError as e:
    logger.warning(f'Failed to read directory {path}')
    raise HTTPException(detail = e.strerror, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/template/{schema}", response_class=HTMLResponse, tags=["Webhooks"])
async def get_template(schema:str):
  '''
  Retrieves the OpenAI Prompt template for the given Tana schema.
  '''
  try:
      with open(f'{path}/{schema}.jn2', 'r') as template_file:
        body = template_file.read()
      return body
  except IOError as e:
    logger.warning(f'Failed to read file {path}/{schema}.jn2')
    raise HTTPException(detail = e.strerror, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/schema/{schema}", response_class=HTMLResponse, tags=["Webhooks"])
async def add_schema(req:Request, 
                     schema:str, 
                     body:str=Body(...)):
  '''
  Create a new webhook endpoint from a Tana schema.
  Generates a standard OpenAI prompt from the schema that will convert data on webhook submission.
  To customize the prompt, call /template/<schema> instead.
  '''
  # create template from standard prompt + body (schema def)
  template = '''TASK: Extract information from CONTEXT 

OUTPUT FORMAT: as a JSON structure following the TYPESCRIPT DEFINITION. Output only a valid JSON structure.

TYPESCRIPT DEFINITION:
''' + body + '''

CONTEXT: {{ context }}

OUTPUT: 
{'''
  return await add_template(req, schema, template)

# Add a new Tana schema by POST of Tana schema to /schema/<typename>
# generates a standard OpenAI prompt from the schema
@router.delete("/schema/{schema}", tags=["Webhooks"])
async def delete(schema:str):
  '''
  Remove the webhook endpoints for a Tana schema previously registered.
  '''
  try:
    if not os.path.exists(path):
      os.mkdir(path)
    os.remove(f'{path}/{schema}.jn2')
    logger.debug(f'Removed template file {path}/{schema}.jn2')
  except IOError as e:
    raise HTTPException(detail = e.strerror, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

  return None

# workhorse function for processing webhooks
async def do_webhook(schema: str, body: str):
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
  
  try:
    # ask OpenAI to turn trash into gold
    completion_request = OpenAICompletion(prompt=prompt,
                                          max_tokens=1000, 
                                          temperature=0, 
                                          model='gpt-4'
                                          )
    with LineTimer('openai'):
      completion = get_chatcompletion(completion_request)
    logger.debug(f'Result from OpenAI: {completion}')

  except Exception as e:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OpenAI Authentication Error. Did you pass your OpenAI API Key in X-OpenAI-API-Key header or set your service env variable?")

  jsonstring = '{' + completion['choices'][0].message.content
  tana_payload = { 'nodes': [json.loads(jsonstring)] }

  callback_url = "https://europe-west1-tagr-prod.cloudfunctions.net/addToNodeV2"
  headers = {'Authorization': 'Bearer ' + settings.tana_api_token}

  try:
    with LineTimer('tana-input'):
      tana_result = httpx.post(callback_url, json=tana_payload, headers=headers)
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)

  if tana_result.is_error:
    logger.warning(f'Tana input API failed. {tana_result.status_code}. Detail: {tana_result.text}')
    raise HTTPException(status_code=tana_result.status_code, detail=tana_result.text)

  return tana_result.content


# Webhook request handlers

# Accept query params /webhook?schema=<schema_name>
@router.post("/webhook", tags=["Webhooks"])
async def webhook(schema:str, body:str=Body(...)):
  return await do_webhook(schema, body)
   
# Accept path parm /webhook/<schema>
@router.post("/webhook/{schema}", tags=["Webhooks"])
async def webhook_alt(schema:str, body:str=Body(...)):
  return await do_webhook(schema, body)

 
# Accept path parm /webhook/<schema>
@router.get("/webhooks", tags=["Webhooks"])
async def webhook_configuration():
  result = []
  schemas = await get_schemas()
  for schema in schemas:
    result = result.append(schema)
  return result