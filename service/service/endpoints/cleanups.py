from fastapi import APIRouter, Body
from fastapi.responses import HTMLResponse
from starlette.requests import Request
from logging import getLogger

router = APIRouter()

logger = getLogger()


@router.post("/cleanup_call_summary", response_class=HTMLResponse, tags=["Cleanup"])
async def cleanup_call_summary(req:Request, body:str=Body(...)):
  """Cleanup a Krisp call summary after cut/paste into Tana"""
  tana_format = bytes(body, "utf-8").decode("unicode_escape")

  output = ""
  indent_next = False
  # really strange paragraph breaks in the call_summary, three spaces
  for line in tana_format.split("   "):
    line = line.strip()
    if line == '- **Summary**':
      continue
    if line == '':
      indent_next = False
      continue

    if indent_next:
      output += (f'  - {line}\n')
    else:
      output += (f'- {line}\n')
    indent_next = False

    if line.startswith('**'):
      indent_next = True
    

  return output
