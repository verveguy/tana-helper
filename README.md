# tana-helper

Simple API service that provides a form of "Semantic search" for Tana along with potentially other useful API services.

All payloads are in JSON.
All results are in Tana paste format.

## Running

You will need `node` already installed.

Using a terminal app, clone this git repo
`git clone https://github.com/verveguy/tana-helper.git`

`cd tana-helper`
`yarn install`
`yarn start`

## Usage

You can hit the `/usage` endpoint to get a Tana paste format self-documenting instructions for this service. When Tana paste can create command nodes, this will be a form of "self-install" into Tana. Right now it returns some documentation and screen shots of commands that you can set up to use this service.

Use the Tana template located at [https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A](https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A)


## Pinecone support

All APIs are POST endpoints

`/pinecone/upsert` accepts Tana node data and creates
embeddings via OpenAI to populate a Pinecone database.

`/pinecone/query` accepts a Tana node context and returns a list of 
Tana node references in Tana paste format as a result.

`/pinecone/delete` accepts a Tana node ID and removes the entry from the
Pinecone database.

`/pinecone/purge` empties the entire Pinecone database. NOT YET IMPLEMENTED

## Self bootstrapping into Tana

To make it easier to configure this for Tana access, you can hit the `/bootstraps` endpoint from any browser and then paste the results into Tana. This will create a set of Tana command nodes that are correctly configured to call the API.

(NOT YET IMPLEMENTED. SEE `/usage`)

## Prerequisites

You will need an OpenAI account that can access the `text-embedding-ada-002` model. (This is configurable, but is the only model currently tested.)

You will also need a Pinecone account and will need to create a Pinecone index within a Pinecone "environment" (Region). The default index name is `tana-helper` although this can also be configured.

## Configuration

This service is intended to be run in one of two ways currently: either as a localhost service, private to your local machine, or as a hosted service on the Vercel hosting platform.

You can either configure this service via a `.env` file for things like OpenAI keys, etc. or you can pass these keys on every API call as part of the JSON payload.

If you are running this as a shared, hosted service, say for your Tana team to use, you can run this on hosted infrastructure. However, you should NOT configure the `.env` file with OpenAI keys, since the service offers unauthenticated access. Instead, you can pass the OpenAI and Pinecone keys on each request.

For `.env` configuration, you will need to copy the supplied `env.template` file as `.env` and fill in the various configuration fields. The config is only read at startup time, so if you change it, you need to restart the service to pick up the changes.

See `env.template` for further comments on configuration.

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
  "threashold": "0.80", // threashold for results. .80 is default
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
