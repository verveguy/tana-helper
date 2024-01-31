from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from service.tana_types import NodeDump, TanaDump, Visualizer
from service.tanaparser import NodeIndex
from logging import getLogger
import re

router = APIRouter()

logger = getLogger()

class Link(BaseModel):
  source: str
  target: str
  reason: str

class RenderNode(BaseModel):
  id: str
  name: Optional[str]
  color: Optional[str] = None

class DirectedGraph(BaseModel):
  directed: bool = False
  multigraph: bool = False
  nodes: List[RenderNode] = []
  links: List[Link] = []


# capture a link if both nodes are in the index
def add_linkage(index:NodeIndex, links:List, source_id:str, target_id:str, reason="unknown"):
  if index.valid(source_id) and index.valid(target_id):
    link = Link(source=source_id, target=target_id, reason=reason)
    links.append(link)

# expand inline refs in node names
def patch_node_name(index:NodeIndex, node:NodeDump):
  # replace <span .. inline refs with actual node names
  # this is to facilitate full text search of the graph
  def subfunc(matchobj):
    ref_id = matchobj.group(1)
    if index.valid(ref_id):
      frag = index.node(ref_id).props.name
      return f'[[{frag}]]'
    return ref_id

  name = node.props.name
  if name and '<span' in name:
    name = re.sub('<span data-inlineref-node="([^"]*)"></span>', subfunc, name)
  return name


@router.post("/class_diagram", tags=["Visualizer"])
async def class_diagram(tana_dump:TanaDump):

  links = []  # final results we build into

  # we just want the class heirarchy
  config = Visualizer(include_content_nodes=False, 
                      include_inline_refs=False,
                      include_tag_tag_links=True,
                      include_node_tag_links=False,
                      include_inline_ref_nodes=False)

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
    new_name = patch_node_name(index, node)
    render_node = RenderNode(id=node.id, name=new_name, color=node.color)
    graph.nodes.append(render_node)

  return graph

