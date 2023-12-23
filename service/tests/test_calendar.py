import requests
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from typing import List, Union
from service.dependencies import CalendarRequest
from .test_types import BASE_URL, APIValidationError, HTTPValidationError


def test_calendar_post_success():
    payload = CalendarRequest(me="example", one2one="example").model_dump(exclude_none=True)
    response = requests.post(f"{BASE_URL}/calendar", json=payload)
    assert response.status_code == 200
    # Additional assertions can be added based on expected response content

def test_calendar_post_validation_error():
    payload = {"invalid": "data"}
    response = requests.post(f"{BASE_URL}/calendar", json=payload)
    assert response.status_code == 422
    error_response = HTTPValidationError.model_validate(response.json())
    # Additional assertions can be added to check the content of the error response
