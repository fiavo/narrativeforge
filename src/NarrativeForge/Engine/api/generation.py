from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from NarrativeForge.Engine.ai_providers.base import CompletionOptions
from NarrativeForge.Engine.agents.base import AgentContext, BaseAgent
from NarrativeForge.Engine.agents import (
    StoryAgent,
    DialogueAgent,
    QuestAgent,
    LoreAgent,
    ConsistencyChecker,
    WorldAgent,
    TimelineAgent,
    CriticAgent,
    RewriteAgent,
)
from NarrativeForge.Engine.pipeline.orchestrator import PipelineOrchestrator
from NarrativeForge.Engine.plugins.plugin_manager import PluginManager
from NarrativeForge.Engine.storage.database import Database
from NarrativeForge.Engine.importing.import_manager import SUPPORTED_EXTENSIONS
from NarrativeForge.Engine.scripting.ink_parser import InkParser
from NarrativeForge.Engine.scripting.yarn_parser import YarnParser

EXPORT_FORMATS = ["json", "markdown", "text", "yaml"]
IMPORT_FORMATS = ["ink", "yarn"]

KNOWN_AGENTS: dict[str, type[BaseAgent]] = {
    "StoryAgent": StoryAgent,
    "DialogueAgent": DialogueAgent,
    "QuestAgent": QuestAgent,
    "LoreAgent": LoreAgent,
    "ConsistencyChecker": ConsistencyChecker,
    "WorldAgent": WorldAgent,
    "TimelineAgent": TimelineAgent,
    "CriticAgent": CriticAgent,
    "RewriteAgent": RewriteAgent,
}

router = APIRouter(prefix="/api", tags=["generation"])

_db: Database | None = None
_orchestrator: PipelineOrchestrator | None = None
_plugin_manager: PluginManager | None = None


def init(db: Database, orchestrator: PipelineOrchestrator, plugin_manager: PluginManager | None = None):
    global _db, _orchestrator, _plugin_manager
    _db = db
    _orchestrator = orchestrator
    _plugin_manager = plugin_manager or PluginManager()


class GenerateRequest(BaseModel):
    project_id: UUID
    request: str = ""
    temperature: float = 0.7


class GenerateResponse(BaseModel):
    content: dict | list | str | None = None
    stages: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


@router.post("/generate", response_model=GenerateResponse)
async def generate(body: GenerateRequest):
    project = await _db.get_project(body.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ctx = AgentContext(
        project=project,
        user_request=body.request,
        generation_params=CompletionOptions(temperature=body.temperature),
    )

    result = await _orchestrator.run(ctx)

    issues = []
    for r in result.results:
        if hasattr(r, "metadata") and r.metadata:
            for issue in r.metadata.get("issues", []):
                issues.append(str(issue))

    metadata = dict(result.metadata)
    if issues:
        metadata["issues"] = issues

    return GenerateResponse(
        content=result.content,
        stages=result.stages_completed,
        metadata=metadata,
    )


class ExportRequest(BaseModel):
    format: str = Field(description="Export format: json, markdown, text, or yaml")
    content: dict | list | str | None = None
    filename: str = Field(default="export", description="Base filename without extension")


class ExportResponse(BaseModel):
    filename: str
    format: str
    content: str


@router.get("/export/formats")
async def list_export_formats():
    return {"formats": EXPORT_FORMATS}


@router.post("/export", response_model=ExportResponse)
async def export_content(body: ExportRequest):
    if body.format not in EXPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown format: {body.format}. Valid formats: {', '.join(EXPORT_FORMATS)}",
        )

    raw = body.content if body.content is not None else ""

    if body.format == "json":
        import json
        export_content = json.dumps(raw, indent=2)
    elif body.format == "yaml":
        import yaml
        export_content = yaml.dump(raw, default_flow_style=False)
    elif body.format == "markdown":
        if isinstance(raw, dict):
            lines = []
            for key, val in raw.items():
                lines.append(f"## {key}\n\n{val}")
            export_content = "\n\n".join(lines)
        elif isinstance(raw, list):
            lines = [f"- {item}" for item in raw]
            export_content = "\n".join(lines)
        else:
            export_content = str(raw)
    else:
        export_content = str(raw)

    filename = f"{body.filename}.{body.format}"

    return ExportResponse(
        filename=filename,
        format=body.format,
        content=export_content,
    )


class ImportRequest(BaseModel):
    filename: str = Field(description="Filename with extension (e.g. dialogue.ink)")
    content: str = Field(description="File content to import")
    format: str = Field(description="Import format: ink or yarn")


class ImportResponse(BaseModel):
    tree_id: str
    name: str
    nodes: dict
    edges: list
    choices: list = Field(default_factory=list)


def _detect_format(filename: str) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    format_map = {".ink": "ink", ".yarn": "yarn"}
    fmt = format_map.get(ext)
    if fmt is None:
        raise ValueError(f"Unsupported extension {ext!r}. Expected one of: {SUPPORTED_EXTENSIONS}")
    return fmt


@router.post("/projects/{project_id}/import", response_model=ImportResponse)
async def import_file(project_id: UUID, body: ImportRequest):
    project = await _db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    fmt = body.format.lower()
    if fmt not in IMPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown format: {fmt}. Valid formats: {', '.join(IMPORT_FORMATS)}",
        )

    if fmt == "ink":
        parser = InkParser()
        tree = parser.parse_dialogue(body.content)
    else:
        parser = YarnParser()
        tree = parser.parse(body.content)

    tree.name = body.filename.rsplit(".", 1)[0] if "." in body.filename else body.filename

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
    choices_data = []
    for node in tree.nodes.values():
        for choice in node.choices:
            choices_data.append(choice.model_dump())

    return ImportResponse(
        tree_id=tree.id,
        name=tree.name,
        nodes=nodes_data,
        edges=edges_data,
        choices=choices_data,
    )


@router.get("/plugins")
async def list_plugins():
    plugins = _plugin_manager.discover()
    return [
        {
            "name": p.name,
            "version": p.version,
            "description": p.description,
            "author": p.author,
            "type": p.plugin_type.value,
            "enabled": p.enabled,
        }
        for p in plugins
    ]


class AgentRequest(BaseModel):
    project_id: UUID
    request: str = ""
    temperature: float = 0.7


class AgentResponse(BaseModel):
    agent_name: str
    content: dict | list | str | None = None
    metadata: dict = Field(default_factory=dict)


@router.post("/agents/{agent_name}", response_model=AgentResponse)
async def invoke_agent(agent_name: str, body: AgentRequest):
    if agent_name not in KNOWN_AGENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent: {agent_name}. Valid agents: {', '.join(KNOWN_AGENTS)}",
        )

    project = await _db.get_project(body.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    agent_class = KNOWN_AGENTS[agent_name]
    agent = agent_class(_orchestrator.provider)

    ctx = AgentContext(
        project=project,
        user_request=body.request,
        generation_params=CompletionOptions(temperature=body.temperature),
    )

    result = await agent.execute(ctx)

    return AgentResponse(
        agent_name=result.agent_name,
        content=result.content,
        metadata=result.metadata,
    )
