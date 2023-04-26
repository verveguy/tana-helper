import { app, baseUrl } from "./server.js";
import { Request, Response } from "express";


app.get('/usage', (req: Request, res: Response) => {
  const usage =
    `
- Pinecone Experiments
  - What is this?
    - These commands take Tana nodes (+context) and add them to the Pinecone vector database. This is done by first passing them to OpenAI to generate an embedding (a vector with 1536 dimensions). This vector is then inserted into Pinecone with the Tana nodeId as the key.
    - Pinecone allows us to then query for "similar nodes", each with a "score" relative to our query. The query is also just a Tana node, converted into an embedding by OpenAI. The richer the query, the better the vector search should be in theory.
    - Importantly, this is not ChatGPT-style "completions". It's a form of search for your own Tana content. It won't find (or generate) things you don't already know. 
    - API URLs
      - BaseURL: ${baseUrl}
  - Pinecone Commands
    - Update Pinecone embedding #command
      - Make API request
        - **Associated data**
          - Avoid using proxy:: [X] 
          - API method:: POST
          - URL:: ${baseUrl}/pinecone/upsert
          - Parse result:: Disregard (don't insert)
          - Payload:: 
            - { 
              - "pinecone": "\${secret:Pinecone}",
              - "openai": "\${secret:OpenAI}",
              - "nodeId": "\${sys:nodeId}",  
              - "tags": "\${sys:tags}", 
              - "context": "\${sys:context}"  
            - }
    - Query Pinecone embedding #command
      - Make API request
        - **Associated data**
          - Avoid using proxy:: [X] 
          - API method:: POST
          - URL:: ${baseUrl}/pinecone/query
          - Parse result:: Tana Paste (default)
          - Payload:: 
            - {
              - "pinecone": "\${secret:Pinecone}",
              - "openai": "\${secret:OpenAI}",
              - "nodeId": "\${sys:nodeId}",
              - "tags": "\${sys:tags}",
              - "score": "0.78",
              - "context": "\${sys:context}"
            - }
    - Remove Pinecone embedding #command
      - Make API request
        - **Associated data**
          - Avoid using proxy:: [X] 
          - Parse result:: Disregard (don't insert)
          - URL:: ${baseUrl}/pinecone/delete
          - Payload:: 
            - {
              - "pinecone": "\${secret:Pinecone}",
              - "openai": "\${secret:OpenAI}",
              - "nodeId": "\${sys:nodeId}",
            - }
          - API method:: POST
  - Calendar commands
    - Get Calendar #command
      - Make API request
        - **Associated data**
          - Avoid using proxy:: [X] 
          - Parse result:: Disregard (don't insert)
          - URL:: ${baseUrl}/pinecone/delete
          - Payload:: 
            - {
              - "pinecone": "\${secret:Pinecone}",
              - "openai": "\${secret:OpenAI}",
              - "nodeId": "\${sys:nodeId}",
            - }
          - API method:: POST
  `;

  res.send(usage);
});
