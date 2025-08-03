import asyncio
import threading
import time

import pytest
import requests
import uvicorn
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from service.main import app

# Test configuration
TEST_BASE_URL = "http://localhost:8000"
TEST_HOST = "127.0.0.1"
TEST_PORT = 8000


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Create a test client for FastAPI application."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def live_server():
    """Start a live server for integration tests."""

    def run_server():
        uvicorn.run(app, host=TEST_HOST, port=TEST_PORT, log_level="warning")

    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    max_retries = 30
    for _i in range(max_retries):
        try:
            response = requests.get(f"{TEST_BASE_URL}/docs")
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    else:
        pytest.fail("Server failed to start")

    yield TEST_BASE_URL

    # Server cleanup happens when daemon thread ends


@pytest.fixture
async def async_client():
    """Create an async client for testing async endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def sample_tana_data():
    """Sample Tana format data for testing."""
    return """- Main Topic
  - Subtopic 1
    - field1:: value1
    - field2:: value2
  - Subtopic 2
    - list_item:: item1
    - list_item:: item2"""


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing."""
    return {
        "name": "Test Object",
        "type": "sample",
        "attributes": {"field1": "value1", "field2": "value2"},
        "items": ["item1", "item2"],
    }


@pytest.fixture
def sample_calendar_data():
    """Sample calendar data for testing."""
    return """- Event: Team Meeting
  - date:: 2024-01-15
  - time:: 10:00 AM
  - duration:: 1 hour
  - attendees::
    - John Doe
    - Jane Smith"""
