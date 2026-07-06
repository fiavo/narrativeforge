from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from NarrativeForge.Engine.models import DialogueTree, DialogueNode, DialogueEdge
from NarrativeForge.Engine.scripting.ink_parser import InkParser
from NarrativeForge.Engine.storage.database import Database

router = APIRouter(prefix="/api", tags=["dialogues"])

_db: Database | None = None


def init(db: Database):
    global _db
    _db = db


class DialogueTreeCreate(BaseModel):
    name: str = ""
    start_node_id: str = ""
    nodes: dict = Field(default_factory=dict)
    edges: list = Field(default_factory=list)


class DialogueTreeResponse(BaseModel):
    id: str
    name: str
    start_node_id: str
    nodes: dict
    edges: list
    variables: dict = Field(default_factory=dict)


def _to_response(tree: DialogueTree) -> DialogueTreeResponse:
    nodes_data = {}
    for k, node in tree.nodes.items():
        nodes_data[k] = {
            "id": node.id,
            "type": node.type.value,
            "content": node.content,
            "choices": [c.model_dump() for c in node.choices],
            "conditions": [c.model_dump() for c in node.conditions],
            "variables_set": node.variables_set,
            "next_node_id": node.next_node_id,
        }
    edges_data = [e.model_dump() for e in tree.edges]
    return DialogueTreeResponse(
        id=tree.id,
        name=tree.name,
        start_node_id=tree.start_node_id,
        nodes=nodes_data,
        edges=edges_data,
        variables=tree.variables.to_dict(),
    )


class InkParseRequest(BaseModel):
    script: str
    name: str = ""


class InkParseResponse(BaseModel):
    tree: DialogueTreeResponse


@router.post("/projects/{project_id}/dialogues", response_model=DialogueTreeResponse, status_code=201)
async def create_dialogue_tree(project_id: UUID, body: DialogueTreeCreate):
    project = await _db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    nodes = {}
    for k, v in body.nodes.items():
        nodes[k] = DialogueNode(**v) if isinstance(v, dict) else v
    edges = [DialogueEdge(**e) if isinstance(e, dict) else e for e in body.edges]

    tree = DialogueTree(
        name=body.name,
        start_node_id=body.start_node_id,
        nodes=nodes,
        edges=edges,
    )
    created = await _db.create_dialogue_tree(project_id, tree)
    return _to_response(created)


@router.get("/projects/{project_id}/dialogues", response_model=list[DialogueTreeResponse])
async def list_dialogue_trees(project_id: UUID):
    project = await _db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    trees = await _db.list_dialogue_trees(project_id)
    return [_to_response(t) for t in trees]


@router.get("/dialogues/{tree_id}", response_model=DialogueTreeResponse)
async def get_dialogue_tree(tree_id: str):
    tree = await _db.get_dialogue_tree(tree_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Dialogue tree not found")
    return _to_response(tree)


@router.delete("/dialogues/{tree_id}", status_code=204)
async def delete_dialogue_tree(tree_id: str):
    deleted = await _db.delete_dialogue_tree(tree_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dialogue tree not found")


@router.post("/dialogues/parse", response_model=InkParseResponse)
async def parse_ink_dialogue(body: InkParseRequest):
    parser = InkParser()
    tree = parser.parse_dialogue(body.script)
    if body.name:
        tree.name = body.name
    return InkParseResponse(tree=_to_response(tree))
