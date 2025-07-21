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
            nodeId=node.id,
            model=model,
        )
        upsert = await chroma_upsert(chroma_req)

    logger.info("ChromaDB populated and ready")
    return index_nodes


async def load_chromadb_from_topics_with_progress(
    topics: list[TanaDocument], model: str, progress_callback=None, observe=False
):
    """Enhanced version with progress callbacks for streaming updates."""

    logger.info("Building ChromaDB vectors from nodes with progress tracking")

    total_topics = len(topics)
    processed_nodes = 0
    total_nodes = 0

    # First pass: count total nodes for accurate progress
    for topic in topics:
        (doc_node, text_nodes) = document_from_topic(topic)
        total_nodes += 1 + len(text_nodes)  # Document + text nodes

    if progress_callback:
        await progress_callback(
            {
                "type": "init",
                "total_topics": total_topics,
                "total_nodes": total_nodes,
                "phase": "starting",
            }
        )

    # Second pass: actual processing with progress updates
    for i, topic in enumerate(topics):
        try:
            # Check for cancellation every topic
            current_task = asyncio.current_task()
            if current_task and current_task.cancelled():
                logger.info("Processing cancelled by user")
                return processed_nodes

            # Send topic-level progress
            if progress_callback:
                await progress_callback(
                    {
                        "type": "topic_start",
                        "current_topic": i + 1,
                        "total_topics": total_topics,
                        "topic_name": topic.name[:100],  # Truncate long names
                        "topic_id": topic.id,
                        "processed_nodes": processed_nodes,
                        "total_nodes": total_nodes,
                        "percentage": round((processed_nodes / total_nodes) * 100, 1),
                        "phase": "processing",
                    }
                )

            # Process the topic
            (doc_node, text_nodes) = document_from_topic(topic)
            all_nodes = [doc_node] + text_nodes

            # Process each node
            for j, node in enumerate(all_nodes):
                # Check for cancellation every 5 nodes
                if j % 5 == 0:
                    current_task = asyncio.current_task()
                    if current_task and current_task.cancelled():
                        logger.info("Processing cancelled by user")
                        return processed_nodes

                chroma_req = ChromaRequest(
                    context=node.text,
                    name=(node.metadata or {}).get("title", ""),
                    nodeId=node.id,
                    model=model,
                )
                await chroma_upsert(chroma_req)
                processed_nodes += 1

                # Yield control to event loop every few nodes for better responsiveness
                if j % 3 == 0:
                    await asyncio.sleep(0)  # Yield to allow signal handling

                # Send node-level progress for large topics (> 20 nodes)
                if len(all_nodes) > 20 and (j + 1) % 5 == 0 and progress_callback:
                    await progress_callback(
                        {
                            "type": "node_progress",
                            "current_topic": i + 1,
                            "total_topics": total_topics,
                            "topic_node": j + 1,
                            "topic_nodes": len(all_nodes),
                            "processed_nodes": processed_nodes,
                            "total_nodes": total_nodes,
                            "percentage": round(
                                (processed_nodes / total_nodes) * 100, 1
                            ),
                            "phase": "processing",
                        }
                    )

            # Send topic completion
            if progress_callback:
                await progress_callback(
                    {
                        "type": "topic_complete",
                        "current_topic": i + 1,
                        "total_topics": total_topics,
                        "topic_name": topic.name[:100],
                        "processed_nodes": processed_nodes,
                        "total_nodes": total_nodes,
                        "percentage": round((processed_nodes / total_nodes) * 100, 1),
                        "phase": "processing",
                    }
                )

        except asyncio.CancelledError:
            logger.info("Processing cancelled by user")
            if progress_callback:
                await progress_callback(
                    {
                        "type": "cancelled",
                        "current_topic": i + 1,
                        "total_topics": total_topics,
                        "processed_nodes": processed_nodes,
                        "phase": "cancelled",
                    }
                )
            raise  # Re-raise to properly handle cancellation

        except Exception as e:
            logger.error(f"Error processing topic {topic.id}: {e}")
            if progress_callback:
                await progress_callback(
                    {
                        "type": "topic_error",
                        "current_topic": i + 1,
                        "total_topics": total_topics,
                        "topic_name": topic.name[:100],
                        "error": str(e),
                        "phase": "error",
                    }
                )
            # Continue with next topic rather than failing completely
            continue

    logger.info(f"ChromaDB populated with {processed_nodes} nodes")

    if progress_callback:
        await progress_callback(
            {
                "type": "complete",
                "total_topics": total_topics,
                "total_nodes": processed_nodes,
                "phase": "complete",
            }
        )

    return processed_nodes


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
async def chroma_preload(request: Request, tana_dump: TanaDump, model: str = "openai"):
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
    request: Request, tana_dump: TanaDump, model: str = "openai"
):
    """Streaming version of preload with real-time progress updates via Server-Sent Events.

    Accepts a Tana dump JSON payload and builds the index from it with progress reporting.
    Returns progress updates as Server-Sent Events in JSON format.

    Progress event types:
    - init: Initial setup with total counts
    - topic_start: Starting to process a topic
    - topic_complete: Completed processing a topic
    - node_progress: Progress within large topics
    - topic_error: Error processing a specific topic
    - complete: All processing completed
    - error: Fatal error occurred
    """

    async def generate_progress():
        process_task = None

        try:
            async with lock:
                start_time = time.time()
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
                        try:
                            await asyncio.wait_for(
                                progress_queue.put(
                                    {
                                        "type": "error",
                                        "message": str(e),
                                        "phase": "error",
                                        "elapsed_seconds": round(
                                            time.time() - start_time, 1
                                        ),
                                    }
                                ),
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
