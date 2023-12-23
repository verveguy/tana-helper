import requests
from pydantic import BaseModel, Field
from typing import Optional, List, Union
from service.dependencies import tana_to_json
from .test_types import BASE_URL, APIValidationError, HTTPValidationError

def test_proxy_post():
    proxy_post()

def proxy_post():
    # Define the path parameter and the complete URL
    path_param = "https://api.restful-api.dev/objects"
    url = f"{BASE_URL}/proxy/POST/{path_param}"

    # Define the request body and headers as needed
    request_body = \
"""
- This is a RESTful data object.  We pass a Tana structure as the value of data field
  - data::
    - Another object
      - field 1:: Foo
      - field 2:: Bar
"""

    # Make the PUT request
    response = requests.post(url, data=request_body)
    print(response)
    # TODO: check the response is as expected

    # Assert the status code or other aspects of the response
    assert response.status_code == 200  # Replace with the expected status code
    # Add more assertions based on the expected response
    return response

def test_proxy_delete():
    
    stored = proxy_post()

    # convert back to JSON and extract the object ID
    body = stored.content
    tana_format = body.decode("unicode_escape")  
    object_graph = tana_to_json(tana_format)
    the_id = object_graph[0]['id']

    # Define the path parameter and the complete URL
    path_param = "https://api.restful-api.dev/objects"
    url = f"{BASE_URL}/proxy/DELETE/{path_param}/{the_id}"

    # Define the request body and headers as needed
    # Make the PUT request
    response = requests.post(url)
    print(response)
    # TODO: check the response is as expected

    # Assert the status code or other aspects of the response
    assert response.status_code == 200  # Replace with the expected status code
    # Add more assertions based on the expected response

    response = requests.post(url)
    print(response)
    # TODO: check the response is as expected

    # Assert the status code or other aspects of the response
    assert response.status_code == 404  # Replace with the expected status code
    # Add more assertions based on the expected response