from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from service.tana_types import GraphLink, NodeDump, TanaDump, TanaTag, Visualizer
from service.tanaparser import IS_TAG_SCHEMA_LINK, NodeIndex, add_linkage, patch_node_name
from logging import getLogger
import re

router = APIRouter()

logger = getLogger()

class ClassGraph(BaseModel):
  directed: bool = False
  multigraph: bool = False
  nodes: List[TanaTag] = []
  links: List[GraphLink] = []

@router.post("/class_diagram", tags=["Visualizer"])
async def class_diagram(tana_dump:TanaDump):

  links = []  # final results we build into

  # we just want the class heirarchy
  config = Visualizer(include_content_nodes=False, 
                      include_inline_refs=False,
                      include_tag_tag_links=True,
                      include_node_tag_links=False,
                      include_inline_ref_nodes=False,
                      include_tag_schema_links=True)

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
  graph = ClassGraph()

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
    render_node = TanaTag(id=node.id, name=new_name, color=node.color)
    graph.nodes.append(render_node)

  return graph


@router.post("/mermaid_classes", response_class=HTMLResponse, tags=["Visualizer"])
async def mermaid_classes(tana_dump:TanaDump):
  graph = await class_diagram(tana_dump)
  # convert graph to mermaid format class diagram
  mermaid = \
    "---\n" +\
    "title: Tana Tag Diagram\n" +\
    '---\n'
  
  mermaid += "classDiagram\n"
  mermaid += "    direction RL\n"
  schema_node = None

  for link in graph.links:
    if link.reason != IS_TAG_SCHEMA_LINK:
      mermaid += f'    {link.target} <|-- {link.source} \n\n'
    else:
      # make a note of the schema node so we can omit it
      schema_node = link.target

  for node in graph.nodes:
    if node.id == schema_node:
      continue
    if node.name:
      encoded_name = node.name.replace('"', "#quot;")
      mermaid += f'    class {node.id}["{encoded_name}"]' + ' {\n'
      # TODO: add all fields of the tag here
      mermaid += "    }\n"
  
      
  mermaid += "\n"

  return mermaid