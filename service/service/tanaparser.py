import re
from pydantic import BaseModel
from typing import List
from service.tana_types import GraphLink, NodeDump, TanaDump, Visualizer
from itertools import combinations
from logging import getLogger

logger = getLogger()

FIELD='SYS_T02'
SUPERTAG='SYS_T01'
TAG='SYS_A13'
COLOR_SPEC='SYS_A11'
TRASH='TRASH'

# linkage reasons

IS_INLINE_REF_LINK='iin'
IS_INDIRECT_REF_LINK='iir'
IS_TAG_LINK='itl'
IS_TAG_TAG_LINK='itn'
IS_CHILD_CONTENT_LINK='icl'
IS_CHILD_REF_LINK='icr'
IS_FIELD_CONTENT_LINK='ifl'

# Workhorse class and methods
# Pass in a Tana JSON dump, get back a DirectedGraph
# If you include an optional 'visualizer' config element
# in your dump, that will control what gets included
# in the output graph. Otherwise, all links get included
# and it is assumed the client will filter as required.

# Basic structure is a index (dict) of nodes and a list of linkages between them
# Each linkage is a tuple of (source_id, target_id, reason)

class NodeIndex(BaseModel):
  tana_dump:TanaDump
  index: dict[str, NodeDump] = {}
  trash: dict[str, NodeDump] = {}
  tags: dict[str, str] = {}
  tag_colors: dict[str, str] = {}
  master_pairs: List[tuple[str, str, str]] = []
  config: Visualizer = Visualizer()

  # populate an index of all the nodes in the tana dump, including trash
  def build_index(self):
    # first, build an index by node.id to make it possible to navigate the graph
    trash_node = None
    for node in self.tana_dump.docs:
      if TRASH in node.id:
        # ignore the trash parent node
        trash_node = node
        # But make sure to put the trash in the trash
        self.trash[trash_node.id] = trash_node
        continue
      self.index[node.id] = node

    # strip all the nodes that are in the trash from the index
    # (wouldn't it be nice if trash could be emptied first?)
    if trash_node is not None:
      trash_children = trash_node.children
      if trash_children:
        for node_id in trash_children:
          if node_id in self.index:
            self.trash[node_id] = self.index[node_id]
            del self.index[node_id]

  # is the node indexed and is it not trashed?
  def valid(self, node_id:str|None):
    return node_id not in self.trash and node_id in self.index

  def trashed(self, node_id:str|None):
    return node_id in self.trash
  
  def node(self, node_id:str):
    return self.index[node_id]
  
  def build_indices(self):
    self.build_index()
    self.build_tag_index()

  # look for tags and build a tag index
  def build_tag_index(self):
    for node in self.tana_dump.docs:

      # skip trashed nodes
      if node.id not in self.index:
        continue

      # do we have a tag?
      if node.children and 'SYS' not in node.id:
        if TAG in node.children:
          if SUPERTAG in node.children:
            # found supertag tuple
            # make sure it's not been trashed
            if node.props.ownerId and node.props.ownerId not in self.trash:
              meta_node:NodeDump = self.index[node.props.ownerId]
              if meta_node:
                tag_id = meta_node.props.ownerId
                if tag_id and tag_id not in self.trash:
                  tag_node = self.index[tag_id]
                  if tag_node.props:
                    tag_name = tag_node.props.name
                    if tag_name:
                      self.tags[tag_name] = tag_node.id
                      if len(node.children) > 2:
                        # we have a superclass as well
                        for child_id in node.children:
                          if 'SYS' in child_id:
                            continue
                          if self.valid(child_id):
                            supertag = self.index[child_id]
                            tag_node.tags.append(supertag.id)
                            # print (f'{tag_name} -> {supertag.props.name}')
                            if self.config.include_tag_tag_links:
                              self.master_pairs.append((tag_id, child_id, IS_TAG_TAG_LINK))
                      else:
                        # print(f'{tag_name} ->')
                        pass
                # else:
                  # trashed_node = self.trash[tag_id]
                  # print(f'Found tag_id {tag_id}, name {trashed_node.props.name} in the TRASH')

          elif FIELD in node.children:
            # found field tuple
            # TODO handle fields similiarly to tags
            continue
          
        # doi we have a tag color specifier?
        elif COLOR_SPEC in node.children:
          color = None
          for color_id in node.children:
            if 'SYS' in color_id:
              continue
            else:
              if self.valid(color_id):
                color = self.index[color_id].props.name
          
          # now find the tag it applies to
          if node.props.ownerId and self.valid(node.props.ownerId):
            meta_node:NodeDump = self.index[node.props.ownerId]
            if meta_node:
              tag_id = meta_node.props.ownerId
              if color and tag_id and self.valid(tag_id):
                self.tag_colors[tag_id] = color
                self.index[tag_id].color = color

  def build_master_pairs(self):
    # Find all the pairs we care about to build our graph viz
    # find all the inline refs first
    node: NodeDump
    for node in self.tana_dump.docs:
      # skip trashed nodes
      if self.trashed(node.id):
        continue

      name = node.props.name

      # TODO: also look for field refs. Those are interesting as well

      # do we have a tag tuple that is NOT the tag definition tuple?
      # this will be the tag of a node.
      if node.children and 'SYS' not in node.id and 'SYS_A13' in node.children:
        if SUPERTAG not in node.children and FIELD not in node.children:
          tag_ids = node.children
          # find the actual data node that owns this tag tuple
          if node.props.ownerId and self.valid(node.props.ownerId):
            meta_node:NodeDump = self.index[node.props.ownerId]
            data_node_id = meta_node.props.ownerId
            if not self.valid(data_node_id):
              if not self.trashed(data_node_id):
                logger.warning(f'Found tag tuple {node.id} with missing data node {data_node_id}')
            elif data_node_id and self.valid(data_node_id):
              data_node:NodeDump = self.node(data_node_id)
              # now create a link from the tag node to the data node
              # for every child that isn't SYS_A13
              for tag_id in tag_ids:
                if 'SYS' in tag_id:
                  continue
                if self.valid(tag_id):

                  if self.config.include_node_tag_links:
                    self.master_pairs.append((data_node_id, tag_id, IS_TAG_LINK))
                    # collect the tags...
                    data_node.tags.append(tag_id)
                  # also apply the color of the tag...
                  if tag_id in self.tag_colors:
                    data_node.color = self.tag_colors[tag_id]
                  else:
                    # tag from another workspace...must be?
                    pass

      # look for inline refs. That's a relationship
      if self.config.include_inline_refs and name and '<span data-inlineref-node=\"' in name:
        frags = name.split('<span data-inlineref-node=\"')
        # build a link between the nodes that are referenced
        # (i.e. treat the node with the inline refs as the 
        # "join node" but don't include it in the output unless asked)
        # TODO: Revisit this decision since we now filter client-side
        if len(frags) > 1:
          # first compute the indirect linkages
          ids = []
            
          for frag in frags[1:]:
            ref_id = frag.split('"')[0]
            if not self.valid(ref_id):
              continue
            ids.append(ref_id)
          
          # for all refs through this node, created paired relationships
          indirect_pairs = list(combinations(ids, 2))
          for pair in indirect_pairs:
            linkage = (pair[0], pair[1], IS_INDIRECT_REF_LINK)
            self.master_pairs.append(linkage)
          
          # now do all direct to ref node links
          if self.config.include_inline_ref_nodes:
            for id in ids:
              linkage = (node.id, id, IS_INLINE_REF_LINK)
              self.master_pairs.append(linkage)

      # what to do with children of regular nodes? Too much graph structure, not enough meaning
      # BUT, we probably want nodes that are tagged and are subnodes of other tagged nodes
      # to be included as a link from the child tagged node to the parent tagged node
      if self.config.include_content_nodes and node.children and 'Root node for file:' not in name and 'SYS' not in node.id:
        for child_id in node.children:
          if self.valid(child_id) and SUPERTAG not in child_id and FIELD not in child_id and 'SYS' not in child_id:
            child_node = self.node(child_id)

            if child_node.props.docType == 'tuple':
              # tuples are fields
              if child_node.children:
                if len(child_node.children) < 2:
                  continue
                # field definition itself is the first child
                field_id = child_node.children[0]
                # values are all the rest...
                value_ids = child_node.children[1:]
                if self.valid(field_id):
                  node.fields.append({"field": field_id, "values": value_ids})
                  # TODO field linkages have extra ID (value_id)
                  linkage = (node.id, field_id, IS_FIELD_CONTENT_LINK)
                  self.master_pairs.append(linkage)
            elif child_node.props.docType == 'search':
              # we don't want to expand search nodes...
              # TODO: revisit this decision
              continue
            elif child_node.props.docType == 'viewDef':
              # we don't want to expand viewDef nodes...
              # TODO: revisit this decision
              continue
            elif child_node.props.docType == 'associatedData':
              # we don't want to expand associated data nodes...
              # TODO: revisit this decision
              continue
            else:
              if child_node.props.ownerId != node.id:
                # this is a child reference, not an owned child
                linkage = (node.id, child_id, IS_CHILD_REF_LINK)
              else:
                linkage = (node.id, child_id, IS_CHILD_CONTENT_LINK)

              self.master_pairs.append(linkage)
              node.content.append(child_id)
    
    return self.master_pairs
  
  link_index: dict[str, dict]|None = None

  def get_linkage_reason(self, source_id:str, target_id:str) -> str:
    if self.link_index is None:
      self.link_index = {}
      for link in self.master_pairs:
        if link[0] not in self.link_index:
          index = {}
          self.link_index[link[0]] = index
        else:
          index = self.link_index[link[0]]

        index[link[1]] = link[2]
    
    return self.link_index[source_id][target_id]

def prune_reference_nodes(context:str) -> str:
  # walk the nested text structure in context
  # and prune out levels of indentation below any line
  # that is a node reference.
  result = ''
  prune_level = 0
  pruning = False
  for line in context.split('\n'):
    # figure out indentation level (2 spaces per)
    indent = (len(line) - len(line.lstrip())) / 2
    if pruning:
      if indent >= prune_level:
        # we are deeper than prune, skip it
        continue
      else:
        # prune is over
        pruning = False

    # is it a direct reference? (NOT inline ref)
    # strict conformance to - [[ ]]\n
    if re.search(r' *- \[\[.*\^.*\]\]', line):
      # yes, it's a reference
      # keep it
      result += line + '\n'
      # but prune everything below it
      prune_level = indent + 1
      pruning = True
    else:
      result += line + '\n'

  return result


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


# capture a link if both nodes are in the index
def add_linkage(index:NodeIndex, links:List, source_id:str, target_id:str, reason="unknown"):
  if index.valid(source_id) and index.valid(target_id):
    link = GraphLink(source=source_id, target=target_id, reason=reason)
    links.append(link)
