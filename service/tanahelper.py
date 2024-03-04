from socket import socket
from multiprocessing import freeze_support, set_start_method, Process
from typing import List

if __name__ == "__main__":
  freeze_support()
  set_start_method('spawn')

import sys
import os
from time import sleep
from PyQt6.QtGui import QIcon, QAction, QDesktopServices
from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu)
from  multiprocessing import Value, freeze_support, set_start_method
from uvicorn import Config, Server
from myuvicorn import STATUS_STOPPING, ServiceWorker, STATUS_CHECK_INTERVAL_MS, STATUS_STARTING, STATUS_UP, STATUS_DOWN

# from myuvicorn import ServiceWorker, STATUS_CHECK_INTERVAL_MS, STATUS_STARTING, STATUS_UP, STATUS_DOWN

# these imports are to satisfy PyInstaller's dependency finder
# since they appear to be "hidden" from it for unknown reasons
import onnxruntime, tokenizers, tqdm
from message import message, os_platform

import logging
logger = logging.getLogger(__name__)

class TanaHelperTrayApp():
  
  def __init__(self):
    self.state = Value('c', STATUS_DOWN)
    self.toggle = False
    self.app = QApplication([])
    self.app.setQuitOnLastWindowClosed(False)
    self.instance = None


  def set_state(self, state):
    self.state.value = state # type: ignore

  def is_state(self, state):
    return self.state.value == state # type: ignore
  
  def start_server(self):
    message('About to start serviceworker')
    self.set_state(STATUS_STARTING)
    self.instance = ServiceWorker(status=self.state)
    self.instance.start()
    message('Started serviceworker')


  def stop_server(self):
    if self.instance:
      message('About to stop serviceworker')
      self.set_state(STATUS_STOPPING)
      self.check_server_status()
      self.instance.terminate()
      self.check_server_status()
      self.instance.join()
      self.set_state(STATUS_DOWN)
      self.instance = None
      message('Stopped serviceworker')
    else:
      message('No serviceworker to stop')


  def toggle_icon(self):
    if self.toggle == False:
      self.tray.setIcon(self.active_icon)
      self.toggle = True
    else:
      self.tray.setIcon(self.icon)
      self.toggle = False


  def reset_icon(self):
    self.tray.setIcon(self.icon)
    self.toggle = False


  def check_server_status(self):
    poll = False
    if self.is_state(STATUS_STARTING):
      self.start_action.setEnabled(False)
      self.stop_action.setEnabled(False)
      self.open_webui.setEnabled(False)
      self.toggle_icon()
      message("Server is starting")
      poll = True
    elif self.is_state(STATUS_STOPPING):
      self.start_action.setEnabled(False)
      self.stop_action.setEnabled(False)
      self.open_webui.setEnabled(False)
      message("Server is still stopping")
      self.toggle_icon()
      poll = True
    elif self.is_state(STATUS_UP):
      self.start_action.setEnabled(False)
      self.stop_action.setEnabled(True)
      self.open_webui.setEnabled(True)
      message("Server is running")
      poll = False
    elif self.is_state(STATUS_DOWN):
      self.start_action.setEnabled(True)
      self.stop_action.setEnabled(False)
      self.open_webui.setEnabled(False)
      message("Server is stopped")
      poll = False
    else:
        message("Server is in an unknown state")
    
    if not poll:
      self.timer.stop()
      self.reset_icon()
  

  def start_service(self):
    if self.is_state(STATUS_DOWN):
      self.start_server()
      self.check_server_status()
      message("Server is starting")
      # start the watchdog timer
      self.timer.start(STATUS_CHECK_INTERVAL_MS)
      message("Server is starting")
    elif self.is_state(STATUS_STARTING):
      message("Server is already starting")
    elif self.is_state(STATUS_STOPPING):
      message("Server is still stopping")
    else:
      message("Server is already started")


  def stop_service(self):
    self.check_server_status()
    if self.is_state(STATUS_UP):
      self.stop_server()
      self.check_server_status()
      message("Server is stopping")
      # start the watchdog timer
      self.timer.start(STATUS_CHECK_INTERVAL_MS)
    elif self.is_state(STATUS_STARTING):
      message("Server is still starting")
    elif self.is_state(STATUS_STOPPING):
      message("Server is already stopping")
    else:
      message("Server is already stopped")


  def quit_app(self):
    self.stop_service()
    # self.state.release()
    self.state = None
    self.app.quit()


  def open_webui_url(self):
    url = QUrl('http://localhost:8000/ui')
    QDesktopServices.openUrl(url)


  def setup_app(self):
    # Create the icon
    if os_platform == 'Darwin':
      icon_path = os.path.join(basedir,'icons', 'icon_16x16_color.png')
      self.active_icon = QIcon(os.path.join(basedir,'icons', 'icon_16x16_color.png'))
      self.icon = QIcon(os.path.join(basedir,'icons', 'icon_16x16_white.png'))
    elif os_platform == 'Windows':
      self.icon = QIcon(os.path.join(basedir,'icons', 'icon_16x16_color.png'))
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

  def start_app(self):
    # create our watchdog timer
    self.timer = QTimer(self.app)
    self.timer.timeout.connect(self.check_server_status)
    # initialize our menu states
    self.check_server_status()
    # start the app
    self.app.exec()
    if self.instance:
      self.instance.join()
      self.instance = None

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
    helperapp.start_app()
    # app has been quit
    message("Exiting")
  
else:
  message("Subprocess spawned (__main__ not detected)")
