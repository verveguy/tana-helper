import asyncio
from logging import getLogger

import aiofiles
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from service.logconfig import get_logger_config

router = APIRouter()

# log streaming
log_config, log_filename = get_logger_config()

logger = getLogger()
# log_file = log_config.logger_file

# TODO: rework this to use the logging stream instead of reading the file
# also don't capture rendered logs - capture raw logs and then
# render them via Rich Console here ...
# This will allow us to resize the virtual Console based on the actual client
# console size - we will need to pass this information over the websocket
# and also support re-rendering the whole log, etc. etc.


@router.websocket("/ws/log")
async def websocket_endpoint_log(websocket: WebSocket) -> None:
    """WebSocket endpoint for client connections

    Args:
        websocket (WebSocket): WebSocket request from client.
    """
    await websocket.accept()
    logger.info("WebSocket connection established for log streaming")

    try:
        # TODO: instead of reading the file, tap into the logging stream before it goes to the file
        async with aiofiles.open(f"{log_filename}") as file:
            # read n lines from the file
            while True:
                line = await file.readline()
                if line != "":
                    try:
                        await websocket.send_text(line)
                    except WebSocketDisconnect:
                        # Client disconnected normally - not an error
                        logger.info("WebSocket client disconnected normally")
                        break
                    except Exception as e:
                        # Only log unexpected errors
                        logger.warning(
                            f"Unexpected error sending WebSocket message: {e}"
                        )
                        break
                else:
                    # TODO: how to make the readline() block until there is a line?
                    await asyncio.sleep(2)

    except WebSocketDisconnect:
        # Client disconnected - this is normal behavior
        logger.info("WebSocket client disconnected during log streaming")
    except Exception as e:
        # Only log actual errors, not disconnections
        logger.error(f"Unexpected error in WebSocket log streaming: {e}")
    finally:
        # Only try to close if the connection is still open
        try:
            if websocket.client_state.name != "DISCONNECTED":
                await websocket.close()
                logger.info("WebSocket connection closed by server")
        except Exception:
            # If we can't close cleanly, it's already closed - no need to log
            pass
