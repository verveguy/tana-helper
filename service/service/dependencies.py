import asyncio
import hashlib
import io
import json
import logging
import re
from datetime import datetime
from io import StringIO
from logging import getLogger
from timeit import timeit
from typing import ForwardRef

import httpx
import pytz
from fastapi import HTTPException, status
from fastapi.concurrency import asynccontextmanager
from openai import APIError, AsyncOpenAI, AuthenticationError, OpenAI, RateLimitError
from pydantic import BaseModel
from snowflake import SnowflakeGenerator

from service.tana_types import TANA_NODE

from . import settings

# Load environment variables from .env file
# load_dotenv()

app_name = "TanaHelper"

# production: Annotated[bool, Field(title="Production",
#   description="Whether we are running in production mode")] \
#     = False

# templates:object = None


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


# OPENAI_EMBEDDING_MODEL = "text-embedding-3-large"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_EMBEDDING_THRESHOLD = 0.45

# OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
# OPENAI_EMBEDDING_THRESHOLD = 0.80


OPENAI_CHAT_MODEL = "gpt-4o"


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
    metadata: dict | None = None
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
    metadata: dict | None = None
    nodeId: str
    returns: str | None = "topic"


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
    Clean up OpenAI error messages to remove JSON formatting
    and extract key information.
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
    Get embeddings for multiple texts in batches with retry logic
    and progress reporting.

    This function processes multiple texts in batches to dramatically
    improve performance over individual API calls (10-50x faster).
    Includes intelligent retry logic, automatic batch splitting,
    and content size monitoring.
    """
    if not content_list:
        # Send completion progress event even for empty input to maintain UI state
        if progress_callback:
            await progress_callback(
                {
                    "type": "embedding_progress",
                    "current_batch": 0,
                    "total_batches": 0,
                    "current_node": 0,
                    "total_nodes": 0,
                    "phase": "embedding",
                }
            )
        return []

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

    # 🎯 RESTORED: Enhanced batch monitoring from OLD function
    total_batches = (len(content_list) + batch_size - 1) // batch_size
    logger.info("🚀 Starting batch embedding processing:")
    logger.info(f"   📊 Total content pieces: {len(content_list):,}")
    logger.info(f"   📦 Batch size: {batch_size}")
    logger.info(f"   🔢 Total batches: {total_batches}")

    all_embeddings = []

    for batch_num in range(total_batches):
        batch_start_idx = batch_num * batch_size
        batch_end_idx = min(batch_start_idx + batch_size, len(content_list))
        batch = content_list[batch_start_idx:batch_end_idx]

        # 🎯 RESTORED: Content size monitoring per batch (from OLD function)
        batch_sizes = [len(text) for text in batch]
        largest_size = max(batch_sizes)
        largest_idx = batch_sizes.index(largest_size)

        logger.info(
            f"📦 Processing batch {batch_num + 1}/{total_batches}: {len(batch)} items"
        )
        logger.info(f"   📏 Largest content in batch: {largest_size:,} characters")

        if largest_size > 16000:  # Warning threshold
            logger.warning(
                f"   ⚠️  Large content detected in batch item {largest_idx}: {largest_size:,} chars"
            )

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

                # Send progress update AFTER this batch is successfully processed
                if progress_callback:
                    processed_so_far = len(all_embeddings)
                    await progress_callback(
                        {
                            "type": "embedding_progress",
                            "current_batch": batch_num + 1,
                            "total_batches": total_batches,
                            "current_node": processed_so_far,
                            "total_nodes": len(content_list),
                            "phase": "embedding",
                        }
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


def create_individual_node_hash(node) -> str:
    """
    Create a content hash for an individual node (Document or TextNode).

    This enables node-level change detection, providing more granular
    optimization than topic-level hashing. Only nodes that have actually
    changed will be reprocessed.

    Args:
        node: Document or TextNode object to hash

    Returns:
        SHA-256 hash string uniquely identifying this node's content
    """
    # Extract content and metadata from the node
    content = node.text if hasattr(node, "text") else ""

    # Extract metadata for hash calculation
    metadata = node.metadata if hasattr(node, "metadata") and node.metadata else {}

    # For Document nodes, include tags and title in hash
    tags = []
    fields_data = []

    if hasattr(node, "metadata") and node.metadata:
        # Extract tags from metadata
        if "supertag" in metadata:
            tags = metadata["supertag"].split() if metadata["supertag"] else []

        # Include relevant metadata fields that affect content meaning
        relevant_fields = ["title", "category", "has_integrated_fields"]
        for field_name in relevant_fields:
            if field_name in metadata:
                fields_data.append(
                    {"name": field_name, "value": str(metadata[field_name])}
                )

        # Include any field data that was integrated into the content
        for key, value in metadata.items():
            if key not in [
                "title",
                "category",
                "supertag",
                "has_integrated_fields",
            ] and not key.startswith("_"):
                fields_data.append({"name": key, "value": str(value)})

    return create_content_hash(content=content, tags=tags, fields=fields_data)


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
    Retrieve the stored content hash for a specific node from ChromaDB.

    Args:
        collection: ChromaDB collection
        node_id: ID of the node to check

    Returns:
        Stored content hash string, or None if not found
    """
    try:
        result = collection.get(ids=[node_id], include=["metadatas"])
        if result["metadatas"] and len(result["metadatas"]) > 0:
            metadata = result["metadatas"][0]
            return metadata.get("content_hash") if metadata else None
        return None
    except Exception as e:
        logger.debug(f"Could not retrieve hash for node {node_id}: {e}")
        return None


def get_stored_node_hashes(collection, node_ids: list[str]) -> dict[str, str]:
    """
    Efficiently retrieve stored content hashes for multiple nodes from ChromaDB.

    This enables batch hash checking for node-level optimization.

    Args:
        collection: ChromaDB collection
        node_ids: List of node IDs to check

    Returns:
        Dictionary mapping node_id -> content_hash for nodes that exist
    """
    if not node_ids:
        return {}

    try:
        result = collection.get(ids=node_ids, include=["metadatas"])
        hash_map = {}

        if result["ids"] and result["metadatas"]:
            for node_id, metadata in zip(
                result["ids"], result["metadatas"], strict=False
            ):
                if metadata and "content_hash" in metadata:
                    hash_map[node_id] = metadata["content_hash"]

        logger.debug(
            f"Retrieved {len(hash_map)} stored hashes for {len(node_ids)} nodes"
        )
        return hash_map

    except Exception as e:
        logger.debug(f"Could not retrieve batch hashes: {e}")
        return {}


def should_skip_processing(collection, node_id: str, current_hash: str) -> bool:
    """
    Determine if we should skip processing this node because it hasn't changed.

    Compares the current content hash with the stored hash in ChromaDB.

    Args:
        collection: ChromaDB collection
        node_id: ID of the node to check
        current_hash: Current content hash of the node

    Returns:
        True if node should be skipped (unchanged), False if it should be processed
    """
    stored_hash = get_stored_content_hash(collection, node_id)

    if stored_hash is None:
        # Node doesn't exist in ChromaDB, so we need to process it
        return False

    # Skip processing if hashes match (content unchanged)
    return stored_hash == current_hash


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


BASE66_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_.~"
BASE = len(BASE66_ALPHABET)

snowflakes = SnowflakeGenerator(42)


def nextflake():
    n = next(snowflakes)
    if n == 0:
        return BASE66_ALPHABET[0].encode("ascii")

    r = StringIO()
    while n:
        n, t = divmod(n, BASE)
        r.write(BASE66_ALPHABET[t])
    return r.getvalue().encode("ascii")[::-1]


# Types for our APIs to use


# Missing data structures from the original implementation
class EmbeddableNode(BaseModel):
    """Node prepared for embedding with hash-based change detection."""

    id: str
    text: str  # The content to embed
    name: str  # Display name
    metadata: dict
    hash: str  # Content hash for change detection
    embedding: list[float] | None = None  # Computed embedding


class TanaTopicNode(BaseModel):
    """Topic node structure from original implementation."""

    id: str
    name: str
    tags: list[str]
    content: list  # Content structure from original format


def prepare_node_for_embedding(
    node_id: str, content_id: str, topic_id: str, name: str, tags: str, context: str
) -> EmbeddableNode:
    """
    Prepare a node for embedding with content hash for change detection.

    This is the missing function from the original implementation that creates
    EmbeddableNode objects with proper hash calculation.
    """
    # Create canonical metadata
    metadata = {
        "category": TANA_NODE,
        "content_id": content_id,
        "topic_id": topic_id,
        "tags": tags,
        "text": context,
    }

    # Calculate content hash for change detection
    content_hash = create_content_hash(
        content=context,
        tags=[tags] if tags else [],
        fields=[],  # Could be extended to include field data
    )

    # Store hash in metadata for ChromaDB storage
    metadata["hash"] = content_hash

    return EmbeddableNode(
        id=node_id, text=context, name=name, metadata=metadata, hash=content_hash
    )


async def get_embeddings(texts: list[str], model: str) -> list:
    """
    Single-batch embedding function for compatibility with original implementation.

    This wraps our get_embeddings_batch function to maintain API compatibility.
    """
    embeddings = await get_embeddings_batch(texts, model=model)

    # Convert to format expected by original implementation
    result = []
    for embedding in embeddings:
        # Create object with .embedding attribute
        embedding_obj = type("EmbeddingResult", (), {"embedding": embedding})()
        result.append(embedding_obj)

    return result
