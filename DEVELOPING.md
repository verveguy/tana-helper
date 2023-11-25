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