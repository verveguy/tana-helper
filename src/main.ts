import express, { NextFunction, Request, Response } from "express";
import bodyParser from "body-parser";
import axios from "axios";
import { PineconeClient } from "@pinecone-database/pinecone";
import { config as dotenvConfig } from 'dotenv';
import cors from 'cors';
import helmet from 'helmet';
import winston from "winston";
import expressWinston from 'express-winston';
import { expressjwt } from "express-jwt";
import jwksRsa, { GetVerificationKey } from "jwks-rsa";


// read .env to get our API keys
dotenvConfig();

const PORT = (process.env.PORT ?? 4000) as number;
const OPENAI_API_KEY = process.env.OPENAI_API_KEY as string;
const PINECONE_API_KEY = process.env.PINECONE_API_KEY as string;
const PINECONE_ENVIRONMENT = process.env.PINECONE_ENVIRONMENT as string;
const PINECONE_INDEX = process.env.PINECONE_INDEX as string;
const AUTH0_AUDIENCE = process.env.AUTH0_AUDIENCE as string;
const AUTH0_DOMAIN = process.env.AUTH0_DOMAIN as string;


// Pinecone keys
const TANA_NAMESPACE = "tana-namespace";
const TANA_INDEX = "tana-helper";
const TANA_TYPE = "tana_type";

// create our web server
const app = express();

// turn on logging via winston
// more options here - https://github.com/bithavoc/express-winston#request-logging
app.use(expressWinston.logger({
  transports: [
    new winston.transports.Console()
  ],
  format: winston.format.combine(
    winston.format.colorize(),
    winston.format.json()
  ),
  meta: false,
  msg: "HTTP  ",
  expressFormat: true,
  colorize: false,
  ignoreRoute: function (req, res) { return false; }
}));

// API security middleware
app.use(helmet());

// Configure CORS for localhost access
const corsOptions = {
  origin: '*',
  methods: ['GET', 'POST'],
};

// activate CORES middleware
app.use(cors(corsOptions));

// assume JSON in all cases
app.use(bodyParser.json({ type: ['text/plain', 'application/json'] }));

//app.use(bodyParser.text({ type: 'text/plain' }));


// connect to Pinecone
const pinecone = new PineconeClient();
await pinecone.init({
  environment: PINECONE_ENVIRONMENT,
  apiKey: PINECONE_API_KEY,
});

// Middleware to accept only connections from localhost
// app.use((req:Request, res:Response, next: NextFunction) => {
//   if (req.hostname === 'localhost' || req.hostname === '127.0.0.1') {
//     next();
//   } else {
//     res.status(403).send('Forbidden');
//   }
// });

// unauthenticated health check endpoint
// keeps Vercel happy
app.get('/', (req:Request, res:Response) => {
  res.send({ success: true, message: "It is working" });
});

// secure the endpoints before declaring them
const secret = jwksRsa.expressJwtSecret({
  cache: true,
  rateLimit: true,
  jwksRequestsPerMinute: 5,
  jwksUri: `https://${AUTH0_DOMAIN}/.well-known/jwks.json`
}) as GetVerificationKey;

const checkJwt = expressjwt({
  secret: secret,
  // Validate the audience and the issuer.
  audience: AUTH0_AUDIENCE,
  issuer: `https://${AUTH0_DOMAIN}/`,
  algorithms: ['RS256']
});

// secure the endpoints
app.use(checkJwt);


// helper functions for working with payloads
// and OpenAI embeddings
async function getOpenAiEmbedding(text:string): Promise<any> {
  const response = await axios.post(
    'https://api.openai.com/v1/embeddings',
    { model: 'text-embedding-ada-002', 
      input: text },
    { headers: { 'Authorization': `Bearer ${OPENAI_API_KEY}` } }
  );
  return response.data;
}

function paramsFromPayload(req:Request) {
  console.log(req.body);
  const node_id = req.body.nodeId;  // what if empty? Barf...
  const threshold = req.body.score ?? 0.80; // default to 0.8
  const top = req.body.top ?? 10; // default to top 10
  const context = req.body.context ?? "";  // not always present
  const supertags = ["#task"]; // TODO: get supertags passed from Tana

  return { context, threshold, top, node_id, supertags };
}


// UPSERT an embedding by Tana node_id
app.post('/upsert', async (req:Request, res:Response) => {
  
  const { context, node_id, supertags} = paramsFromPayload(req);
  const embedding = await getOpenAiEmbedding(context);
  
  // convert embedding to pinecode upsert
  const upsertRequest = {
    namespace: TANA_NAMESPACE,
    vectors: [
      {
        id: node_id,
        metadata: {
          category: TANA_TYPE,
          supertag: supertags,
        },
        values: embedding.data[0].embedding,
      }
    ],
  };

  const index = pinecone.Index(TANA_INDEX);

  await index.upsert({upsertRequest});
  
  console.log(`Upserted document with ID: ${node_id}`);
  res.status(200).send();
});


// DELETE an embedding by Tana node_id
app.post('/delete', async (req:Request, res:Response) => {
  
  const { node_id } = paramsFromPayload(req);
  const index = pinecone.Index(TANA_INDEX);
 
  const deleteRequest = {
    namespace: TANA_NAMESPACE,
    ids: [ node_id ]
  };

  await index.delete1(deleteRequest);

  console.log(`Deleted document with ID: ${node_id}`);
  res.status(200).send();
});


// QUERY embeddings by comparative embedding
// returns: Tana paste formatted node references
app.post('/query', async (req:Request, res:Response) => {
  const { context, threshold, top, supertags } = paramsFromPayload(req);
  const embedding = await getOpenAiEmbedding(context);

  const index = pinecone.Index(TANA_INDEX);

  const queryRequest = {
    namespace: TANA_NAMESPACE,
    vector: embedding.data[0].embedding,
    topK: top,
    includeValues: true,
    includeMetadata: true,
    filter: {
      category: TANA_TYPE,
      supertag: { $in: supertags },
    }
  };

  const query_response = await index.query({queryRequest});
  const best = query_response.matches?.filter((value, index, results) => { 
      const score = value?.score ?? 0;
      if (score > threshold) {
        console.log(`Matching score ${score} > ${threshold}`);
        return value;
      }
      else {
        console.log(`Low score: ${score} < ${threshold}`);
      }
    });
  const documentIds:string[] | undefined = best?.map((match:any) => match.id as string);

  // convert documentIds back to Tana paste format as refs
  let tanaPasteFormat = "";
  if (best?.length == 0) {
    tanaPasteFormat = "No sufficiently well-scored results"
  }
  else {
    for (let node of documentIds ?? []) {
      tanaPasteFormat += "- [[^" + node + "]]\n";
    }
  }

  res.status(200).send(tanaPasteFormat);
});

app.listen(PORT, 'localhost', () => {
  console.log(`Server is listening on http://localhost:${PORT}`);
});


export default app;
