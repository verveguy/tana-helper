from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QProcess
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu)
import subprocess
import os


app = QApplication([])
app.setQuitOnLastWindowClosed(False)

process = None

# When packaged, the start binary is a sibling to this file
# TODO: figure out how to make this also work in debug mode
basedir = os.path.dirname(__file__)

def message(s):
    print(s)

def start_service():
    cmd = os.path.join(basedir, '..', 'MacOS', 'start')
    pid = subprocess.Popen(['/usr/bin/open', '-W', cmd]).pid
    #subprocess.run(['open', '-W', cmd.name], stdin=None, stdout=None, stderr=None)
    message(f"Service started with pid={pid}")

def quit_app():
    # TODO: terminate service. Will require tracking pid.
    app.quit()


# Create the icon
icon = QIcon(os.path.join(basedir,'icons', 'white_16x16.png'))


# Create the tray
tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

# Create the menu
menu = QMenu()
action = QAction("Start tana-helper")
action.triggered.connect(start_service)
menu.addAction(action)

# Add a Quit option to the menu.
quit_action = QAction("Quit")
quit_action.triggered.connect(quit_app)
menu.addAction(quit_action)

# Add the menu to the tray
tray.setContextMenu(menu)

app.exec()
