import json
from pathlib import Path
from uuid import UUID

from NarrativeForge.Engine.models import Project, StoryBible


class JsonStore:
    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project: Project) -> Path:
        d = self.base_dir / str(project.id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_project(self, project: Project, story_bible: StoryBible) -> Path:
        data = {
            "project": project.model_dump(mode="json"),
            "story_bible": story_bible.model_dump(mode="json"),
        }
        path = self._project_dir(project) / f"{project.name}.nforge"
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return path

    def load_project(self, path: str | Path) -> tuple[Project, StoryBible]:
        raw = Path(path).read_text(encoding="utf-8")
        data = json.loads(raw)
        project = Project(**data["project"])
        story_bible = StoryBible(**data["story_bible"])
        return project, story_bible

    def list_projects(self) -> list[Path]:
        results: list[Path] = []
        for d in sorted(self.base_dir.iterdir()):
            if not d.is_dir():
                continue
            for f in d.glob("*.nforge"):
                results.append(f)
        return results

    def delete_project(self, project_id: UUID) -> bool:
        d = self.base_dir / str(project_id)
        if d.exists() and d.is_dir():
            for f in d.iterdir():
                f.unlink()
            d.rmdir()
            return True
        return False
