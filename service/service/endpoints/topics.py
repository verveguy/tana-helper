from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from service.tana_types import NodeDump, TanaDump, Visualizer
from service.tanaparser import IS_CHILD_CONTENT_LINK, IS_TAG_LINK, NodeIndex
from logging import getLogger
import re

router = APIRouter()

logger = getLogger()

class Link(BaseModel):
  source: str
  target: str
  reason: str

class TanaField(BaseModel):
  id: str
  name: str
  value: str
  tag_id: str = ''

class TanaTag(BaseModel):
  id: str
  name: str
  description: Optional[str]
  color: Optional[str]

class TanaDocument(BaseModel):
  id: str # the tana node id
  name: Optional[str]
  description: Optional[str]
  tags: List[str] = []
  fields: List[TanaField] = []
  content: str = ''

class DocumentDump(BaseModel):
  documents: List[TanaDocument] = []
  tags: List[TanaTag] = [] 
  links: List[Link] = []


# capture a link if both nodes are in the index
def add_linkage(index:NodeIndex, links:List, source_id:str, target_id:str, reason="unknown"):
  if index.valid(source_id) and index.valid(target_id):
    link = Link(source=source_id, target=target_id, reason=reason)
    links.append(link)

# expand inline refs in node names
def patch_node_name(index:NodeIndex, node_id:str) -> str:
  # replace <span .. inline refs with actual node names
  # this is to facilitate full text search of the graph
  def subfunc(matchobj):
    ref_id = matchobj.group(1)
    if index.valid(ref_id):
      frag = index.node(ref_id).props.name
      return f'[[{frag}^{ref_id}]]'
    return ref_id

  name = index.node(node_id).props.name
  if name and '<span' in name:
      name = re.sub('<span data-inlineref-node="([^"]*)"></span>', subfunc, name)
  return name


@router.post("/topics", tags=["Extractor"])
async def topics(tana_dump:TanaDump):

  # we just want top level tagged nodes and their child contents
  config = Visualizer(include_content_nodes=True, 
                      include_inline_refs=False,
                      include_tag_tag_links=False,
                      include_node_tag_links=True,
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


  # start from the top 
  # find pairs that are tagged nodes only
  # and collect these into the initial list
  # gathering content along the way
  topics = {}
  for (source_id, target_id, reason) in final_pairs:
    if reason == IS_TAG_LINK:
      node = index.node(source_id)
      topic = TanaDocument(id=source_id, 
                          name=patch_node_name(index, source_id),
                          description=node.props.description,
                          )
      
      topics[source_id] = topic

      # add all the tag names
      for tag_id in node.tags:
        topic.tags.append(index.node(tag_id).props.name)

      # add all the field names and values
      for field_id in node.fields:
        field = TanaField(id=field_id, 
                          name=index.node(field_id).props.name,
                          value='unknown'
                          )
        topic.fields.append(field)

      # recursively build up content
      topic.content = recurse_content(index, source_id)

  return topics

def recurse_content(index:NodeIndex, node_id:str, depth_limit=10) -> str:
  content_node = index.node(node_id)
  content = patch_node_name(index, node_id)
  for content_id in content_node.content:
    depth_limit = depth_limit - 1
    if depth_limit > 0:
      content = content + '\n' + recurse_content(index, content_id, depth_limit)
  return content
