from fastapi import APIRouter, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Annotated
from pydantic import BaseModel
import pinecone
import openai
from typing import Optional, Type

from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.vectorstores import Pinecone
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.agents import load_tools, initialize_agent, AgentType
from langchain.utilities.serpapi import SerpAPIWrapper
from langchain.agents.react.base import DocstoreExplorer
from langchain import Wikipedia
from langchain.agents import Tool
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.callbacks import AimCallbackHandler, StdOutCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.schema import OutputParserException
from langchain.tools import BaseTool, tool
from langchain.chains.qa_with_sources import load_qa_with_sources_chain

from .pinecone import get_tana_nodes_for_query

from ..dependencies import *


router = APIRouter()

#@router.post('/ask')
@router.post('/ask', response_class=HTMLResponse)
async def ask(req: ChainsRequest):

  def tana_pinecone_run(query:str):
    req_dict = req.dict()
    req_dict['nodeId'] = ""
    pinecone_req = PineconeRequest.parse_obj(req_dict)
    pinecone_req.context = query
    results = get_tana_nodes_for_query(pinecone_req, True)
    return results
 
  class TanaPineconeTool(BaseTool):
    """Tool that adds the capability to query Pinecone for Tana nodes"""
    name = "tana_pinecone"
    description = (
       "This tool searches your Tana knowledgebase for notes that match a question. "
       "Useful for when you need to answer questions based on your existing knowledge. "
       "Each note in Tana has a unique NOTE ID formatted as [[^id]]. "
       "When you use this tool to search your Tana knowledgebase, it will return an array of one or more Tana notes in JSON format. Each note will have the text of the note as the 'answer' property and will also have the Tana NOTE ID as the 'sources' property . "
       "Your Final Answer should always include the Tana NOTES IDs you have referenced as your SOURCES."
    )

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
      result = tana_pinecone_run(query)
      return result

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
      """Use the tool asynchronously."""
      raise NotImplementedError("TanPineconeTool does not support async") 

  aim_callback = AimCallbackHandler(
    repo=".",
    experiment_name="Q:" + req.context,
  )

  callbacks = [StdOutCallbackHandler(), aim_callback]

  # completion llm
  llm = ChatOpenAI(
      openai_api_key=req.openai,
      model_name=req.model,
      temperature=0.0,
      verbose=True,
      callbacks=callbacks
  )

  tools = load_tools(
    [
        "serpapi",
        "llm-math", 
        "python_repl", 
        #"requests_all",
        "wikipedia", 
        "wolfram-alpha",
    ],
    llm=llm,
    wolfram_alpha_appid=req.wolfram,
    serpapi_api_key=req.serpapi,
    callbacks=callbacks
  )

  # now add our additional custom tools
  tana_pinecone = TanaPineconeTool()

  tools.extend([tana_pinecone, 
              ])

  agent = initialize_agent(
    agent="zero-shot-react-description", 
    tools=tools, 
    llm=llm,
    verbose=True,
    max_iterations=req.iterations,
    callbacks=callbacks
  )

  
  formatted_question = (
      f"The current date and time is: {get_date()}. The user's question is: {req.context} "
      "I should check to see if I know the answer before using other tools. "
      "My Final Answer should ALWAYS include the any Note IDs or websites I have consulted as my SOURCES."
      "If my next Action is None, I should try to come up with a new Thought."
  )

  aim_callback.flush_tracker(langchain_asset=agent, reset=False, finish=True)

  # this is a silly way to handle the error
  try:
      response = agent.run(formatted_question)
  except OutputParserException as e:
      response = str(e)
      if not response.startswith("Could not parse LLM output: `"):
          raise e
      response = response.removeprefix("Could not parse LLM output: `").removesuffix("`")

  return response


