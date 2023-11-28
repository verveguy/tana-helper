import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import subprocess

from typing import Optional
from pydantic import BaseModel
from fastapi.responses import HTMLResponse

from logging import getLogger

logger = getLogger()

router = APIRouter()

class CalendarRequest(BaseModel):
    me: Optional[str] = None
    one2one: Optional[str] = None
    meeting: Optional[str] = None
    person: Optional[str] = None
    solo: Optional[bool] = None
    calendar: Optional[str] = None
    offset: Optional[str] = None
    range: Optional[str] = None

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
        logger.error(f'Exception running command {script} {args}: {e}')
    return "", "Failed to run command"

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
    if payload.solo:
        args += ["-solo"]

    cwd = os.getcwd()
    output, err = run_command(os.path.join(cwd,cmd), args)

    if err:
        return "Error running getcalendar.swift script.\nError {err}", err

    if not output:
        return "No events found. Check that you are requesting the correct calendar.", None

    return output, None
