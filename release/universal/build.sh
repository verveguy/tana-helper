#!/bin/sh

NAME='Tana Helper'
BASE="dist/dmg/$NAME.app"
ARM64_NAME="$NAME (12.6-arm64).app"
ARM64="builds/$ARM64_NAME"
X86_64_NAME="$NAME (12.7-x86_64).app"
X86_64="builds/$X86_64_NAME"


# BUILD Windows ARM
./build_win.sh


# BUILD Mac ARM64 and Mac x86_64
rm -rf builds
mkdir -p builds

# Parallelize this
# BUILD X86
echo "Building X86_64 architecture"
git push Monterey-x86
ssh -t administrator@Monterey-x86 "zsh --login -c 'cd ~/dev/tana/tana-helper/release; ./build.sh'"

# BUILD ARM64
echo "Building ARM64 architecture"
git push Monterey-arm
ssh -t admin@Monterey-arm "zsh --login -c 'cd ~/dev/tana/tana-helper/release; ./build.sh'"

# Wait for both background processes to finish
#wait

rsync -a "administrator@Monterey-x86:~/dev/tana/tana-helper/release/dist/dmg/" builds/
rsync -a "admin@Monterey-arm:~/dev/tana/tana-helper/release/dist/dmg/" builds/

# LIPO the two into one
echo "Lipo-ing the two architectures into one"
rm -rf "dist"
mkdir -p "dist/dmg"

nest=""

count=`ls -Rl | grep "^-" | wc -l`

# lipo_files takes three params
#   - the base directory
#   - the current subpath
#   - and the current leaf folder to process
# It will recurse into any subfolders and lipo any files it finds
# It will copy any non-link files it finds
# It will copy any links it finds
# It will create any folders it needs to
# It will preserve the folder structure of the base directory
# It will preserve the file structure of the base directory

lipo_files () {
  local parent=$1
  local subpath=$2
  local folder=$3

  local oldnest=$nest
  nest=$nest+
  #echo "Subpath: $subpath Folder: $folder"
  # preserve line ending
  OIFS="$IFS"
  IFS=$'\n'
  for file in `ls -A $parent/$subpath/$folder`; do
    local filename=$(basename "$file")
    local mid="$subpath/$folder/$filename"
    local elem="$parent/$mid"
    mkdir -p "$BASE/$subpath/$folder"
    # if the file is a link, copy it as a link
    if [ -L "$elem" ]; then
      # copy the link itself
      cp -P "$parent/$mid" "$BASE/$mid"
      printf "\r$nest copied link $elem"
    # if the file is a non-link directory, recurse into it
    elif [ -d "$elem" ]; then
      lipo_files "$parent" "$subpath/$folder" "$filename"
    # else try and lipo the file
    else
      if lipo -create -output "$BASE/$mid" "$ARM64/$mid" "$X86_64/$mid" 2> /dev/null; then
        printf "\r$nest lipo'd file $mid"
      # if lipo fails, then just copy it
      else
        cp "$parent/$mid" "$BASE/$mid"
        printf "\r$nest copied file $mid"
      fi
    fi
  done
  IFS="$OIFS"



  nest=$oldnest
}

# use arm64 build as our "primary" and recurse that structure
lipo_files "$ARM64" "Contents" ""

# Codesign the resulting app bundle
echo "Codesigning the resulting app bundle"
codesign --sign "Developer ID Application: Brett Adam (264JVTH455)" "$BASE" --force

# Create the DMG.
echo "Creating DMG for distribution"
create-dmg \
  --volname "$NAME" \
  --volicon "../$NAME.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "$NAME.app" 175 120 \
  --hide-extension "$NAME.app" \
  --app-drop-link 425 120 \
  "dist/$NAME.dmg" \
  "dist/dmg/"

echo "Mac build DONE!"
echo ""

echo "DONE!"

