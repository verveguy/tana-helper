import requests
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from typing import List, Union
from service.dependencies import OPENAI_CHAT_MODEL, OPENAI_EMBEDDING_MODEL, ChromaRequest, CalendarRequest
from service.settings import settings
from .test_types import BASE_URL, APIValidationError, HTTPValidationError


def test_chroma_upsert_success():
    payload = ChromaRequest(
        nodeId="12345",
        model=OPENAI_CHAT_MODEL,
        embedding_model=OPENAI_EMBEDDING_MODEL,
        context="test context",
        name="test",
        environment="local",
        score=0.8,
        top=10,
        tags="test"
    ).model_dump(exclude_none=True)
    response = requests.post(f"{BASE_URL}/chroma/upsert", json=payload)
    assert response.status_code == 204
    # Additional assertions can be added based on expected response content

def test_chroma_upsert_validation_error():
    payload = {"invalid": "data"}
    response = requests.post(f"{BASE_URL}/chroma/upsert", json=payload)
    assert response.status_code == 422
    error_response = HTTPValidationError.model_validate(response.json())
    # Additional assertions can be added to check the content of the error response

def test_chroma_delete_success():
    payload = ChromaRequest(
        nodeId="12345",
        model=OPENAI_CHAT_MODEL,
        embedding_model=OPENAI_EMBEDDING_MODEL,
        context="test context",
        name="test",
        environment="local",
        score=0.8,
        top=10,
        tags="test"
    ).model_dump(exclude_none=True)
    response = requests.post(f"{BASE_URL}/chroma/delete", json=payload)
    assert response.status_code == 204
    # Additional assertions can be added based on expected response content

def test_chroma_delete_validation_error():
    payload = {"invalid": "data"}
    response = requests.post(f"{BASE_URL}/chroma/delete", json=payload)
    assert response.status_code == 422
    error_response = HTTPValidationError.model_validate(response.json())
    # Additional assertions can be added to check the content of the error response

def test_chroma_query():
    query_payload = ChromaRequest(
        nodeId="12345",
        model=OPENAI_CHAT_MODEL,
        embedding_model=OPENAI_EMBEDDING_MODEL,
        context="test context",
        name="test",
        environment="local",
        score=0.8,
        top=10,
        tags="test"
    ).model_dump(exclude_none=True)
    response = requests.post(f"{BASE_URL}/chroma/query", json=query_payload)
    assert response.status_code == 200
    # Additional assertions based on expected response content


def test_chroma_upsert_delete_query_flow():
    # Upsert a node
    upsert_payload = ChromaRequest(
        nodeId="1234567890",
        # ... other fields
    ).model_dump(exclude_none=True)
    upsert_response = requests.post(f"{BASE_URL}/chroma/upsert", json=upsert_payload)
    assert upsert_response.status_code == 204

    # Delete the node
    delete_payload = ChromaRequest(nodeId="unique-node-id").model_dump(exclude_none=True)
    delete_response = requests.post(f"{BASE_URL}/chroma/delete", json=delete_payload)
    assert delete_response.status_code == 204

    # Query to check if the node is deleted
    query_payload = ChromaRequest(nodeId="unique-node-id").model_dump(exclude_none=True)
    query_response = requests.post(f"{BASE_URL}/chroma/query", json=query_payload)
    assert query_response.status_code == 200
    # Here you should add assertions to check that the response indicates the node is not found
