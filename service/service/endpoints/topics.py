import re
from logging import getLogger
from typing import Optional, List, Tuple

from fastapi import APIRouter
from pydantic import BaseModel
from service.dependencies import TANA_NODE, TanaNodeMetadata

from service.tana_types import GraphLink, NodeDump, TanaDocument, TanaDump, TanaField, TanaTag, Visualizer
from service.tanaparser import IS_CHILD_CONTENT_LINK, IS_TAG_LINK, NodeIndex, patch_node_name, prune_reference_nodes

router = APIRouter()

logger = getLogger()

class DocumentDump(BaseModel):
  documents: List[TanaDocument] = []
  tags: List[TanaTag] = [] 
  links: List[GraphLink] = []


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
      topic_name = patch_node_name(index, source_id)
      topic = TanaDocument(id=source_id, 
                          name=topic_name,
                          description=node.props.description,
                          fields=[],
                          tags = tag_list(index, node.tags)
                          # content
                          )
      
      topics.append(topic)
      
      topic.content = [(source_id, False, '- '+topic_name)]

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
            topic.content.append((None, False, f"  - {field_name}:: {value_contents[0]}"))
            for value in value_contents[1:]:
              topic.content.append((None, False, f"    - {value}"))
          # and remove any structured fields
          topic.fields = None

      # recursively build up child content for "sentence splitting"
      topic.content += recurse_content(index, source_id)
      
  return topics

def indent(depth:int) -> str:
    return '  '*depth
  
def add_tags(index, tag_ids:List[str]) -> str:
  if len(tag_ids) > 0:
    tags = [''] # so we get an initial space
    tags.extend(tag_list(index, tag_ids))
    return ' '.join(tags)
  return ''

def tag_list(index, tag_ids) -> list[str]:
  tags = []
  for tag_id in tag_ids:
    tag_name = index.node(tag_id).props.name
    if ' ' in tag_name:
      tags.append(f'[[#{tag_name}]]')
    else:
      tags.append(f'#{tag_name}')
  return tags

def is_reference_content(name:str) -> Tuple[bool, str]:
  node_id = None
  
  is_ref = re.match(r'\s*-\s*\[\[.*\^\w+\]\]', name)
  if is_ref:
    match = re.match(r'\s*-\s*\[\[.*\^(\w+)\]\]', name)
    if match:
      node_id = match.group(1)

  return is_ref, node_id # type: ignore


def tana_node_ids_from_text(text:str) -> List[str]:
  results = re.findall(r'\[\[.*\^(\w+)\]\]', text)
  return results

# TODO: think about the way we want to represent the topic nodes
# for the purpose of RAG generation. Chunks, parents, sentences, etc.
# Headings are distinct nodes in Tana for example...
# Also think about whether content nodes should just be text or should
# themselves be richer nodes with fields and tags in the index

# TODO: now that we "prune" reference nodes, do we need depth_limit?

def recurse_content(index:NodeIndex, parent_id:str, depth_limit=10) -> list[tuple[str|None, bool, str]]:
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
        content.append((content_id, True, indent(11 - depth_limit)+'- [['+patch_node_name(index, content_id)+'^'+content_id+']]'+add_tags(index, content_node.tags)))
      else:
        # this is a regular text node, untagged and not a reference

        # TODO: decide what, if anything, to do with fields on such nodes
        
        # here we know the Tana nodeId of the child, so we capture it as content_id
        content.append((content_id, False, indent(11 - depth_limit)+'- '+patch_node_name(index, content_id)))
        if depth_limit > 0:
          content += recurse_content(index, content_id, depth_limit - 1)
    else:
      # this is a Tana reference link, so don't recurse
      content.append((content_id, True, indent(11 - depth_limit)+'- [['+patch_node_name(index, content_id)+'^'+content_id+']]'+add_tags(index, content_node.tags)))

  return content


def tags_from_name(name:str) -> List[str]:
  '''Extracts tags from a Tana node name'''
  tags = re.findall(r'#(?:\[\[)?([^,\]]*)(?:\]\])?', name)
  return tags

def extract_topic_from_context(tana_id:str, tana_context:str):
  '''Extracts a single TanaDocument object and TextNodes from a Tana context string'''
  
  # First, prune the content. We don't want to include the content of references nodes
  # since they will already be embedded directly from preloading

  # TODO: consider the case where they have NOT been embedded
  # and in fact should be embedded as distinct TanaDocument objects
  # (either as refresh of existing embeddings or as nodes not yet embedded)
  pruned_content = prune_reference_nodes(tana_context)
  name = pruned_content.split('\n')[0]

  # create a document with the whole (pruned) text blob as first [content] triple
  topic = TanaDocument(id=tana_id,
                      description=None,
                      fields=[],
                      tags=tags_from_name(name),
                      name=name
                      )
  
  topic.content = [(tana_id, False, '- '+name)]

  fields = []
  for line in pruned_content.split('\n'):
    if '::' in line:
      # extract fields from context
      field_name, value = line.split('::', 1)
      match = re.match(r'\s*-\s*(.*)', field_name)
      if match:
        field_name = match.group(1)
      value = value.strip()
      field = TanaField(field_id='', name=field_name, value_id='', value=value)
      (ref, ref_id) = is_reference_content(value)
      if ref:
        field.value_id = ref_id
      fields.append(field)
    else:
      # we've hit a content line, break it down for "sentence splitting"
      (ref, ref_id) = is_reference_content(line)
      if ref:
        topic.content.append((ref_id, True, line))
      else:
        # Unfortunately, we don't know the Tana node id of the child content
        # unlike in the preload case (where we build from full graph info)
        topic.content.append((None, False, line))

  
  topic.fields = fields

  return topic

