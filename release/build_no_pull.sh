#!/bin/sh
set -euo pipefail # return error if any command fails

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
    NAME="TanaHelper-$OS_VERSION-$ARCH"
    
    mkdir -p "dist/$NAME.app"
    ditto '../service/dist/TanaHelper.app' "dist/$NAME.app"
    echo "Mac .app bundles done"

elif [[ "$OSTYPE" == "msys"* ]]; then
    OS_VERSION="11"
    ARCH="win"
    NAME="TanaHelper-$OS_VERSION-$ARCH"
    mkdir -p "dist"
    powershell Compress-Archive ../service/dist/tanahelpermenu/ "dist/$NAME.zip"
    echo "Windows .zip done"
fi