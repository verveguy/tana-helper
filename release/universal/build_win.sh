#!/bin/sh

# remotely building on Windows is a pain to setup.
# Make sure OpenSSH server is installed and correctly configured
# with keys, etc.

# Then set up the git bash shell as default login shell
# See https://unix.stackexchange.com/questions/557751/how-can-i-execute-command-through-ssh-remote-is-windows
# New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value "C:\Program Files\Git\bin\sh.exe" -PropertyType String -Force


NAME='Tana Helper'

# BUILD Windows ARM
echo "Building Windoze architecture"
git push Windows-arm
ssh Windows-arm "cd ~/dev/tana/tana-helper/release; ./build.sh"

# TODO: consider tarring this stuff up on the remote end
# then pulling back to the Mac before repackaging in a way
# that windows users can easily unpack.
scp -r "Windows-arm:~/dev/tana/tana-helper/release/dist/win/tanahelper*.tar.gz" builds/

