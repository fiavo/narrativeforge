import json
from pathlib import Path
from uuid import UUID

from NarrativeForge.Engine.models import Project, StoryBible, Version
from NarrativeForge.Engine.versioning.diff_engine import DiffEngine, DiffResult


class VersionManager:
    def __init__(self, versions_dir: str | Path):
        self.versions_dir = Path(versions_dir)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.diff_engine = DiffEngine()

    def _project_dir(self, project_id: UUID) -> Path:
        d = self.versions_dir / str(project_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _version_path(self, project_id: UUID, version_id: UUID) -> Path:
        return self._project_dir(project_id) / f"{version_id}.json"

    def create_snapshot(
        self,
        project: Project,
        story_bible: StoryBible,
        description: str = "",
        author: str = "",
    ) -> Version:
        project_dir = self._project_dir(project.id)
        existing = self.list_versions(project.id)
        next_number = max((v.version_number for v in existing), default=0) + 1

        snapshot = {
            "project": project.model_dump(mode="json"),
            "story_bible": story_bible.model_dump(mode="json"),
        }

        version = Version(
            project_id=project.id,
            version_number=next_number,
            description=description,
            author=author,
            snapshot=snapshot,
            size_bytes=len(json.dumps(snapshot, default=str).encode()),
        )

        path = self._version_path(project.id, version.id)
        data = version.model_dump(mode="json")
        # Convert UUID keys to strings for JSON serialization
        data = {k: str(v) if isinstance(v, UUID) else v for k, v in data.items()}
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return version

    def list_versions(self, project_id: UUID) -> list[Version]:
        project_dir = self._project_dir(project_id)
        versions = []
        for path in project_dir.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            versions.append(Version(**data))
        versions.sort(key=lambda v: v.version_number, reverse=True)
        return versions

    def get_version(self, project_id: UUID, version_id: UUID) -> Version | None:
        path = self._version_path(project_id, version_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return Version(**data)

    def compare_versions(
        self, project_id: UUID, version_id_a: UUID, version_id_b: UUID
    ) -> DiffResult:
        v_a = self.get_version(project_id, version_id_a)
        v_b = self.get_version(project_id, version_id_b)
        if v_a is None or v_b is None:
            raise ValueError("One or both versions not found")
        return self.diff_engine.compute_diff(v_a.snapshot, v_b.snapshot)

    def restore_version(self, project_id: UUID, version_id: UUID) -> tuple[Project, StoryBible] | None:
        version = self.get_version(project_id, version_id)
        if version is None:
            return None
        project = Project(**version.snapshot["project"])
        story_bible = StoryBible(**version.snapshot["story_bible"])
        return project, story_bible

    def delete_version(self, project_id: UUID, version_id: UUID) -> bool:
        path = self._version_path(project_id, version_id)
        if path.exists():
            path.unlink()
            return True
        return False
