from fastapi import APIRouter, status
from fastapi.responses import HTMLResponse
from ..dependencies import ExecRequest
from starlette.requests import Request
import json

router = APIRouter()


@router.post("/exec", response_class=HTMLResponse)
def exec_function(req: ExecRequest):
    namespace = {}
    namespace['result'] = None
    
    
    def set_prop(prop):
      namespace[prop] = req.payload[prop]
    
    [set_prop(prop) for prop in req.payload.keys()]
    invocation = req.code + '\n' + 'result = ' + req.call
    exec(invocation, namespace)
    result = namespace['result']
    return result

@router.post("/exec_loose", response_class=HTMLResponse)
async def exec_loose(req: Request):
    body = await req.body()
    body = body.decode('utf-8')

    print(body)
    # find non-JSON parts Code, Params and Call
    # extract values
    mode = ''
    code = ''
    params = ''
    call = ''
    first_code = False

    for line in body.splitlines():
      keyword = line.strip()
      if keyword == '- python\\n' or keyword == '- Python\\n':
        continue
      if keyword == 'Code:' or keyword == 'Code':
        mode = 'code'
        first_code = True
      elif keyword == 'Call:' or keyword == 'Call':
        mode = 'call'
        first_code = True
      elif keyword == 'Params:' or keyword == 'Params':
        mode = 'params'
      else:
        if first_code:
            line = line.strip()
            first_code = False
        if mode == 'code':
          code += line+'\n'
        elif mode == 'call':
          call += line+'\n'
        elif mode == 'params':
          params += line+'\n'

    payload = json.loads(params)

    # now that we've normalized the data, do regular call
    exec_req = ExecRequest(code=code, call=call, payload=payload)
    return exec_function(exec_req)


def do_something():
  return "Hello world!"

result = do_something()