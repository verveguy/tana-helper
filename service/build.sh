#!/bin/sh

# first build the start wrapper for the service
# pyinstaller start.spec --noconfirm

# build the .app bundle containing our menubar convenience app
# this will contain the start wrapper as well.

test -f "dist" && rm -r "dist"
pyinstaller tanahelper.spec --noconfirm
