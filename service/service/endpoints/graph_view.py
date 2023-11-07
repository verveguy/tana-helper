from fastapi import APIRouter, Body, Header
from fastapi.responses import HTMLResponse
from service.dependencies import tana_to_json
from service.tana_types import *
from starlette.requests import Request
from logging import getLogger
from itertools import combinations
from functools import lru_cache
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


# Workhorse method
# Pass in a Tana JSON dump, get back a DirectedGraph
# If you include an optional 'visualizer' config element
# in your dump, that will control what gets included
# in the output graph. Otherwise, all links get included
# and it is assumed the client will filter as required.

@router.post("/graph")
async def graph(tana_dump:TanaDump):

  # walk the data and build a hash of node ids
  node: Node
  index = {} # fast access to all nodes by id
  trash = {} # nodes we should treat as "trashed"
  tags = {} # tag nodes we discover
  tag_colors = {} # colors for tags we discover  
  master_pairs = [] # working set of pairs along the way
  links = []  # final results we build into

  config = tana_dump.visualize
  if config is None:
    config = Visualizer()

  def add_linkage(source_id:str, target_id:str, reason="unknown"):
    # add a link if nodes are in index
    # TODO: what if they're trashed?
    # we seem to have errors in trash...
    if source_id in index and target_id in index:
      link = Link(source=source_id, target=target_id, reason=reason)
      links.append(link)
 
  def patch_node_name(node:Node):
    # replace <span .. inline refs with actual node names
    # this is to facilitate full text search of the graph
    def subfunc(matchobj):
      ref_id = matchobj.group(1)
      if ref_id in index:
        frag = index[ref_id].props.name
        return f'[[{frag}]]'
      return ref_id

    name = node.props.name
    if name and '<span' in name:
        name = re.sub('<span data-inlineref-node="([^"]*)"></span>', subfunc, name)
    return name

  # first, build an index by node.id to make it possible to navigate the graph
  trash_node = None
  for node in tana_dump.docs:
    if 'TRASH' in node.id:
      # ignore the trash
      trash_node = node
      # But make sure to put the trash in the trash
      trash[trash_node.id] = trash_node
      continue
    index[node.id] = node

  # strip all the nodes that are in the trash from the index
  # TODO: figure better way to check node trashed status in code below
  # (wouldn't it be nice if trash could be emptied first?)
  if trash_node is not None:
    trash_children = trash_node.children
    if trash_children:
      for node_id in trash_children:
        if node_id in index:
          trash[node_id] = index[node_id]
          #del index[node_id]

  # look for tags and build a tag index
  # TODO: extract this as a function so we can use it in other tana dump 
  # parsing projects ...
  for node in tana_dump.docs:

    # skip trashed nodes
    if node.id not in index:
      continue

    # do we have a tag?
    if node.children and 'SYS' not in node.id:
      if 'SYS_A13' in node.children:
        if 'SYS_T01' in node.children:
          # found supertag tuple
          # make sure it's not been trashed
          if node.props.ownerId not in trash:
            meta_node:Node = index[node.props.ownerId]
            if meta_node:
              tag_id = meta_node.props.ownerId
              if tag_id not in trash:
                tag_node = index[tag_id]
                if tag_node.props:
                  tag_name = tag_node.props.name
                  tags[tag_name] = tag_node.id
                  if len(node.children) > 2:
                    # we have a superclass as well
                    for child_id in node.children:
                      if 'SYS' in child_id:
                        continue
                      if child_id not in trash and child_id in index:
                        supertag = index[child_id]
                        print (f'{tag_name} -> {supertag.props.name}')
                        if config.include_tag_tag_links:
                          master_pairs.append((tag_id, child_id, 'itn'))
                  else:
                    print(f'{tag_name} ->')
              else:
                trashed_node = trash[tag_id]
                print(f'Found tag_id {tag_id}, name {trashed_node.props.name} in the TRASH')



        elif 'SYS_T02' in node.children:
          # found field tuple
          # TODO handle fields similiarly to tags
          continue
        
      elif 'SYS_A11' in node.children:
        # this is a tag color specifier
        color = None
        for color_id in node.children:
          if 'SYS' in color_id:
            continue
          else:
            if color_id not in trash:
              color = index[color_id].props.name
        
        # now find the tag it applies to
        if node.props.ownerId in index:
          meta_node:Node = index[node.props.ownerId]
          if meta_node:
            tag_id = meta_node.props.ownerId
            if tag_id not in trash:
              tag_colors[tag_id] = color
              index[tag_id].color = color

  # OK, now that we have the basic dump indexed...

  # Find all the pairs we care about to build our graph viz
  # find all the inline refs first
  for node in tana_dump.docs:
    # skip trashed nodes
    if node.id in trash:
      continue

    name = node.props.name

    # also look for field refs. Those are interesting as well

    # do we have a tag tuple that is NOT the tag definition tuple?
    # this will be the tag of a node.
    if node.children and 'SYS' not in node.id and 'SYS_A13' in node.children:
      if 'SYS_T01' not in node.children and 'SYS_T02' not in node.children:
        tag_ids = node.children
        # find the actual data node that owns this tag tuple
        if node.props.ownerId not in trash:
          meta_node:Node = index[node.props.ownerId]
          data_node_id = meta_node.props.ownerId
          if data_node_id not in trash:
            # now create a link from the tag node to the data node
            # for every child that isn't SYS_A13
            for tag_id in tag_ids:
              if 'SYS' in tag_id:
                continue
              if tag_id not in trash:
                if config.include_node_tag_links:
                  master_pairs.append((data_node_id, tag_id, 'itl'))
                # also apply the color of the tag...
                if tag_id in tag_colors:
                  index[data_node_id].color = tag_colors[tag_id]
                else:
                  # tag from another workspace...must be?
                  pass

    # look for inline refs. That's a relationship
    if config.include_inline_refs and name and '<span data-inlineref-node=\"' in name:
      frags = name.split('<span data-inlineref-node=\"')
      # build a link between the nodes that are referenced
      # (i.e. treat the node with the inline refs as the 
      # "join node" but don't include it in the output unless asked)
      if len(frags) > 1:
        # first compute the indirect linkages
        ids = []
          
        for frag in frags[1:]:
          ref_id = frag.split('"')[0]
          if ref_id in trash:
            continue
          ids.append(ref_id)
        
        # for all refs through this node, created paired relationships
        indirect_pairs = list(combinations(ids, 2))
        for pair in indirect_pairs:
          linkage = (pair[0], pair[1], 'iir')
          master_pairs.append(linkage)
        
        # now do all direct to ref node links
        if config.include_inline_ref_nodes:
          for id in ids:
            linkage = (node.id, id, 'iin')
            master_pairs.append(linkage)

    # what to do with children of regular nodes? Too much graph structure, not enough meaning
    # BUT, we probably want nodes that are tagged and are subnodes of other tagged nodes
    # to be included as a link from the child tagged node to the parent tagged node

  # strip the links down to the unique set
  master_pairs = set(master_pairs)
  final_pairs = set()
  # also remove redundant bidirectional links
  [final_pairs.add((a, b, r)) for (a, b, r) in master_pairs
    if (a, b, r) not in final_pairs and (b, a, r) not in final_pairs]

  # build links
  for pair in final_pairs:
    add_linkage(pair[0], pair[1], pair[2])

  # build the retrun structure...
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
    node = index[node_id]
    # patch up node name
    new_name = patch_node_name(node)
    render_node = RenderNode(id=node.id, name=new_name, color=node.color)
    graph.nodes.append(render_node)


  return graph

