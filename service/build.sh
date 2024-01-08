#!/bin/sh
set -euo pipefail # return error if any command fails

# activate correct python virtual env
poetry env use 3.11
case "$OSTYPE" in
  darwin*)  source .venv/bin/activate;; 
  linux*)   echo "LINUX" ;;
  msys*)    source .venv/Scripts/activate ;;
esac

poetry install --no-root

test -d "service/bin" && rm -r "service/bin"
mkdir -p service/bin

test -d "dist" && rm -r "dist"

if [[ "$OSTYPE" == "darwin"* ]]; then
    # build the Calendar helper swift script first
    # Compile for macOS
    echo "Building MacOS specific calendar helper..."

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

    
    # build the python bundle for menubar app and start wrapper
    # build the .app bundle 

    echo "Building tanahelper .app using pyinstaller..."
    test -d "dist" && rm -r "dist"
    pyinstaller tanahelper.spec --noconfirm

elif [[ "$OSTYPE" == "msys"* ]]; then
    # Windows builds anything?
    # not here
    echo "Windows does not support Calendar helper"

    # build the python bundle for menubar app and start wrapper
    # build the .exe bundle 
    # NOTE: we do this differently for Mac and Win since Windows suffers false positives
    # on the pysinstaller bootloader unless we use --clean
    echo "Building tanahelper .exe using pyinstaller..."
    pyinstaller tanahelper.spec --noconfirm --clean
fi
