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

# Create the DMG.
echo_blue "Creating DMG for distribution"

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

mv builds/*.zip dist/

echo_blue "END builds"


end=$(date +%s)
echo "Elapsed Time: $(($end-$start)) seconds"
