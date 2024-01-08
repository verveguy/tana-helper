#!/bin/sh

# remotely building on Windows is a pain to setup.
# Make sure OpenSSH server is installed and correctly configured
# with keys, etc.

# Then set up the git bash shell as default login shell
# See https://unix.stackexchange.com/questions/557751/how-can-i-execute-command-through-ssh-remote-is-windows
# New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value "C:\Program Files\Git\bin\sh.exe" -PropertyType String -Force

# ensure we clean up background processes when we are killed
trap "exit" INT TERM 
trap "kill 0" EXIT

error() {
  echo_red "Build failed" >&2
  exit 1
}

trap error ERR

start=$(date +%s)


NAME='Tana Helper'
BASE="dist/dmg/$NAME.app"
ARM64_NAME="$NAME (12.6-arm64).app"
ARM64="builds/$ARM64_NAME"
X86_64_NAME="$NAME (12.7-x86_64).app"
X86_64="builds/$X86_64_NAME"


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

echo_blue "START builds"

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
}

waitalljobs() { # PID...
  local i=0
  local spin='-\|/'
  while :; do
    checkjobs "$@"
    if [ $? -ne 0 ]; then
      return 1
    fi
    (("$#" > 0)) || break
    i=$(( (i+1) %4 ))
    printf "\r${spin:$i:1}"
    sleep .1
   done
}

# BUILD Mac ARM64 and Mac x86_64
echo_blue "Cleaning up from previous builds"
rm -rf builds
rm -rf dist
mkdir -p builds

echo_blue "Updating remote git repos"

git push Monterey-x86
git push Monterey-arm
git push windows-x86

echo_blue "Starting parallel builds"

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

# Parallelize building the three architectures

remote_build "Monterey-x86" "x86_64" &
pid1=$!
remote_build "Monterey-arm" "arm64" &
pid2=$!
remote_build "windows-x86" "win" &
winpid=$!

# wait for all builds to complete
# wait_for_process_completion $pid1 $pid2 #$pid3
waitalljobs $pid1 $pid2 $winpid

# Mac specific build of Universal bindary

# LIPO the two into one
echo_blue "Preparing Universal Map .app"
echo_blue "Lipo-ing the two architectures into one"
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
      printf "\r$nest copied link $elem\033[K"
    # if the file is a non-link directory, recurse into it
    elif [ -d "$elem" ]; then
      lipo_files "$parent" "$subpath/$folder" "$filename"
    # else try and lipo the file
    else
      if lipo -create -output "$BASE/$mid" "$ARM64/$mid" "$X86_64/$mid" 2> /dev/null; then
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

# use arm64 build as our "primary" and recurse that structure
lipo_files "$ARM64" "Contents" "" > builds/lipo.log 2>&1 &
lipopid=$!

# show process spinner
waitalljobs $lipopid
echo_blue "Completed Universal .app build"

# Codesign the resulting app bundle
echo_blue "Codesigning the resulting .app bundle"
codesign --sign "Developer ID Application: Brett Adam (264JVTH455)" "$BASE" --force

# Create the DMG.
echo_blue "Creating DMG for distribution"
create-dmg \
  --volname "$NAME" \
  --volicon "$NAME.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "$NAME.app" 175 120 \
  --hide-extension "$NAME.app" \
  --app-drop-link 425 120 \
  "dist/$NAME.dmg" \
  "dist/dmg/"

echo_blue "Mac DMG built"
echo ""

# and wait for the Windows build if it's still not done
waitalljobs $winpid

echo "Builds complete"

mv builds/*.zip dist/

echo "END builds"

end=$(date +%s)
echo "Elapsed Time: $(($end-$start)) seconds"


