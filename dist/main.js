/*
    Simple API service that provides a form of "Semantic search" for
    Tana.

    ./upsert accepts Tana node data and creates
    embeddings via OpenAI to populate a Pinecone database.

    ./query accepts a Tana node context and returns a list of
    Tana node references in Tana paste format as a result.
    
    ./delete accepts a Tana node ID and removes the entry from the
    Pinecone database.

    TODO:

    Add ./purge to dump all records in the database.

*/
import express from "express";
import bodyParser from "body-parser";
import axios from "axios";
import { PineconeClient } from "@pinecone-database/pinecone";
import { config as dotenvConfig } from 'dotenv';
import cors from 'cors';
import helmet from 'helmet';
import winston from "winston";
import expressWinston from 'express-winston';
import { expressjwt } from "express-jwt";
import jwksRsa from "jwks-rsa";
// read .env to get our API keys
dotenvConfig();
const LOCAL_SERVICE = (process.env.LOCAL_SERVICE ?? false);
const PORT = (process.env.PORT ?? 4000);
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const OPENAI_EMBEDDING_MODEL = process.env.OPENAI_EMBEDDING_MODEL;
const PINECONE_API_KEY = process.env.PINECONE_API_KEY;
const PINECONE_ENVIRONMENT = process.env.PINECONE_ENVIRONMENT;
const PINECONE_INDEX = process.env.PINECONE_INDEX;
const AUTH0_AUDIENCE = process.env.AUTH0_AUDIENCE;
const AUTH0_DOMAIN = process.env.AUTH0_DOMAIN;
if (OPENAI_API_KEY === undefined
    || OPENAI_EMBEDDING_MODEL === undefined
    || PINECONE_API_KEY === undefined
    || PINECONE_ENVIRONMENT === undefined
    || PINECONE_INDEX === undefined) {
    throw new Error("Missing OpenAI or Pinecone configuration. These keys are all required.");
}
if (!LOCAL_SERVICE) {
    if (AUTH0_AUDIENCE === undefined
        || AUTH0_DOMAIN === undefined) {
        throw new Error("Missing Auth0 configuration. These keys are required when running as a hosted service.");
    }
}
// Localservice operation is configured differently. Notify such.
if (LOCAL_SERVICE) {
    console.log('Running as local service. No authentication required.');
}
// Pinecone keys that are not configured
const TANA_NAMESPACE = "tana-namespace";
const TANA_TYPE = "tana_type";
// create our web server
const app = express();
// turn on logging via winston
// more options here - https://github.com/bithavoc/express-winston#request-logging
app.use(expressWinston.logger({
    transports: [
        new winston.transports.Console()
    ],
    format: winston.format.combine(winston.format.colorize(), winston.format.json()),
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
    origin: 'https://app.tana.inc',
    methods: ['GET', 'POST'],
};
// activate CORS middleware
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
// keeps Vercel happy. Declare this before 
// adding 
app.get('/', (req, res) => {
    res.send({ success: true, message: "It is working" });
});
// If we are running in production, secure the endpoints 
// before declaring them using Auth0
// TODO: find simpler method to secure things
if (!LOCAL_SERVICE) {
    console.log('Enabling Auth0 authentication on API endpoints');
    const secret = jwksRsa.expressJwtSecret({
        cache: true,
        rateLimit: true,
        jwksRequestsPerMinute: 5,
        jwksUri: `https://${AUTH0_DOMAIN}/.well-known/jwks.json`
    });
    const checkJwt = expressjwt({
        secret: secret,
        // Validate the audience and the issuer.
        audience: AUTH0_AUDIENCE,
        issuer: `https://${AUTH0_DOMAIN}/`,
        algorithms: ['RS256']
    });
    // secure the endpoints
    app.use(checkJwt);
}
//-------------------------
// helper functions for working with payloads
// and OpenAI embeddings
async function getOpenAiEmbedding(text) {
    const response = await axios.post('https://api.openai.com/v1/embeddings', {
        model: `${OPENAI_EMBEDDING_MODEL}`,
        input: text
    }, { headers: { 'Authorization': `Bearer ${OPENAI_API_KEY}` } });
    return response.data;
}
function paramsFromPayload(req) {
    // debug log
    console.log(req.body);
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
//-------------------------
// API ENDPOINTS START HERE
// UPSERT an embedding by Tana node_id
app.post('/upsert', async (req, res) => {
    const { context, node_id, supertags } = paramsFromPayload(req);
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
    const index = pinecone.Index(PINECONE_INDEX);
    await index.upsert({ upsertRequest });
    console.log(`Upserted document with ID: ${node_id}`);
    res.status(200).send();
});
// DELETE an embedding by Tana node_id
app.post('/delete', async (req, res) => {
    const { node_id } = paramsFromPayload(req);
    const index = pinecone.Index(PINECONE_INDEX);
    const deleteRequest = {
        namespace: TANA_NAMESPACE,
        ids: [node_id]
    };
    await index.delete1(deleteRequest);
    console.log(`Deleted document with ID: ${node_id}`);
    res.status(200).send();
});
// QUERY embeddings by comparative embedding
// returns: Tana paste formatted node references
app.post('/query', async (req, res) => {
    const { context, threshold, top, supertags } = paramsFromPayload(req);
    const embedding = await getOpenAiEmbedding(context);
    const index = pinecone.Index(PINECONE_INDEX);
    const queryRequest = {
        namespace: TANA_NAMESPACE,
        vector: embedding.data[0].embedding,
        topK: top,
        includeValues: true,
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
    const query_response = await index.query({ queryRequest });
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
    const documentIds = best?.map((match) => match.id);
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
    console.log(tanaPasteFormat);
    res.status(200).send(tanaPasteFormat);
});
// PURGE to dump the database
// TODO: Implement this!
app.post('/purge', async (req, res) => {
    console.log(req.body);
    res.status(200).send("Not yet implemented");
});
// LOG so we can see the data in the log
app.post('/log', async (req, res) => {
    console.log(req.body);
    res.status(200).send();
});
app.listen(PORT, 'localhost', () => {
    console.log(`Server is listening on http://localhost:${PORT}`);
});
export default app;
//# sourceMappingURL=main.js.map