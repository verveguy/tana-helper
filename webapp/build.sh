#!/bin/sh
yarn build

# push build artifacts to service for packaging
mkdir -p ../service/service/dist
cp -rp dist/* ../service/service/dist
