
import multiprocessing
import syslog
from typing import List
from uvicorn import Config, Server
from socket import socket

# Define identifier
syslog.openlog("TanaHelper")

def message(s):
  syslog.syslog(syslog.LOG_ALERT, s)

STATUS_CHECK_INTERVAL_MS  = 1000
STATUS_STARTING = b'S'
STATUS_UP = b'U'
STATUS_DOWN = b'D'

# override the UvicornServer class to add a status flag
class MyUvicornServer(Server):

  def __init__(self, config: Config, status):
    message("MyUvicornServer created")
    super().__init__(config=config)
    self.status_flag = status

  async def startup(self, sockets=None):
    message("MyUvicornServer startup() called")
    await super().startup(sockets=sockets)
    self.status_flag.value = STATUS_UP
    message("Server started")

  async def shutdown(self, sockets: List[socket] | None = None) -> None:
    message("MyUvicornServer shutdown() called")
    result = await super().shutdown(sockets)
    self.status_flag.value = STATUS_DOWN
    message("Server stopped")
    return result

# Process wrapper to spawn multiprocessing subprocess
class ServiceWorker(multiprocessing.Process):

  def __init__(self, status):
    message("UvicornServer created")
    self.status = status
    super().__init__()

  def stop(self):
    message("UvicornServer stop() called")
    self.terminate()

  def run(self, *args, **kwargs):
    message("ServiceWorker run() called")
    self.config = Config("service.main:app", host="127.0.0.1", port=8000, log_level="info", )
    self.server = MyUvicornServer(config=self.config, status=self.status)
    message("UvicornServer run() calling...")
    self.server.run()
