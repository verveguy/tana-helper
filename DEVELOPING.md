# Developing

The following notes are for folks that want to build from scratch.

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

`pipx install poetry`

### Build everything, including .app and .dmg
`cd release`
`./build.sh`

### Universal build

You'll need two machines, arm64 and x86_64

Setting up remote machines

`mkdir tana/tana-helper.git`
`cd tana-helper.git`
`git config --bool core.bare true`

Add these as remotes to your local git repo in whatever fashion you've set up (ssh, etc.)

`cd release/universal`
`./build.sh`


## Windows 11

Requires VSCode to be installed for /usr/bin/bash support

install node.js from download
install python from download

using powershell administrator:
`pip install pipx`
(set up cmd line per prompts)

Using VSCode terminal:
`pipx install poetry`

Using VSCode terminal in the `release` directory
`./build.sh`





