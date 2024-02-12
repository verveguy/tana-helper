#!/bin/sh

# functions for use in our primary build scripts

error() {
  echo_red "Build failed" >&2
  exit 1
}

# ANSI color codes
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

timestamp() {
  date +"%T" # current time
}

echo_blue() {
  echo "\r$(timestamp) ${BLUE}$1${NC}"
}

echo_red() {
  echo "\r$(timestamp) ${RED}$1${NC}"
}

# wait with spinner function
wait_for_process_completion() {
  local pids="$@"
  local spin='-\|/'
  local i=0

  while kill -0 $pids 2>/dev/null
  do
    i=$(( (i+1) %4 ))
    printf "\r${spin:$i:1}"
    sleep .1
  done
  printf "\r"
}

checkjobs() { # PID
 for pid in "$@"; do
    shift
    if kill -0 "$pid" 2>/dev/null; then
      set -- "$@" "$pid"
    elif wait "$pid"; then
      echo_blue "Background job complete"
    else
      echo_red "Background job failed"
      return 1
    fi
  done
  return "$@" # there might be fewer jobs left after this check...
}

waitalljobs() { # PID...
  local i=0
  local spin='-\|/'
  while :; do
    for pid in "$@"; do
      shift
      if kill -0 "$pid" 2>/dev/null; then
        set -- "$@" "$pid"
      elif wait "$pid"; then
        echo_blue "Background job complete"
      else
        echo_red "Background job failed"
        return 1
      fi
    done
    (("$#" > 0)) || break
    i=$(( (i+1) %4 ))
    printf "\r${spin:$i:1}"
    sleep .1
   done
}

remote_build() {
  local host=$1
  local arch=$2
  local log="builds/build_${arch}.log"

  echo_blue "Building $arch architecture"
  # if window arch, slightly different
  if [ "$arch" = "win" ]; then
    ssh "$host" "cd ~/dev/tana/tana-helper/release; git pull; ./build.sh" > "$log" 2>&1
    if [ $? -ne 0 ]; then
      echo_red "Build failed for $arch"
      tail -n 1 "$log"
      return 1
    fi
    echo_blue "Fetching $arch build"    
    scp -r "${host}:~/dev/tana/tana-helper/release/dist/*" builds/ >> "$log" 2>&1
  else
    ssh "$host" "zsh --login -c 'cd ~/dev/tana/tana-helper/release; git pull; ./build.sh'" > "$log" 2>&1
    if [ $? -ne 0 ]; then
      echo_red "\rBuild failed for $arch"
      tail -n 1 "$log"
      return 1
    fi
    echo_blue "Fetching $arch build"
    rsync -a "${host}:~/dev/tana/tana-helper/release/dist/*" builds/ >> "$log" 2>&1
  fi

  echo_blue "Completed $arch build"
}

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
  local BASE=$1
  local SOURCE1=$2
  local SOURCE2=$3
  
  local nest=""

  local count=`ls -Rl | grep "^-" | wc -l`

  inner_lipo () {
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
        printf "\r$nest copied link $elem\033[K"
      # if the file is a non-link directory, recurse into it
      elif [ -d "$elem" ]; then
        inner_lipo "$parent" "$subpath/$folder" "$filename"
      # else try and lipo the file
      else
        if lipo -create -output "$BASE/$mid" "$SOURCE1/$mid" "$SOURCE2/$mid" 2> /dev/null; then
          printf "\r$nest lipo'd file $mid\033[K"
        # if lipo fails, then just copy it
        else
          cp "$parent/$mid" "$BASE/$mid"
          printf "\r$nest copied file $mid\033[K"
        fi
      fi
    done
    IFS="$OIFS"

    nest=$oldnest
  }

  # start the recursion
  inner_lipo "$SOURCE1" "Contents" ""
}

codesign_app() {
  local BASE=$1

  # Codesign the resulting app bundle
  echo_blue "Codesigning $BASE"
  codesign --deep --force --options=runtime --entitlements ./entitlements.plist --sign "AF8D80217A4FEB07B4D853648FD1790FCE81FB9F" --timestamp "$BASE"

  echo_blue "Verifying deep codesigning of ${BASE} bundle"
  codesign --verbose=4 --display --deep --strict "$BASE"
}


# TODO: Figure out how to use codesign and notarize options of create-dmg
# to avoid having to do this in two steps and with external notarize.py script

create_dmg() {
  local NAME=$1

  # Create the DMG.
  create-dmg \
    --volname "$NAME" \
    --volicon "$NAME.icns" \
    --window-pos 200 120 \
    --window-size 600 300 \
    --icon-size 100 \
    --icon "$NAME.app" 175 120 \
    --hide-extension "$NAME.app" \
    --app-drop-link 425 120 \
    --no-internet-enable \
    "dist/$NAME.dmg" \
    "dist/dmg/"

    # --codesign <signature>
    #   codesign the disk image with the specified signature
    # --notarize <credentials>
    #   notarize the disk image (waits and staples) with the keychain stored credentials
}

notarize_dmg() {
  local NAME=$1

  # Notarize the .dmg
  python notarize.py "$NAME"
}

assess() {
  local BASE=$1

  # Verify the .app bundle
  echo_blue "spctl assess $BASE"
  spctl --ignore-cache --assess --verbose "$BASE"
}
