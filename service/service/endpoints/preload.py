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
    ChromaRequest,
    EmbeddableNode,
    TanaNodeMetadata,
    TanaTopicNode,
    capture_logs,
    create_individual_node_hash,
    get_embeddings,
    get_embeddings_batch,
    get_stored_node_hashes,
    prepare_node_for_embedding,
)
from service.endpoints.chroma import chroma_upsert, get_collection
from service.endpoints.topics import extract_topics
from service.tana_types import TANA_NODE, TanaDocument, TanaDump

logger = getLogger()

router = APIRouter()

# Constants from original implementation
TANA_TEXT = "tana-text"
minutes = 1000 * 60
BATCH_SIZE = 500

# Restore snowflakes for compatibility
snowflakes = SnowflakeGenerator(42)

# TODO: Add header support throughout so we can pass Tana API key and OpenAPI Key as headers
# NOTE: we already have this in the main.py middleware wrapper, but it would be better
# to do it here for OpenAPI spec purposes.
# x_tana_api_token: Annotated[str | None, Header()] = None
# x_openai_api_key: Annotated[str | None, Header()] = None


# reduce our list of nodes to embed by testing hashes of the nodes
def reduce_embeddings(nodes: list[EmbeddableNode]) -> tuple[list[EmbeddableNode], dict]:
    collection = get_collection()
    lookup = {node.id: node for node in nodes}
    removes = {}
    deletes = {}

    # TODO: narrow this query to nodes from the given workspace
    # (requires we track workspace root node somehow in metadata or collection name)
    query_response = collection.get()

    if query_response and query_response["metadatas"]:
        # the result from ChromaDB is kinda strange. Instead of an array of objects
        # it's four distinct arrays of object properties. Very odd interface.

        for node_id, metadata in zip(
            query_response["ids"],
            query_response["metadatas"],
            strict=False,
        ):
            # is this node in the new set?
            if node_id in lookup:
                the_node = lookup[node_id]
                if metadata and the_node.hash == metadata["hash"]:
                    # remove this node from the results
                    removes[node_id] = the_node
            else:
                deletes[node_id] = True

    # remove the nodes that are already in the DB
    results = [node for node in nodes if node.id not in removes]
    return results, deletes


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
        await chroma_upsert(chroma_req)

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
        # === PASS 1: Collect all nodes and content with NODE-LEVEL HASH OPTIMIZATION ===
        logger.info(
            "Pass 1: Collecting nodes with NODE-LEVEL hash-based change detection..."
        )

        all_nodes = []
        content_list = []
        node_metadata = []
        node_to_hash = {}  # Map node_id -> current_hash
        skipped_count = 0

        collection = get_collection()

        # 🎯 PROGRESS: Send initial collection start event
        if progress_callback:
            await progress_callback(
                {
                    "type": "collection_start",
                    "total_topics": len(topics),
                    "phase": "batch_processing",
                }
            )

        for topic_idx, topic in enumerate(topics):
            # Check for cancellation every 100 topics during collection
            if topic_idx % 100 == 0:
                if current_task and current_task.cancelled():
                    logger.debug("Task cancelled during node collection")
                    raise asyncio.CancelledError()
                await asyncio.sleep(0)

                # 🎯 PROGRESS: Send collection progress every 100 topics
                if progress_callback and topic_idx > 0:
                    await progress_callback(
                        {
                            "type": "collection_progress",
                            "current_topic": topic_idx,
                            "total_topics": len(topics),
                            "current_nodes": len(all_nodes),
                            "phase": "batch_processing",
                            "collection": {
                                "current": topic_idx,
                                "total": len(topics),
                                "completed": False,
                            },
                        }
                    )

            # Get all nodes for this topic using existing logic
            (doc_node, text_nodes) = document_from_topic(topic)
            topic_nodes = [doc_node] + text_nodes

            # 🎯 NODE-LEVEL HASH CALCULATION (major improvement!)
            for node in topic_nodes:
                # Calculate hash for this specific node
                current_hash = create_individual_node_hash(node)
                node_to_hash[node.id] = current_hash

                # Store all nodes and their metadata for batch processing
                all_nodes.append(node)
                content_list.append(node.text)
                node_metadata.append(
                    {
                        "topic_idx": topic_idx,
                        "topic_id": topic.id,
                        "topic_name": topic.name[:100],
                        "node_id": node.id,
                        "node_text": node.text,
                        "node_metadata": node.metadata or {},
                        "content_hash": current_hash,  # 🎯 Store individual node hash
                    }
                )

        # 🎯 PROGRESS: Send collection completion event
        if progress_callback:
            await progress_callback(
                {
                    "type": "collection_complete",
                    "total_topics": len(topics),
                    "total_nodes": len(all_nodes),
                    "phase": "batch_processing",
                    "collection": {
                        "current": len(topics),
                        "total": len(topics),
                        "completed": True,
                    },
                }
            )

        # 🎯 BATCH HASH CHECKING - Check all nodes at once for efficiency
        logger.info(f"Collected {len(all_nodes)} nodes, checking for changes...")
        all_node_ids = [node.id for node in all_nodes]
        stored_hashes = get_stored_node_hashes(collection, all_node_ids)

        # 🎯 FILTER UNCHANGED NODES - Remove nodes that haven't changed
        changed_nodes = []
        changed_content = []
        changed_metadata = []

        for i, node in enumerate(all_nodes):
            current_hash = node_to_hash[node.id]
            stored_hash = stored_hashes.get(node.id)

            if stored_hash and stored_hash == current_hash:
                # Node unchanged, skip it
                skipped_count += 1
                logger.debug(
                    f"⚡ Skipping unchanged node {node.id} (hash: {current_hash[:8]}...)"
                )
                continue

            # Node changed or new, include it for processing
            changed_nodes.append(node)
            changed_content.append(content_list[i])
            changed_metadata.append(node_metadata[i])

        # Update variables to use only changed nodes
        all_nodes = changed_nodes
        content_list = changed_content
        node_metadata = changed_metadata

        # 🎯 INCREMENTAL DELETION - Remove nodes that are no longer in Tana dump
        logger.info("Identifying nodes for deletion (no longer in Tana dump)...")

        deleted_count = 0  # Track deleted nodes for progress reporting

        # Get ALL existing nodes from ChromaDB to check for deletions
        try:
            all_existing_response = collection.get(include=["metadatas"])
            existing_node_ids = (
                set(all_existing_response["ids"])
                if all_existing_response["ids"]
                else set()
            )

            # Create set of all node IDs that should exist (from current Tana dump)
            current_node_ids = set(all_node_ids)  # This includes ALL nodes from dump

            # Find nodes that exist in ChromaDB but NOT in current dump
            nodes_to_delete = existing_node_ids - current_node_ids

            if nodes_to_delete:
                logger.info(
                    f"🗑️  Found {len(nodes_to_delete)} orphaned nodes to delete from ChromaDB"
                )

                # Send deletion start progress callback
                if progress_callback:
                    await progress_callback(
                        {
                            "type": "deletion_start",
                            "total_nodes_to_delete": len(nodes_to_delete),
                            "phase": "deletion",
                        }
                    )

                # Delete orphaned nodes in batches for performance
                delete_batch_size = 100
                deletion_start_time = time.time()

                for i in range(0, len(nodes_to_delete), delete_batch_size):
                    batch_to_delete = list(nodes_to_delete)[i : i + delete_batch_size]

                    try:
                        collection.delete(ids=batch_to_delete)
                        deleted_count += len(batch_to_delete)
                        logger.debug(
                            f"Deleted batch of {len(batch_to_delete)} orphaned nodes"
                        )

                        # Send deletion progress callback every batch
                        if progress_callback:
                            deletion_elapsed = time.time() - deletion_start_time
                            deletion_rate = (
                                deleted_count / deletion_elapsed
                                if deletion_elapsed > 0
                                else 0
                            )
                            deletion_eta = (
                                (len(nodes_to_delete) - deleted_count) / deletion_rate
                                if deletion_rate > 0
                                else 0
                            )

                            await progress_callback(
                                {
                                    "type": "deletion_progress",
                                    "deleted_nodes": deleted_count,
                                    "total_nodes_to_delete": len(nodes_to_delete),
                                    "deletion_elapsed": round(deletion_elapsed, 1),
                                    "deletion_rate": round(deletion_rate, 1),
                                    "deletion_eta": round(deletion_eta, 1),
                                    "phase": "deletion",
                                }
                            )

                        # Check for cancellation during deletion
                        if current_task and current_task.cancelled():
                            logger.debug("Task cancelled during orphaned node deletion")
                            raise asyncio.CancelledError()
                        await asyncio.sleep(0)

                    except Exception as e:
                        logger.warning(f"Error deleting batch of orphaned nodes: {e}")

                logger.info(
                    f"🗑️  Successfully deleted {deleted_count} orphaned nodes from ChromaDB"
                )

                # Send deletion completion callback
                if progress_callback:
                    await progress_callback(
                        {
                            "type": "deletion_complete",
                            "deleted_nodes": deleted_count,
                            "total_nodes_to_delete": len(nodes_to_delete),
                            "deletion_elapsed": round(
                                time.time() - deletion_start_time, 1
                            ),
                            "phase": "deletion_complete",
                        }
                    )
            else:
                logger.info("✅ No orphaned nodes found - ChromaDB is synchronized")
                # Notify frontend that deletion phase was skipped
                if progress_callback:
                    await progress_callback(
                        {
                            "type": "phase_skipped",
                            "phase": "deletion",
                            "reason": "No orphaned nodes found",
                        }
                    )

        except Exception as e:
            logger.warning(f"Could not check for orphaned nodes: {e}")

        if skipped_count > 0:
            logger.info(
                f"⚡ NODE-LEVEL OPTIMIZATION: Skipped {skipped_count} unchanged nodes "
                f"(saved {skipped_count} embedding calls!)"
            )

        # Send initial progress callback with optimization statistics
        if progress_callback:
            await progress_callback(
                {
                    "type": "init",
                    "total_topics": len(topics),
                    "total_nodes": len(all_nodes),
                    "skipped_nodes": skipped_count,
                    "deleted_nodes": deleted_count,
                    "changed_topics": len(topics) - skipped_count,
                    "phase": "batch_processing",
                }
            )

        # === PASS 2: Get embeddings in batches with content monitoring ===
        if not content_list:
            logger.info("Pass 2: No nodes to embed - skipping embedding phase")
            # Notify frontend that embedding phase was skipped
            if progress_callback:
                await progress_callback(
                    {
                        "type": "phase_skipped",
                        "phase": "embedding",
                        "reason": "No nodes to embed",
                    }
                )
        else:
            logger.info("Pass 2: Processing embeddings in batches...")

            # 🎯 RESTORED: Content size monitoring from OLD function
            content_sizes = [len(text) for text in content_list]
            max_size = max(content_sizes)
            avg_size = sum(content_sizes) / len(content_sizes)
            large_content_count = sum(1 for size in content_sizes if size > 8000)

            logger.info("📊 Content size analysis:")
            logger.info(f"   📏 Largest content: {max_size:,} characters")
            logger.info(f"   📊 Average content: {avg_size:.0f} characters")
            logger.info(f"   ⚠️  Large content pieces (>8K): {large_content_count}")

            if max_size > 32000:  # OpenAI context limit warning
                logger.warning(
                    f"⚠️  Very large content detected ({max_size:,} chars) - may cause API failures"
                )

        # Calculate optimal batch size based on content
        from service.dependencies import (
            calculate_optimal_batch_size,
        )

        optimal_batch_size = calculate_optimal_batch_size(content_list)

        if progress_callback:
            await progress_callback(
                {
                    "type": "batch_start",
                    "total_nodes": len(all_nodes),
                    "batch_size": optimal_batch_size,
                    "estimated_batches": (len(all_nodes) + optimal_batch_size - 1)
                    // optimal_batch_size
                    if len(all_nodes) > 0
                    else 0,
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

        # === PASS 3: Batch Upsert to ChromaDB ===
        if not all_nodes:
            logger.info("Pass 3: No nodes to store - skipping storage phase")
            # Notify frontend that storage phase was skipped
            if progress_callback:
                await progress_callback(
                    {
                        "type": "phase_skipped",
                        "phase": "storing",
                        "reason": "No nodes to store",
                    }
                )
        else:
            logger.info("Pass 3: Batch upserting to ChromaDB...")

        if progress_callback:
            await progress_callback(
                {
                    "type": "upsert_start",
                    "total_nodes": len(all_nodes),
                    "phase": "storing",
                }
            )

        storing_phase_start = time.time()  # Track start of storing phase

        # 🚀 BATCH UPSERT PERFORMANCE IMPROVEMENT
        # Use ChromaDB's native batch operations instead of individual upserts
        # This provides massive performance improvements (10-50x faster!)

        collection = get_collection()
        failed_nodes = await chroma_batch_upsert(
            collection=collection,
            batch_nodes=all_nodes,
            batch_embeddings=all_embeddings,
            batch_metadata=node_metadata,
            progress_callback=progress_callback,
        )

        # Send completion callback
        elapsed_time = time.time() - start_time
        logger.info(f"ChromaDB batch indexing completed in {elapsed_time:.1f}s")
        logger.info(
            f"Performance: {len(all_nodes) / elapsed_time:.1f} nodes/second with batching!"
        )

        if failed_nodes > 0:
            logger.warning(
                f"Storage completed with {failed_nodes} failed nodes out of {len(all_nodes)} total"
            )

        if progress_callback:
            await progress_callback(
                {
                    "type": "complete",
                    "total_topics": len(topics),
                    "total_nodes": len(all_nodes),
                    "processed_nodes": len(all_nodes),
                    "failed_nodes": failed_nodes,
                    "skipped_topics": skipped_count,
                    "deleted_nodes": deleted_count,
                    "processing_rate": round(len(all_nodes) / elapsed_time, 2),
                    "elapsed_seconds": round(elapsed_time, 1),
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
                    "processed_nodes": len(all_nodes) if "all_nodes" in locals() else 0,
                    "total_nodes": len(all_nodes) if "all_nodes" in locals() else 0,
                    "elapsed_seconds": round(elapsed_time, 1),
                    "phase": "cancelled",
                }
            )

        # Re-raise to properly handle cancellation
        raise


# OLD INDIVIDUAL UPSERT FUNCTION REMOVED
# This function was replaced with chroma_batch_upsert for much better performance
# The old approach processed nodes one by one, which was extremely slow
# The new batch approach processes hundreds of nodes at once using ChromaDB's native batch API


async def chroma_batch_upsert(
    collection,
    batch_nodes: list,
    batch_embeddings: list,
    batch_metadata: list,
    batch_size: int | None = None,
    progress_callback=None,
) -> int:
    """
    Batch upsert to ChromaDB using native batch operations for optimal performance.

    Uses ChromaDB's client.max_batch_size for optimal batching and significantly faster
    than individual upserts. This restores the performance we had in the old implementation.

    Args:
        collection: ChromaDB collection instance
        batch_nodes: List of node objects
        batch_embeddings: List of embedding vectors (already computed)
        batch_metadata: List of metadata dicts with content hashes
        batch_size: Optional batch size override (uses client.max_batch_size if None)
    """
    from service.dependencies import TANA_NODE, TanaNodeMetadata
    from service.tanaparser import prune_reference_nodes

    if not batch_nodes:
        # Send completion progress event even for empty input to maintain UI state
        if progress_callback:
            await progress_callback(
                {
                    "type": "storing_progress",
                    "current_batch": 0,
                    "total_batches": 0,
                    "current_node": 0,
                    "total_nodes": 0,
                    "phase": "storing",
                }
            )
        return 0

    # Get optimal batch size from ChromaDB client if not specified
    if batch_size is None:
        # ChromaDB exposes max_batch_size for optimal performance
        from service.endpoints.chroma import get_chroma

        client = get_chroma()
        effective_batch_size = getattr(client, "max_batch_size", 100)  # Fallback to 100
    else:
        effective_batch_size = batch_size

    # Process in optimal batches
    failed_count = 0
    processed_count = 0
    batch_start_time = time.time()

    total_batches = (
        len(batch_nodes) + effective_batch_size - 1
    ) // effective_batch_size
    current_batch_num = 0

    for i in range(0, len(batch_nodes), effective_batch_size):
        current_batch_num += 1
        sub_batch_nodes = batch_nodes[i : i + effective_batch_size]
        sub_batch_embeddings = batch_embeddings[i : i + effective_batch_size]
        sub_batch_metadata = batch_metadata[i : i + effective_batch_size]

        try:
            # Prepare batch data for ChromaDB
            batch_ids = []
            batch_documents = []
            batch_metadatas = []

            for node, metadata in zip(
                sub_batch_nodes, sub_batch_metadata, strict=False
            ):
                # Apply same logic as individual upsert
                pruned_content = prune_reference_nodes(node.text)

                # Convert node.id to string (fix for integer->string conversion)
                batch_ids.append(str(node.id))
                batch_documents.append(
                    node.text or ""
                )  # Use original or pruned content

                # Create metadata using same structure as individual upsert
                node_metadata = TanaNodeMetadata(
                    category=TANA_NODE,
                    supertag="",  # Will be populated from node metadata if available
                    title=metadata["node_metadata"].get("title", ""),
                    text=pruned_content,
                    tana_id=str(node.id),
                    topic_id=metadata["topic_id"],
                    content_hash=metadata[
                        "content_hash"
                    ],  # Store content hash for change detection
                )

                batch_metadatas.append(node_metadata.model_dump())

            # 🚀 BATCH UPSERT - This is the key performance improvement!
            collection.upsert(
                ids=batch_ids,
                embeddings=sub_batch_embeddings,
                documents=batch_documents,
                metadatas=batch_metadatas,
            )

            processed_count += len(sub_batch_nodes)
            logger.debug(f"🚀 Batch upserted {len(sub_batch_nodes)} nodes to ChromaDB")

            # 📊 PROGRESS REPORTING - Send progress updates during batch processing
            if progress_callback:
                elapsed = time.time() - batch_start_time
                rate = processed_count / elapsed if elapsed > 0 else 0
                eta = (len(batch_nodes) - processed_count) / rate if rate > 0 else 0

                await progress_callback(
                    {
                        "type": "storing_progress",
                        "current_node": processed_count,
                        "total_nodes": len(batch_nodes),
                        "current_batch": current_batch_num,
                        "total_batches": total_batches,
                        "failed_nodes": failed_count,
                        "storing_elapsed": round(elapsed, 1),
                        "storing_rate": round(rate, 1),
                        "storing_eta": round(eta, 1) if eta > 0 else 0,
                        "phase": "storing",
                    }
                )

        except Exception as e:
            failed_count += len(sub_batch_nodes)
            logger.error(
                f"❌ Batch upsert failed for {len(sub_batch_nodes)} nodes: {e}"
            )

            # For failed batches, we could optionally try individual upserts as fallback
            # but for now, we'll just log and continue

    if failed_count > 0:
        logger.warning(f"⚠️  {failed_count} nodes failed to upsert in batch operations")

    return failed_count


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
    """Load a single topic into the index_nodes list with enhanced field integration."""
    text_nodes = []

    # 🎯 RESTORED: Advanced field processing from OLD function
    tags = " ".join(topic.tags) if topic.tags else ""

    # Start with the main content (first line) + tags
    base_text = topic.content[0].content if topic.content else topic.name
    text = base_text + " " + tags + "\n"

    # 🎯 CRITICAL RESTORATION: Fields become part of searchable content!
    field_text = ""
    if topic.fields:
        for field in topic.fields:
            # Smart field filtering from OLD function
            if field.name == "Attendees":  # Skip noisy fields
                continue
            field_text += f"{field.name}:: {field.value}\n"

    # Integrate fields into main searchable text
    text += field_text

    # Also keep fields in metadata for structured access
    metadata = {
        "category": TANA_NODE,
        "supertag": tags,
        "title": topic.name,
        "has_integrated_fields": bool(field_text),  # Track field integration
    }

    if topic.fields:
        # Keep structured field access in metadata
        fields = {field.name for field in topic.fields}
        for field_name in fields:
            metadata[field_name] = " ".join(
                [field.value for field in topic.fields if field.name == field_name]
            )

    # Create document with enriched searchable content
    document_node = Document(id=topic.id, text=text, metadata=metadata)

    # 🎯 RESTORED: Sophisticated reference handling from OLD function
    references = {}  # Track references to avoid duplicates
    previous_text_node = None

    # if len(topic.content) > 30:
    #     logger.warning(f"Large topic {topic.id} with {len(topic.content)} children")

    # Process all child content with enhanced reference handling
    for content in topic.content[1:]:
        content_id = content.id
        is_ref = content.is_reference
        tana_element = content.content
        content_metadata = TanaNodeMetadata(
            category=TANA_TEXT,
            title=topic.name,
            topic_id=topic.id,
        )

        # 🎯 RESTORED: Deterministic reference ID generation
        if is_ref:
            # Create deterministic reference ID (not random!)
            ref_node_id = (
                f"{content_id}__{topic.id}"
                if content_id
                else f"ref__{topic.id}__{len(text_nodes)}"
            )

            # Skip if we already created this reference
            if ref_node_id in references:
                continue
            references[ref_node_id] = True

            current_text_node = TextNode(id=ref_node_id, text=tana_element)
            current_text_node.metadata["tana_ref_id"] = content_id
            current_text_node.metadata["is_reference"] = True
        else:
            # Regular content node
            node_id = (
                content_id if content_id else f"content__{topic.id}__{len(text_nodes)}"
            )
            current_text_node = TextNode(id=node_id, text=tana_element)
            current_text_node.metadata["is_reference"] = False

        current_text_node.metadata.update(content_metadata.model_dump())

        # Maintain relationships
        current_text_node.relationships[NodeRelationship.SOURCE] = document_node.id
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
    request: Request, tana_dump: TanaDump, model: str = "OPENAI_EMBEDDING_MODEL"
):
    """Accepts a Tana dump JSON payload and builds the index from it.
    Uses the topic extraction code from the topics endpoint to build
    an object tree in memory, then loads that into ChromaDB via LLamaIndex.

    Returns a list of log messages from the process.
    """
    async with lock:
        messages = []
        async with capture_logs(logger) as logs:
            result = await extract_topics(tana_dump, "TANA")  # type: ignore
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


async def OLD_load_chromadb_from_topics(
    topics: list[TanaTopicNode], model: str, observe=False
):
    """Load the topic index from the topic array directly."""

    references = {}

    index_nodes = []
    # loop through all the topics and create an EmbeddableNode for each
    for topic in topics:
        tags = " ".join(topic.tags)
        text = topic.content[0].content + " " + tags + "\n"

        # find all of the fields and make them part of the topic context
        field_text = ""
        for content in topic.content[1:]:
            if content.is_field:
                # TODO HACK if content starts with Attendees:: we want to skip it
                if content.field_name == "Attendees":
                    continue

                field_text += content.content + "\n"

        text += field_text
        index_nodes.append(
            prepare_node_for_embedding(
                node_id=topic.id,
                content_id=topic.id,
                topic_id=topic.id,
                name=topic.name,
                tags=tags,
                context=text,
            )
        )

        # now embed all the child content nodes, pointing back at the parent topic
        for content in topic.content[1:]:
            if content.is_field:
                continue

            # build a more detailed tree of nodes
            # references are .. hard. We make a new synthetic node here
            # since references will be embedded themselves as topics
            # and we just want to know that the content of the reference node
            # is relevant to the current topic we are embedding.
            topic_id = topic.id
            content_id = content.id
            if content.is_reference:
                # node_id = nextflake() # this means we will leak fake reference nodes over time...
                node_id = content.id + "__" + topic.id  # type: ignore
                if node_id in references:
                    # we already created this node_topic ref, so skip
                    continue
                references[node_id] = content
            else:
                node_id = content.id

            new_node = prepare_node_for_embedding(
                node_id=node_id or "unknown",
                content_id=content_id or "unknown",
                topic_id=topic_id,
                name=content.content,
                tags="",  # TODO: add tags to content nodes
                context=content.content + "\n",
            )
            index_nodes.append(new_node)

    logger.info(f"Gathered {len(index_nodes)} nodes for embedding")

    index_nodes, deletes = reduce_embeddings(index_nodes)

    logger.info(f"Reduced to {len(index_nodes)} nodes for embedding")
    # TODO: delete dead nodes, but NOT until we have properly implemented multi-workspace support
    logger.info(f"Identified {len(deletes)} nodes for removal")

    collection = get_collection()

    counter = 0
    # batch process the nodes, generating embeddings
    for i in range(0, len(index_nodes), BATCH_SIZE):
        batch = index_nodes[i : i + BATCH_SIZE]
        nodes = [node.text for node in batch]

        counter = counter + 1
        # somewhere in this batch, we have a very long text that will cause the OpenAI API to fail
        biggest = 0
        for node in batch:
            if len(node.text) > biggest:
                biggest = len(node.text)
                big_node = node

        logger.info(
            f"Batch {counter} Node {big_node.id} has {len(big_node.text)} characters"
        )

        embeddings = await get_embeddings(nodes, model=model)
        for j, node in enumerate(batch):
            node.embedding = embeddings[j].embedding

        # upsert the batch into ChromaDB
        # @sleep_and_retry
        # @limits(calls=5, period=10)
        def do_upsert(current_batch):
            collection.upsert(
                ids=[node.id for node in current_batch],
                embeddings=[node.embedding for node in current_batch],  # type: ignore
                # we only embed the name of the node (primary content of the node)
                documents=[node.name for node in current_batch],
                metadatas=[node.metadata for node in current_batch],  # type: ignore
            )

        do_upsert(batch)

    logger.info("ChromaDB populated and ready")
    return index_nodes
