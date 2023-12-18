#!/bin/sh

# Add a new remote build machine

# ssh into the remote machine and create our directory tree
ssh $1 "mkdir -p ~/dev/tana/"

# create a new bare repo
ssh $1 "git init --bare ~/dev/tana/tana-helper.git"

# add the remote
git remote add $1 $1:/~/dev/tana/tana-helper.git

# push to the remote
git push $1

# clone the repo on the remote machine
ssh $1 "git clone ~/dev/tana/tana-helper.git ~/dev/tana/tana-helper"

# checkout main branch
ssh $1 "cd ~/dev/tana/tana-helper; git checkout main"

echo "DONE adding remote $1"
