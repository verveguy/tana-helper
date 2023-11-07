# Pinecone integration

First, see the Tana templates located at [https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A](https://app.tana.inc/?bundle=cVYW2gX8nY.G3v4049e-A)

All APIs are POST endpoints

`/pinecone/upsert` accepts Tana node data and creates
embeddings via OpenAI to populate a Pinecone database.

`/pinecone/query` accepts a Tana node context and returns a list of 
Tana node references in Tana paste format as a result.

`/pinecone/delete` accepts a Tana node ID and removes the entry from the
Pinecone database.

`/pinecone/purge` empties the entire Pinecone database. NOT YET IMPLEMENTED

(TODO: update docs and code for Authorization headers. See Webhooks support already implemented)

## Pinecone API stuff

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
