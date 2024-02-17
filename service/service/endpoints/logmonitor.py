import asyncio
import aiofiles
from fastapi import APIRouter, Request, Response, WebSocket, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from service.logconfig import get_logger_config
from service.dependencies import settings

router = APIRouter()

# log streaming
log_config, log_filename = get_logger_config()
# log_file = log_config.logger_file

@router.websocket("/ws/log")
async def websocket_endpoint_log(websocket: WebSocket) -> None:
  """WebSocket endpoint for client connections

  Args:
      websocket (WebSocket): WebSocket request from client.
  """
  await websocket.accept()

  try:
    # TODO: instead of reading the file, tap into the logging stream before it goes to the file
    async with aiofiles.open(f"{log_filename}", "r") as file:
      # read n lines from the file
      while True:
        line = await file.readline()
        if line != '':
          await websocket.send_text(line)
        else:
          # TODO: how to make the readline() block until there is a line?
          await asyncio.sleep(2)

  except Exception as e:
    print(e)
  finally:
    await websocket.close()

