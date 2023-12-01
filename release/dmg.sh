#!/bin/sh

# you need to first build the app image
# on both remote dev boxes
# ./build.sh

# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
rm -rf "dist"
mkdir -p "dist/dmg/$NAME.app"

# Copy the app bundle to the dmg folder.
ditto '../service/dist/Tana Helper.app' "dist/dmg/$NAME.app"

# Create the DMG.
create-dmg \
  --volname "$NAME" \
  --volicon "Tana Helper.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "$NAME.app" 175 120 \
  --hide-extension "$NAME.app" \
  --app-drop-link 425 120 \
  "dist/$NAME.dmg" \
  "dist/dmg/"