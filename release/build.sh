#!/bin/sh
set -euo pipefail # return error if any command fails

# first make sure we are up to date
echo "Updating from git"
git pull

./build_no_pull.sh