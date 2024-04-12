import os
import fastapi
import asyncio
import anyio
import starlette
import h11
import logging
import sys
import uvicorn
from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
from service.settings import settings
from typing import Optional

import logging
import os
import platform
from logging.handlers import RotatingFileHandler

# BASED ON https://www.pythonbynight.com/blog/sharpen-your-code

# TODO: figure out what production should mean now
production = False

class LoggerConfig(BaseModel):
  handlers: list
  format: str
  date_format: Optional[str] = None
  logger_file: Optional[Path] = None
  # level: int = logging.DEBUG  # change this for DEBUG
  level: int = logging.INFO # change this for DEBUG


def get_log_path(app_name):
    if platform.system() == "Windows":
        base_dir = os.path.join(os.getenv('APPDATA'), app_name, "Logs") #type: ignore
    else:  # macOS and Linux-like
        base_dir = os.path.join(os.path.expanduser('~'), "Library", "Logs", app_name)
        
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    
    return os.path.join(base_dir, "application.log")


LOGGER_FILE = Path(get_log_path('TanaHelper'))  # where log is stored
DATE_FORMAT = "%d %b %Y | %H:%M:%S"
LOGGER_FORMAT = "%(asctime)s | %(threadName)s | %(message)s"

@lru_cache
def get_logger_config():
  """Installs RichHandler (Rich library) if not in production
  environment, or use the production log configuration.
  """

  logger_config = None
  if not production:
    from rich.logging import RichHandler
    from rich.console import Console
    
    rich_props = {
      'rich_tracebacks': True,
      'tracebacks_show_locals': False,
      'show_time': False,
      'tracebacks_suppress': [fastapi, uvicorn, asyncio, anyio, starlette, h11]
    }

    rich_handler = RichHandler(
      **rich_props
    )

    # TODO: turns this into a log stream, rather than a file
    # so we can pass raw logs to websocket monitor in logmonitor.py
    # TODO: Can Rich format log lines without a Console width or do we
    # need to glue all of this together somehow and pass width back to this 
    # layer?
    rich_log_file = open(LOGGER_FILE, "wt")
    rich_file_handler = RichHandler(
      console=Console(file=rich_log_file, force_terminal=True, soft_wrap=True, width=100),
      **rich_props
    )

    # output_file_handler = RotatingFileHandler(LOGGER_FILE, maxBytes=10*1024*1024, backupCount=5)
    # handler_format = logging.Formatter(
    #   LOGGER_FORMAT, datefmt=DATE_FORMAT)
    # output_file_handler.setFormatter(handler_format)

    logger_config = LoggerConfig(
      handlers=[
        rich_handler,
        # output_file_handler,
        rich_file_handler
      ],
      format=LOGGER_FORMAT, # changed from None
      date_format=DATE_FORMAT,
      logger_file=LOGGER_FILE,
    )

    return logger_config, os.path.abspath(rich_log_file.name)

  else:
    output_file_handler = logging.FileHandler(LOGGER_FILE)
    handler_format = logging.Formatter(
      LOGGER_FORMAT, datefmt=DATE_FORMAT)
    output_file_handler.setFormatter(handler_format)

    # Stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(handler_format)

    logger_config = LoggerConfig(
      handlers=[output_file_handler, stdout_handler],
      format="%(levelname)s: %(asctime)s %(threadName)s \t%(message)s",
      date_format="%d-%b-%y %H:%M:%S",
      logger_file=LOGGER_FILE,
    )

    return logger_config, os.path.abspath(LOGGER_FILE)


def setup_rich_logger():
  """Cycles through uvicorn root loggers to
  remove handler, then runs `get_logger_config()`
  to populate the `LoggerConfig` class with Rich
  logger parameters.
  """

  # Remove all handlers from root logger
  # and proprogate to root logger.
  for name in logging.root.manager.loggerDict.keys():
    logging.getLogger(name).handlers = []
    logging.getLogger(name).propagate = True

  logger_config, log_file_name = get_logger_config()  # get Rich logging config

  logging.basicConfig(
    level=logger_config.level,
    format=logger_config.format,
    datefmt=logger_config.date_format,
    handlers=logger_config.handlers,
  )

  # return path to log file
  return log_file_name
