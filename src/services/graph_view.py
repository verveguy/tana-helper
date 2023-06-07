from fastapi import APIRouter, Body, Header
from fastapi.responses import HTMLResponse
from ..dependencies import tana_to_json
from ..tana_types import *
from starlette.requests import Request
from logging import getLogger
from itertools import combinations

router = APIRouter()

logger = getLogger()

class Link(BaseModel):
  source: str
  target: str

class DirectedGraph(BaseModel):
  directed: bool = False
  multigraph: bool = False
  nodes: List[Node] = []
  links: List[Link] = []

def add_inline_ref(index, links, source_id:str, target_id:str):
  # add a link if nodes are in index
  if source_id in index and target_id in index:
    link = Link(source=source_id, target=target_id)
    links.append(link)

  
@router.post("/graph")
async def graph(tana_dump:TanaDump):

  # walk the data and build a hash of node ids
  node: Node
  index = {}
  graph = DirectedGraph()
  tags = {}

  # first, build an index by node.id to make it possible to navigate the graph
  trash = None
  for node in tana_dump.docs:
    if 'TRASH' in node.id:
      # ignore the trash
      trash = node
      continue
    index[node.id] = node

  # strip all the nodes that are in the trash from the index
  # TODO: figure better way to check node trashed status in code below
  # (wouldn't it be nice if trash could be emptied first?)
  if trash is not None:
    trash_children = trash.children
    if trash_children:
      for node_id in trash_children:
        if node_id in index:
          del index[node_id]

  # look for tags and build a tag index
  # TODO: extract this as a function so we can use it in other tana dump 
  # parsing projects ...
  for node in tana_dump.docs:
    # do we have a tag?
    if node.children and 'SYS' not in node.id and 'SYS_A13' in node.children:
      if 'SYS_T01' in node.children:
        # found supertag tuple
        # make sure it's not been trashed
        if node.props.ownerId in index:
          tuple_node:Node = index[node.props.ownerId]
          if tuple_node:
            tag_id = tuple_node.props.ownerId
            if tag_id in index:
              tag_node = index[tag_id]
              if tag_node.props:
                tags[tag_node.props.name] = tag_node.id
      elif 'SYS_T02' in node.children:
        # found field tuple
        # TODO handle fields similiarly to tags
        continue

  # OK, now that we have the basic dump indexed...

  # Find all the pairs we care about to build our graph viz
  master_pairs = []
  # find all the inline refs first
  for node in tana_dump.docs:
    name = node.props.name

    # also look for field refs. Those are interesting as well

    # do we have a tag tuple that is NOT the tag definition tuple?
    if node.children and 'SYS' not in node.id and 'SYS_A13' in node.children:
      if 'SYS_T01' not in node.children and 'SYS_T02' not in node.children:
        tag_ids = node.children
        # find the actual data node that owns this tag tuple
        if node.props.ownerId in index:
          meta_node:Node = index[node.props.ownerId]
          data_node_id = meta_node.props.ownerId
          if data_node_id in index:
            # now create a link from the tag node to the data node
            # for every child that isn't SYS_A13
            for tag_id in tag_ids:
              if 'SYS' in tag_id:
                continue
              if tag_id in index:
                master_pairs.append((data_node_id, tag_id))

    # look for inline refs. That's a relationship
    # DISABLED for testing with tags
    if False and name and '<span data-inlineref-node=\"' in name:
      frags = name.split('<span data-inlineref-node=\"')
      # build a link between the nodes that are referenced
      # # (i.e. treat the node with the inline refs as the 
      # # "join node" but don't include it in the output)
      if len(frags) > 2:
        ids = []
        for frag in frags[1:]:
          ids.append(frag.split('"')[0])
        
        # for all refs through this node, created paired relationships
        pairs = list(combinations(ids, 2))
        master_pairs.extend(pairs)

    # what to do with children of regular nodes? Too much graph structure, not enough meaning
    # BUT, we probably want nodes that are tagged and are subnodes of other tagged nodes
    # to be included as a link from the child tagged node to the parent tagged node

  # strip the links down to the unique set
  final_pairs = set()
  # also remove redundat bidirectional links
  [final_pairs.add((a, b)) for (a, b) in master_pairs
    if (a, b) not in final_pairs and (b, a) not in final_pairs]

  # build links
  for pair in final_pairs:
    add_inline_ref(index, graph.links, pair[0], pair[1])

  count = 0
  new_graph = DirectedGraph()
  node_ids = []

  # only include nodes that are linked
  for link in graph.links:
    new_graph.links.append(link)
    node_ids.append(link.source)
    node_ids.append(link.target)
    count = count + 1
    if count > 500:
      break
  
  node_ids = list(set(node_ids))
  for node_id in node_ids:
    new_graph.nodes.append(index[node_id])


  return new_graph

