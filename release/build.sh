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
    
    # Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
    mkdir -p "dist/dmg/$NAME.app"

    # Copy the app bundle to the dmg folder.
    ditto '../service/dist/Tana Helper.app' "dist/dmg/$NAME.app"
    echo "Mac .app bundle done"
elif [[ "$OSTYPE" == "msys"* ]]; then
    # Windows bundle done
    mkdir -p "dist/win"
    # move files from service/dist to dist/win/
    # mv ../service/dist/tanahelper dist/win/
    tar -cvzf dist/win/tanahelper.tar.gz ../service/dist/tanahelper
    echo "Windows bundle done"
fi