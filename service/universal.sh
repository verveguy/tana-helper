#!/bin/sh

pip uninstall $1 -y
pip cache purge

export ARCHFLAGS='-arch i386 -arch x86_64'

# first attempt a binary universal install
ARCHFLAGS='-arch i386 -arch x86_64' pip install $1

# if that fails, try a source build
if [ $? -ne 0 ]; then
  ARCHFLAGS='-arch i386 -arch x86_64' pip install --no-binary :all: $1
fi
