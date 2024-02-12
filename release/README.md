# BUILDING

Make sure you have a few tools installed

python
create-dmg

Create a copoy of the .env.template file, rename to `.env` and ensure your Apple ID, 
app-specific password and Developer ID hash are all correct.

## To build a single arch locally

`build_local.sh`

## To build all the archs using remote build machines

Make sure the remotes are set up and named according to the build_all.sh script.
Currently there are three assumed:

monterey-arm64
monterey-x86
windows-x86  (windows 11)

(Although it may be that windows cross-compiles on arm so a VM can be used on an M1 Mac)

You can use `add_remote.sh` to do the initial git repo setup

Set the branch on all remotes using `switch_branch.sh`

Build all the remotes and merge the outputs using `build_all.sh`

Note that the local machine is NOT assumed to be a build machine since the use-case
for multi-arch builds is typically to use an older MacOS as the base OS 

## Build problems

Operation not permitted during create_dmg phase: Terminal and VSCode need "Allow full filesystem access" permission. (via system settings app)

# TODO
Looks like notarization may still cause some pain. 
Currently, we build the DMG and then notarize that, expecting that the whole thing will be notarized properly
However, the ticket we get back is only stapled to the DMG. 

We may need to staple it to the .app bundles inside the DMG as well.
(So they can be copied off the DMG and then run)

See this [blog posting on notarization](https://deciphertools.com/blog/notarizing-dmg/)

Check this with 
`xcrun stapler validate`