# tana-helper
Simple API service that provides a form of "Semantic search" for Tana along with potentially other useful API services.

All payloads are in JSON (with the exception of one, documented below)
All results are in Tana paste format.

## Running
You will need `python3` already installed as well as `virtualenv`

You can install `virtualenv` via:

`pip install virtualenv`

Using a terminal app, clone this git repo

`git clone https://github.com/verveguy/tana-helper.git`

`cd tana-helper`

Create a virtualenv called `env` ad activate it

`python3 -m venv env` 

`source env/bin/activate`

`uvicorn src.main:app`

## Usage
For details, see the Tana template located at [https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A](https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A)


## Pinecone support
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
