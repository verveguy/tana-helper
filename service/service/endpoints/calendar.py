import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import subprocess

from typing import Optional
from pydantic import BaseModel
from fastapi.responses import HTMLResponse

from logging import getLogger

from service.dependencies import CalendarRequest
import re

logger = getLogger()

router = APIRouter()


@router.post("/calendar", response_class=HTMLResponse, tags=["Calendar"])
async def get_calendar(request: CalendarRequest):
  # Run the calendar_auth.scpt1 script
  output, err = run_command(os.path.abspath(os.path.join(os.sep, 'usr', 'bin', 'osascript')), [os.path.join('scripts', 'calendar_auth.scpt')])
  if err:
    return f'Failed to run calendar_auth.scpt script.\nError {err}'

  # now run the actual getcalendar swift workhorse
  output, err = run_calendar_swift_script(request)
  if err:
    return f'Error running getcalendar.swift script.\nError {err}'

  return output

def run_command(script:str, args:list) -> tuple[str, str]:
  logger.info(f"run_command:script={script} args={' '.join(args)}")
  try:
    process = subprocess.Popen([script] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout.decode('utf-8'), stderr.decode('utf-8')
  except Exception as e:
    message = f'Exception running command {script} {args}: {e}'
    logger.error(message)
  return "", message

def run_calendar_swift_script(payload: CalendarRequest):
  cmd = os.path.join('bin', 'getcalendar')
  args = ["-noheader"]

  if payload.calendar:
    args += ["-calendar", payload.calendar]
  if payload.me:
    args += ["-me", payload.me]
  if payload.one2one:
    args += ["-one2one", payload.one2one]
  if payload.meeting:
    args += ["-meeting", payload.meeting]
  if payload.person:
    args += ["-person", payload.person]
  if payload.offset:
    args += ["-offset", payload.offset]
  if payload.range:
    args += ["-range", payload.range]
  if payload.date:
    # unwrap tana date format [[date:2024-03-20]] to 2024-03-20
    date = re.sub(r'\[\[date:(.*?)\]\]', r'\1', payload.date)
    args += ["-date", date]
  if payload.solo:
    args += ["-solo"]

  cwd = os.getcwd()
  output, err = run_command(os.path.join(cwd,cmd), args)

  if err:
    return "Error running getcalendar.swift script.\nError {err}", err

  if not output:
    return "No events found. Check that you are requesting the correct calendar.", None

  return output, None
