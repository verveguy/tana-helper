#!/bin/sh
set -euo pipefail # return error if any command fails

yarn install

yarn build

# push build artifacts to service for packaging
mkdir -p ../service/service/dist
cp -rp dist/* ../service/service/dist
