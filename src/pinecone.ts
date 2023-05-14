/*
    Simple API service that provides a form of "Semantic search" for
    Tana using OpenAI and Pinecone.

    ./pinecone/upsert accepts Tana node data and creates
    embeddings via OpenAI to populate a Pinecone database.

    ./pinecone/query accepts a Tana node context and returns a list of 
    Tana node references in Tana paste format as a result.
    
    ./pinecone/delete accepts a Tana node ID and removes the entry from the
    Pinecone database.

    TODO:

    Add ./pinecone/purge to dump all records in the database.
*/

import { Request, Response } from "express";
import axios from "axios";
import { PineconeClient, QueryRequest } from "@pinecone-database/pinecone";
import { LOCAL_SERVICE, app } from './server.js';

let OPENAI_API_KEY = process.env.OPENAI_API_KEY as string;
let PINECONE_API_KEY = process.env.PINECONE_API_KEY as string;

let OPENAI_EMBEDDING_MODEL = process.env.OPENAI_EMBEDDING_MODEL ?? "text-embedding-ada-002";
let PINECONE_ENVIRONMENT = process.env.PINECONE_ENVIRONMENT ?? "asia-southeast1-gcp";
let PINECONE_INDEX = process.env.PINECONE_INDEX ?? "tana-helper";

// Pinecone keys that are not configured
const TANA_NAMESPACE = "tana-namespace";
const TANA_TYPE = "tana_node";

if (OPENAI_EMBEDDING_MODEL === undefined
  || PINECONE_ENVIRONMENT === undefined
) {
  throw new Error("Missing OpenAI or Pinecone configuration. These keys are all required.");
}

//-------------------------
// helper functions for working with payloads
// and OpenAI embeddings


async function getOpenAIEmbedding(text: string): Promise<any> {
  const response = await axios.post(
    'https://api.openai.com/v1/embeddings',
    {
      model: `${OPENAI_EMBEDDING_MODEL}`,
      input: text
    },
    { headers: { 'Authorization': `Bearer ${OPENAI_API_KEY}` } }
  );
  return response.data;
}

function paramsFromPayload(req: Request) {
  // debug log
  if (LOCAL_SERVICE) {
    console.log(req.body);
  }

  const node_id = req.body.nodeId; // what if empty? Barf...
  if (node_id === undefined) {
    throw new Error("Missing node_id. node_id is required on all API calls.");
  }

  const threshold = req.body.score ?? 0.80; // default to 0.8
  const top = req.body.top ?? 10; // default to top 10
  const context = req.body.context ?? ""; // not always present
  const supertags = req.body.tags == "" ? undefined : req.body.tags;

  return { context, threshold, top, node_id, supertags };
}

function getKeysFromPayload(req: Request) {
  OPENAI_API_KEY = req.body.openai ?? OPENAI_API_KEY;
  PINECONE_API_KEY = req.body.pinecone ?? PINECONE_API_KEY;

  OPENAI_EMBEDDING_MODEL = req.body.model ?? OPENAI_EMBEDDING_MODEL;
  PINECONE_ENVIRONMENT = req.body.environment ?? PINECONE_ENVIRONMENT;
  PINECONE_INDEX = req.body.index ?? PINECONE_INDEX;

  if (OPENAI_API_KEY === undefined || PINECONE_API_KEY === undefined) {
    throw new Error("Missing OpenAI and/or Pinecone API keys. These keys are all required.");
  }
}


// TODO: move to utils file
// connect to Pinecone
async function getPinecone() {
  const pinecone = new PineconeClient();
  await pinecone.init({
    environment: PINECONE_ENVIRONMENT,
    apiKey: PINECONE_API_KEY,
  });
  return pinecone;
}


//-------------------------
// API ENDPOINTS START HERE
// UPSERT an embedding by Tana node_id
app.post('/pinecone/upsert', async (req: Request, res: Response) => {

  getKeysFromPayload(req);

  const { context, node_id, supertags } = paramsFromPayload(req);
  const embedding = await getOpenAIEmbedding(context);

  // convert embedding to pinecode upsert
  // we include the context as the text: metadata
  // so that other systems like langchain can use the context data
  // without calling back to Tana
  const upsertRequest = {
    namespace: TANA_NAMESPACE,
    vectors: [
      {
        id: node_id,
        metadata: {
          category: TANA_TYPE,
          supertag: supertags,
          text: context
        },
        values: embedding.data[0].embedding,
      }
    ],
  };

  const pinecone = await getPinecone();
  const index = pinecone.Index(PINECONE_INDEX);

  await index.upsert({ upsertRequest });

  if (LOCAL_SERVICE) {
    console.log(`Upserted document with ID: ${node_id}`);
  }

  res.status(200).send();
});


// DELETE an embedding by Tana node_id
app.post('/pinecone/delete', async (req: Request, res: Response) => {

  getKeysFromPayload(req);

  const { node_id } = paramsFromPayload(req);

  const deleteRequest = {
    namespace: TANA_NAMESPACE,
    ids: [node_id]
  };

  const pinecone = await getPinecone();
  const index = pinecone.Index(PINECONE_INDEX);

  await index.delete1(deleteRequest);

  if (LOCAL_SERVICE) {
    console.log(`Deleted document with ID: ${node_id}`);
  }

  res.status(200).send();
});


// QUERY embeddings by comparative embedding
// returns: Tana paste formatted node references
app.post('/pinecone/query', async (req: Request, res: Response) => {

  getKeysFromPayload(req);

  const { context, threshold, top, supertags } = paramsFromPayload(req);
  const embedding = await getOpenAIEmbedding(context);

  const queryRequest: QueryRequest = {
    namespace: TANA_NAMESPACE,
    vector: embedding.data[0].embedding,
    topK: top,
    includeMetadata: true,
    filter: {
      category: TANA_TYPE,
    }
  };

  // if we have supertags, include in query
  if (supertags !== undefined) {
    // split strings into array
    queryRequest.filter = {
      category: TANA_TYPE,
      supertag: { $in: supertags.split(' ') },
    };
  }

  const pinecone = await getPinecone();
  const index = pinecone.Index(PINECONE_INDEX);

  const query_response = await index.query({ queryRequest });
  const best = query_response.matches?.filter((value, index, results) => {
    const score = value?.score ?? 0;
    if (score > threshold) {
      if (LOCAL_SERVICE) {
        console.log(`Matching score ${score} > ${threshold}`);
      }
      return value;
    }
    else {
      if (LOCAL_SERVICE) {
        console.log(`Low score: ${score} < ${threshold}`);
      }
    }
  });
  const documentIds: string[] | undefined = best?.map((match: any) => match.id as string);

  // convert documentIds back to Tana paste format as refs
  let tanaPasteFormat = "";
  if (best?.length == 0) {
    tanaPasteFormat = "No sufficiently well-scored results";
  }
  else {
    for (let node of documentIds ?? []) {
      tanaPasteFormat += "- [[^" + node + "]]\n";
    }
  }
  if (LOCAL_SERVICE) {
    console.log(tanaPasteFormat);
  }

  res.status(200).send(tanaPasteFormat);
});


// PURGE to dump the database
// TODO: Implement this!
app.post('/pinecone/purge', async (req: Request, res: Response) => {
  getKeysFromPayload(req);

  if (LOCAL_SERVICE) {
    console.log(req.body);
  }
  res.status(200).send("Not yet implemented");
});

export default app;
