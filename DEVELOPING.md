# Developing

## Mac OSX

Install homebrew (will install XCode tools if required)
`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

### Install base toolset
`brew install python@3.11`
`brew install node`
`brew install yarn`
`brew install create-dmg`

Add python install location to PATH

Edit ~/.zprofile or whichever shell you use
`echo "PATH=$PATH:/usr/local/opt/python@3.11/libexec/bin/" >> ~/.zprofile`

`pip install poetry`

### Build everything, including .app and .dmg
`cd release`
`./build.sh`

## Windows 11
(no idea...)


# Universal build

You'll need two machines, arm64 and x86_64

Setting up remote machines

mkdir tana/tana-helper.git
cd tana-helper.git
git config --bool core.bare true

cd release/universal
./build.sh



