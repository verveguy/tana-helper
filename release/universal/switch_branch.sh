#!/bin/sh

# List of hosts
hosts=("Monterey-x86" "Monterey-arm" "Windows-arm")

# Loop through each host
for host in "${hosts[@]}"
do
  # SSH into the host and switch branches
  ssh "$host" "cd ~/dev/tana/tana-helper/release && git checkout $1"
done

