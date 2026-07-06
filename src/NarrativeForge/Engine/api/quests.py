from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from NarrativeForge.Engine.models import QuestGraph, QuestNode, QuestEdge
from NarrativeForge.Engine.scripting.ink_parser import InkParser
from NarrativeForge.Engine.storage.database import Database

router = APIRouter(prefix="/api", tags=["quests"])

_db: Database | None = None


def init(db: Database):
    global _db
    _db = db


class QuestGraphCreate(BaseModel):
    name: str = ""
    start_node_id: str = ""
    nodes: dict = Field(default_factory=dict)
    edges: list = Field(default_factory=list)


class QuestGraphResponse(BaseModel):
    id: str
    name: str
    start_node_id: str
    nodes: dict
    edges: list
    variables: dict = Field(default_factory=dict)


def _to_response(graph: QuestGraph) -> QuestGraphResponse:
    nodes_data = {}
    for k, node in graph.nodes.items():
        nodes_data[k] = {
            "id": node.id,
            "type": node.type.value,
            "name": node.name,
            "description": node.description,
            "objectives": node.objectives,
            "rewards": node.rewards,
            "conditions": [c.model_dump() for c in node.conditions],
            "next_node_ids": node.next_node_ids,
        }
    edges_data = [e.model_dump() for e in graph.edges]
    return QuestGraphResponse(
        id=graph.id,
        name=graph.name,
        start_node_id=graph.start_node_id,
        nodes=nodes_data,
        edges=edges_data,
        variables=graph.variables.to_dict(),
    )


class InkQuestParseRequest(BaseModel):
    script: str
    name: str = ""


class InkQuestParseResponse(BaseModel):
    graph: QuestGraphResponse


@router.post("/projects/{project_id}/quests", response_model=QuestGraphResponse, status_code=201)
async def create_quest_graph(project_id: UUID, body: QuestGraphCreate):
    project = await _db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    nodes = {}
    for k, v in body.nodes.items():
        nodes[k] = QuestNode(**v) if isinstance(v, dict) else v
    edges = [QuestEdge(**e) if isinstance(e, dict) else e for e in body.edges]

    graph = QuestGraph(
        name=body.name,
        start_node_id=body.start_node_id,
        nodes=nodes,
        edges=edges,
    )
    created = await _db.create_quest_graph(project_id, graph)
    return _to_response(created)


@router.get("/projects/{project_id}/quests", response_model=list[QuestGraphResponse])
async def list_quest_graphs(project_id: UUID):
    project = await _db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    graphs = await _db.list_quest_graphs(project_id)
    return [_to_response(g) for g in graphs]


@router.get("/quests/{graph_id}", response_model=QuestGraphResponse)
async def get_quest_graph(graph_id: str):
    graph = await _db.get_quest_graph(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Quest graph not found")
    return _to_response(graph)


@router.delete("/quests/{graph_id}", status_code=204)
async def delete_quest_graph(graph_id: str):
    deleted = await _db.delete_quest_graph(graph_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Quest graph not found")


@router.post("/quests/parse", response_model=InkQuestParseResponse)
async def parse_ink_quest(body: InkQuestParseRequest):
    parser = InkParser()
    graph = parser.parse_quest(body.script)
    if body.name:
        graph.name = body.name
    return InkQuestParseResponse(graph=_to_response(graph))
