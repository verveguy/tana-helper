#!/bin/sh
set -euo pipefail # return error if any command fails

pnpm install

pnpm build

# push build artifacts to service for packaging
rm -rf ../service/service/dist
mkdir -p ../service/service/dist
cp -rp dist/* ../service/service/dist
