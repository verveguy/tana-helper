import asyncio
import json
import os
import tempfile
import time
from logging import getLogger

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse

# This is here to satisfy runtime import needs
# that pyinstaller appears to miss
from snowflake import SnowflakeGenerator

from service.dependencies import (
    TANA_NODE,
    TANA_TEXT,
    ChromaRequest,
    TanaNodeMetadata,
    capture_logs,
)
from service.endpoints.chroma import chroma_upsert
from service.endpoints.topics import TanaDocument, extract_topics
from service.tana_types import TanaDump

logger = getLogger()

snowflakes = SnowflakeGenerator(42)

router = APIRouter()

minutes = 1000 * 60

# TODO: Add header support throughout so we can pass Tana API key and OpenAPI Key as headers
# NOTE: we already have this in the main.py middleware wrapper, but it would be better
# to do it here for OpenAPI spec purposes.
# x_tana_api_token: Annotated[str | None, Header()] = None
# x_openai_api_key: Annotated[str | None, Header()] = None

# TODO: change this to remove LLamaindex and simply go directly to ChromaDB


async def load_chromadb_from_topics(
    topics: list[TanaDocument], model: str, observe=False
):
    """Load the topic index from the topic array directly."""

    logger.info("Building ChromaDB vectors from nodes")

    index_nodes = []
    # loop through all the topics and create a Document for each
    for topic in topics:
        (doc_node, text_nodes) = document_from_topic(topic)
        index_nodes.append(doc_node)
        index_nodes.extend(text_nodes)

    logger.info(f"Gathered {len(index_nodes)} tana nodes")
    logger.info("Preparing storage context")

    for node in index_nodes:
        logger.info(f"Node {node.id} {node.metadata}")
        chroma_req = ChromaRequest(
            context=node.text,
            name=(node.metadata or {}).get(
                "title", ""
            ),  # Extract name from metadata, handle None
            nodeId=str(node.id),  # Convert integer to string!
            model=model,
        )
        upsert = await chroma_upsert(chroma_req)

    logger.info("ChromaDB populated and ready")
    return index_nodes


async def load_chromadb_from_topics_with_progress(
    topics: list[TanaDocument], model: str, progress_callback=None, observe=False
):
    """Load topics into ChromaDB with batch processing and progress reporting.

    This function uses batch processing for dramatic performance improvements:
    1. First pass: Collect all nodes and their content
    2. Second pass: Process embeddings in batches (10-50x faster!)
    3. Third pass: Upsert to ChromaDB with progress updates

    Args:
        topics: List of Tana documents to process
        model: Model to use for embeddings (e.g., "openai")
        progress_callback: Optional callback function for progress updates
        observe: Whether to use observe mode for processing
    """

    start_time = time.time()

    logger.info("Building ChromaDB vectors from nodes with BATCH processing")

    # Check for cancellation at the start
    current_task = asyncio.current_task()
    if current_task and current_task.cancelled():
        logger.debug("Task was cancelled before starting")
        return

    try:
        # === PASS 1: Collect all nodes and content with change detection ===
        logger.info("Pass 1: Collecting nodes and detecting changes...")

        from service.dependencies import (
            create_node_content_hash,
            should_skip_processing,
        )
        from service.endpoints.chroma import get_collection

        # Get ChromaDB collection for change detection
        collection = get_collection()

        all_nodes = []
        content_list = []
        node_metadata = []
        skipped_count = 0

        for topic_idx, topic in enumerate(topics):
            # Check for cancellation every 100 topics during collection
            if topic_idx % 100 == 0:
                if current_task and current_task.cancelled():
                    logger.debug("Task cancelled during node collection")
                    raise asyncio.CancelledError()
                await asyncio.sleep(0)

            # 🎯 CHANGE DETECTION: Skip unchanged topics
            if should_skip_processing(topic, collection):
                skipped_count += 1
                continue

            # Get all nodes for this topic using existing logic
            (doc_node, text_nodes) = document_from_topic(topic)
            topic_nodes = [doc_node] + text_nodes

            # Calculate content hash for this topic
            content_hash = create_node_content_hash(topic)

            for node in topic_nodes:
                all_nodes.append(node)
                content_list.append(node.text)
                # Store metadata for later ChromaDB upsert
                node_metadata.append(
                    {
                        "topic_idx": topic_idx,
                        "topic_id": topic.id,
                        "topic_name": topic.name[:100],
                        "node_id": node.id,
                        "node_text": node.text,
                        "node_metadata": node.metadata or {},
                        "content_hash": content_hash,  # 🎯 Include content hash
                    }
                )

        total_nodes = len(all_nodes)
        logger.info(f"Collected {total_nodes} nodes from {len(topics)} topics")
        if skipped_count > 0:
            logger.info(
                f"⚡ OPTIMIZATION: Skipped {skipped_count} unchanged topics (saved {skipped_count} embedding calls!)"
            )

        # Send initial progress callback with skip information
        if progress_callback:
            await progress_callback(
                {
                    "type": "init",
                    "total_topics": len(topics),
                    "total_nodes": total_nodes,
                    "skipped_topics": skipped_count,
                    "changed_topics": len(topics) - skipped_count,
                    "phase": "batch_processing",
                }
            )

        # === PASS 2: Get embeddings in batches ===
        logger.info("Pass 2: Processing embeddings in batches...")

        # Calculate optimal batch size based on content
        from service.dependencies import (
            calculate_optimal_batch_size,
            get_embeddings_batch,
        )

        optimal_batch_size = calculate_optimal_batch_size(content_list)

        if progress_callback:
            await progress_callback(
                {
                    "type": "batch_start",
                    "total_nodes": total_nodes,
                    "batch_size": optimal_batch_size,
                    "estimated_batches": (total_nodes + optimal_batch_size - 1)
                    // optimal_batch_size,
                    "phase": "embedding",
                }
            )

        # Get all embeddings in batches - this is the key performance improvement!
        all_embeddings = await get_embeddings_batch(
            content_list,
            model=model,
            batch_size=optimal_batch_size,
            progress_callback=progress_callback,
        )

        logger.info(
            f"Successfully generated {len(all_embeddings)} embeddings using batch processing"
        )

        # === PASS 3: Upsert to ChromaDB with progress ===
        logger.info("Pass 3: Upserting to ChromaDB...")

        if progress_callback:
            await progress_callback(
                {"type": "upsert_start", "total_nodes": total_nodes, "phase": "storing"}
            )

        processed_nodes = 0
        current_topic_idx = -1
        storing_phase_start = time.time()  # Track start of storing phase
        failed_nodes = 0  # Track failed storage operations

        # Process each node with its embedding
        for i, (node, embedding, metadata) in enumerate(
            zip(all_nodes, all_embeddings, node_metadata, strict=False)
        ):
            # Check for cancellation every 50 nodes during upsert
            if i % 50 == 0:
                if current_task and current_task.cancelled():
                    logger.debug("Task cancelled during ChromaDB upsert")
                    raise asyncio.CancelledError()
                await asyncio.sleep(0)

            # Track topic changes for progress reporting
            if metadata["topic_idx"] != current_topic_idx:
                current_topic_idx = metadata["topic_idx"]

                if progress_callback:
                    await progress_callback(
                        {
                            "type": "topic_start",
                            "current_topic": current_topic_idx + 1,
                            "total_topics": len(topics),
                            "topic_name": metadata["topic_name"],
                            "topic_id": metadata["topic_id"],
                            "processed_nodes": processed_nodes,
                            "total_nodes": total_nodes,
                            "failed_nodes": failed_nodes,
                            "phase": "storing",
                        }
                    )

            try:
                # Create ChromaRequest for this node (using existing structure)
                # FIX: Convert node.id (integer) to string for ChromaRequest
                chroma_req = ChromaRequest(
                    context=node.text,
                    name=metadata["node_metadata"].get("title", ""),
                    nodeId=str(node.id),  # Convert integer to string!
                    model=model,
                )

                # Use existing chroma_upsert but bypass the embedding call
                # We'll need to modify this to accept pre-computed embeddings
                await chroma_upsert_with_embedding(
                    chroma_req, embedding, metadata["content_hash"]
                )
                processed_nodes += 1

            except Exception as e:
                failed_nodes += 1
                logger.error(f"Error upserting node {node.id}: {e}")

                # Send error callback but continue processing - now with better error info
                if progress_callback:
                    await progress_callback(
                        {
                            "type": "node_error",
                            "current_topic": current_topic_idx + 1,
                            "topic_id": metadata["topic_id"],
                            "node_id": str(
                                node.id
                            ),  # Convert to string for consistency
                            "error": str(e),
                            "processed_nodes": processed_nodes,
                            "total_nodes": total_nodes,
                            "failed_nodes": failed_nodes,
                            "phase": "storing",
                        }
                    )

            # Send progress update every 100 nodes with enhanced timing info
            if processed_nodes % 100 == 0 and progress_callback:
                storing_elapsed = time.time() - storing_phase_start

                await progress_callback(
                    {
                        "type": "storing_progress",
                        "processed_nodes": processed_nodes,
                        "total_nodes": total_nodes,
                        "failed_nodes": failed_nodes,
                        "current_topic": current_topic_idx + 1,
                        "total_topics": len(topics),
                        "phase": "storing",
                        "storing_elapsed": round(storing_elapsed, 1),
                        "storing_rate": round(processed_nodes / storing_elapsed, 2)
                        if storing_elapsed > 0
                        else 0,
                    }
                )

        # Send completion callback with failure summary
        elapsed_time = time.time() - start_time
        logger.info(f"ChromaDB batch indexing completed in {elapsed_time:.1f}s")
        logger.info(
            f"Performance: {processed_nodes / elapsed_time:.1f} nodes/second with batching!"
        )

        if failed_nodes > 0:
            logger.warning(
                f"Storage completed with {failed_nodes} failed nodes out of {total_nodes} total"
            )

        if progress_callback:
            await progress_callback(
                {
                    "type": "complete",
                    "processed_nodes": processed_nodes,
                    "total_nodes": total_nodes,
                    "failed_nodes": failed_nodes,
                    "elapsed_seconds": round(elapsed_time, 1),
                    "processing_rate": round(processed_nodes / elapsed_time, 2),
                    "phase": "complete",
                }
            )

    except asyncio.CancelledError:
        # Handle cancellation gracefully
        elapsed_time = time.time() - start_time
        logger.info("Batch processing cancelled by user")

        if progress_callback:
            await progress_callback(
                {
                    "type": "cancelled",
                    "message": "Batch processing cancelled by user",
                    "processed_nodes": processed_nodes
                    if "processed_nodes" in locals()
                    else 0,
                    "total_nodes": total_nodes if "total_nodes" in locals() else 0,
                    "elapsed_seconds": round(elapsed_time, 1),
                    "phase": "cancelled",
                }
            )

        # Re-raise to properly handle cancellation
        raise


async def chroma_upsert_with_embedding(
    req: ChromaRequest, embedding: list[float], content_hash: str
):
    """
    Upsert to ChromaDB using a pre-computed embedding and content hash.

    This bypasses the embedding generation step since we've already computed
    embeddings in batches for better performance. Also stores the content hash
    for future change detection.
    """
    from service.dependencies import TANA_NODE, TanaNodeMetadata
    from service.endpoints.chroma import get_collection
    from service.tanaparser import prune_reference_nodes

    # Use the same logic as the original chroma_upsert but with pre-computed embedding
    pruned_content = prune_reference_nodes(req.context)
    req.context = pruned_content

    collection = get_collection()

    metadata = TanaNodeMetadata(
        category=TANA_NODE,
        supertag=req.tags,
        title=req.name,
        text=req.context,
        tana_id=req.nodeId,
        topic_id=req.nodeId,
        content_hash=content_hash,  # 🎯 Store content hash for change detection
    )

    if req.context is None:
        logger.warning(f"Empty context for {req.nodeId}")

    # Upsert with the pre-computed embedding
    def do_upsert():
        collection.upsert(
            ids=req.nodeId,
            embeddings=embedding,  # Use pre-computed embedding!
            documents=req.name,
            metadatas=metadata.model_dump(),
        )

    do_upsert()


class Document:
    def __init__(self, id: str, text: str, metadata: dict | None = None):
        if not id:
            raise ValueError("Document must have an id")
        if not text:
            raise ValueError("Document must have text")
        self.id = id
        self.text = text
        self.metadata = metadata if metadata else {}


class TextNode(Document):
    def __init__(
        self,
        id: str,
        text: str,
        relationships: dict | None = None,
        metadata: dict | None = None,
    ):
        super().__init__(id, text, metadata)
        self.relationships = relationships if relationships else {}


class NodeRelationship:
    SOURCE = "source"
    NEXT = "next"
    PREVIOUS = "previous"


def document_from_topic(topic) -> tuple[Document, list[TextNode]]:
    """Load a single topic into the index_nodes list."""
    text_nodes = []

    metadata = {
        "category": TANA_NODE,
        "supertag": " ".join([tag for tag in topic.tags]),
        "title": topic.name,
    }

    if topic.fields:
        # get all the fields as metadata as well
        fields = set([field.name for field in topic.fields])
        for field_name in fields:
            metadata[field_name] = " ".join(
                [field.value for field in topic.fields if field.name == field_name]
            )

    # what other props do we need to create?
    # document = Document(id_=topic.id, text=topic.name) # type: ignore
    # we only add the first line and fields to the document payload
    # anything else and we blow out the token limits (and cost a lot!)
    text = topic.content[0][2]
    document_node = Document(
        id=topic.id, text=text, metadata=metadata
    )  # first line only

    # # make a note of the document in our nodes list
    # index_nodes.append(document_node)

    # now iterate all the remaining topic.content and create a node for each
    # each of these is simply a string, being the name of a tana child node
    # but with [[]name^id]] reference syntax used for references
    # TODO: make these tana_nodes richer structurally
    # TODO: use actual tana node id here perhaps?
    previous_text_node = None
    if len(topic.content) > 30:
        logger.warning(f"Large topic {topic.id} with {len(topic.content)} children")

    # process all the child content records...
    for content_id, is_ref, tana_element in topic.content[1:]:
        content_metadata = TanaNodeMetadata(
            category=TANA_TEXT,
            title=topic.name,
            topic_id=topic.id,
            # TODO: ? 'supertag': ' '.join(['#' + tag for tag in topic.tags]),
            # text gets added below...
        )

        # wire up the tana_node as an index_node with the text as the payload
        if is_ref:
            ref_id = next(snowflakes)
            current_text_node = TextNode(id=ref_id, text=tana_element)  # type: ignore
            current_text_node.metadata["tana_ref_id"] = content_id
        else:
            current_text_node = TextNode(id=content_id, text=tana_element)

        current_text_node.metadata = content_metadata.model_dump()

        # check if this is a reference node and add additional metadata
        # TODO: backport this to chroma upsert...?

        current_text_node.relationships[NodeRelationship.SOURCE] = document_node.id
        # wire up next/previous
        if previous_text_node:
            current_text_node.relationships[NodeRelationship.PREVIOUS] = (
                previous_text_node.id
            )
            previous_text_node.relationships[NodeRelationship.NEXT] = (
                current_text_node.id
            )

        text_nodes.append(current_text_node)
        previous_text_node = current_text_node

    return (document_node, text_nodes)


# attempt to parallelize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()


# Note: accepts ?model= query param
@router.post("/chroma/preload", tags=["preload"])
async def chroma_preload(
    request: Request, tana_dump: TanaDump, model: str = "text-embedding-ada-002"
):
    """Accepts a Tana dump JSON payload and builds the index from it.
    Uses the topic extraction code from the topics endpoint to build
    an object tree in memory, then loads that into ChromaDB via LLamaIndex.

    Returns a list of log messages from the process.
    """
    async with lock:
        messages = []
        async with capture_logs(logger) as logs:
            result = await extract_topics(tana_dump, "JSON")  # type: ignore
            logger.info("Extracted topics from Tana dump")

            # save output to a temporary file
            with tempfile.TemporaryDirectory() as tmp:
                path = os.path.join(tmp, "topics.json")
                logger.info(f"Saving topics to {path}")
                # use path
                with open(path, "w") as f:
                    json_result = jsonable_encoder(result)
                    f.write(json.dumps(json_result))

                logger.info("Loading index ...")
            # don't use file anymore...
            # load_index_from_file(path)
            # load directly from in-memory representation
            await load_chromadb_from_topics(result, model=model)
            # load_index_from_topics(result, model=model)

            # logger.info(f'Deleted temp file {path}')
            messages = logs.getvalue()
        return messages


@router.post("/chroma/preload/stream", tags=["preload"])
async def chroma_preload_stream(
    request: Request, tana_dump: TanaDump, model: str = "text-embedding-ada-002"
):
    """Streaming version of preload with real-time progress updates via Server-Sent Events.

    Accepts a Tana dump JSON payload and builds the index from it with progress reporting.
    Returns progress updates as Server-Sent Events in JSON format.

    Progress event types:
    - init: Initial setup with total counts
    - batch_start: Starting batch processing
    - batch_progress: Progress within batch processing
    - topic_start: Starting to process a topic
    - topic_complete: Completed processing a topic
    - node_progress: Progress within large topics
    - node_error: Error processing a specific node
    - complete: All processing completed
    - error: Fatal error occurred
    - cancelled: Processing was cancelled
    """

    async def generate_progress():
        process_task = None
        start_time = time.time()

        try:
            async with lock:
                progress_queue = asyncio.Queue()

                # Extract topics first to get total count
                logger.info("Extracting topics from Tana dump for streaming preload")
                result = await extract_topics(tana_dump, "JSON")  # type: ignore
                logger.info(f"Extracted {len(result)} topics from Tana dump")

                # Progress callback function to queue SSE events
                async def progress_callback(data):
                    # Add timing information
                    elapsed = time.time() - start_time
                    data["elapsed_seconds"] = round(elapsed, 1)

                    # Calculate ETA for processing phases
                    if (
                        data.get("processed_nodes", 0) > 0
                        and data.get("total_nodes", 0) > 0
                    ):
                        progress_ratio = data["processed_nodes"] / data["total_nodes"]
                        if (
                            progress_ratio > 0.05
                        ):  # Only calculate ETA after 5% progress
                            estimated_total_time = elapsed / progress_ratio
                            eta_seconds = estimated_total_time - elapsed
                            data["eta_seconds"] = round(max(0, eta_seconds), 1)
                            data["processing_rate"] = round(
                                data["processed_nodes"] / elapsed, 2
                            )

                    # Put the progress data in the queue (with timeout to avoid blocking)
                    try:
                        await asyncio.wait_for(progress_queue.put(data), timeout=5.0)
                    except TimeoutError:
                        # If we can't queue progress updates, the client likely disconnected
                        logger.debug(
                            "Progress queue full, client may have disconnected"
                        )

                # Start processing in a background task
                async def process_topics():
                    try:
                        await load_chromadb_from_topics_with_progress(
                            result, model=model, progress_callback=progress_callback
                        )
                        logger.info("Streaming preload completed successfully")
                    except asyncio.CancelledError:
                        logger.info("Processing cancelled by user")
                        try:
                            await asyncio.wait_for(
                                progress_queue.put(
                                    {
                                        "type": "cancelled",
                                        "message": "Processing cancelled by user",
                                        "phase": "cancelled",
                                        "elapsed_seconds": round(
                                            time.time() - start_time, 1
                                        ),
                                    }
                                ),
                                timeout=1.0,
                            )
                        except (TimeoutError, asyncio.CancelledError):
                            pass  # Queue is full or cancelled, client disconnected
                        raise  # Re-raise to properly handle cancellation
                    except Exception as e:
                        logger.error(f"Error in background processing: {e}")
                        # Send comprehensive error information to frontend
                        error_data = {
                            "type": "error",
                            "message": str(e),
                            "error_type": type(e).__name__,
                            "phase": "error",
                            "elapsed_seconds": round(time.time() - start_time, 1),
                        }

                        # Include additional error context for common issues
                        if (
                            "model" in str(e).lower()
                            and "does not exist" in str(e).lower()
                        ):
                            error_data["message"] = (
                                f"OpenAI embedding model error: {str(e)}"
                            )
                            error_data["help"] = (
                                "Please check that your OpenAI API key has access to the embedding model."
                            )
                        elif (
                            "api_key" in str(e).lower()
                            or "authentication" in str(e).lower()
                        ):
                            error_data["message"] = (
                                f"OpenAI authentication error: {str(e)}"
                            )
                            error_data["help"] = (
                                "Please check your OpenAI API key configuration."
                            )
                        elif "rate limit" in str(e).lower():
                            error_data["message"] = f"OpenAI rate limit error: {str(e)}"
                            error_data["help"] = "Please wait a moment and try again."

                        try:
                            await asyncio.wait_for(
                                progress_queue.put(error_data),
                                timeout=1.0,
                            )
                        except (TimeoutError, asyncio.CancelledError):
                            pass  # Queue is full or cancelled, client disconnected
                    finally:
                        # Signal completion (with timeout to avoid hanging)
                        try:
                            await asyncio.wait_for(
                                progress_queue.put(None), timeout=1.0
                            )
                        except (TimeoutError, asyncio.CancelledError):
                            pass  # Client disconnected, no need to signal completion

                # Start the background task
                process_task = asyncio.create_task(process_topics())

                # Yield progress updates as they come
                try:
                    while True:
                        try:
                            # Wait for progress update with timeout
                            data = await asyncio.wait_for(
                                progress_queue.get(), timeout=30.0
                            )

                            if data is None:  # Processing completed
                                break

                            # Send the SSE event
                            event_data = f"data: {json.dumps(data)}\n\n"
                            yield event_data

                        except TimeoutError:
                            # Send keepalive event
                            keepalive_data = {
                                "type": "keepalive",
                                "elapsed_seconds": round(time.time() - start_time, 1),
                            }
                            yield f"data: {json.dumps(keepalive_data)}\n\n"
                            continue

                except asyncio.CancelledError:
                    # Client disconnected, cancel background processing gracefully
                    logger.debug(
                        "Client disconnected, cancelling background processing"
                    )
                    if process_task and not process_task.done():
                        process_task.cancel()
                        try:
                            await asyncio.wait_for(process_task, timeout=5.0)
                        except (TimeoutError, asyncio.CancelledError):
                            logger.debug(
                                "Background task cancelled/timed out during cleanup"
                            )
                    raise

                # Wait for the processing task to complete
                if process_task and not process_task.done():
                    await process_task

        except asyncio.CancelledError:
            # This is expected when client disconnects, don't log as error
            logger.debug("Streaming cancelled (client disconnected)")
            raise
        except Exception as e:
            logger.error(f"Error in streaming preload: {e}")
            error_data = {
                "type": "error",
                "message": str(e),
                "error_type": type(e).__name__,
                "phase": "error",
                "elapsed_seconds": round(time.time() - start_time, 1)
                if "start_time" in locals()
                else 0,
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        finally:
            # Final cleanup
            if process_task and not process_task.done():
                logger.debug("Cleaning up background task")
                process_task.cancel()
                try:
                    await asyncio.wait_for(process_task, timeout=2.0)
                except (TimeoutError, asyncio.CancelledError):
                    logger.debug("Background task cleanup completed")

    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )
