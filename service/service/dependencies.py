import io
import logging
import re
from datetime import datetime
from logging import getLogger
from timeit import timeit
from typing import ForwardRef

import httpx
import pytz
from fastapi import HTTPException, status
from fastapi.concurrency import asynccontextmanager
from openai import APIError, AsyncOpenAI, AuthenticationError, OpenAI, RateLimitError
from pydantic import BaseModel

from . import settings

# Load environment variables from .env file
# load_dotenv()

app_name = "TanaHelper"

# production: Annotated[bool, Field(title="Production",
#   description="Whether we are running in production mode")] \
#     = False

# templates:object = None


# Types for our APIs to use

TANA_TEXT = "tana-text"
TANA_NODE = "tana-node"


class CalendarRequest(BaseModel):
    me: str | None = None
    one2one: str | None = None
    meeting: str | None = None
    person: str | None = None
    solo: bool | None = None
    calendar: str | None = None
    offset: str | None = None
    range: str | None = None
    date: str | None = None
    # model_config = ConfigDict(extra='forbid')


class HelperRequest(BaseModel):
    context: str = ""
    name: str = ""


class NodeRequest(HelperRequest):
    nodeId: str


class ExecRequest(BaseModel):
    code: str | None = ""
    call: str
    payload: dict


class OpenAIRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
    embedding_model: str = "text-embedding-ada-002"


class OpenAICompletion(OpenAIRequest):
    prompt: str
    max_tokens: int | None
    temperature: int | None = 0


class EmbeddingRequest(HelperRequest, OpenAIRequest):
    # union type, nothing to add
    pass


class PineconeRequest(EmbeddingRequest):
    pinecone: str
    environment: str | None = settings.settings.tana_environment
    index: str | None = settings.settings.tana_index
    score: float | None = 0.80
    top: int | None = 10
    tags: str | None = ""
    nodeId: str


class PineconeNode(BaseModel):
    category: str = TANA_NODE
    supertag: list[str] | None = []
    text: str


class ChromaStoreRequest(BaseModel):
    environment: str | None = "local"


class ChromaRequest(EmbeddingRequest, ChromaStoreRequest):
    score: float | None = 0.80
    top: int | None = 10
    tags: str | None = ""
    nodeId: str


class LlamaRequest(EmbeddingRequest):
    score: float | None = 0.80
    top: int | None = 10
    tags: str | None = ""
    nodeId: str


class LlamaindexAsk(BaseModel):
    query: str


class TanaNodeMetadata(BaseModel):
    category: str = TANA_NODE
    title: str
    supertag: str | None = None
    topic_id: str
    tana_id: str | None = None
    text: str | None = None


class QueueRequest(HelperRequest):
    pass


class WeaviateRequest(EmbeddingRequest):
    environment: str | None = settings.settings.tana_environment
    index: str | None = settings.settings.tana_index
    score: float | None = 0.80
    top: int | None = 10
    tags: str | None = ""
    nodeId: str | None = None


class ChainsRequest(HelperRequest, OpenAIRequest):
    serpapi: str | None = None
    wolfram: str | None = None
    iterations: int | None = 6


# Tana Input API


class SuperTag(BaseModel):
    id: str


Node = ForwardRef("Node")  # type: ignore


class Node(BaseModel):
    name: str
    description: str | None = None
    supertags: list[SuperTag] | None = None
    children: list[Node] | None = None


# Pydantic models can be nested, this is how you reference the same model
# Node.update_forward_refs()
# Node.model_rebuild()


class AddToNodeRequest(BaseModel):
    nodes: list[Node]
    targetNodeId: str | None = None


# Utility classes

logger = getLogger()


class TanaInputAPIClient:
    def __init__(
        self,
        base_url: str = "https://europe-west1-tagr-prod.cloudfunctions.net",
        auth_token: str | None = None,
    ):
        self.base_url = base_url
        self.client = httpx.Client(verify=True)
        self.headers = {"Content-Type": "application/json"}
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

    def add_to_inbox(self, request_data: AddToNodeRequest):
        url = f"{self.base_url}/addToNodeV2"
        response = self.client.post(
            url, json=request_data.model_dump(exclude_unset=True), headers=self.headers
        )
        return response


def clean_openai_error_message(error_str: str) -> str:
    """
    Clean up OpenAI error messages to remove JSON formatting and extract key information.
    """
    try:
        # Try to extract the error message from JSON-like structure
        # Look for patterns like "{'error': {'message': '...'}}"
        json_pattern = r"{'error':\s*{'message':\s*'([^']+)'"
        match = re.search(json_pattern, error_str)
        if match:
            return match.group(1)

        # Try to extract from "Error code: XXX - {...}" pattern
        error_code_pattern = r"Error code: \d+ - .*'message':\s*'([^']+)'"
        match = re.search(error_code_pattern, error_str)
        if match:
            return match.group(1)

        # If no JSON pattern found, return the original string
        return error_str
    except Exception:
        # If anything goes wrong with parsing, return original
        return error_str


# OpenAI helper functions


async def get_embedding(req: EmbeddingRequest):
    """
    Get embeddings from OpenAI API with proper error handling.

    The middleware ensures global settings are always fresh from file + headers.

    Raises appropriate HTTPExceptions for different error types:
    - 401 for authentication errors
    - 429 for rate limit errors
    - 400 for other API errors
    - 503 for service unavailable
    """
    # Use global settings (refreshed by middleware on every request)
    api_key = settings.settings.openai_api_key
    logger = getLogger()
    logger.info("get_embedding called - using refreshed settings")

    # Log the settings object ID for debugging (but not the key value)
    logger.info(f"get_embedding using settings object ID: {id(settings.settings)}")

    # Check if API key is missing or looks like a placeholder
    if not api_key or api_key == "OPENAI_API_KEY NOT SET" or "NOT SET" in api_key:
        logger.error("OpenAI API key not configured for embeddings")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OpenAI API key not configured. Please set your API key in configuration.",
        )

    openai_client = AsyncOpenAI(api_key=api_key)
    content = req.name + req.context

    try:
        embedding = await openai_client.embeddings.create(
            input=content, model=req.embedding_model
        )
        return embedding.data  # type: ignore
    except AuthenticationError as e:
        logger = getLogger()
        logger.error(f"OpenAI authentication failed for embedding request: {str(e)}")
        clean_message = clean_openai_error_message(str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OpenAI authentication failed: {clean_message}. Please check your API key.",
        ) from e
    except RateLimitError as e:
        logger = getLogger()
        logger.warning(f"OpenAI rate limit exceeded for embedding request: {str(e)}")
        clean_message = clean_openai_error_message(str(e))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"OpenAI rate limit exceeded: {clean_message}. Please try again later.",
        ) from e
    except APIError as e:
        logger = getLogger()
        logger.error(f"OpenAI API error for embedding request: {str(e)}")
        clean_message = clean_openai_error_message(str(e))
        # Handle other OpenAI API errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OpenAI API error: {clean_message}. Please check your API key.",
        ) from e
    except Exception as e:
        logger = getLogger()
        logger.error(f"Unexpected error in get_embedding: {str(e)}")
        # Handle any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service temporarily unavailable: {str(e)}",
        ) from e


def get_chatcompletion(req: OpenAICompletion) -> dict:
    """
    Get chat completion from OpenAI API with proper error handling.

    The middleware ensures global settings are always fresh from file + headers.

    Raises appropriate HTTPExceptions for different error types:
    - 401 for authentication errors
    - 429 for rate limit errors
    - 400 for other API errors
    - 503 for service unavailable
    """
    # Use global settings (refreshed by middleware on every request)
    api_key = settings.settings.openai_api_key

    # Check if API key is missing or looks like a placeholder
    if not api_key or api_key == "OPENAI_API_KEY NOT SET" or "NOT SET" in api_key:
        logger = getLogger()
        logger.error(
            f"OpenAI API key not configured for chat completion. Current value: {api_key}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OpenAI API key not configured. Please set your API key in configuration.",
        )

    openai_client = OpenAI(api_key=api_key)

    try:
        completion = openai_client.chat.completions.create(
            messages=[{"role": "user", "content": req.prompt}],
            model=req.model,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
        return completion  # type: ignore
    except AuthenticationError as e:
        logger = getLogger()
        logger.error(
            f"OpenAI authentication failed for chat completion request: {str(e)}"
        )
        clean_message = clean_openai_error_message(str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OpenAI authentication failed: {clean_message}. Please check your API key.",
        ) from e
    except RateLimitError as e:
        logger = getLogger()
        logger.warning(
            f"OpenAI rate limit exceeded for chat completion request: {str(e)}"
        )
        clean_message = clean_openai_error_message(str(e))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"OpenAI rate limit exceeded: {clean_message}. Please try again later.",
        ) from e
    except APIError as e:
        logger = getLogger()
        logger.error(f"OpenAI API error for chat completion request: {str(e)}")
        clean_message = clean_openai_error_message(str(e))
        # Handle other OpenAI API errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OpenAI API error: {clean_message}. Please check your API key.",
        ) from e
    except Exception as e:
        logger = getLogger()
        logger.error(f"Unexpected error in get_chatcompletion: {str(e)}")
        # Handle any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service temporarily unavailable: {str(e)}",
        ) from e


def get_date():
    # Set the desired timezone (EST)
    est_timezone = pytz.timezone("US/Eastern")

    # Get the current date and time in UTC
    current_date_time_utc = datetime.now(pytz.utc)

    # Convert the UTC time to the desired timezone (EST)
    current_date_time_est = current_date_time_utc.astimezone(est_timezone)

    # Format and print the current date and time in EST
    formatted_date_time = current_date_time_est.strftime("%Y-%m-%d %H:%M:%S")

    return formatted_date_time


# helper function for timing execution of various calls
class LineTimer:
    def __init__(self, name=None):
        self.name = " '" + name + "'" if name else ""

    def __enter__(self):
        self.start = timeit.default_timer()

    def __exit__(self, exc_type, exc_value, traceback):
        self.took = (timeit.default_timer() - self.start) * 1000.0
        logger.info("Code block" + self.name + " took: " + str(self.took) + " ms")


# essentially, context managers are aspect-oriented constructs for python
@asynccontextmanager
async def capture_logs(logger):
    # add a local capture to our logger
    logs = io.StringIO("")
    eh = logging.StreamHandler(logs)
    formatter = logging.Formatter(
        "%(asctime)s - %(module)s.%(funcName)s() - %(levelname)s - %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    eh.setFormatter(formatter)
    logger.addHandler(eh)
    yield logs
    logger.removeHandler(eh)
