import multiprocessing
from time import sleep
from typing import List, Optional
from uvicorn import Config, Server
import socket
from message import message
# import service.small_main
import service.main

STATUS_CHECK_INTERVAL_MS  = 1000
STATUS_STARTING = b'S'
STATUS_UP = b'U'
STATUS_DOWN = b'D'
STATUS_STOPPING = b'X'

# override the UvicornServer class to add a status flag
class MyUvicornServer(Server):

  def __init__(self, config: Config, status):
    message("MyUvicornServer created")
    self.status = status
    super().__init__(config=config)

  def run(self, sockets: Optional[List[socket.socket]] = None) -> None:
    message("MyUvicornServer run() called")
    super().run(sockets=sockets)
    message("MyUvicornServer run() called")

  async def startup(self, sockets=None):
    message("MyUvicornServer startup() called")
    await super().startup(sockets=sockets)
    self.status.value = STATUS_UP
    message("Server started")

  async def shutdown(self, sockets: List[socket.socket] | None = None) -> None:
    message("MyUvicornServer shutdown() called")
    result = await super().shutdown(sockets)
    self.status.value = STATUS_DOWN
    message("Server stopped")
    return result

# Process wrapper to spawn multiprocessing subprocess
class ServiceWorker(multiprocessing.Process):

  def __init__(self, status):
    message("UvicornServer created")
    self.status = status
    self.server = None
    super().__init__()

  def stop(self):
    message("UvicornServer stop() called")
    self.status.value = STATUS_STOPPING

    self.close()


  def stopXX(self):
    message("UvicornServer stop() called")
    self.status.value = STATUS_STOPPING
    sleep(10)
    self.status.value = STATUS_DOWN
    self.terminate()
    self.close()


  def run(self, *args, **kwargs):
    message("ServiceWorker run() called")
    self.status.value = STATUS_STARTING
    try:
      self.config = Config("service.main:app", host="127.0.0.1", port=8000, log_level="info", loop="asyncio")
      self.server = MyUvicornServer(config=self.config, status=self.status)
      message("calling MyUvicornServer.run()")
      self.server.run()
      message("ServiceWorker run() done")
    except Exception as e:
      message(f"ServiceWorker run() exception: {e}")
      self.status.value = STATUS_DOWN
    


  def runXX(self, *args, **kwargs):
    message("ServiceWorker run() called")
    self.status.value = STATUS_STARTING
    sleep(10)
    self.status.value = STATUS_UP
    message("ServiceWorker run() done")

