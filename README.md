# tana-helper
Simple API service that provides a form of "Semantic search" for Tana along with potentially other useful API services.

All payloads are in JSON (with the exception of one, documented below)
All results are in Tana paste format.

# Running
You will need `python3` already installed as well as `virtualenv`

NOTE: Your version of python3 should be at least 3.9
Check it with `python3 --version`

Upgrade python3 in whatever fashion you choose ([homebrew](https://brew.sh) is good)

You can install `virtualenv` via:

`pip install virtualenv`

Using a terminal app, clone this git repo:

`git clone https://github.com/verveguy/tana-helper.git`

`cd tana-helper`

Create a virtualenv called `env` and activate it

`python3 -m venv env` 

For Mac/Linux:

`source env/bin/activate`

For Windows 11:

 `.\\env\\Scripts\\Activate.ps1`
 
 If you have problems doing this due to "Execution Policy", open PowerShell as Administrator and do `set-executionpolicy remotesigned`. This should let you run the virtualenv `Activate.ps1` script)

You will then need to install the various python packages required by the service.

`pip install -r requirements.txt`

Then you can start the service:

`uvicorn src.main:app`

(If you want to hack on tana-helper, run it with `--reload` to ease development iterations)

## Experimental deployment to Deta Space
If you want to host this service somewhere, there's experimental support for Deta Space in the main branch. Learn more about Deta Space [here](https://deta.space/).

However, there's something wrong with Tana Proxy fetch right now...

# Usage

There's a few different services provided by tana-helper: you may not want all of them.
You can remove services by modifying the file `src/main/py`. Comment out the line for the service you don't want.

Each has a Tana template associated with it (links below)

## Pinecone support

For details, see the Tana templates located at [https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A](https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A)

All APIs are POST endpoints

`/pinecone/upsert` accepts Tana node data and creates
embeddings via OpenAI to populate a Pinecone database.

`/pinecone/query` accepts a Tana node context and returns a list of 
Tana node references in Tana paste format as a result.

`/pinecone/delete` accepts a Tana node ID and removes the entry from the
Pinecone database.

`/pinecone/purge` empties the entire Pinecone database. NOT YET IMPLEMENTED

## Pushing nodes to inline references support

`/inlinerefs` Given a node, finds and returns all inline refs as fields in Tana paste format.

See the [Tana template](https://app.tana.inc/?bundle=cVYW2gX8nY.Eb8g90_U2G) for more information.

## Python exec() helper

`/exec` Executes an arbitrary chunk of python code passed as a parameter. Useful for adding simple functions to Tana.

`/exec_loose` Same thing, but without the strict JSON format parameters requirement. Allows use of Tana formatted code nodes.

See the [Tana template](https://app.tana.inc/?bundle=cVYW2gX8nY.l7dQ2eDwJK) for more information.

## Self bootstrapping into Tana

(NOT YET IMPLEMENTED. SEE `/usage`)

To make it easier to configure this for Tana access, you can hit the `/bootstraps` endpoint from any browser and then paste the results into Tana. This will create a set of Tana command nodes that are correctly configured to call the API.


## Prerequisites
You will need an OpenAI account that can access the `text-embedding-ada-002` model. (This is configurable, but is the only model currently tested.)

You will also need a Pinecone account and will need to create a Pinecone index within a Pinecone "environment" (Region). The default index name is `tana-helper` although this can also be configured.

## Configuration
This service is intended to be run as a local server. At some point, I'll figure out how to get it running on a common hosting platform again.

## JSON payload format

### Pinecone API stuff

`/pinecone/upsert` and `/pinecone/query` both accept
``` 
{ 
  "nodeId": "${sys:nodeId}",  
  "tags": "${sys:tags}", 
  "context": "${sys:context}" 
}
```

`/pinecone/query` also accepts
```
  "top": "10",  // how many results to return, maximum. 10 is default
  "threshold": "0.80", // threashold for results. .80 is default
```

`/pinecone/delete` accepts
``` 
{ 
  "nodeId": "${sys:nodeId}",  
}
```

And all Pinecone related API calls optionally accept
```
  "pinecone": "${secret:Pinecone}", // required if not configured in .env
  "openai": "${secret:OpenAI}", // required if not configured in .env
  "index": "${secret:PineconeIndex}",  // defaults to tana-helper
```

### Calendar API stuff
The Calendar API previously supported by tana-helper has been moved out to [tana-calendar-helper](https://github.com/verveguy/tana-calendar-helper).
Why? These features are only available on a local Mac and so it was confusing to have Mac-only features in this service, which is intended to be run on a hosted server supporting team usage.
