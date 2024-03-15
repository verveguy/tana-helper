# tana-helper
Simple API service that provides a variety useful API services to complement your daily use of [Tana](https://tana.inc)

All payloads are in JSON (with the exception of one, documented below). All results are in Tana paste format unless otherwise stated.

See the [Tana Publish page](https://tana.pub/EufhKV4ZMH/tana-helper) for more usage information and examples

There's also a [Tana template](https://app.tana.inc/?bundle=cVYW2gX8nY.EufhKV4ZMH) that you can load into your Tana workspace with all the Tana commands preconfigured, demo nodes, etc.

## Prerequisites

A number of the capabilities of `tana-helper` need OpenAI and other services. For these, you'll need an OpenAI key.

## Configuration
This service is intended to be run as a local server. It also has some experimental support for hosting on Deta Space. See [Webhooks README](docs/README_WEBHOOKS.md) for details.

# Installation
`tana-helper` includes a python base API service and a React Typescript web app.

You can either install from source (instructions below), or if you are on a Mac you can try the pre-built .app package. Check the Releases section of this github repository for latest downlodable .dmg disk image.

## Prebuilt Mac OS .app

Mac OS app bundles have been tested on Monterey (12.x), Ventura (13.x) and Sonoma (14.x) on both Intel and Apple Silicon. If you have any problems with these, please add an issue here or come find me on the Tana slack community.

To launch `tana-helper`, double-click the Mac .app. You'll get a menu bar app with a single `Start tana-helper` menu item. This will launch a Terminal window showing the log as the helper service starts up.

## Prebuilt Windows .exe
Windows prebuilt binaries have been tested on Windows 11. 

To launch `tana-helper`, double-click the .exe. You'll get a task bar app with a single `Start tana-helper` menu item available via right-click. This will launch a Command console window showing the log as the helper service starts up.


# Installation from source

First, using a terminal app, clone this git repo:

    git clone https://github.com/verveguy/tana-helper.git

And change into the source directory before proceeding.

    cd tana-helper

## Mac OSX

Install homebrew if you don't already have it (will install XCode tools if required)

    /bin/bash -c “$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)“

### Install base toolset

    brew install python@3.11
    brew install node
    brew install yarn
    brew install create-dmg

Add python install location to PATH
Edit `~/.zprofile` or whichever shell you use

    echo “PATH=$PATH:/usr/local/opt/python@3.11/libexec/bin/” >> ~/.zprofile
    source ~/.zprofile
    pip install poetry

### Build everything, including .app and .dmg

    cd release
    ./build.sh

## Windows
(instructions coming soon!)

For Windows 11:

     .\\.venv\\Scripts\\Activate.ps1
 
 If you have problems doing this due to "Execution Policy", open PowerShell as Administrator and do `set-executionpolicy remotesigned`. This should let you run the virtualenv `Activate.ps1` script)

## Run the service

Then you can start the service:

    cd service
    uvicorn service.main:app

(If you want to hack on `tana-helper`, run it with `--reload` to ease development iterations)

## Experimental deployment to Deta Space
If you want to host this service somewhere, there's experimental support for Deta Space in the main branch. Learn more about Deta Space [here](https://deta.space/).

However, there's something wrong with Tana Proxy fetch right now...

# Usage

There's a few different services provided by tana-helper: you may not want all of them.
You can remove services by modifying the file `src/main/py`. Comment out the line for the service you don't want.

See the [Tana Publish page](https://tana.pub/EufhKV4ZMH/tana-helper) for more usage information and examples

There's also a [Tana template](https://app.tana.inc/?bundle=cVYW2gX8nY.EufhKV4ZMH) that you can load into your Tana workspace with all the Tana commands preconfigured, demo nodes, etc.

## Calendar API stuff

This API wraps a small service, written in Go, that helps Tana get your Calendar for the day. Provides an API you can call from Tana.

The Calendar integration API features are only available on a local Mac. There's no Windows support for calendar integration. Relies on Apple's Calendar.app and associated API to fetch the calendar data. If Calendar.app is configured to synchronize calendars from iCloud, Google and/or Microsoft Office, this will see all of that data.

## Graph Visualizer!

Inspired by the marketing visualization on the Tana.inc website, `tana-helper` provides a 3D visualization of your Tana workspace.

Check out this [video demo](https://share.cleanshot.com/7J6d6F6l)

For details, see [Visualizer README](docs/README_VISUALIZER.md)

## Webhooks support!

Based on the inspiring example from @houshuang (see [recording](https://share.cleanshot.com/PNDJjGp4)), `tana-helper` now provides a powerful form of webhook processing.

Basically, you can shovel any text, email, etc at the `/webhook/<tana_type>` endpoint and it will process it into JSON using OpenAI and push the resulting JSON into Tana via the [Tana Input API](https://help.tana.inc/tana-input-api.html).

So you can call this webhook from pretty much any integration platform such as Zapier or for email, use the [cloudmailin.com](https://cloudmailin.com) service as @houshuang did.

See [Webhooks README](docs/README_WEBHOOKS.md) for more details.

## Vector database support

ChromaDB, Weaviate and Pinecone are all vector databases that let you take arbitrary chunks of text, turn them into "embeddings" (vectors) via OpenAI and then store. Why do this? So that you can take some other chunk of text, turn it into a vector and then use that vector to _query your database_.

This is a very powerful idea. It basically means Tana can have full semantic similarity search today, while we wait for Tana themselves to make this magical as part of the product.

There's three variants offered by `tana-helper`: ChromaDB and Weaviate (both local on your laptop) and Pinecone (hosted service). The latter requires a Pinecone account and you will need to create a Pinecone index within a Pinecone "environment" (Region). The default index name is `tana-helper` although this can also be configured.

For details, see the Tana templates located at [https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A](https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A)

See [Pinecone README](docs/README_PINECONE.md) for more details.

## LLamaindex support

DISABLED CURRENTLY PENDING BETTER RESULTS

Beyond upserting/querying a vector database, `tana-helper` now has the start of some functionality built on top of the [llamaindex](https://www.llamaindex.ai/) opensource RAG toolkit. Llamaindex allows you to build a "document index" on top of a vector database (in this case, ChromaD, so everything is stored locally). 

APIs are provided for preloading your entire Tana workspace from a Tana JSON Export file, building a llamaindex for the whole workspace, as well as incrementally "updating" individual Tana notebook nodes within the index.

The index can then be used to answer questions about your own Tana workspace via the `/research` endpoint. The question you pose will be transformed into a number of more specific questions which are then used as embedding queries against the llamaindex. The results of all this retrieval will then be fed to an LLM to process into a response to your original question. 

Results are variable at this point: I'm hopeful that Tana themselves will build this kind of feature into the product at some point. I think the truth is that implementing RAG pipelines in code is far less flexible than having some kind of interactive "RAG chat" capability. The problem is getting it integrated with Tana and having access to your entire workspace...

NOTE: for those of you digging into the code, you'll see there's some initial support for using [Ollama](https://ollama.ai/) locally to let you use LLMs and embeddings other than OpenAI. I've been pretty disappointed with other LLM's so far, which is why I'm not yet making this a more generally "finished" feature. I'm not sure it's worth it...

## Pushing nodes to inline references support

This is a useful addition to Tana depending on your workflow. Basically, it lets you take notes from say, a meeting, where you've used inline refs to link the note to various concept nodes and then "push" the new note to those concept nodes rather than just relying on the backlinks UI in Tana. (Which I find very limiting and disruptive to my reading flow)

`/inlinerefs` Given a node, finds and returns all inline refs as fields in Tana paste format.

See the [Tana template](https://app.tana.inc/?bundle=cVYW2gX8nY.Eb8g90_U2G) for more information.

## Python exec() helper

Ever want to run some chunk of code inside Tana? Well, now you can (kinda).

`/exec` Executes an arbitrary chunk of python code passed as a parameter. Useful for adding simple functions to Tana.

`/exec_loose` Same thing, but without the strict JSON format parameters requirement. Allows use of Tana formatted code nodes.

See the [Tana template](https://app.tana.inc/?bundle=cVYW2gX8nY.l7dQ2eDwJK) for more information.

### JSON Proxy helper

Makes it easier to call external services that expect JSON. Lets you proxy requests to the external service via `tana-helper`, converting Tana nodes on the way in to JSON and converting JSON responses back to Tana nodes on the way back.


## Self bootstrapping into Tana

(NOT YET POSSIBLE. SEE `/usage`)



