from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Types for our APIs to use

TANA_TEXT = "tana-text"
TANA_NODE = "tana-node"


class Props(BaseModel):
    created: int
    name: str = ""
    description: str | None = None
    ownerId: str | None = Field(default=None, alias="_ownerId")
    metaNodeId: str | None = Field(default=None, alias="_metaNodeId")
    docType: str | None = Field(default=None, alias="_docType")
    sourceId: str | None = Field(default=None, alias="_sourceId")
    view: str | None = None
    editMode: bool | None = False
    done: bool | int | None | None = None


class NodeDump(BaseModel):
    id: str
    props: Props
    touchCounts: list[int] | None = None
    modifiedTs: list[int] | None = None
    children: list[str] | None = None
    associationMap: dict[str, str] | None = None
    underConstruction: bool | None = None
    inbound_refs: list[str] | None = []
    outbound_refs: list[str] | None = []
    color: str | None = None
    tags: list[str] = []
    content: list[str] = []
    fields: list[dict] = []


# config for graph visualization.
# By default, we include all linkages
class Visualizer(BaseModel):
    include_tag_tag_links: bool = True
    include_node_tag_links: bool = True
    include_inline_refs: bool = True
    include_inline_ref_nodes: bool = True
    include_content_nodes: bool = False
    include_tag_schema_links: bool | None = False
    # make this hashable
    model_config = ConfigDict(frozen=True)


class TanaDump(BaseModel):
    formatVersion: int
    docs: list[NodeDump]
    editors: list[list[int | str]]
    workspaces: dict[str, str]
    lastTxid: int | None = None
    lastFbKey: str | None = None
    optimisticTransIds: list[Any] | None = None
    currentWorkspaceId: str | None = None

    visualize: Visualizer | None = None


class TanaField(BaseModel):
    field_id: str
    name: str
    value_id: str
    value: str
    # tag_id: str = ''


class TanaTag(BaseModel):
    id: str
    name: str
    description: str | None = None
    color: str | None = None


class TanaDocument(BaseModel):
    id: str  # the tana node id
    name: str
    description: str | None
    tags: list[str] = []
    fields: list[TanaField] | None
    # TODO: consider whether we should preserve more node structure here
    content: list["TanaContentElement"] = []


class TanaContent(BaseModel):
    id: str  # the tana node id
    name: str
    description: str | None


class TanaContentElement(BaseModel):
    id: str | None = None
    is_reference: bool = False
    is_field: bool = False
    field_name: str | None = None
    content: str


# A Tana Topic is anything that is tagged. This is the "logical document" of the Tana
# workspace for the purpose of our RAG efforts
class TanaTopicNode(TanaContent):
    tags: list[str] = []
    fields: list[TanaField] | None
    # TODO: consider whether we should preserve more node structure here
    content: list["TanaContentElement"] = []


# A Tana Content Node is a child of a topic node. We split this out for
# finer grained embedding purposes - and because single topics are too
# large to embed in one go.
# Content Nodes are assumed to be flat text - no fields, no tags.
class TanaContentNode(TanaContent):
    topic_id: str  # the parent topic we are part of


class TanaNodeMetadata(BaseModel):
    category: str = TANA_NODE
    title: str
    supertag: str | None = None
    topic_id: str | None = None
    node_id: str | None = None
    text: str | None = None
    hash: int


class GraphLink(BaseModel):
    source: str
    target: str
    reason: str
