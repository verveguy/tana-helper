# Developing

The following notes are for folks that want to build from scratch.

## Mac OSX

Install homebrew (will install XCode tools if required)
`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

Install uv package manager (fast!)
`curl -LsSf https://astral.sh/uv/install.sh | sh`

### Install base toolset
`brew install node`
`brew install yarn`
`brew install create-dmg`

### Build everything, including .app and .dmg
`cd release`
`./build_one.sh`

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

Install uv package manager
`$ powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

Using VSCode terminal in the `release` directory
`./build.sh`





