from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from NarrativeForge.Engine.models import Project, StoryBible, Version
from NarrativeForge.Engine.versioning import VersionManager
from NarrativeForge.Engine.versioning.diff_engine import DiffType
from NarrativeForge.Engine.storage.database import Database

router = APIRouter(prefix="/api", tags=["versions"])

_db: Database | None = None
_vm: VersionManager | None = None


def init(db: Database, vm: VersionManager):
    global _db, _vm
    _db = db
    _vm = vm


async def _require_project(project_id: UUID) -> Project:
    project = await _db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


class SnapshotCreate(BaseModel):
    description: str = ""
    author: str = ""


class VersionResponse(BaseModel):
    id: UUID
    project_id: UUID
    version_number: int
    timestamp: str
    description: str
    author: str
    size_bytes: int


def _to_response(v: Version) -> VersionResponse:
    return VersionResponse(
        id=v.id,
        project_id=v.project_id,
        version_number=v.version_number,
        timestamp=v.timestamp.isoformat(),
        description=v.description,
        author=v.author,
        size_bytes=v.size_bytes,
    )


class DiffEntryResponse(BaseModel):
    path: str
    diff_type: DiffType
    old_value: object = None
    new_value: object = None


class CompareRequest(BaseModel):
    version_id_a: UUID
    version_id_b: UUID


class CompareResponse(BaseModel):
    differences: list[DiffEntryResponse]


class RestoreResponse(BaseModel):
    project_id: UUID
    version_id: UUID


# ── Project-scoped version endpoints ──────────────────────────


@router.post(
    "/projects/{project_id}/versions",
    response_model=VersionResponse,
    status_code=201,
)
async def create_snapshot(project_id: UUID, body: SnapshotCreate):
    project = await _require_project(project_id)
    bible = StoryBible(project_id=project.id)
    version = _vm.create_snapshot(project, bible, description=body.description, author=body.author)
    return _to_response(version)


@router.get(
    "/projects/{project_id}/versions",
    response_model=list[VersionResponse],
)
async def list_versions(project_id: UUID):
    await _require_project(project_id)
    versions = _vm.list_versions(project_id)
    return [_to_response(v) for v in versions]


# ── Version-scoped endpoints ──────────────────────────────────


@router.get("/versions/{version_id}", response_model=VersionResponse)
async def get_version(version_id: UUID):
    for project in await _db.list_projects():
        version = _vm.get_version(project.id, version_id)
        if version:
            return _to_response(version)
    raise HTTPException(status_code=404, detail="Version not found")


@router.post("/versions/compare", response_model=CompareResponse)
async def compare_versions(body: CompareRequest):
    for project in await _db.list_projects():
        try:
            diff = _vm.compare_versions(project.id, body.version_id_a, body.version_id_b)
            return CompareResponse(
                differences=[
                    DiffEntryResponse(
                        path=d.path,
                        diff_type=d.diff_type,
                        old_value=d.old_value,
                        new_value=d.new_value,
                    )
                    for d in diff.differences
                ]
            )
        except ValueError:
            continue
    raise HTTPException(status_code=404, detail="One or both versions not found")


@router.post("/versions/{version_id}/restore", response_model=RestoreResponse)
async def restore_version(version_id: UUID):
    for project in await _db.list_projects():
        result = _vm.restore_version(project.id, version_id)
        if result:
            restored_project, restored_bible = result
            await _db.delete_project(project.id)
            restored_project.id = project.id
            restored_project.story_bible_id = project.story_bible_id
            await _db.create_project(restored_project)
            return RestoreResponse(project_id=project.id, version_id=version_id)
    raise HTTPException(status_code=404, detail="Version not found")


@router.delete("/versions/{version_id}", status_code=204)
async def delete_version(version_id: UUID):
    for project in await _db.list_projects():
        if _vm.delete_version(project.id, version_id):
            return
    raise HTTPException(status_code=404, detail="Version not found")
