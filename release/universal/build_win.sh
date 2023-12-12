#!/bin/sh

# remotely building on Windows is a pain to setup.
# Make sure OpenSSH server is installed and correctly configured
# with keys, etc.

# Then set up the git bash shell as default login shell
# See https://unix.stackexchange.com/questions/557751/how-can-i-execute-command-through-ssh-remote-is-windows
# New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value "C:\Program Files\Git\bin\sh.exe" -PropertyType String -Force


NAME='Tana Helper'
BASE="dist/dmg/$NAME.app"
ARM64_NAME="$NAME (12.6-arm64).app"
ARM64="builds/$ARM64_NAME"
X86_64_NAME="$NAME (12.7-x86_64).app"
X86_64="builds/$X86_64_NAME"

# BUILD Windows ARM
echo "Building Windoze ARM architecture"
git push Windows-arm
#ssh -t Windows-arm "cd ~/dev/tana/tana-helper/release; ./build.sh"
ssh Windows-arm "cd ~/dev/tana/tana-helper/release; ./build.sh"

