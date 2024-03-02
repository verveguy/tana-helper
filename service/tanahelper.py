import socket
import syslog
from multiprocessing import freeze_support, set_start_method, Process
from typing import List

# Define identifier
syslog.openlog("TanaHelper")

def message(s):
  syslog.syslog(syslog.LOG_ALERT, s)

if __name__ == "__main__":
  freeze_support()
  set_start_method('spawn')
  message('started main process')
else:
  message('started subprocess')

import sys
import platform
import os
from time import sleep
from PyQt6.QtGui import QIcon, QAction, QDesktopServices
from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu)
from  multiprocessing import Value, freeze_support, set_start_method
from uvicorn import Config, Server
# from myuvicorn import ServiceWorker, STATUS_CHECK_INTERVAL_MS, STATUS_STARTING, STATUS_UP, STATUS_DOWN

# these imports are to satisfy PyInstaller's dependency finder
# since they appear to be "hidden" from it for unknown reasons
import onnxruntime, tokenizers, tqdm


import logging
logger = logging.getLogger(__name__)


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
class ServiceWorker(Process):

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


class TanaHelperTrayApp():
  
  def __init__(self):
    self.state = Value('c', STATUS_DOWN)
    self.toggle = False
    self.app = QApplication([])
    self.app.setQuitOnLastWindowClosed(False)
    self.instance = None

  def quit(self):
    self.app.quit()

  def start_server(self):
    message('About to start serviceworker')
    self.instance = ServiceWorker(status=self.state)
    self.instance.start()
    message('Started serviceworker')

  def stop_server(self):
    if self.instance:
      self.instance.stop()
    message('Stopped serviceworker')

  def check_server_status(self):
    if self.state.value == STATUS_STARTING:
      self.start_action.setEnabled(False)
      if self.toggle == False:
        self.tray.setIcon(self.active_icon)
        self.toggle = True
      else:
        self.tray.setIcon(self.icon)
        self.toggle = False
      message("Server is starting")
    elif self.state.value == STATUS_UP:
      self.start_action.setEnabled(False)
      self.stop_action.setEnabled(True)
      self.open_webui.setEnabled(True)
      message("Server is running")
      self.timer.stop()
      self.tray.setIcon(self.icon)
      self.toggle = False
    elif self.state.value == STATUS_DOWN:
      self.start_action.setEnabled(True)
      self.stop_action.setEnabled(False)
      self.open_webui.setEnabled(False)
      message("Server is stopped")
      self.timer.stop()
      self.tray.setIcon(self.icon)
      self.toggle = False
      # clean up any zombie process
      if self.instance:
        self.instance.join()
        self.instance = None
    else:
      message("Server is in an unknown state")

  def start_service(self):
    if self.state.value == STATUS_DOWN:
      self.start_server()
      self.state.value = STATUS_STARTING
      # start the watchdog timer
      self.timer.start(STATUS_CHECK_INTERVAL_MS)
      self.check_server_status()
      message("Server is starting")
    elif self.state.value == STATUS_STARTING:
      message("Server is already starting")
    else:
      message("Server is already started")

  def stop_service(self):
    if self.state.value == STATUS_UP:
      self.stop_server()
      message("Server is stopping")
      # start the watchdog timer
      self.timer.start(STATUS_CHECK_INTERVAL_MS)
    elif self.state.value == STATUS_STARTING:
      message("Server is starting")
    else:
      message("Server is already stopped")

  def quit_app(self):
    self.stop_service()
    self.app.quit()

  def open_webui_url(self):
    url = QUrl('http://localhost:8000/ui')
    QDesktopServices.openUrl(url)

  def setup_app(self):
    # Create the icon
    plat = platform.system()
    if plat == 'Darwin':
      self.active_icon = QIcon(os.path.join(basedir,'icons', 'icon_16x16.png'))
      self.icon = QIcon(os.path.join(basedir,'icons', 'icon_16x16_white.png'))
    elif plat == 'Windows':
      self.icon = QIcon(os.path.join(basedir,'icons', 'icon_16x16.png'))
      self.active_icon = QIcon(os.path.join(basedir,'icons', 'icon_16x16_white.png'))

    # Create the tray
    self.tray = QSystemTrayIcon()
    self.tray.setIcon(self.icon)
    self.tray.setVisible(True)

    # Create the menu
    self.menu = QMenu()

    # Create the menu
    self.start_action = QAction("Start tana-helper")
    self.start_action.triggered.connect(self.start_service)
    self.menu.addAction(self.start_action)

    # add actions
    self.stop_action = QAction("Stop tana-helper")
    self.stop_action.triggered.connect(self.stop_service)
    self.menu.addAction(self.stop_action)

    # add actions
    self.open_webui = QAction("Open Web UI")
    self.open_webui.triggered.connect(self.open_webui_url)
    self.menu.addAction(self.open_webui)

    # add actions
    # self.start_subprocess_action = QAction("Start tana-helper")
    # self.start_subprocess_action.triggered.connect(self.start_service_subprocess)
    # self.menu.addAction(self.start_subprocess_action)

    # Add a Quit option to the menu.
    self.quit_action = QAction("Quit")
    self.quit_action.triggered.connect(self.quit_app)
    self.menu.addAction(self.quit_action)

    # Add the menu to the tray
    self.tray.setContextMenu(self.menu)

  def start(self):
    # create our watchdog timer
    self.timer = QTimer(self.app)
    self.timer.timeout.connect(self.check_server_status)
    # initialize our menu states
    self.check_server_status()
    # start the app
    self.app.exec()

#  __main__ test doesn't work in multiprocessing situation on Mac OS
# when running as a bundled .app
if __name__ == "__main__":
  message("Process spawned (__main__ detected)")
  parent_process = True

  # look for the multiprocessing sentinel
  for arg in sys.argv:
    if 'from multiprocessing' in arg:
      parent_process = False
      message("Is subprocess")

  if parent_process:
    # When packaged, the start binary is a sibling to this file
    # TODO: figure out how to make this also work in debug mode
    basedir = os.path.dirname(__file__)
    message(f"Install dir = {basedir}")
    cwd = os.getcwd()
    message(f"Current working dir = {cwd}")

    helperapp = TanaHelperTrayApp()
    helperapp.setup_app()
    # this won't return until we quit the app
    helperapp.start()
    # app has been quit
    message("Exiting")
  else:
    message("Subprocess spawned (__main__ detected)")
    sleep(60)
    message("Subprocess exited")
else:
  message("Subprocess spawned (__main__ not detected)")
