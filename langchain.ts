/*
    Experimenting with langchain.

    Port of the Simple Lanchain Tools example from replit.com

    https://replit.com/@BrettAdam/Simple-Langchain-Tools#main.py


*/

import { PineconeClient } from "@pinecone-database/pinecone";
import { Request, Response } from "express";
import { initializeAgentExecutorWithOptions } from "langchain/agents";
import { ConversationChain, RetrievalQAChain, StuffDocumentsChain, VectorDBQAChain, loadQAChain, loadQARefineChain } from "langchain/chains";
import { OpenAIEmbeddings } from "langchain/embeddings/openai";
import { OpenAI } from "langchain/llms/openai";
import { BufferMemory } from "langchain/memory";
import { ChainTool, SerpAPI } from "langchain/tools";
import { PineconeStore } from "langchain/vectorstores/pinecone";
import { LOCAL_SERVICE, app } from './server.js';
import { Calculator } from "langchain/tools/calculator";
import { WebBrowser } from "langchain/tools/webbrowser";


let OPENAI_API_KEY = process.env.OPENAI_API_KEY as string;
let PINECONE_API_KEY = process.env.PINECONE_API_KEY as string;

let OPENAI_EMBEDDING_MODEL = process.env.OPENAI_EMBEDDING_MODEL ?? "text-embedding-ada-002";
let PINECONE_ENVIRONMENT = process.env.PINECONE_ENVIRONMENT ?? "asia-southeast1-gcp";
let PINECONE_INDEX = process.env.PINECONE_INDEX ?? "tana-helper";

// Pinecone keys that are not configured
const TANA_NAMESPACE = "tana-namespace";
const TANA_TYPE = "tana_type";

let WOLFRAM_ALPHA_APP_ID = process.env.WOLFRAM_ALPHA_APP_ID as string;
let SERPAPI_API_KEY = process.env.SERPAPI_API_KEY as string;

if (OPENAI_EMBEDDING_MODEL === undefined
  || PINECONE_ENVIRONMENT === undefined
) {
  throw new Error("Missing OpenAI or Pinecone configuration. These keys are all required.");
}

//-------------------------
// helper functions

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

function paramsFromPayload(req: Request) {
  // debug log
  if (LOCAL_SERVICE) {
    console.log(req.body);
  }

  const temperature = req.body.temperature ?? 0.0; // default to 0.0
  const threshold = req.body.score ?? 0.80; // default to 0.8
  const context = req.body.context ?? ""; // not always present
  const top = req.body.top ?? 5; // not always present
  const supertags = req.body.tags == "" ? undefined : req.body.tags;
  const modelVersion = req.body.modelVersion ?? "gpt-4";
  const chat = req.body.chat ?? false;
  return { context, threshold, top, modelVersion, chat, temperature, supertags };
}

// TODO: Extract this to a util package
function getKeysFromPayload(req: Request) {
  OPENAI_API_KEY = req.body.openai ?? OPENAI_API_KEY;
  PINECONE_API_KEY = req.body.pinecone ?? PINECONE_API_KEY;

  OPENAI_EMBEDDING_MODEL = req.body.model ?? OPENAI_EMBEDDING_MODEL;
  PINECONE_ENVIRONMENT = req.body.environment ?? PINECONE_ENVIRONMENT;
  PINECONE_INDEX = req.body.index ?? PINECONE_INDEX;

  WOLFRAM_ALPHA_APP_ID = req.body.wolframAppID ?? WOLFRAM_ALPHA_APP_ID;
  SERPAPI_API_KEY = req.body.serpapi ?? SERPAPI_API_KEY;

  if (OPENAI_API_KEY === undefined || PINECONE_API_KEY === undefined) {
    throw new Error("Missing OpenAI and/or Pinecone API keys. These keys are all required.");
  }
}


//-------------------------
// API ENDPOINTS START HERE
// UPSERT an embedding by Tana node_id
app.post('/ask', async (req: Request, res: Response) => {

  getKeysFromPayload(req);

  const { context, modelVersion, supertags, top, temperature, chat } = paramsFromPayload(req);

  // TODO: how to specify ChatGPT 4?
  const model = new OpenAI({ openAIApiKey: OPENAI_API_KEY, temperature: temperature, modelName: modelVersion });
  const embeddings = new OpenAIEmbeddings({ openAIApiKey: OPENAI_API_KEY });

  // We make a series of small chains for various tools
  // the link them together into a "tool chain" for an agent to use

  // Make a Pinecone retriever chain
  const pinecone = await getPinecone();
  const pineconeIndex = pinecone.Index(PINECONE_INDEX);

  const vectorStore = await PineconeStore.fromExistingIndex(embeddings, { pineconeIndex });

  const vector_chain = RetrievalQAChain.fromLLM(model,
    vectorStore.asRetriever(), 
  );

  const vector_tool = new ChainTool({
    name: "pinecone",
    description: "Provides information from your Pinecone notebook. You should use this whenever possible to integrate your previous knowledge with new information. The best way to use your notebook is to ask it long form questions: the more detail in the question, the better the result should be.",
    chain: vector_chain,
  });

  // Serp Tool
  const serp_tool = new SerpAPI(SERPAPI_API_KEY, {
    location: "Austin,Texas,United States",
    hl: "en",
    gl: "us",
  });

  // Calculator tool

  const calc_tool = new Calculator();

  const web_browser_tool = new WebBrowser({ model, embeddings });

  // wolfram alpha tool? Python only?
  // const wolfram_tool = 

  const tools = [serp_tool, vector_tool, calc_tool, web_browser_tool];

  // TODO: figure out how to add memory and chat mode

  const executor = await initializeAgentExecutorWithOptions(tools, model, {
    agentType: "chat-zero-shot-react-description",
    verbose: true
  });

  const input = context;

  const result = await executor.call({ input });

  res.status(200).send(result);
});

