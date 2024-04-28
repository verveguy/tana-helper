#!/bin/sh

# Build all the various builds in parallel across two Mac OS X
# build machines (Intel and ARM) and a Windows build machine.

# remotely building on Windows is a pain to setup.
# Make sure OpenSSH server is installed and correctly configured
# with keys, etc.

# Then set up the git bash shell as default login shell
# See https://unix.stackexchange.com/questions/557751/how-can-i-execute-command-through-ssh-remote-is-windows
# New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value "C:\Program Files\Git\bin\sh.exe" -PropertyType String -Force

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

X86_64_NAME="$NAME-12.7-x86_64.app"
X86_64="builds/$X86_64_NAME"

echo_blue "START builds"

# BUILD Mac ARM64 and Mac x86_64
echo_blue "Cleaning up from previous builds"
rm -rf builds
rm -rf dist
mkdir -p builds

echo_blue "Updating remote git repos"

git push Monterey-x86
git push Monterey-arm
git push windows-x86

echo_blue "Starting parallel builds"

# Parallelize building the three architectures

remote_build "Monterey-x86" "x86_64" &
pid1=$!
remote_build "Monterey-arm" "arm64" &
pid2=$!
remote_build "windows-x86" "win" &
winpid=$!

# wait for all builds to complete
# wait_for_process_completion $pid1 $pid2 #$pid3

waitalljobs $pid1 $pid2 # $winpid

# Mac specific build of Universal binary

# LIPO the two into one
echo_blue "Preparing Universal Mac .app"
echo_blue "Lipo-ing the two architectures into one"
mkdir -p "dist/dmg"

# BUild Mac Helper.app next
# use arm64 build as our "primary" and recurse that structure
APP="dist/dmg/${NAME}.app"

echo_blue "Lipo-ing ${APP}"
lipo_files "$APP" "$ARM64" "$X86_64" > builds/lipo_app.log 2>&1 &
lipopid2=$!

# show process spinner
waitalljobs $lipopid2
echo_blue "Completed Universal Helper.app build"

echo_blue "Codesigning ${APP}"
codesign_app "$APP"

# Create the DMG.
echo_blue "Creating DMG for distribution"

create_dmg "$NAME"

echo_blue "Codesigning the .dmg"

codesign_app "dist/$NAME.dmg"

echo_blue "Notarizing the .dmg"
notarize_dmg "dist/$NAME.dmg"

# now we can assess the app and see what it says
# assess "$APP"

echo_blue "Verifying deep codesigning of .dmg"
codesign --verbose=4 --display --deep --strict "dist/$NAME.dmg"

# ALL DONE
echo_blue "Mac DMG built, signed, notarized and verified"
echo ""

# and wait for the Windows build if it's still not done
# TODO figure out how to wait on a PID that might have completed
# without error
# waitalljobs $winpid

echo_blue "Builds complete"

mv builds/*.zip dist/

echo_blue "END builds"

end=$(date +%s)
echo "Elapsed Time: $(($end-$start)) seconds"


