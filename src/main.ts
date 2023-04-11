import express, { NextFunction, Request, Response } from "express";
import bodyParser from "body-parser";
import axios from "axios";
import { PineconeClient, QueryRequest } from "@pinecone-database/pinecone";
import { config as dotenvConfig } from 'dotenv';
import { QueryResponse, UpsertOperationRequest, UpsertRequest } from "@pinecone-database/pinecone/dist/pinecone-generated-ts-fetch";
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
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


const app = express();

// API security middleware
app.use(helmet());

// Configure CORS for localhost access
const corsOptions = {
  origin: '*',
  methods: ['GET', 'POST'],
};

// activate CORES middleware
app.use(cors(corsOptions));

// adding morgan for HTTP logging
app.use(morgan('combined'));

// for the occasional JSON response
app.use(bodyParser.json());

app.use(bodyParser.text({ type: 'text/plain' }));

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

// unauthenticated helath check endpoint
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

app.use(checkJwt);

async function getOpenAiEmbedding(text:string): Promise<any> {
  const response = await axios.post(
    'https://api.openai.com/v1/embeddings',
    { model: 'text-embedding-ada-002', 
      input: text },
    { headers: { 'Authorization': `Bearer ${OPENAI_API_KEY}` } }
  );
  return response.data;
}



app.post('/upsert', async (req:Request, res:Response) => {
  const lines:string[] = req.body.split(/\r?\n/);

  // strip first line as tana node ID
  // const tana_node_id = `doc-${Date.now()}`;
  const tana_node_id = lines[0].trim();
  const text = lines.slice(1).reduce((result, next) => {return result + next + '\n'})
  const embedding = await getOpenAiEmbedding(text);
  
  // TODO: extract tana node id from text
  const tana_supertag = "#task";

  // TODO: convert embedding to pinecode upsert
  const upsertRequest = {
    namespace: "tana-namespace",
    vectors: [
      {
        id: tana_node_id,
        metadata: {
          category: "tana_type",
          supertag: tana_supertag,
        },
        values: embedding.data[0].embedding,
      }
    ],
  };

  const index = pinecone.Index("tana-helper");

  const upsert_result = await index.upsert({upsertRequest});
  res.status(200).send(`Upserted document with ID: ${tana_node_id}`);
});

app.post('/query', async (req:Request, res:Response) => {
  const text = req.body;
  const embedding = await getOpenAiEmbedding(text);

  const index = pinecone.Index("tana-helper");

  const queryRequest = {
    namespace: "tana-namespace",
    vector: embedding.data[0].embedding,
    topK: 10,
    includeValues: true,
    includeMetadata: true,
  };

  const query_response = await index.query({queryRequest});
  const documentIds:string[] | undefined = query_response.matches?.map((match:any) => match.id as string);

  // TODO: convert documentIds to Tan apaste format
  let tanaPasteFormat = "%%tana%%\n- Results from Pinecone\n";
  for (let node of documentIds ?? []) {
    tanaPasteFormat += "  - [[^"+node+"]]\n";
  }

  res.status(200).send(tanaPasteFormat);
});

app.listen(PORT, 'localhost', () => {
  console.log(`Server is listening on http://localhost:${PORT}`);
});


export default app;