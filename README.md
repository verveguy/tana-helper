# tana-helper

Simple API service that provides a form of "Semantic search" for Tana.

`./upsert` accepts Tana node data and creates
embeddings via OpenAI to populate a Pinecone database.

`./query` accepts a Tana node context and returns a list of 
Tana node references in Tana paste format as a result.

`./delete` accepts a Tana node ID and removes the entry from the
Pinecone database.

## Configuration

This service is intended to be run in one of two ways currently: either as a localhost service, private to your local machine, or as a hosted service on the Vercel hosting platform.

When run on Vercel, you need to configure it for Auth0 Machine2Machine security. This is currently left as an exercise for the reader.

You will need to copy the supplied `env.template` file as `.env` and fill in the various configuration fields. The config is only read at startup time, so if you change it, you need to restart the service to pick up the changes.

Importantly, you will need an OpenAI account that can access the `text-embedding-ada-002` model. (This is configurable, but is the only model currently tested.)

You will also need a Pinecone account and will need to create a Pinecone index within a Pinecone "environment" (Region). The default index name is `tana-helper` although this can also be configured.

If you are running this as a shared, hosted service, say for your Tana team to use, you can run this on hosted infrastructure. However, you should NOT configure the .env file with OpenAI keys, since the service offers
unauthenticated access. Instead, you can pass the OpenAI and Pinecone keys on each request.

See `env.template` for further comments on configuration.

## JSON payload format

`./upsert` and `./query` both accept
``` 
{ 
  "nodeId": "${sys:nodeId}",  
  "tags": "${sys:tags}", 
  "context": "${sys:context}" 
}
```

`./query` also accepts
```
  "top": "10",  // how many results to return, maximum. 10 is default
  "threashold": "0.80", // threashold for results. .80 is default
```

`./delete` accepts
``` 
{ 
  "nodeId": "${sys:nodeId}",  
}

And all API calls optionally accept
```
  // optional, required if not configured in .env
  "pinecone": "${secret:Pinecone}",
  "openai": "${secret:OpenAI}",
```
## TODO

Potentially use another solution to secure the API endpoints on Vercel.
(Could be as simple as a hard-coded .env secret. Anything more complex is overkill)