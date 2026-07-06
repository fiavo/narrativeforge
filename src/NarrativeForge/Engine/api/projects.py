from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from NarrativeForge.Engine.models import GameGenre, Project
from NarrativeForge.Engine.storage.database import Database

router = APIRouter(prefix="/api/projects", tags=["projects"])

_db: Database | None = None


def init(db: Database):
    global _db
    _db = db


class ProjectCreate(BaseModel):
    name: str
    genre: GameGenre
    sub_genres: list[GameGenre] = Field(default_factory=list)
    target_audience: str = ""
    tone: str = ""
    themes: list[str] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    genre: GameGenre
    sub_genres: list[GameGenre]
    target_audience: str
    tone: str
    themes: list[str]
    story_bible_id: UUID | None
    settings: dict
    created_at: str
    updated_at: str


def _to_response(p: Project) -> ProjectResponse:
    return ProjectResponse(
        id=p.id,
        name=p.name,
        genre=p.genre,
        sub_genres=p.sub_genres,
        target_audience=p.target_audience,
        tone=p.tone,
        themes=p.themes,
        story_bible_id=p.story_bible_id,
        settings=p.settings,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects():
    projects = await _db.list_projects()
    return [_to_response(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID):
    project = await _db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _to_response(project)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreate):
    project = Project(
        name=body.name,
        genre=body.genre,
        sub_genres=body.sub_genres,
        target_audience=body.target_audience,
        tone=body.tone,
        themes=body.themes,
        settings=body.settings,
    )
    created = await _db.create_project(project)
    return _to_response(created)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: UUID):
    deleted = await _db.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
