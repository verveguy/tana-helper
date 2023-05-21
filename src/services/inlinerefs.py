from fastapi import APIRouter, Response, status
from fastapi.responses import HTMLResponse
from ..dependencies import NodeRequest
import re

router = APIRouter()

@router.post("/inlinerefs", response_class=HTMLResponse)
def inlinerefs(req: NodeRequest, response: Response):
  # find all the refs in the context
  pattern = re.compile(r'(\[\[[^\]]*\]\])')
  matches = re.findall(pattern, req.context)

  if len(matches) > 0:
    result = ''.join(["- inline ref::"+id+"\n" for id in matches])
    return result
  else:
    response.status_code=status.HTTP_204_NO_CONTENT
    return None