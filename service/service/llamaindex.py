import math
from functools import lru_cache
from logging import getLogger

from typing import List, Dict, Any, Optional
from pydantic import Field, validator

# Phoenix can display in real time the traces automatically
# collected from your LlamaIndex application.

# This is here to satisfy runtime import needs 
# that pyinstaller appears to miss

from llama_index.utils import truncate_text

from llama_index.schema import BaseNode, TextNode, NodeRelationship, NodeRelationship, NodeWithScore, QueryBundle
from llama_index.callbacks import CallbackManager, LlamaDebugHandler, OpenInferenceCallbackHandler
from llama_index.embeddings import OpenAIEmbedding, OllamaEmbedding
from llama_index.query_pipeline import QueryPipeline
from llama_index.llms import OpenAI, Ollama
from llama_index.llms.base import BaseLLM
from llama_index.vector_stores.types import VectorStore
from llama_index.vector_stores.chroma import ChromaVectorStore, _to_chroma_filter
from llama_index import PromptTemplate, VectorStoreIndex, StorageContext, ServiceContext
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from llama_index import ServiceContext
from llama_index.query_pipeline import CustomQueryComponent
from llama_index.postprocessor.types import BaseNodePostprocessor
from llama_index.vector_stores.types import BasePydanticVectorStore, VectorStoreQuery, VectorStoreQueryResult
from llama_index.vector_stores.utils import (
  legacy_metadata_dict_to_node,
  metadata_dict_to_node,
  node_to_metadata_dict,
)

from service.endpoints.chroma import get_collection, get_tana_nodes_by_id
from service.endpoints.topics import tana_node_ids_from_text


logger = getLogger()

minutes = 1000 * 60

@lru_cache() # reuse connection to chroma
def get_chroma_vector_store():
  chroma_collection = get_collection()
  vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
  logger.info("Llamaindex (chroma) vector store ready")
  return vector_store

# use this to ease switching backends
def get_vector_store():
  return get_chroma_vector_store()


openai_model = "gpt-4-1106-preview"

# get the LLM 
@lru_cache() # reuse connection to ollama
def get_llm(model:str="openai", debug=False, observe=False):
  if model == "openai":
    # TODO: also allow which openAI model to be parameterized?
    llm = OpenAI(model=openai_model, request_timeout=(5 * minutes), temperature=0)
    embed_model = OpenAIEmbedding(embed_batch_size=250)
  else:
    # assume the model is via ollama
    # TODO: try catch errors here
    llm = Ollama(model=model, request_timeout=(5 * minutes))
    embed_model = OllamaEmbedding(model_name=model, embed_batch_size=250)
  
  callback_managers = []

  if observe:
    callback_managers += [OpenInferenceCallbackHandler()]

  if debug:
    callback_managers += [LlamaDebugHandler(print_trace_on_end=True)]
  
  # llm_predictor=LLMPredictor(llm=llm)

  service_context = ServiceContext.from_defaults(llm=llm,
                                                 embed_model=embed_model, # or 'local'
                                                 callback_manager=CallbackManager(callback_managers)
                                                )
  logger.info(f'Llamaindex {model} service context ready')
  return service_context, llm

@lru_cache() # reuse connection to llama_index
def get_index(model:str, observe=False):
  vector_store = get_vector_store()
  service_context, llm = get_llm(model, observe=observe)

  # create a storage context to load our index from
  storage_context = StorageContext.from_defaults(vector_store=vector_store)
  logger.info("Llamaindex storage context ready")

  # load the index from the vector store
  index = VectorStoreIndex.from_vector_store(vector_store=vector_store, service_context=service_context, storage_context=storage_context) # type: ignore
  logger.info("Connected to Llamaindex")
  return index, service_context, storage_context, llm


def create_index(model, observe, index_nodes):
  vector_store = get_vector_store()

  # create a storage context in order to create a new index
  storage_context = StorageContext.from_defaults(vector_store=vector_store)
  logger.info("Llamaindex storage context ready")

  # initialize the LLM.
  # TODO: how to allow this to be parameterized?
  (service_context, _) = get_llm(model=model, observe=observe)

  # create the index; this will embed the documents and nodes and store them in the vector store
  # TODO: ensure we are upserting by topic id, otherwise we will have duplicates
  # and will have to drop the index first
  # TODO: consider whether we should add documents only, and use the loader (transformation) 
  # pipeline support to have those expanded into nodes as it goes...
  # This appears to populate any underlying docstore at the same time.
  # However, it's unclear how nodes get related to documents internally
  # for the purpose of updating nodes later.
  index = VectorStoreIndex(index_nodes, service_context=service_context, storage_context=storage_context)
  return index


def get_node(vector_store: VectorStore, node_id: str) -> BaseNode:
  """Get node from vector store."""
  result = chroma_vector_store_get(vector_store, [node_id] ) 
  if result.nodes:
    node = result.nodes[0]
    if not isinstance(node, BaseNode):
      raise ValueError(f"Node {node_id} is not a Node.")
    return node
  else:
    raise ValueError(f"Can't find node {node_id} in vector store.")


def get_forward_nodes(
  node_with_score: NodeWithScore, num_nodes: int, vector_store: VectorStore
) -> Dict[str, NodeWithScore]:
  """Get forward nodes."""
  node = node_with_score.node
  nodes: Dict[str, NodeWithScore] = {node.node_id: node_with_score}
  cur_count = 0
  # get forward nodes in an iterative manner
  while cur_count < num_nodes:
    if NodeRelationship.NEXT not in node.relationships:
      break

    next_node_info = node.next_node
    if next_node_info is None:
      break

    next_node_id = next_node_info.node_id
    next_node = get_node(vector_store, next_node_id)
    nodes[next_node.node_id] = NodeWithScore(node=next_node)
    node = next_node
    cur_count += 1
  return nodes


def get_backwards_nodes(
  node_with_score: NodeWithScore, num_nodes: int, vector_store: VectorStore
  ) -> Dict[str, NodeWithScore]:
  """Get backward nodes."""
  node = node_with_score.node
  # get backward nodes in an iterative manner
  nodes: Dict[str, NodeWithScore] = {node.node_id: node_with_score}
  cur_count = 0
  while cur_count < num_nodes:
    prev_node_info = node.prev_node
    if prev_node_info is None:
        break
    prev_node_id = prev_node_info.node_id
    prev_node = get_node(vector_store, prev_node_id)
    if prev_node is None:
        break
    nodes[prev_node.node_id] = NodeWithScore(node=prev_node)
    node = prev_node
    cur_count += 1
  return nodes


class WidenNodeWindowPostProcessor(BaseNodePostprocessor):
  """WidenNodeWindow Node post-processor.

  Fetches additional nodes from the vector store,
  based on the relationships of the nodes.

  Args:
    vector_store (BaseVectorStroe): The vector store.
    num_nodes (int): The number of nodes to return (default: 1)
    mode (str): The mode of the post-processor.
      Can be "previous", "next", or "both.

  """

  storage_context: StorageContext
  num_nodes: int = Field(default=1)
  mode: str = Field(default="next")

  @validator("mode")
  def _validate_mode(cls, v: str) -> str:
    """Validate mode."""
    if v not in ["next", "previous", "both"]:
        raise ValueError(f"Invalid mode: {v}")
    return v

  @classmethod
  def class_name(cls) -> str:
    return "WidenNodeWindowPostProcessor"

  def _postprocess_nodes(
    self,
    nodes: List[NodeWithScore],
    query_bundle: Optional[QueryBundle] = None,
  ) -> List[NodeWithScore]:
    """Postprocess nodes."""
    all_nodes: Dict[str, NodeWithScore] = {}
    for node in nodes:
      all_nodes[node.node.node_id] = node
      if self.mode == "next":
        all_nodes.update(get_forward_nodes(node, self.num_nodes, self.storage_context.vector_store))
      elif self.mode == "previous":
        all_nodes.update(
          get_backwards_nodes(node, self.num_nodes, self.storage_context.vector_store)
        )
      elif self.mode == "both":
        all_nodes.update(get_forward_nodes(node, self.num_nodes, self.storage_context.vector_store))
        all_nodes.update(
          get_backwards_nodes(node, self.num_nodes, self.storage_context.vector_store)
        )
      else:
        raise ValueError(f"Invalid mode: {self.mode}")

    all_nodes_values: List[NodeWithScore] = list(all_nodes.values())
    sorted_nodes: List[NodeWithScore] = []
    for node in all_nodes_values:
      # variable to check if cand node is inserted
      node_inserted = False
      for i, cand in enumerate(sorted_nodes):
        node_id = node.node.node_id
        # prepend to current candidate
        prev_node_info = cand.node.prev_node
        next_node_info = cand.node.next_node
        if prev_node_info is not None and node_id == prev_node_info.node_id:
          node_inserted = True
          sorted_nodes.insert(i, node)
          break
        # append to current candidate
        elif next_node_info is not None and node_id == next_node_info.node_id:
          node_inserted = True
          sorted_nodes.insert(i + 1, node)
          break

      if not node_inserted:
        sorted_nodes.append(node)

    return sorted_nodes


class DecomposeQueryWithNodeContext(CustomQueryComponent):
  """Referenced nodes component."""

  llm: BaseLLM = Field(..., description="OpenAI LLM")

  def _validate_component_inputs(
    self, input: Dict[str, Any]
  ) -> Dict[str, Any]:
    """Validate component inputs during run_component."""
    # NOTE: this is OPTIONAL but we show you here how to do validation as an example
    return input

  @property
  def _input_keys(self) -> set:
    """Input keys dict."""
    # NOTE: These are required inputs. If you have optional inputs please override
    # `optional_input_keys_dict`
    return {"query"}

  @property
  def _output_keys(self) -> set:
    return {"questions"}

  def _run_component(self, **kwargs) -> Dict[str, Any]:
    """Run the component."""
    # first get all the Tana nodes from the query context
    tana_nodes = tana_node_ids_from_text(kwargs["query"])
    context = '\n'.join(get_tana_nodes_by_id(tana_nodes))

    # use QueryPipeline itself here for convenience
    prompt_tmpl = PromptTemplate(
      "You are an expert Q&A system that is trusted around the world.\n"
      "You have access to a body of notes on various topics, meetings, etc.\n"
      "Your TASK is to propose a number of specific research QUESTIONS that would help to answer the question posed.\n"
      "The QUESTIONS should be optimized for a semantic similarity search.\n"
      "Only respond with the QUESTIONS themselves. Do not add any extraneous comments.\n"
      "Each question should be numbered and on a separate line.\n"
      "{query}\n"
      "Also use this initial information from the notebook to help shape the research questions:\n"
      "{nodes}\n"
      )
    p = QueryPipeline(chain=[prompt_tmpl, self.llm])
    response = p.run(query=kwargs["query"], nodes=context)
    questions = response.message.content
    
    return {"questions": questions.split('\n')}


def chroma_vector_store_get(vector_store:VectorStore, node_ids:List[str], **kwargs: Any) -> VectorStoreQueryResult:
  """Query index nodes by ID
  Args:
      node_ids (List[int]): node IDs
  """

  results = vector_store._collection.get( #type: ignore
    ids=node_ids,
    include=['metadatas', 'documents'],
    **kwargs,
  )

  logger.debug(f"> Got {len(results['documents'])} nodes:")
  nodes = []
  similarities = []
  ids = []
  for node_id, text, metadata in zip(
    results["ids"],
    results["documents"],
    results["metadatas"]
  ):
    try:
      node = metadata_dict_to_node(metadata)
      node.set_content(text)
    except Exception:
      # NOTE: deprecated legacy logic for backward compatibility
      metadata, node_info, relationships = legacy_metadata_dict_to_node(
          metadata
      )

      node = TextNode(
        text=text,
        id_=node_id,
        metadata=metadata,
        start_char_idx=node_info.get("start", None),
        end_char_idx=node_info.get("end", None),
        relationships=relationships,
      )

    nodes.append(node)

    similarities.append(1.0)

    logger.debug(
      f"> [Node {node_id}] "
      f"{truncate_text(str(text), 100)}"
    )
    ids.append(node_id)

  return VectorStoreQueryResult(nodes=nodes, similarities=similarities, ids=ids)
