from pydantic import BaseModel

BASE_URL = "http://localhost:8000"


class APIValidationError(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class HTTPValidationError(BaseModel):
    detail: list[APIValidationError]
