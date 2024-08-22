#!/bin/sh
set -euo pipefail # return error if any command fails

yarn install

yarn build
