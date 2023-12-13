#!/bin/sh

# activate correct python virtual env
poetry env use 3.11
case "$OSTYPE" in
  darwin*)  source .venv/bin/activate;; 
  linux*)   echo "LINUX" ;;
  msys*)    source .venv/Scripts/activate ;;
esac

poetry install --no-root

test -f "service/bin" && rm -r "service/bin"
mkdir -p service/bin

if [[ "$OSTYPE" == "darwin"* ]]; then
    # build the Calendar helper swift script first
    # Compile for macOS

    echo "Building for macOS arm64..."
    ARCH=arm64
    swiftc service/scripts/getcalendar.swift -o service/bin/getcalendar.${ARCH} -target arm64-apple-macosx10.15

    echo "Building for macOS amd64..."
    ARCH=amd64
    swiftc service/scripts/getcalendar.swift -o service/bin/getcalendar.${ARCH} -target x86_64-apple-macosx10.15

    echo "Packaging universal binary..."
    lipo -create -output service/bin/getcalendar service/bin/getcalendar.arm64 service/bin/getcalendar.amd64

    echo "Removing arch builds..."
    rm service/bin/*.arm64 service/bin/*.amd64
elif [[ "$OSTYPE" == "msys"* ]]; then
    # Windows builds anything?
    # not here
    echo "Windows does not support Calendar helper"
fi

# build the python bundle for menubar app and start wrapper
# build the .app / .exe bundle 

test -f "dist" && rm -r "dist"
pyinstaller tanahelper.spec --noconfirm
