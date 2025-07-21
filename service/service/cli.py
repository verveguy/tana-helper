"""CLI entry points for running the Tana Helper service."""

import sys

import uvicorn


def dev():
    """Start development server with hot reloading."""
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
    except KeyboardInterrupt:
        print("\n🛑 Development server stopped")
        sys.exit(0)


def serve():
    """Start production server."""
    try:
        uvicorn.run(
            "service.main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            use_colors=True,
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        sys.exit(0)


def debug():
    """Start development server with debug logging."""
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
    except KeyboardInterrupt:
        print("\n🛑 Debug server stopped")
        sys.exit(0)
