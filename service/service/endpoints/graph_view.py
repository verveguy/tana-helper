from logging import getLogger

from fastapi import APIRouter
from pydantic import BaseModel

from service.tana_types import GraphLink, TanaDump, Visualizer
from service.tanaparser import NodeIndex, add_linkage, patch_node_name

router = APIRouter()

logger = getLogger()


class RenderNode(BaseModel):
    id: str
    name: str | None
    color: str | None = None


class DirectedGraph(BaseModel):
    directed: bool = False
    multigraph: bool = False
    nodes: list[RenderNode] = []
    links: list[GraphLink] = []


@router.post("/graph", tags=["Visualizer"])
async def graph(tana_dump: TanaDump):
    links = []  # final results we build into

    # For client-side filtering, we ignore the visualizer config and return ALL links
    # The client will filter based on reason codes
    config = Visualizer(
        include_tag_tag_links=True,
        include_node_tag_links=True,
        include_inline_refs=True,
        include_inline_ref_nodes=True,
        include_content_nodes=True,
        include_tag_schema_links=True,
    )

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
    [
        final_pairs.add((a, b, r))
        for (a, b, r) in candidate_pairs
        if (a, b, r) not in final_pairs and (b, a, r) not in final_pairs
    ]

    # build links - include ALL links for client-side filtering
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
