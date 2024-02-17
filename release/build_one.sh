#!/bin/sh

# Build a single binary locally for testing cycles

# Magical codesigning and notarization commands courtesy of https://github.com/nuxeo/nuxeo-drive/blob/master/tools/osx/deploy_ci_agent.sh
#

source ./build_funcs.sh

# ensure we clean up background processes when we are killed
trap "exit" INT TERM 
trap "kill 0" EXIT

trap error ERR

start=$(date +%s)

# load .env file
set -a
source .env
set +a

NAME='TanaHelper'
SVCNAME="${NAME}Service"

# set up the names of the two builds
# pattern is TanaHelper-OS_REV-ARCH.app 
# where OS_REV is the OS version and ARCH is the architecture
# of the build machine
ARM64_NAME="$NAME-12.6-arm64.app"
ARM64="builds/$ARM64_NAME"
SVCARM64_NAME="$SVCNAME-12.6-arm64.app"
SVCARM64="builds/$SVCARM64_NAME"


echo_blue "START builds"

# BUILD Mac ARM64 and Mac x86_64
echo_blue "Cleaning up from previous builds"
rm -rf builds
rm -rf dist
mkdir -p builds

echo_blue "Starting build"

# Run local release build
./build_no_pull.sh > builds/release.log 2>&1 &
buildpid=$!

# show process spinner
waitalljobs $buildpid

# since we don't have to lipo multiple builds into one, we can just rename the build
APP="dist/dmg/${NAME}.app"
SVCAPP="dist/dmg/${SVCNAME}.app"

mkdir -p dist/dmg/

mv dist/${NAME}-*.app "$APP"
mv dist/${SVCNAME}-*.app "$SVCAPP"

# codesigning, etc
codesign_app "$SVCAPP"

# Place Service.app inside Helper.app package
echo_blue "Placing Service.app inside Helper.app package"
ditto "${SVCAPP}" "${APP}/Contents/MacOS/${SVCNAME}.app"

# REMOVE the copy of Service.app from the DMG tree
echo_blue "Removing Service.app from DMG tree"
rm -rf "${SVCAPP}"

echo_blue "Codesigning ${APP}"
codesign_app "$APP"

# Create the DMG.
echo_blue "Creating DMG for distribution"

read -p "Continue?"

create_dmg "$NAME"

echo_blue "Codesigning the .dmg"

codesign_app "dist/$NAME.dmg"

echo_blue "Notarizing the .dmg"
notarize_dmg "dist/$NAME.dmg"

# now we can assess the app and see what it says
assess "$APP"

echo_blue "Verifying deep codesigning of .dmg"
codesign --verbose=4 --display --deep --strict "dist/$NAME.dmg"

# ALL DONE
echo_blue "Mac DMG built, signed, notarized and verified"
echo ""

echo_blue "Builds complete"

echo_blue "END builds"

end=$(date +%s)
echo "Elapsed Time: $(($end-$start)) seconds"


