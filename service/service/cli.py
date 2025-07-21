"""CLI entry points for running the Tana Helper service."""

import logging
import signal
import sys

import uvicorn


def _setup_signal_handlers():
    """Setup clean signal handling to avoid stack traces."""

    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def _suppress_uvicorn_shutdown_logs():
    """Suppress uvicorn's verbose shutdown logging."""
    # Reduce log level for uvicorn's access logger during shutdown
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.WARNING)

    # Suppress asyncio cancellation warnings
    asyncio_logger = logging.getLogger("asyncio")
    asyncio_logger.setLevel(logging.ERROR)


def dev():
    """Start development server with hot reloading."""
    _setup_signal_handlers()

    try:
        uvicorn.run(
            "service.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            use_colors=True,
            access_log=True,
        )
    except (KeyboardInterrupt, SystemExit):
        _suppress_uvicorn_shutdown_logs()
        print("🛑 Development server stopped cleanly")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


def serve():
    """Start production server."""
    _setup_signal_handlers()

    try:
        uvicorn.run(
            "service.main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            use_colors=True,
            access_log=True,
        )
    except (KeyboardInterrupt, SystemExit):
        _suppress_uvicorn_shutdown_logs()
        print("🛑 Server stopped cleanly")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


def debug():
    """Start development server with debug logging."""
    _setup_signal_handlers()

    try:
        uvicorn.run(
            "service.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="debug",
            use_colors=True,
            access_log=True,
        )
    except (KeyboardInterrupt, SystemExit):
        _suppress_uvicorn_shutdown_logs()
        print("🛑 Debug server stopped cleanly")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
