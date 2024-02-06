from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from service.tana_types import GraphLink, NodeDump, TanaDump, Visualizer
from service.tanaparser import NodeIndex, add_linkage, patch_node_name
from logging import getLogger
import re

router = APIRouter()

logger = getLogger()

class RenderNode(BaseModel):
  id: str
  name: Optional[str]
  color: Optional[str] = None

class DirectedGraph(BaseModel):
  directed: bool = False
  multigraph: bool = False
  nodes: List[RenderNode] = []
  links: List[GraphLink] = []


@router.post("/graph", tags=["Visualizer"])
async def graph(tana_dump:TanaDump):

  links = []  # final results we build into

  config = tana_dump.visualize
  if config is None:
    config = Visualizer()

  index = NodeIndex(tana_dump=tana_dump, config=config)

  # build our primary indices first, so we can easily navigate the dump
  index.build_indices()
  
  # OK, now that we have the basic dump indexed...
  # build a collection of meaningful linkages
  index.build_master_pairs()
 
  # Now that we have the dump converted to a set of directed 
  # tuples, we can build a graph from it.

  # strip the links down to the unique set
  candidate_pairs = set(index.master_pairs)
  final_pairs = set()

  # also remove redundant bidirectional links
  [final_pairs.add((a, b, r)) for (a, b, r) in candidate_pairs
    if (a, b, r) not in final_pairs and (b, a, r) not in final_pairs]

  # build links
  for pair in final_pairs:
    add_linkage(index, links, pair[0], pair[1], pair[2])

  # build the return structure...
  graph = DirectedGraph()

  count = 0
  node_ids = []

  # only include nodes that are linked
  for link in links:
    graph.links.append(link)
    node_ids.append(link.source)
    node_ids.append(link.target)
    count = count + 1
  
  node_ids = list(set(node_ids))
  for node_id in node_ids:
    node = index.node(node_id)
    # patch up node names
    new_name = patch_node_name(index, node_id)
    render_node = RenderNode(id=node.id, name=new_name, color=node.color)
    graph.nodes.append(render_node)


  return graph

