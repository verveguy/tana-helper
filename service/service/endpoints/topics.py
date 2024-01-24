import re
from logging import getLogger
from typing import Optional, List, Tuple

from fastapi import APIRouter
from pydantic import BaseModel

from service.tana_types import NodeDump, TanaDump, Visualizer
from service.tanaparser import IS_CHILD_CONTENT_LINK, IS_TAG_LINK, NodeIndex

router = APIRouter()

logger = getLogger()

class Link(BaseModel):
  source: str
  target: str
  reason: str

class TanaField(BaseModel):
  field_id: str
  name: str
  value_id: str
  value: str
  #tag_id: str = ''

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
  fields: Optional[List[TanaField]]
  # TODO: consider whether we should preserve more node structure here
  content: List[Tuple[str, int, str]] = []

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
async def extract_topics(tana_dump:TanaDump, format:str='TANA') -> List[TanaDocument]:
  '''Given a Tana dump JSON payload, return a list of topics and their content.

  Topics are defined as nodes that are tagged with a supertag.

  Uses the main Tana dump parsing code from the Visualizer, but then walks
  the resulting index to extract topics intended for use by RAG.

  See the RAG articles by Prince 
  '''

  
  # we just want top level tagged nodes and their child contents
  # TODO: figure out what we weant to do with fields
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
  master_pairs = index.build_master_pairs()
 
  # Now that we have the dump converted to a set of directed 
  # tuples, we can build a graph from it.

  # strip the links down to the unique set
  candidate_pairs = set(master_pairs)
  final_pairs = set()

  # also remove redundant bidirectional links
  [final_pairs.add((a, b, r)) for (a, b, r) in candidate_pairs
    if (a, b, r) not in final_pairs and (b, a, r) not in final_pairs]
  
  # start from the top and only
  # iterate nodes that are tagged. We call these "topics"
  # For each topic, we want the fields and tags of the node
  # We also want a flattened list of content nodes that are
  # direct children of the topic node. We call these "content"
  
  # remap the final pairs to a list of topics
  sources = set([(source_id, reason) for (source_id, _, reason) in final_pairs])
  topics = []
  for (source_id, reason) in sources:
    if reason == IS_TAG_LINK:
      node = index.node(source_id)
      topic_name = patch_node_name(index, source_id)+add_tags(index, node.tags)
      topic = TanaDocument(id=source_id, 
                          name=topic_name,
                          description=node.props.description,
                          fields=[]
                          )
      
      topics.append(topic)
      
      topic.content = [(source_id, 0, '- '+topic_name)]

      # add all the tag names as structured elems 
      for tag_id in node.tags:
        topic.tags.append(index.node(tag_id).props.name)

      # add all the field names and values
      for field_dict in node.fields:
        field_id = field_dict['field']
        field_name=index.node(field_id).props.name
        value_ids = field_dict['values']
                
        value_contents = []
        for value_id in value_ids:
          if not index.valid(value_id):
            logger.warning(f'Invalid field value_id: {value_id} for field: {field_id}. Presumably trashed node.')
            continue
          
          value_node = index.node(value_id)
          if len(value_node.tags) > 0:
            # if it's tagged, again assume it's a ref, not an inline content node
            value = '[['+patch_node_name(index, value_id)+'^'+value_id+']]'+add_tags(index, index.node(value_id).tags)
          else:
            value = patch_node_name(index, value_id)

          value_contents += [value]

          # so how do we want to represent fields?
          if format == 'JSON':
            # structure fields as metadata
            field = TanaField(field_id=field_id,
                              value_id=value_id,
                              name=index.node(field_id).props.name,
                              value=value)
          
            topic.fields.append(field) # type: ignore
        
        #TODO: redo all ths code to use field value_ids instead of ''
        if format == 'TANA':
          # structure fields in Tana paste format
          if len(value_contents) > 0 and len(value_contents[0]) > 0:
            topic.content += [('', 0,  f"  - {field_name}:: {value_contents[0]}")]
            for value in value_contents[1:]:
              topic.content += [('', 0, f"    - {value}")]
          # and remove any structured fields
          topic.fields = None

      # recursively build up child content
      topic.content += recurse_content(index, source_id)

  return topics

def indent(depth:int) -> str:
    return '  '*depth
  
def add_tags(index, tag_ids:List[str]) -> str:
  if len(tag_ids) > 0:
    tags = [''] # so we get an initial space
    for tag_id in tag_ids:
      tag_name = index.node(tag_id).props.name
      if ' ' in tag_name:
        tags += [f'[[#{tag_name}]]']
      else:
        tags += [f'#{tag_name}']
    return ' '.join(tags)
  return ''

def is_reference_content(name:str) -> Tuple[bool, str]:
  node_id = None
  
  is_ref = re.match(r'\[\[.*\^\w+\]\]', name)
  if is_ref:
    node_id = re.match(r'\[\[.*\^(\w+)\]\]', name).group(1) # type: ignore

  return is_ref, node_id # type: ignore


def node_ids_from_text(text:str) -> List[str]:
  results = re.findall(r'\[\[.*\^(\w+)\]\]', text)
  return results

# TODO: think about the way we want to represent the topic nodes
# for the purpose of RAG generation. Chunks, parents, sentences, etc.
# Headings are distinct nodes in Tana for example...
# Also think about whether content nodes should just be text or should
# themselves be richer nodes with fields and tags in the index
# TODO: what do we do about references to other nodes?
def recurse_content(index:NodeIndex, parent_id:str, depth_limit=10) -> List[Tuple[str, int, str]]:
  parent_node = index.node(parent_id)
  content = []

  for content_id in parent_node.content:
    content_node = index.node(content_id)
    reason = index.get_linkage_reason(parent_id, content_id)
    if reason is IS_CHILD_CONTENT_LINK:
      if len(content_node.tags) > 0:
        # this is a tagged topic in it's own right, don't recurse
        # and treat it like a referenced node. (Yes, this isn't Tana's way
        # but we want to reduce redundant content and Day nodes mess with this
        # concept rather badly)
        content.append((content_id, 1, indent(11 - depth_limit)+'- [['+patch_node_name(index, content_id)+'^'+content_id+']]'+add_tags(index, content_node.tags)))
      else:
        # this is a regular text node, untagged and not a reference
        # TODO: decide what, if anything, to do with fields on such nodes
        content.append((content_id, 0, indent(11 - depth_limit)+'- '+patch_node_name(index, content_id)))
        if depth_limit > 0:
          content += recurse_content(index, content_id, depth_limit - 1)
    else:
      # this is a Tana reference link, so don't recurse
      content.append((content_id, 1, indent(11 - depth_limit)+'- [['+patch_node_name(index, content_id)+'^'+content_id+']]'+add_tags(index, content_node.tags)))

  return content
