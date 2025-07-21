import requests

from service.dependencies import ChromaRequest

from .test_types import BASE_URL, HTTPValidationError


def test_chroma_upsert_success():
    payload = ChromaRequest(
        nodeId="12345",
        model="gpt-3.5-turbo",
        embedding_model="text-embedding-ada-002",
        context="test context",
        name="test",
        environment="local",
        score=0.8,
        top=10,
        tags="test",
    ).model_dump(exclude_none=True)
    response = requests.post(f"{BASE_URL}/chroma/upsert", json=payload)
    assert response.status_code == 204
    # Additional assertions can be added based on expected response content


def test_chroma_upsert_validation_error():
    payload = {"invalid": "data"}
    response = requests.post(f"{BASE_URL}/chroma/upsert", json=payload)
    assert response.status_code == 422
    error_response = HTTPValidationError.model_validate(response.json())
    # Verify that we have validation errors
    assert len(error_response.detail) > 0
    assert error_response.detail[0].type is not None


def test_chroma_delete_success():
    payload = ChromaRequest(
        nodeId="12345",
        model="gpt-3.5-turbo",
        embedding_model="text-embedding-ada-002",
        context="test context",
        name="test",
        environment="local",
        score=0.8,
        top=10,
        tags="test",
    ).model_dump(exclude_none=True)
    response = requests.post(f"{BASE_URL}/chroma/delete", json=payload)
    assert response.status_code == 204
    # Additional assertions can be added based on expected response content


def test_chroma_delete_validation_error():
    payload = {"invalid": "data"}
    response = requests.post(f"{BASE_URL}/chroma/delete", json=payload)
    assert response.status_code == 422
    error_response = HTTPValidationError.model_validate(response.json())
    # Verify that we have validation errors
    assert len(error_response.detail) > 0
    assert error_response.detail[0].type is not None


def test_chroma_query():
    query_payload = ChromaRequest(
        nodeId="12345",
        model="gpt-3.5-turbo",
        embedding_model="text-embedding-ada-002",
        context="test context",
        name="test",
        environment="local",
        score=0.8,
        top=10,
        tags="test",
    ).model_dump(exclude_none=True)
    response = requests.post(f"{BASE_URL}/chroma/query", json=query_payload)
    assert response.status_code == 200
    # Additional assertions based on expected response content


def test_chroma_upsert_delete_query_flow():
    # Upsert a node
    upsert_payload = ChromaRequest(
        nodeId="1234567890",
        model="gpt-3.5-turbo",
        embedding_model="text-embedding-ada-002",
        context="test context for flow",
        name="test flow",
        environment="local",
        score=0.8,
        top=10,
        tags="test flow",
    ).model_dump(exclude_none=True)
    upsert_response = requests.post(f"{BASE_URL}/chroma/upsert", json=upsert_payload)
    assert upsert_response.status_code == 204

    # Delete the node
    delete_payload = ChromaRequest(
        nodeId="1234567890",
        context="",
        name="",
    ).model_dump(exclude_none=True)
    delete_response = requests.post(f"{BASE_URL}/chroma/delete", json=delete_payload)
    assert delete_response.status_code == 204

    # Query to check if the node is deleted
    query_payload = ChromaRequest(
        nodeId="1234567890",
        context="",
        name="",
    ).model_dump(exclude_none=True)
    query_response = requests.post(f"{BASE_URL}/chroma/query", json=query_payload)
    assert query_response.status_code == 200
    # Here you should add assertions to check that the response indicates the node is not found
