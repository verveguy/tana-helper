from fastapi import APIRouter, Response, status
from fastapi.responses import HTMLResponse
from service.dependencies import NodeRequest
import re

router = APIRouter()

@router.post("/inlinerefs", response_class=HTMLResponse)
def inlinerefs(req: NodeRequest, response: Response):
  if not req.context:
    response.status_code=status.HTTP_204_NO_CONTENT
    return None    
  
  # find all the refs in the context
  pattern = re.compile(r'(\[\[[^\]]*\]\])')
  # just use the first line, since we only want the primary node
  first = req.context.partition('\n')[0]
  matches = re.findall(pattern, first)

  if len(matches) > 0:
    result = ''.join(["- inline ref::"+id+"\n" for id in matches])
    return result
  else:
    response.status_code=status.HTTP_204_NO_CONTENT
    return None
