#!/bin/sh

# check that we have a single paameter
if [ "$#" -ne 1 ]; then
  echo "Usage: switch_branch.sh <branch>"
  exit 1
fi

# List of hosts
hosts=("Monterey-x86" "Monterey-arm" "Windows-arm")

# Loop through each host
for host in "${hosts[@]}"
do
  # SSH into the host and switch branches
  ssh "$host" "cd ~/dev/tana/tana-helper/release && git checkout $1"
done

