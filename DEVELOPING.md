# Developing

The following notes are for folks that want to build from scratch.

## Code Formatting Standards

This project uses modern code formatting tools to ensure consistent code style.

### Frontend (webapp): Prettier + ESLint

The webapp uses **Prettier** for code formatting with **ESLint** integration.

**Configuration:**
- Single quotes, 100 char line length, trailing commas
- Configured in `.prettierrc.json` and `.eslintrc.json`

**Commands:**
```bash
cd webapp
pnpm format              # Format all code
pnpm format:check        # Check formatting (CI/CD)
pnpm lint               # Run ESLint
pnpm lint:fix           # Fix ESLint issues
```

### Backend (service): Ruff

The Python service uses **Ruff** for both linting and formatting (replaces Black, isort, flake8, pyupgrade).

**Configuration:**
- 88 char line length (Black standard), Python 3.11+ target
- Configured in `pyproject.toml` under `[tool.ruff]`

**Commands:**
```bash
cd service
uv run ruff check .                    # Check for issues
uv run ruff check . --fix             # Auto-fix issues
uv run ruff format .                   # Format code
uv run ruff check . --fix && uv run ruff format .  # Full cleanup
```

### VS Code Setup (Recommended)

The project includes VS Code configuration for automatic formatting on save.

**Installation:**
1. Install the recommended extensions when prompted, or run:
   ```bash
   code --install-extension esbenp.prettier-vscode
   code --install-extension charliermarsh.ruff
   code --install-extension dbaeumer.vscode-eslint
   ```

2. Open the project: `code .`

**Automatic Configuration:**
- **Frontend (webapp/)**: Prettier + ESLint will format TypeScript/React files on save
- **Backend (service/)**: Ruff will format and fix Python files on save
- **Extensions recommended**: VS Code will suggest required extensions

**Manual Setup for Other Editors:**
Set up your editor (PyCharm, etc.) with Prettier and Ruff extensions for automatic formatting on save.

## Mac OSX

Install homebrew (will install XCode tools if required)
`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

### Install base toolset
`brew install pyenv`
`brew install node`
`brew install pnpm`
`brew install create-dmg`

`pyenv install 3.11.7`

`pip install uv`

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
install pnpm
install pyenv

Use pyenv to install Python versions:

`pyenv install 3.11.7`

using powershell administrator:
`pip install pipx`
(set up cmd line per prompts)

Set up VSCode to use gitbash terminal

Using VSCode terminal:
`pip install uv`





