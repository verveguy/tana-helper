import asyncio
import hashlib
import io
import json
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
    content_hash: str | None = None  # For change detection


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


async def get_embeddings_batch(
    content_list: list[str],
    model: str = "text-embedding-ada-002",
    batch_size: int = 100,
    max_retries: int = 3,
    progress_callback=None,
) -> list[list[float]]:
    """
    Get embeddings for multiple texts in batches with retry logic and progress reporting.

    This function processes multiple texts in batches to dramatically improve performance
    by reducing the number of HTTP requests to OpenAI's API.

    Args:
        content_list: List of text strings to embed
        model: OpenAI embedding model to use
        batch_size: Maximum number of texts per batch (considers token limits)
        max_retries: Number of retry attempts for failed requests
        progress_callback: Optional callback for progress updates during embedding

    Returns:
        List of embedding vectors (list of floats for each input text)

    Raises:
        HTTPException: For authentication, rate limit, or API errors
    """
    # Use global settings (refreshed by middleware on every request)
    api_key = settings.settings.openai_api_key
    logger = getLogger()

    # Check if API key is missing or looks like a placeholder
    if not api_key or api_key == "OPENAI_API_KEY NOT SET" or "NOT SET" in api_key:
        logger.error("OpenAI API key not configured for batch embeddings")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OpenAI API key not configured. Please set your API key in configuration.",
        )

    openai_client = AsyncOpenAI(api_key=api_key)
    all_embeddings = []

    total_batches = (len(content_list) + batch_size - 1) // batch_size
    logger.info(
        f"Processing {len(content_list)} texts in {total_batches} batches of {batch_size}"
    )

    # Process in batches to respect token limits and improve performance
    for i in range(0, len(content_list), batch_size):
        batch = content_list[i : i + batch_size]
        batch_num = (i // batch_size) + 1

        logger.debug(
            f"Processing batch {batch_num}/{total_batches} with {len(batch)} texts"
        )

        # Send progress update for this batch
        if progress_callback:
            processed_so_far = len(all_embeddings)
            await progress_callback(
                {
                    "type": "embedding_progress",
                    "batch_num": batch_num,
                    "total_batches": total_batches,
                    "processed_nodes": processed_so_far,
                    "total_nodes": len(content_list),
                    "phase": "embedding",
                }
            )

        # Retry logic for this batch
        for attempt in range(max_retries):
            try:
                # Single API call for entire batch - this is the key optimization!
                response = await openai_client.embeddings.create(
                    input=batch,  # OpenAI accepts list of strings
                    model=model,
                )

                # Extract embeddings from response
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.debug(
                    f"Successfully processed batch {batch_num} with {len(batch_embeddings)} embeddings"
                )
                break  # Success, exit retry loop

            except RateLimitError as e:
                wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Rate limit hit on batch {batch_num}, attempt {attempt + 1}. Waiting {wait_time}s..."
                )

                if attempt == max_retries - 1:
                    logger.error(
                        f"Rate limit exceeded after {max_retries} attempts for batch {batch_num}"
                    )
                    clean_message = clean_openai_error_message(str(e))
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"OpenAI rate limit exceeded: {clean_message}. Please try again later.",
                    ) from e

                await asyncio.sleep(wait_time)

            except AuthenticationError as e:
                logger.error(
                    f"OpenAI authentication failed for batch {batch_num}: {str(e)}"
                )
                clean_message = clean_openai_error_message(str(e))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"OpenAI authentication failed: {clean_message}. Please check your API key.",
                ) from e

            except APIError as e:
                logger.error(f"OpenAI API error for batch {batch_num}: {str(e)}")

                # For token limit errors, try splitting the batch
                if "token" in str(e).lower() and len(batch) > 1:
                    logger.info(f"Token limit hit, splitting batch {batch_num} in half")
                    mid = len(batch) // 2
                    batch1_embeddings = await get_embeddings_batch(
                        batch[:mid],
                        model,
                        batch_size=mid,
                        max_retries=max_retries,
                        progress_callback=progress_callback,
                    )
                    batch2_embeddings = await get_embeddings_batch(
                        batch[mid:],
                        model,
                        batch_size=len(batch) - mid,
                        max_retries=max_retries,
                        progress_callback=progress_callback,
                    )
                    all_embeddings.extend(batch1_embeddings + batch2_embeddings)
                    break

                if attempt == max_retries - 1:
                    clean_message = clean_openai_error_message(str(e))
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"OpenAI API error: {clean_message}. Please check your API key.",
                    ) from e

                await asyncio.sleep(2**attempt)

            except Exception as e:
                logger.error(f"Unexpected error in batch {batch_num}: {str(e)}")

                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Service temporarily unavailable: {str(e)}",
                    ) from e

                await asyncio.sleep(2**attempt)

        # Cooperative yielding for cancellation support
        await asyncio.sleep(0)

    logger.info(
        f"Successfully processed all {len(content_list)} texts, got {len(all_embeddings)} embeddings"
    )
    return all_embeddings


def calculate_optimal_batch_size(content_list: list[str]) -> int:
    """
    Calculate optimal batch size based on content length to respect token limits.

    OpenAI has ~8192 token limit per request. We estimate ~4 characters per token
    and leave some safety margin.
    """
    if not content_list:
        return 100

    # Conservative estimates for token limits
    max_tokens_per_request = 7000  # Leave safety margin from 8192 limit
    chars_per_token = 4
    max_chars_per_request = max_tokens_per_request * chars_per_token

    # Calculate average content length
    avg_length = sum(len(content) for content in content_list) / len(content_list)

    # Calculate optimal batch size, with reasonable min/max bounds
    if avg_length > 0:
        optimal_size = max(10, min(500, int(max_chars_per_request / avg_length)))
    else:
        optimal_size = 100

    logger = getLogger()
    logger.info(
        f"Calculated optimal batch size: {optimal_size} (avg content length: {avg_length:.0f} chars)"
    )
    return optimal_size


def create_content_hash(
    content: str,
    tags: list[str] | None = None,
    fields: list | None = None,
    modified_ts: list[int] | None = None,
) -> str:
    """
    Create a SHA-256 hash of the node content for change detection.

    This enables us to skip embedding generation and ChromaDB updates for unchanged content,
    providing massive performance improvements for incremental updates.

    Args:
        content: The text content of the node
        tags: List of tags associated with the node
        fields: List of fields/metadata associated with the node
        modified_ts: Modification timestamps from Tana

    Returns:
        SHA-256 hash string that uniquely identifies this content version
    """
    # Create a canonical representation of all content that affects meaning
    content_data = {
        "content": content.strip() if content else "",
        "tags": sorted(tags or []),  # Sort for consistency
        "fields": sorted(
            fields or [], key=lambda x: str(x)
        ),  # Sort fields for consistency
        "modified_ts": modified_ts or [],
    }

    # Convert to deterministic JSON string
    content_json = json.dumps(content_data, sort_keys=True, separators=(",", ":"))

    # Generate SHA-256 hash
    content_hash = hashlib.sha256(content_json.encode("utf-8")).hexdigest()

    return content_hash


def create_node_content_hash(topic) -> str:
    """
    Create a content hash for a TanaDocument/topic.

    This is a convenience function that extracts the relevant fields
    from a topic and creates a hash for change detection.
    """
    # Extract all content text
    content_parts = []
    for _, _, text in topic.content:
        content_parts.append(text)
    full_content = "\n".join(content_parts)

    # Extract fields as serializable data
    fields_data = []
    if topic.fields:
        for field in topic.fields:
            fields_data.append(
                {
                    "name": field.name,
                    "value": field.value,
                    "field_id": field.field_id,
                    "value_id": field.value_id,
                }
            )

    return create_content_hash(
        content=full_content, tags=topic.tags, fields=fields_data
    )


def get_stored_content_hash(collection, node_id: str) -> str | None:
    """
    Retrieve the stored content hash for a node from ChromaDB.

    Returns None if the node doesn't exist or has no stored hash.
    """
    try:
        # Get the existing node metadata
        result = collection.get(ids=[node_id])

        if result and result["metadatas"] and len(result["metadatas"]) > 0:
            metadata = result["metadatas"][0]
            return metadata.get("content_hash")

        return None

    except Exception:
        # Node doesn't exist or other error
        return None


def should_skip_processing(topic, collection) -> bool:
    """
    Determine if we should skip processing this topic because it hasn't changed.

    Returns True if the content hash matches what's stored in ChromaDB,
    indicating the node is unchanged and can be skipped.
    """
    try:
        current_hash = create_node_content_hash(topic)
        stored_hash = get_stored_content_hash(collection, topic.id)

        if stored_hash and current_hash == stored_hash:
            logger = getLogger()
            logger.debug(
                f"Skipping unchanged node {topic.id} (hash: {current_hash[:8]}...)"
            )
            return True

        return False

    except Exception as e:
        # If there's any error with hash comparison, err on the side of processing
        logger = getLogger()
        logger.debug(f"Error checking content hash for {topic.id}: {e}, will process")
        return False


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
