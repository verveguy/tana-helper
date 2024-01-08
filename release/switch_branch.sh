#!/bin/sh

# check that we have a single paameter
if [ "$#" -ne 1 ]; then
  echo "Usage: switch_branch.sh <branch>"
  exit 1
fi

# List of hosts
hosts=("Monterey-x86" "Monterey-arm" "windows-x86")

# Loop through each host
for host in "${hosts[@]}"
do
  echo "Configuring $host"
  git push $host $1
  # SSH into the host and switch branches
  ssh "$host" "cd ~/dev/tana/tana-helper/release && git fetch && git pull && git checkout $1"
done

