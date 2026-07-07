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
from NarrativeForge.Engine.storage.database import Database

EXPORT_FORMATS = ["json", "markdown", "text", "yaml"]

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


def init(db: Database, orchestrator: PipelineOrchestrator):
    global _db, _orchestrator
    _db = db
    _orchestrator = orchestrator


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
