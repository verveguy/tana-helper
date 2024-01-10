# Developing

The following notes are for folks that want to build from scratch.

## Mac OSX

Install homebrew (will install XCode tools if required)
`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

### Install base toolset
`brew install pyenv`
`brew install node`
`brew install yarn`
`brew install create-dmg`

`pyenv install 3.11.7`

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

Requires GitBash to be installed for build script support

install node
install yarn
install pyenv

Use pyenv to install Python versions:

`pyenv install 3.11.7`

using powershell administrator:
`pip install pipx`
(set up cmd line per prompts)

Set up VSCode to use gitbash terminal

Using VSCode terminal:
`pipx install poetry`

Using VSCode terminal in the `release` directory
`./build.sh`





