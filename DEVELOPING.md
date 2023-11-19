# Developing

## Mac OSX

Install homebrew
(will install XCode tools if required)

### Install base toolset
`brew install python@3.11`
`brew install node`
`brew install yarn`
`brew install create-dmg`

Add python install location to PATH

`(~/.zprofile or whichever shell you use)`
`PATH=$PATH:/usr/local/opt/python@3.11/libexec/bin/`

`pip install poetry`

### Build everything, including .app and .dmg
`cd release`
`./build.sh`

## Windows 11
(no idea...)