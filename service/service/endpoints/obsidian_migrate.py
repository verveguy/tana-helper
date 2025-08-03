import asyncio
import contextlib
import json
import os
import re
import shutil
from logging import getLogger

import pytz
from dateutil.parser import parse
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from service.dependencies import capture_logs
from service.endpoints.topics import extract_topics
from service.tana_types import TanaDump, TanaTopicNode

logger = getLogger()

router = APIRouter()


def convert_partial_date(input_str: str, timezone: str) -> str:
    # Parse the start and end times
    input_dt = parse(input_str)

    # Convert to the specified timezone
    tz = pytz.timezone(timezone)
    input_dt = input_dt.astimezone(tz)

    # Format the datetime strings in ISO-8601 format
    input_dt_str = input_dt.isoformat()
    return input_dt_str


def convert_to_iso8601(input_str: str) -> str:
    # Parse the input string to a dictionary
    data = json.loads(input_str)

    # Extract the dateTimeString and timezone
    date_time_string = data["dateTimeString"]
    timezone = data["timezone"]

    # Split the dateTimeString into start and end times
    if "/" in date_time_string:
        start_str, end_str = date_time_string.split("/")
        start_dt_str = convert_partial_date(start_str, timezone)
        end_dt_str = convert_partial_date(end_str, timezone)
        result = f"{start_dt_str}/{end_dt_str}"
    else:
        result = convert_partial_date(date_time_string, timezone)

    return result


def simple_name(name: str) -> str:
    """Convert a Tana node name to a simple string for a file name.
    Replaces references of form [[text^id]] with text.

    e.g. the string 'Meeting with [[Brett Adam^124]] and John' becomes 'Meeting with Brett Adam and John'
    """
    simple_name = re.sub(r"\[\[(.*)\^.*\]\]", r"\1", name)
    return simple_name


def obsidian_reference(name: str) -> str:
    """Convert a Tana node name to a simple string for a file name.
    Replaces references of form [[text^id]] with [[id|text]].

    e.g. the string 'Meeting with [[Brett Adam^124]] and John' becomes 'Meeting with Brett Adam and John'
    """
    obs_link = re.sub(r"\[\[([^\[\^]*)\^([^\]]+)\]\]", r"[[\2|\1]]", name)
    return obs_link


def convert_links(content: str) -> str:
    """Convert all the Tana references in the content to Obsidian references"""
    obs = re.sub(r"\[\[([^\[\^]*)\^([^\]]+)\]\]", r"[[\2|\1]]", content)
    return obs


def strip_links(content: str) -> str:
    """Convert all the Tana references in the content to Obsidian references"""
    obs = re.sub(r"\[\[([^\[\^]*)\^([^\]]+)\]\]", r"\1", content)
    # strip all colons because they are not allowed in titles or filenames
    obs = re.sub(r":", "", obs)
    return obs


def unwrap_reference(content: str):
    """Convert all the Tana references in the content to Obsidian references"""
    obs = re.search(r"([ -]*)\[\[(.+)\^([^\]]+)\]\](.*)", content)
    if obs:
        return obs.groups()
    else:
        return "", content, "", ""


def obsidian_frontmatter_field(content: str) -> str:
    """Fields need formatting with tags after the quotes"""
    dt = re.search('({"dateTimeString":[^}]+})', content)
    if dt:
        obs = content.replace(dt.group(0), f'"{convert_to_iso8601(dt.group(0))}"')
    else:
        obs = re.sub(r"\[\[([^\[\^]*)\^([^\]]+)\]\]", r'"[[\2|\1]]"', content)
    return obs


@contextlib.contextmanager
# temporarily change to a different working directory
def working_directory(path):
    _oldcwd = os.getcwd()
    os.chdir(os.path.abspath(path))

    try:
        yield
    finally:
        os.chdir(_oldcwd)


async def export_topics_to_obsidian(topics: list[TanaTopicNode]):
    """Dump all the topics to markdown files for obsidian"""

    logger.info("Building obsidian vault")

    # create a temporary directory for the vault
    tmpdirname = os.path.expanduser("~")
    if tmpdirname:
        # create a directory for the vault
        # copy static vault template
        basedir = os.path.join(tmpdirname, "vault")
        shutil.copytree(os.path.join("static", "vault"), basedir, dirs_exist_ok=True)

        with working_directory(basedir):
            logger.info(f"Created vault directory {basedir}")

            # loop through all the topics and create a markdown file for each
            for topic in topics:
                filename = simple_name(topic.id) + ".md"
                os.makedirs(
                    os.path.dirname(os.path.join(basedir, filename)), exist_ok=True
                )
                # write the topic content to the file
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("---\n")
                    f.write(f"aliases:\n  - {strip_links(topic.name)}\n")
                    # f.write(f'title: {strip_links(topic.name)}\n')
                    f.write(f"id: {topic.id}\n")
                    # f.write(f'tags:\n')
                    # f.write('Fields:\n')

                    # first, write all the fields to the properties section of the markdown file
                    for content in topic.content[1:]:
                        if content.is_field:
                            f.write(f"{obsidian_frontmatter_field(content.content)}\n")

                    f.write("---\n")

                    # then the name of the topic with links embedded
                    f.write(convert_links(topic.name) + "\n")

                    # next write all the tags to this file
                    tags = " ".join(topic.tags)
                    f.write(tags + "\n")

                    # now all the child nodes
                    for content in topic.content[1:]:
                        if content.is_field:
                            continue
                        else:
                            if content.is_reference:
                                indent, name, id, tags = unwrap_reference(
                                    content.content
                                )
                                f.write(
                                    f"{indent}{convert_links(name)} {tags} ([[{content.id}|link]])\n"
                                )
                            else:
                                f.write(convert_links(content.content) + "\n")

        logger.info(f"Obsidian vault populated and ready at {basedir}")


async def export_topics_to_obsidian_with_progress(
    topics: list[TanaTopicNode], progress_callback=None
):
    """Dump all the topics to markdown files for obsidian with progress updates"""

    logger.info("Building obsidian vault with progress updates")

    # create a temporary directory for the vault
    tmpdirname = os.path.expanduser("~")
    if tmpdirname:
        # create a directory for the vault
        # copy static vault template
        basedir = os.path.join(tmpdirname, "vault")
        shutil.copytree(os.path.join("static", "vault"), basedir, dirs_exist_ok=True)

        with working_directory(basedir):
            logger.info(f"Created vault directory {basedir}")

            # loop through all the topics and create a markdown file for each
            for i, topic in enumerate(topics):
                logger.info(f"Processing topic {i + 1}/{len(topics)}: {topic.name}")

                # Send progress update if callback provided
                if progress_callback:
                    await progress_callback(
                        {
                            "type": "processing",
                            "current_topic": i + 1,
                            "total_topics": len(topics),
                            "current_topic_name": topic.name,
                            "current_topic_id": topic.id,
                            "percentage": int(((i + 1) / len(topics)) * 100),
                        }
                    )

                filename = simple_name(topic.id) + ".md"
                os.makedirs(
                    os.path.dirname(os.path.join(basedir, filename)), exist_ok=True
                )
                # write the topic content to the file
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("---\n")
                    f.write(f"aliases:\n  - {strip_links(topic.name)}\n")
                    # f.write(f'title: {strip_links(topic.name)}\n')
                    f.write(f"id: {topic.id}\n")
                    # f.write(f'tags:\n')
                    # f.write('Fields:\n')

                    # first, write all the fields to the properties section of the markdown file
                    for content in topic.content[1:]:
                        if content.is_field:
                            f.write(f"{obsidian_frontmatter_field(content.content)}\n")

                    f.write("---\n")

                    # then the name of the topic with links embedded
                    f.write(convert_links(topic.name) + "\n")

                    # next write all the tags to this file
                    tags = " ".join(topic.tags)
                    f.write(tags + "\n")

                    # now all the child nodes
                    for content in topic.content[1:]:
                        if content.is_field:
                            continue
                        else:
                            if content.is_reference:
                                indent, name, id, tags = unwrap_reference(
                                    content.content
                                )
                                f.write(
                                    f"{indent}{convert_links(name)} {tags} ([[{content.id}|link]])\n"
                                )
                            else:
                                f.write(convert_links(content.content) + "\n")

        logger.info(f"Obsidian vault populated and ready at {basedir}")


# attempt to parallelize non-async code
# see https://github.com/tiangolo/fastapi/discussions/6347
lock = asyncio.Lock()


# Note: accepts ?model= query param
@router.post("/migrate/obsidian", tags=["migrate"])
async def migrate_to_obsidian(request: Request, tana_dump: TanaDump):
    """Accepts a Tana dump JSON payload and builds an Obsidian vault from it.

    Returns a list of log messages from the process.
    """
    async with lock:
        messages = []
        async with capture_logs(logger) as logs:
            topics = await extract_topics(tana_dump, "OBSIDIAN")  # type: ignore
            logger.info("Extracted topics from Tana dump")

            # make a vault from the topics
            await export_topics_to_obsidian(topics)

            messages = logs.getvalue()
        return messages


@router.post("/migrate/obsidian/stream", tags=["migrate"])
async def migrate_to_obsidian_stream(request: Request, tana_dump: TanaDump):
    """Accepts a Tana dump JSON payload and builds an Obsidian vault from it with streaming progress updates.

    Returns a streaming response with progress updates.
    """
    async with lock:
        async with capture_logs(logger) as logs:
            topics = await extract_topics(tana_dump, "OBSIDIAN")  # type: ignore
            logger.info("Extracted topics from Tana dump")

            async def generate_progress():
                # Send initial progress
                yield f"data: {json.dumps({'type': 'starting', 'total_topics': len(topics)})}\n\n"

                # Create a queue for real-time progress updates
                progress_queue = asyncio.Queue()

                async def progress_callback(data):
                    # Put progress update in queue for immediate streaming
                    await progress_queue.put(data)
                    # Small delay to allow network layer to send data
                    await asyncio.sleep(0.01)

                # Start the export process in the background
                export_task = asyncio.create_task(
                    export_topics_to_obsidian_with_progress(topics, progress_callback)
                )

                # Stream progress updates in real-time
                while not export_task.done() or not progress_queue.empty():
                    try:
                        # Wait for progress update with timeout
                        progress_data = await asyncio.wait_for(
                            progress_queue.get(), timeout=0.05
                        )
                        yield f"data: {json.dumps(progress_data)}\n\n"
                    except TimeoutError:
                        # Check if export is complete and queue is empty
                        if export_task.done() and progress_queue.empty():
                            break
                        # Continue waiting for more progress updates
                        continue

                # Wait for export to complete
                await export_task

                # Send completion
                yield f"data: {json.dumps({'type': 'complete', 'total_topics': len(topics), 'vault_path': os.path.expanduser('~/vault')})}\n\n"

            return StreamingResponse(
                generate_progress(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
