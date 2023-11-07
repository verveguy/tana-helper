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
from service.dependencies import settings
from typing import Optional

# BASED ON https://www.pythonbynight.com/blog/sharpen-your-code

class LoggerConfig(BaseModel):
    handlers: list
    format: str
    date_format: Optional[str] = None
    logger_file: Optional[Path] = None
    # level: int = logging.DEBUG  # change this for DEBUG
    level: int = logging.INFO # change this for DEBUG


LOGGER_FILE = Path(settings.logger_file)  # where log is stored
DATE_FORMAT = "%d %b %Y | %H:%M:%S"
LOGGER_FORMAT = "%(asctime)s | %(threadName)s | %(message)s"

@lru_cache
def get_logger_config():
    """Installs RichHandler (Rich library) if not in production
    environment, or use the production log configuration.
    """

    if not settings.production:
        from rich.logging import RichHandler
        output_file_handler = logging.FileHandler(LOGGER_FILE)
        handler_format = logging.Formatter(
            LOGGER_FORMAT, datefmt=DATE_FORMAT)
        output_file_handler.setFormatter(handler_format)

        return LoggerConfig(
            handlers=[
                RichHandler(
                    rich_tracebacks=True,
                    tracebacks_show_locals=True,
                    show_time=False,
                    tracebacks_suppress=[fastapi, uvicorn, asyncio, anyio, starlette, h11]
                ),
                output_file_handler
            ],
            format=LOGGER_FORMAT, # changed from None
            date_format=DATE_FORMAT,
            logger_file=LOGGER_FILE,
        )

    output_file_handler = logging.FileHandler(LOGGER_FILE)
    handler_format = logging.Formatter(
        LOGGER_FORMAT, datefmt=DATE_FORMAT)
    output_file_handler.setFormatter(handler_format)

    # Stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(handler_format)

    return LoggerConfig(
        handlers=[output_file_handler, stdout_handler],
        format="%(levelname)s: %(asctime)s %(threadName)s \t%(message)s",
        date_format="%d-%b-%y %H:%M:%S",
        logger_file=LOGGER_FILE,
    )

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

    logger_config = get_logger_config()  # get Rich logging config

    logging.basicConfig(
        level=logger_config.level,
        format=logger_config.format,
        datefmt=logger_config.date_format,
        handlers=logger_config.handlers,
    )