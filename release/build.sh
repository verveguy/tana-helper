#!/bin/sh

# first make sure we are up to date
echo "Updating from git"
git pull

# first, build the webapp. It will push its artifacts to the service
echo "Building webapp"
(cd ../webapp; ./build.sh)

# now build the service and the app wrapper
echo "Building service .app / .exe package"
(cd ../service/; ./build.sh)


rm -rf "dist"

if [[ "$OSTYPE" == "darwin"* ]]; then

    OS_VERSION=$(sw_vers -productVersion | awk -F '.' '{print $1 "." $2}')
    ARCH=$(uname -m)
    NAME="Tana Helper ($OS_VERSION-$ARCH)"
    
    mkdir -p "dist/$NAME.app"
    ditto '../service/dist/Tana Helper.app' "dist/$NAME.app"
    echo "Mac .app bundle done"
elif [[ "$OSTYPE" == "msys"* ]]; then
    OS_VERSION="11"
    ARCH="win"
    NAME="Tana Helper ($OS_VERSION-$ARCH)"
    mkdir -p "dist"
    powershell Compress-Archive ../service/dist/tanahelper/ "dist/TanaHelper-(11-win).zip"
    echo "Windows .zip done"
fi