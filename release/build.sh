#!/bin/sh

# first, build the webapp. It will push its artifacts to the service
(cd ../webapp; ./build.sh)

# now build the service and the app wrapper
(cd ../service/; ./build.sh)

# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
test -f "dist" && rm -r "dist"
mkdir -p dist/dmg

# Empty the dmg folder.
rm -r dist/dmg/*

# Copy the app bundle to the dmg folder.
cp -r "../service/dist/Tana Helper.app" dist/dmg

# If the DMG already exists, delete it.
test -f "dist/Tana Helper.dmg" && rm "dist/Tana Helper.dmg"

# Create the DMG.
create-dmg \
  --volname "Tana Helper" \
  --volicon "Tana Helper.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "Tana Helper.app" 175 120 \
  --hide-extension "Tana Helper.app" \
  --app-drop-link 425 120 \
  "dist/Tana Helper.dmg" \
  "dist/dmg/"