from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from NarrativeForge.Engine.ai_providers.base import CompletionOptions
from NarrativeForge.Engine.agents.base import AgentContext
from NarrativeForge.Engine.pipeline.orchestrator import PipelineOrchestrator
from NarrativeForge.Engine.storage.database import Database

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
