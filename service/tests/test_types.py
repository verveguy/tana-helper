from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from typing import List, Union

BASE_URL = "http://localhost:8000"

class APIValidationError(BaseModel):
    loc: List[Union[str, int]]
    msg: str
    type: str

class HTTPValidationError(BaseModel):
    detail: List[APIValidationError]
