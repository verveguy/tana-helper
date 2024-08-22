#!/bin/sh
set -euo pipefail # return error if any command fails

# make sure dist is clean
rm -rf ../service/service/dist
mkdir -p ../service/service/dist

yarn install

yarn build
