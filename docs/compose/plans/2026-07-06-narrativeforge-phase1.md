# NarrativeForge Phase 1: Core Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working Windows desktop application with AI-powered narrative generation for game developers.

**Architecture:** Layered monolith — WPF frontend (C# .NET 8) communicates with FastAPI Python backend over localhost HTTP. SQLite + JSON hybrid storage. Three AI agents (Story, Director, Consistency Checker) orchestrated through a six-stage generation pipeline.

**Tech Stack:** C# .NET 8, WPF, AvalonDock, CommunityToolkit.Mvvm, Python 3.11+, FastAPI, SQLAlchemy, llama-cpp-python, Pydantic

## Global Constraints

- WPF target: .NET 8.0, Windows-only
- Python target: 3.11+
- All AI outputs pass through full pipeline before delivery
- Locked Story Bible elements must never be modified by AI
- .nforge files are self-contained JSON archives
- SQLite for queries, JSON for project portability
- Local LLM support required (no API keys needed)
- Every task ends with a commit
- TDD: write failing test first, then implement

---

## Task 1: Python Project Scaffolding

**Covers:** [S4]

**Files:**
- Create: `src/NarrativeForge.Engine/pyproject.toml`
- Create: `src/NarrativeForge.Engine/main.py`
- Create: `src/NarrativeForge.Engine/config.py`
- Create: `src/NarrativeForge.Engine/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`

**Interfaces:**
- Produces: FastAPI app instance in `main.py`, config object in `config.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "narrativeforge-engine"
version = "0.1.0"
description = "AI-powered narrative engine for game development"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "sqlalchemy>=2.0.23",
    "aiosqlite>=0.19.0",
    "httpx>=0.25.0",
]

[project.optional-dependencies]
llm = [
    "llama-cpp-python>=0.2.0",
]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.1.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **Step 2: Create config.py**

```python
from pathlib import Path
from pydantic import BaseModel


class Config(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    projects_dir: Path = Path("projects")
    database_url: str = "sqlite+aiosqlite:///narrativeforge.db"
    default_model: str = "llama-3-8b"
    max_context_tokens: int = 4096
    temperature: float = 0.7

    model_config = {"env_prefix": "NF_"}


config = Config()
```

- [ ] **Step 3: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config

app = FastAPI(
    title="NarrativeForge Engine",
    version="0.1.0",
    description="AI-powered narrative engine for game development",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.host, port=config.port, reload=True)
```

- [ ] **Step 4: Create __init__.py files**

Create empty `__init__.py` in: `src/NarrativeForge.Engine/`, `tests/`, `tests/unit/`

- [ ] **Step 5: Run health check**

```bash
cd src/NarrativeForge.Engine
pip install -e ".[dev]"
uvicorn main:app --host 127.0.0.1 --port 8000 &
curl http://127.0.0.1:8000/health
# Expected: {"status":"ok","version":"0.1.0"}
kill %1
```

- [ ] **Step 6: Commit**

```bash
git add src/NarrativeForge.Engine/pyproject.toml src/NarrativeForge.Engine/main.py src/NarrativeForge.Engine/config.py src/NarrativeForge.Engine/__init__.py tests/__init__.py tests/unit/__init__.py
git commit -m "feat: scaffold Python FastAPI project with config and health endpoint"
```

---

## Task 2: Data Models

**Covers:** [S5]

**Files:**
- Create: `src/NarrativeForge.Engine/models/__init__.py`
- Create: `src/NarrativeForge.Engine/models/project.py`
- Create: `src/NarrativeForge.Engine/models/character.py`
- Create: `src/NarrativeForge.Engine/models/location.py`
- Create: `src/NarrativeForge.Engine/models/timeline.py`
- Create: `src/NarrativeForge.Engine/models/relationship.py`
- Create: `src/NarrativeForge.Engine/models/story_bible.py`
- Create: `tests/unit/test_models.py`

**Interfaces:**
- Produces: Pydantic models used by all downstream tasks (agents, storage, API)

- [ ] **Step 1: Write failing tests for models**

```python
# tests/unit/test_models.py
import pytest
from models.project import Project, GameGenre
from models.character import Character, PersonalityProfile, CharacterRole
from models.location import Location
from models.timeline import TimelineEvent
from models.relationship import Relationship, RelationshipType
from models.story_bible import StoryBible


def test_project_creation():
    p = Project(name="Test RPG", genre=GameGenre.RPG)
    assert p.name == "Test RPG"
    assert p.genre == GameGenre.RPG
    assert p.id is not None


def test_character_creation():
    c = Character(name="Arion", role=CharacterRole.PROTAGONIST)
    assert c.name == "Arion"
    assert c.role == CharacterRole.PROTAGONIST
    assert c.is_alive is True
    assert c.is_locked is False


def test_location_creation():
    loc = Location(name="Darkwood Forest", type="forest")
    assert loc.name == "Darkwood Forest"
    assert loc.connected_to == []


def test_timeline_event():
    evt = TimelineEvent(title="The Great War", order=1)
    assert evt.title == "The Great War"
    assert evt.participants == []


def test_relationship():
    rel = Relationship(
        source_id="char-1",
        target_id="char-2",
        type=RelationshipType.ENEMY,
    )
    assert rel.strength == 1.0
    assert rel.is_bidirectional is False


def test_story_bible_creation():
    sb = StoryBible(project_id="proj-1")
    assert sb.characters == {}
    assert sb.locked_elements == set()


def test_character_personality():
    p = PersonalityProfile(traits=["brave", "loyal"], fears=["betrayal"])
    assert "brave" in p.traits
    assert len(p.fears) == 1


def test_project_genre_all_values():
    genres = list(GameGenre)
    assert len(genres) >= 20
    assert GameGenre.RPG in genres
    assert GameGenre.HORROR in genres
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_models.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement models/project.py**

```python
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class GameGenre(str, Enum):
    RPG = "rpg"
    JRPG = "jrpg"
    OPEN_WORLD = "open_world"
    HORROR = "horror"
    SCI_FI = "sci_fi"
    FANTASY = "fantasy"
    MEDIEVAL = "medieval"
    CYBERPUNK = "cyberpunk"
    DETECTIVE = "detective"
    ZOMBIE = "zombie"
    PSYCHOLOGICAL = "psychological"
    SURVIVAL = "survival"
    ROMANCE = "romance"
    COMEDY = "comedy"
    DARK_FANTASY = "dark_fantasy"
    STEAMPUNK = "steampunk"
    HISTORICAL = "historical"
    MYTHOLOGY = "mythology"
    LOVECRAFTIAN = "lovecraftian"
    NOIR = "noir"
    MILITARY = "military"
    POST_APOCALYPSE = "post_apocalypse"
    VAMPIRE = "vampire"
    WEREWOLF = "werewolf"
    MYSTERY = "mystery"
    THRILLER = "thriller"
    SUPERHERO = "superhero"
    CRIME = "crime"
    SCHOOL = "school"
    ANIME = "anime"


class ProjectSettings(BaseModel):
    default_temperature: float = 0.7
    max_tokens: int = 4096
    narrative_style: str = "third_person"


class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    genre: GameGenre
    sub_genres: list[str] = Field(default_factory=list)
    target_audience: str = ""
    tone: str = ""
    themes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    story_bible_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
```

- [ ] **Step 4: Implement models/character.py**

```python
from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field


class CharacterRole(str, Enum):
    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    NPC = "npc"
    COMPANION = "companion"
    MENTOR = "mentor"
    TRICKSTER = "trickster"


class PersonalityProfile(BaseModel):
    traits: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    fears: list[str] = Field(default_factory=list)
    desires: list[str] = Field(default_factory=list)


class CharacterArc(BaseModel):
    current_state: str = ""
    growth_direction: str = ""
    key_moments: list[str] = Field(default_factory=list)


class Character(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    alias: list[str] = Field(default_factory=list)
    role: CharacterRole = CharacterRole.NPC
    personality: PersonalityProfile = Field(default_factory=PersonalityProfile)
    backstory: str = ""
    motivation: str = ""
    goals: list[str] = Field(default_factory=list)
    fears: list[str] = Field(default_factory=list)
    relationships: dict[str, str] = Field(default_factory=dict)
    arc: CharacterArc = Field(default_factory=CharacterArc)
    dialogue_style: str = ""
    appearance: str = ""
    is_alive: bool = True
    is_locked: bool = False
```

- [ ] **Step 5: Implement models/location.py**

```python
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class Location(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str = ""
    description: str = ""
    connected_to: list[str] = Field(default_factory=list)
    inhabitants: list[str] = Field(default_factory=list)
    factions_present: list[str] = Field(default_factory=list)
    significance: str = ""
    is_locked: bool = False
```

- [ ] **Step 6: Implement models/timeline.py**

```python
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    timestamp: str = ""
    participants: list[str] = Field(default_factory=list)
    location_id: str = ""
    consequences: list[str] = Field(default_factory=list)
    order: int = 0
```

- [ ] **Step 7: Implement models/relationship.py**

```python
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class RelationshipType(str, Enum):
    ENEMY = "enemy"
    ALLY = "ally"
    PARENT = "parent"
    CHILD = "child"
    LOVES = "loves"
    LEADS = "leads"
    MEMBER_OF = "member_of"
    MENTORS = "mentors"
    RIVALS = "rivals"
    SIBLING = "sibling"


class Relationship(BaseModel):
    source_id: str
    target_id: str
    type: RelationshipType
    strength: float = 1.0
    is_bidirectional: bool = False
    notes: str = ""
```

- [ ] **Step 8: Implement models/story_bible.py**

```python
from __future__ import annotations

from pydantic import BaseModel, Field

from models.character import Character
from models.location import Location
from models.relationship import Relationship
from models.timeline import TimelineEvent


class LoreEntry(BaseModel):
    id: str = ""
    title: str = ""
    content: str = ""
    category: str = ""


class Faction(BaseModel):
    id: str = ""
    name: str = ""
    description: str = ""
    members: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)


class StoryBible(BaseModel):
    project_id: str
    characters: dict[str, Character] = Field(default_factory=dict)
    locations: dict[str, Location] = Field(default_factory=dict)
    factions: dict[str, Faction] = Field(default_factory=dict)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    lore_entries: dict[str, LoreEntry] = Field(default_factory=dict)
    relationships: list[Relationship] = Field(default_factory=list)
    locked_elements: set[str] = Field(default_factory=set)
```

- [ ] **Step 9: Create models/__init__.py**

```python
from models.project import Project, GameGenre
from models.character import Character, CharacterRole, PersonalityProfile
from models.location import Location
from models.timeline import TimelineEvent
from models.relationship import Relationship, RelationshipType
from models.story_bible import StoryBible, LoreEntry, Faction

__all__ = [
    "Project", "GameGenre",
    "Character", "CharacterRole", "PersonalityProfile",
    "Location", "TimelineEvent",
    "Relationship", "RelationshipType",
    "StoryBible", "LoreEntry", "Faction",
]
```

- [ ] **Step 10: Run tests to verify they pass**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_models.py -v
# Expected: 8 passed
```

- [ ] **Step 11: Commit**

```bash
git add src/NarrativeForge.Engine/models/ tests/unit/test_models.py
git commit -m "feat: add core data models (Project, Character, Location, Timeline, Relationship, StoryBible)"
```

---

## Task 3: Storage Layer — SQLite + JSON

**Covers:** [S9]

**Files:**
- Create: `src/NarrativeForge.Engine/storage/__init__.py`
- Create: `src/NarrativeForge.Engine/storage/database.py`
- Create: `src/NarrativeForge.Engine/storage/json_store.py`
- Create: `tests/unit/test_storage.py`

**Interfaces:**
- Consumes: models from Task 2
- Produces: `Database` class with CRUD methods, `JsonStore` for .nforge files

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_storage.py
import pytest
import tempfile
from pathlib import Path
from storage.database import Database
from storage.json_store import JsonStore
from models.project import Project, GameGenre
from models.character import Character, CharacterRole


@pytest.fixture
async def db():
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.init()
    yield database
    await database.close()


@pytest.fixture
def json_store(tmp_path):
    return JsonStore(tmp_path)


async def test_create_and_get_project(db):
    project = Project(name="Test Game", genre=GameGenre.FANTASY)
    await db.create_project(project)
    loaded = await db.get_project(project.id)
    assert loaded is not None
    assert loaded.name == "Test Game"


async def test_list_projects(db):
    p1 = Project(name="Game 1", genre=GameGenre.RPG)
    p2 = Project(name="Game 2", genre=GameGenre.HORROR)
    await db.create_project(p1)
    await db.create_project(p2)
    projects = await db.list_projects()
    assert len(projects) == 2


async def test_create_and_get_character(db):
    project = Project(name="Test", genre=GameGenre.RPG)
    await db.create_project(project)
    char = Character(name="Hero", role=CharacterRole.PROTAGONIST)
    await db.create_character(project.id, char)
    chars = await db.list_characters(project.id)
    assert len(chars) == 1
    assert chars[0].name == "Hero"


async def test_delete_project(db):
    project = Project(name="Delete Me", genre=GameGenre.RPG)
    await db.create_project(project)
    await db.delete_project(project.id)
    loaded = await db.get_project(project.id)
    assert loaded is None


def test_save_and_load_nforge(json_store):
    project = Project(name="My Game", genre=GameGenre.FANTASY)
    path = json_store.save_project(project, {})
    loaded_project, loaded_bible = json_store.load_project(path)
    assert loaded_project.name == "My Game"
    assert loaded_project.genre == GameGenre.FANTASY


def test_nforge_file_extension(json_store):
    project = Project(name="Test", genre=GameGenre.RPG)
    path = json_store.save_project(project, {})
    assert path.suffix == ".nforge"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_storage.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement storage/database.py**

```python
from __future__ import annotations

import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from models.project import Project
from models.character import Character


class Base(DeclarativeBase):
    pass


class ProjectRow(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    genre: Mapped[str]
    data_json: Mapped[str]


class CharacterRow(Base):
    __tablename__ = "characters"
    id: Mapped[str] = mapped_column(primary_key=True)
    project_id: Mapped[str]
    name: Mapped[str]
    data_json: Mapped[str]
    is_locked: Mapped[bool] = mapped_column(default=False)


class Database:
    def __init__(self, url: str):
        self.engine: AsyncEngine = create_async_engine(url)
        self._session_factory = None

    async def init(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        await self.engine.dispose()

    async def create_project(self, project: Project) -> None:
        async with AsyncSession(self.engine) as session:
            row = ProjectRow(
                id=project.id,
                name=project.name,
                genre=project.genre.value,
                data_json=project.model_dump_json(),
            )
            session.add(row)
            await session.commit()

    async def get_project(self, project_id: str) -> Project | None:
        async with AsyncSession(self.engine) as session:
            row = await session.get(ProjectRow, project_id)
            if row is None:
                return None
            return Project.model_validate_json(row.data_json)

    async def list_projects(self) -> list[Project]:
        async with AsyncSession(self.engine) as session:
            result = await session.execute(text("SELECT data_json FROM projects"))
            rows = result.fetchall()
            return [Project.model_validate_json(r[0]) for r in rows]

    async def delete_project(self, project_id: str) -> None:
        async with AsyncSession(self.engine) as session:
            await session.execute(
                text("DELETE FROM projects WHERE id = :id"), {"id": project_id}
            )
            await session.execute(
                text("DELETE FROM characters WHERE project_id = :id"), {"id": project_id}
            )
            await session.commit()

    async def create_character(self, project_id: str, character: Character) -> None:
        async with AsyncSession(self.engine) as session:
            row = CharacterRow(
                id=character.id,
                project_id=project_id,
                name=character.name,
                data_json=character.model_dump_json(),
                is_locked=character.is_locked,
            )
            session.add(row)
            await session.commit()

    async def list_characters(self, project_id: str) -> list[Character]:
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                text("SELECT data_json FROM characters WHERE project_id = :pid"),
                {"pid": project_id},
            )
            rows = result.fetchall()
            return [Character.model_validate_json(r[0]) for r in rows]
```

- [ ] **Step 4: Implement storage/json_store.py**

```python
from __future__ import annotations

import json
from pathlib import Path

from models.project import Project
from models.story_bible import StoryBible


class JsonStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_project(self, project: Project, story_bible: dict) -> Path:
        data = {
            "version": "1.0",
            "project": project.model_dump(mode="json"),
            "story_bible": story_bible,
        }
        path = self.base_dir / f"{project.id}.nforge"
        path.write_text(json.dumps(data, indent=2, default=str))
        return path

    def load_project(self, path: Path) -> tuple[Project, dict]:
        data = json.loads(path.read_text())
        project = Project.model_validate(data["story_bible"] if "project" not in data else data["project"])
        story_bible = data.get("story_bible", {})
        return project, story_bible

    def list_projects(self) -> list[Path]:
        return list(self.base_dir.glob("*.nforge"))
```

- [ ] **Step 5: Create storage/__init__.py**

```python
from storage.database import Database
from storage.json_store import JsonStore

__all__ = ["Database", "JsonStore"]
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_storage.py -v
# Expected: 6 passed
```

- [ ] **Step 7: Commit**

```bash
git add src/NarrativeForge.Engine/storage/ tests/unit/test_storage.py
git commit -m "feat: add SQLite + JSON storage layer with project and character CRUD"
```

---

## Task 4: Narrative Graph

**Covers:** [S8]

**Files:**
- Create: `src/NarrativeForge.Engine/memory/__init__.py`
- Create: `src/NarrativeForge.Engine/memory/graph_store.py`
- Create: `tests/unit/test_graph.py`

**Interfaces:**
- Consumes: StoryBible from Task 2
- Produces: `NarrativeGraph` class with traversal methods used by agents and consistency checker

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_graph.py
import pytest
from memory.graph_store import NarrativeGraph
from models.character import Character
from models.relationship import Relationship, RelationshipType
from models.story_bible import StoryBible


def test_build_graph_from_story_bible():
    sb = StoryBible(project_id="p1")
    sb.characters = {
        "c1": Character(name="Hero", id="c1"),
        "c2": Character(name="Villain", id="c2"),
    }
    sb.relationships = [
        Relationship(source_id="c1", target_id="c2", type=RelationshipType.ENEMY),
    ]
    graph = NarrativeGraph.from_story_bible(sb)
    assert graph.node_count() == 2
    assert graph.edge_count() == 1


def test_get_neighbors():
    sb = StoryBible(project_id="p1")
    sb.characters = {
        "c1": Character(name="A", id="c1"),
        "c2": Character(name="B", id="c2"),
        "c3": Character(name="C", id="c3"),
    }
    sb.relationships = [
        Relationship(source_id="c1", target_id="c2", type=RelationshipType.ALLY),
        Relationship(source_id="c1", target_id="c3", type=RelationshipType.PARENT),
    ]
    graph = NarrativeGraph.from_story_bible(sb)
    neighbors = graph.get_neighbors("c1")
    assert len(neighbors) == 2
    neighbor_ids = {n.id for n in neighbors}
    assert "c2" in neighbor_ids
    assert "c3" in neighbor_ids


def test_find_path():
    sb = StoryBible(project_id="p1")
    sb.characters = {
        "c1": Character(name="A", id="c1"),
        "c2": Character(name="B", id="c2"),
        "c3": Character(name="C", id="c3"),
    }
    sb.relationships = [
        Relationship(source_id="c1", target_id="c2", type=RelationshipType.ALLY),
        Relationship(source_id="c2", target_id="c3", type=RelationshipType.ALLY),
    ]
    graph = NarrativeGraph.from_story_bible(sb)
    path = graph.find_path("c1", "c3")
    assert path is not None
    assert len(path) == 3


def test_find_path_no_route():
    sb = StoryBible(project_id="p1")
    sb.characters = {
        "c1": Character(name="A", id="c1"),
        "c2": Character(name="B", id="c2"),
    }
    graph = NarrativeGraph.from_story_bible(sb)
    path = graph.find_path("c1", "c2")
    assert path is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_graph.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement memory/graph_store.py**

```python
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from models.story_bible import StoryBible
from models.relationship import Relationship


@dataclass
class GraphNode:
    id: str
    type: str
    name: str
    properties: dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    target_id: str
    relationship: str
    weight: float = 1.0


class NarrativeGraph:
    def __init__(self):
        self.nodes: dict[str, GraphNode] = {}
        self.adjacency: dict[str, list[GraphEdge]] = defaultdict(list)

    @classmethod
    def from_story_bible(cls, sb: StoryBible) -> NarrativeGraph:
        graph = cls()

        for char_id, char in sb.characters.items():
            graph.nodes[char_id] = GraphNode(
                id=char_id, type="character", name=char.name
            )

        for loc_id, loc in sb.locations.items():
            graph.nodes[loc_id] = GraphNode(
                id=loc_id, type="location", name=loc.name
            )

        for faction_id, faction in sb.factions.items():
            graph.nodes[faction_id] = GraphNode(
                id=faction_id, type="faction", name=faction.name
            )

        for rel in sb.relationships:
            graph.adjacency[rel.source_id].append(
                GraphEdge(
                    target_id=rel.target_id,
                    relationship=rel.type.value,
                    weight=rel.strength,
                )
            )
            if rel.is_bidirectional:
                graph.adjacency[rel.target_id].append(
                    GraphEdge(
                        target_id=rel.source_id,
                        relationship=rel.type.value,
                        weight=rel.strength,
                    )
                )

        return graph

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return sum(len(edges) for edges in self.adjacency.values())

    def get_neighbors(self, node_id: str) -> list[GraphNode]:
        neighbors = []
        for edge in self.adjacency.get(node_id, []):
            if edge.target_id in self.nodes:
                neighbors.append(self.nodes[edge.target_id])
        return neighbors

    def find_path(self, start_id: str, end_id: str) -> list[str] | None:
        if start_id not in self.nodes or end_id not in self.nodes:
            return None

        visited: set[str] = set()
        queue: deque[tuple[str, list[str]]] = deque([(start_id, [start_id])])

        while queue:
            current, path = queue.popleft()
            if current == end_id:
                return path
            if current in visited:
                continue
            visited.add(current)

            for edge in self.adjacency.get(current, []):
                if edge.target_id not in visited:
                    queue.append((edge.target_id, path + [edge.target_id]))

        return None

    def get_relationships(self, node_id: str) -> list[GraphEdge]:
        return self.adjacency.get(node_id, [])
```

- [ ] **Step 4: Create memory/__init__.py**

```python
from memory.graph_store import NarrativeGraph

__all__ = ["NarrativeGraph"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_graph.py -v
# Expected: 4 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/NarrativeForge.Engine/memory/ tests/unit/test_graph.py
git commit -m "feat: add narrative graph with traversal and pathfinding"
```

---

## Task 5: AI Provider Abstraction

**Covers:** [S10]

**Files:**
- Create: `src/NarrativeForge.Engine/ai_providers/__init__.py`
- Create: `src/NarrativeForge.Engine/ai_providers/base.py`
- Create: `src/NarrativeForge.Engine/ai_providers/llama_provider.py`
- Create: `src/NarrativeForge.Engine/ai_providers/openai_compatible.py`
- Create: `tests/unit/test_providers.py`

**Interfaces:**
- Produces: `AIProvider` ABC, `LlamaProvider`, `OpenAICompatibleProvider`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_providers.py
import pytest
from ai_providers.base import AIProvider, Message


def test_message_creation():
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"


def test_system_message():
    msg = Message.system("You are a story writer.")
    assert msg.role == "system"


def test_user_message():
    msg = Message.user("Write a story")
    assert msg.role == "user"


def test_assistant_message():
    msg = Message.assistant("Once upon a time...")
    assert msg.role == "assistant"


async def test_mock_provider():
    from unittest.mock import AsyncMock, MagicMock

    class MockProvider(AIProvider):
        def __init__(self):
            self.name = "mock"

        async def complete(self, messages, temperature=0.7, max_tokens=4096):
            return "Mock response"

        async def stream(self, messages, temperature=0.7, max_tokens=4096):
            yield "Mock "
            yield "streaming"

    provider = MockProvider()
    result = await provider.complete([Message.user("test")])
    assert result == "Mock response"

    chunks = []
    async for chunk in provider.stream([Message.user("test")]):
        chunks.append(chunk)
    assert "".join(chunks) == "Mock streaming"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_providers.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement ai_providers/base.py**

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class Message:
    role: str
    content: str

    @classmethod
    def system(cls, content: str) -> Message:
        return cls(role="system", content=content)

    @classmethod
    def user(cls, content: str) -> Message:
        return cls(role="user", content=content)

    @classmethod
    def assistant(cls, content: str) -> Message:
        return cls(role="assistant", content=content)

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class AIProvider(ABC):
    name: str

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        pass
```

- [ ] **Step 4: Implement ai_providers/llama_provider.py**

```python
from __future__ import annotations

from typing import AsyncIterator

from ai_providers.base import AIProvider, Message


class LlamaProvider(AIProvider):
    def __init__(self, model_path: str, n_ctx: int = 4096, n_gpu_layers: int = 0):
        self.name = "llama_cpp"
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self._llm = None

    def _load_model(self):
        if self._llm is None:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False,
            )

    def _format_prompt(self, messages: list[Message]) -> str:
        parts = []
        for msg in messages:
            if msg.role == "system":
                parts.append(f"<|system|>\n{msg.content}\n")
            elif msg.role == "user":
                parts.append(f"<|user|>\n{msg.content}\n")
            elif msg.role == "assistant":
                parts.append(f"<|assistant|>\n{msg.content}\n")
        parts.append("<|assistant|>\n")
        return "".join(parts)

    async def complete(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        self._load_model()
        prompt = self._format_prompt(messages)
        output = self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|user|>", "<|system|>"],
        )
        return output["choices"][0]["text"]

    async def stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        self._load_model()
        prompt = self._format_prompt(messages)
        output = self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|user|>", "<|system|>"],
            stream=True,
        )
        for chunk in output:
            yield chunk["choices"][0]["text"]
```

- [ ] **Step 5: Implement ai_providers/openai_compatible.py**

```python
from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from ai_providers.base import AIProvider, Message


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, base_url: str, api_key: str = "not-needed", model: str = "default"):
        self.name = "openai_compatible"
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._client = httpx.AsyncClient(timeout=120.0)

    async def complete(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        response = await self._client.post(
            f"{self.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [m.to_dict() for m in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    async def stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        async with self._client.stream(
            "POST",
            f"{self.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [m.to_dict() for m in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
```

- [ ] **Step 6: Create ai_providers/__init__.py**

```python
from ai_providers.base import AIProvider, Message
from ai_providers.llama_provider import LlamaProvider
from ai_providers.openai_compatible import OpenAICompatibleProvider

__all__ = ["AIProvider", "Message", "LlamaProvider", "OpenAICompatibleProvider"]
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_providers.py -v
# Expected: 5 passed
```

- [ ] **Step 8: Commit**

```bash
git add src/NarrativeForge.Engine/ai_providers/ tests/unit/test_providers.py
git commit -m "feat: add AI provider abstraction with llama-cpp and OpenAI-compatible backends"
```

---

## Task 6: AI Agents — Base, Story, Director, Consistency

**Covers:** [S6]

**Files:**
- Create: `src/NarrativeForge.Engine/agents/__init__.py`
- Create: `src/NarrativeForge.Engine/agents/base.py`
- Create: `src/NarrativeForge.Engine/agents/story_agent.py`
- Create: `src/NarrativeForge.Engine/agents/director_agent.py`
- Create: `src/NarrativeForge.Engine/agents/consistency_checker.py`
- Create: `tests/unit/test_agents.py`

**Interfaces:**
- Consumes: AIProvider from Task 5, NarrativeGraph from Task 4, models from Task 2
- Produces: Agent classes used by the pipeline in Task 7

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_agents.py
import pytest
from unittest.mock import AsyncMock
from agents.base import AgentContext, AgentResult
from agents.story_agent import StoryAgent
from agents.director_agent import DirectorAgent
from agents.consistency_checker import ConsistencyChecker
from ai_providers.base import AIProvider, Message
from models.project import Project, GameGenre
from models.story_bible import StoryBible
from memory.graph_store import NarrativeGraph


class FakeProvider(AIProvider):
    def __init__(self):
        self.name = "fake"

    async def complete(self, messages, temperature=0.7, max_tokens=4096):
        return '{"score": 8, "content": "Generated narrative text", "issues": []}'

    async def stream(self, messages, temperature=0.7, max_tokens=4096):
        yield "Generated text"


def make_context():
    project = Project(name="Test", genre=GameGenre.FANTASY)
    sb = StoryBible(project_id=project.id)
    graph = NarrativeGraph.from_story_bible(sb)
    return AgentContext(
        project=project,
        story_bible=sb,
        graph=graph,
        user_request="Write an opening chapter",
        generation_params={},
        previous_results=[],
        locked_elements=set(),
    )


async def test_story_agent_execute():
    agent = StoryAgent(FakeProvider())
    result = await agent.execute(make_context())
    assert isinstance(result, AgentResult)
    assert result.agent_name == "story"
    assert len(result.content) > 0


async def test_director_agent_execute():
    agent = DirectorAgent(FakeProvider())
    result = await agent.execute(make_context())
    assert isinstance(result, AgentResult)
    assert result.agent_name == "director"


async def test_consistency_checker_execute():
    agent = ConsistencyChecker(FakeProvider())
    result = await agent.execute(make_context())
    assert isinstance(result, AgentResult)
    assert result.agent_name == "consistency_checker"
    assert "issues" in result.metadata
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_agents.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement agents/base.py**

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ai_providers.base import AIProvider
from models.project import Project
from models.story_bible import StoryBible
from memory.graph_store import NarrativeGraph


@dataclass
class AgentContext:
    project: Project
    story_bible: StoryBible
    graph: NarrativeGraph
    user_request: str
    generation_params: dict
    previous_results: list[AgentResult]
    locked_elements: set[str]


@dataclass
class AgentResult:
    agent_name: str
    content: str
    metadata: dict = field(default_factory=dict)
    changes: dict = field(default_factory=dict)


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self, provider: AIProvider):
        self.provider = provider

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        pass

    def build_system_prompt(self, context: AgentContext) -> str:
        return "You are a professional game narrative designer."
```

- [ ] **Step 4: Implement agents/story_agent.py**

```python
from __future__ import annotations

from agents.base import BaseAgent, AgentContext, AgentResult


class StoryAgent(BaseAgent):
    name = "story"

    def build_system_prompt(self, context: AgentContext) -> str:
        genre = context.project.genre.value
        tone = context.project.tone or "immersive"
        return (
            f"You are a AAA game narrative writer specializing in {genre} games.\n"
            f"Tone: {tone}\n"
            f"Write with emotional depth, vivid imagery, and compelling character voice.\n"
            f"Never break continuity with the story bible.\n"
            f"Focus on show-don't-tell, pacing, and player engagement."
        )

    async def execute(self, context: AgentContext) -> AgentResult:
        from ai_providers.base import Message

        system = self.build_system_prompt(context)
        user_msg = self._build_user_prompt(context)

        response = await self.provider.complete([
            Message.system(system),
            Message.user(user_msg),
        ], temperature=context.generation_params.get("temperature", 0.7))

        return AgentResult(
            agent_name=self.name,
            content=response,
            metadata={"genre": context.project.genre.value},
        )

    def _build_user_prompt(self, context: AgentContext) -> str:
        parts = [f"Request: {context.user_request}"]

        if context.story_bible.characters:
            char_list = ", ".join(context.story_bible.characters.keys())
            parts.append(f"Known characters: {char_list}")

        if context.story_bible.locations:
            loc_list = ", ".join(context.story_bible.locations.keys())
            parts.append(f"Known locations: {loc_list}")

        if context.previous_results:
            for prev in context.previous_results:
                parts.append(f"Previous context ({prev.agent_name}): {prev.content[:500]}")

        return "\n".join(parts)
```

- [ ] **Step 5: Implement agents/director_agent.py**

```python
from __future__ import annotations

from agents.base import BaseAgent, AgentContext, AgentResult


class DirectorAgent(BaseAgent):
    name = "director"

    def build_system_prompt(self, context: AgentContext) -> str:
        return (
            "You are the Director Agent — the orchestrator of narrative generation.\n"
            "Your job is to analyze requests, decompose them into steps,\n"
            "coordinate other agents, and ensure coherent output.\n"
            "Always maintain story bible consistency and respect locked elements."
        )

    async def execute(self, context: AgentContext) -> AgentResult:
        from ai_providers.base import Message

        system = self.build_system_prompt(context)
        user_msg = (
            f"Analyze this narrative request and provide a structured plan:\n"
            f"Request: {context.user_request}\n"
            f"Genre: {context.project.genre.value}\n"
            f"Characters in bible: {len(context.story_bible.characters)}\n"
            f"Locations in bible: {len(context.story_bible.locations)}\n"
        )

        response = await self.provider.complete([
            Message.system(system),
            Message.user(user_msg),
        ], temperature=0.3)

        return AgentResult(
            agent_name=self.name,
            content=response,
            metadata={"analysis": "complete"},
        )
```

- [ ] **Step 6: Implement agents/consistency_checker.py**

```python
from __future__ import annotations

from agents.base import BaseAgent, AgentContext, AgentResult


class ConsistencyChecker(BaseAgent):
    name = "consistency_checker"

    def build_system_prompt(self, context: AgentContext) -> str:
        return (
            "You are the Consistency Checker — a narrative quality assurance agent.\n"
            "Analyze the provided content against the story bible.\n"
            "Detect: plot holes, timeline contradictions, character behavior violations,\n"
            "lore conflicts, dead character resurrection, geography errors.\n"
            "Return JSON with: score (0-10), issues (list of {severity, description, location})."
        )

    async def execute(self, context: AgentContext) -> AgentResult:
        import json
        from ai_providers.base import Message

        system = self.build_system_prompt(context)

        story_bible_summary = self._summarize_bible(context)
        content_to_check = ""
        if context.previous_results:
            content_to_check = "\n".join(r.content for r in context.previous_results)

        user_msg = (
            f"Story Bible:\n{story_bible_summary}\n\n"
            f"Content to validate:\n{content_to_check or context.user_request}\n\n"
            f"Return JSON: {{\"score\": <0-10>, \"issues\": [{{\"severity\": \"...\", "
            f"\"description\": \"...\", \"location\": \"...\"}}]}}"
        )

        response = await self.provider.complete([
            Message.system(system),
            Message.user(user_msg),
        ], temperature=0.1)

        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            parsed = {"score": 5, "issues": [{"severity": "warning", "description": "Could not parse checker output", "location": "output"}]}

        return AgentResult(
            agent_name=self.name,
            content=response,
            metadata={"issues": parsed.get("issues", []), "score": parsed.get("score", 5)},
        )

    def _summarize_bible(self, context: AgentContext) -> str:
        parts = []
        for char_id, char in context.story_bible.characters.items():
            parts.append(f"Character: {char.name} (ID: {char_id}, alive: {char.is_alive}, role: {char.role.value})")
        for loc_id, loc in context.story_bible.locations.items():
            parts.append(f"Location: {loc.name} (ID: {loc_id})")
        for rel in context.story_bible.relationships:
            parts.append(f"Relationship: {rel.source_id} --{rel.type.value}--> {rel.target_id}")
        return "\n".join(parts) if parts else "Empty story bible"
```

- [ ] **Step 7: Create agents/__init__.py**

```python
from agents.base import BaseAgent, AgentContext, AgentResult
from agents.story_agent import StoryAgent
from agents.director_agent import DirectorAgent
from agents.consistency_checker import ConsistencyChecker

__all__ = [
    "BaseAgent", "AgentContext", "AgentResult",
    "StoryAgent", "DirectorAgent", "ConsistencyChecker",
]
```

- [ ] **Step 8: Run tests to verify they pass**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_agents.py -v
# Expected: 4 passed
```

- [ ] **Step 9: Commit**

```bash
git add src/NarrativeForge.Engine/agents/ tests/unit/test_agents.py
git commit -m "feat: add AI agents (Story, Director, Consistency Checker) with provider abstraction"
```

---

## Task 7: Multi-Stage Generation Pipeline

**Covers:** [S7]

**Files:**
- Create: `src/NarrativeForge.Engine/pipeline/__init__.py`
- Create: `src/NarrativeForge.Engine/pipeline/orchestrator.py`
- Create: `tests/unit/test_pipeline.py`

**Interfaces:**
- Consumes: all agents from Task 6, AIProvider from Task 5
- Produces: `PipelineOrchestrator` used by API routes

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_pipeline.py
import pytest
from pipeline.orchestrator import PipelineOrchestrator, PipelineResult
from agents.base import AgentContext
from ai_providers.base import AIProvider, Message
from models.project import Project, GameGenre
from models.story_bible import StoryBible
from memory.graph_store import NarrativeGraph


class FakeProvider(AIProvider):
    def __init__(self):
        self.name = "fake"

    async def complete(self, messages, temperature=0.7, max_tokens=4096):
        return '{"score": 9, "content": "Pipeline output", "issues": []}'

    async def stream(self, messages, temperature=0.7, max_tokens=4096):
        yield "Pipeline output"


def make_context():
    project = Project(name="Test", genre=GameGenre.FANTASY)
    sb = StoryBible(project_id=project.id)
    graph = NarrativeGraph.from_story_bible(sb)
    return AgentContext(
        project=project,
        story_bible=sb,
        graph=graph,
        user_request="Write a prologue",
        generation_params={},
        previous_results=[],
        locked_elements=set(),
    )


async def test_pipeline_executes_all_stages():
    orchestrator = PipelineOrchestrator(FakeProvider())
    result = await orchestrator.run(make_context())
    assert isinstance(result, PipelineResult)
    assert len(result.stages_completed) > 0
    assert len(result.content) > 0


async def test_pipeline_returns_consistency_score():
    orchestrator = PipelineOrchestrator(FakeProvider())
    result = await orchestrator.run(make_context())
    assert "consistency_score" in result.metadata


async def test_pipeline_stages_in_order():
    orchestrator = PipelineOrchestrator(FakeProvider())
    result = await orchestrator.run(make_context())
    expected_order = ["director", "story", "consistency_checker"]
    assert result.stages_completed[:3] == expected_order
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_pipeline.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement pipeline/orchestrator.py**

```python
from __future__ import annotations

from dataclasses import dataclass, field

from ai_providers.base import AIProvider
from agents.base import AgentContext, AgentResult
from agents.story_agent import StoryAgent
from agents.director_agent import DirectorAgent
from agents.consistency_checker import ConsistencyChecker


@dataclass
class PipelineResult:
    content: str
    stages_completed: list[str] = field(default_factory=list)
    results: list[AgentResult] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class PipelineOrchestrator:
    def __init__(self, provider: AIProvider):
        self.director = DirectorAgent(provider)
        self.story = StoryAgent(provider)
        self.consistency = ConsistencyChecker(provider)

    async def run(self, context: AgentContext) -> PipelineResult:
        results: list[AgentResult] = []
        stages: list[str] = []

        # Stage 1: Director analyzes and plans
        director_result = await self.director.execute(context)
        results.append(director_result)
        stages.append("director")

        # Stage 2: Story agent generates content
        context_with_director = AgentContext(
            project=context.project,
            story_bible=context.story_bible,
            graph=context.graph,
            user_request=context.user_request,
            generation_params=context.generation_params,
            previous_results=results,
            locked_elements=context.locked_elements,
        )
        story_result = await self.story.execute(context_with_director)
        results.append(story_result)
        stages.append("story")

        # Stage 3: Consistency check
        context_with_all = AgentContext(
            project=context.project,
            story_bible=context.story_bible,
            graph=context.graph,
            user_request=context.user_request,
            generation_params=context.generation_params,
            previous_results=results,
            locked_elements=context.locked_elements,
        )
        consistency_result = await self.consistency.execute(context_with_all)
        results.append(consistency_result)
        stages.append("consistency_checker")

        # Extract final content and metadata
        final_content = story_result.content
        consistency_score = consistency_result.metadata.get("score", 0)
        issues = consistency_result.metadata.get("issues", [])

        return PipelineResult(
            content=final_content,
            stages_completed=stages,
            results=results,
            metadata={
                "consistency_score": consistency_score,
                "issues": issues,
                "director_analysis": director_result.content,
            },
        )
```

- [ ] **Step 4: Create pipeline/__init__.py**

```python
from pipeline.orchestrator import PipelineOrchestrator, PipelineResult

__all__ = ["PipelineOrchestrator", "PipelineResult"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_pipeline.py -v
# Expected: 3 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/NarrativeForge.Engine/pipeline/ tests/unit/test_pipeline.py
git commit -m "feat: add multi-stage generation pipeline with Director, Story, and Consistency stages"
```

---

## Task 8: FastAPI Routes

**Covers:** [S12]

**Files:**
- Create: `src/NarrativeForge.Engine/api/__init__.py`
- Create: `src/NarrativeForge.Engine/api/projects.py`
- Create: `src/NarrativeForge.Engine/api/generation.py`
- Modify: `src/NarrativeForge.Engine/main.py`
- Create: `tests/unit/test_api.py`

**Interfaces:**
- Consumes: Database from Task 3, PipelineOrchestrator from Task 7
- Produces: REST endpoints consumed by WPF frontend

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_create_project(client):
    response = await client.post("/api/projects", json={
        "name": "Test Game",
        "genre": "fantasy",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Game"
    assert "id" in data


async def test_list_projects(client):
    await client.post("/api/projects", json={"name": "Game A", "genre": "rpg"})
    await client.post("/api/projects", json={"name": "Game B", "genre": "horror"})
    response = await client.get("/api/projects")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_project(client):
    create_resp = await client.post("/api/projects", json={"name": "My Game", "genre": "fantasy"})
    project_id = create_resp.json()["id"]
    response = await client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "My Game"


async def test_delete_project(client):
    create_resp = await client.post("/api/projects", json={"name": "Delete", "genre": "rpg"})
    project_id = create_resp.json()["id"]
    response = await client.delete(f"/api/projects/{project_id}")
    assert response.status_code == 200
    get_resp = await client.get(f"/api/projects/{project_id}")
    assert get_resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_api.py -v
# Expected: FAIL — routes not registered
```

- [ ] **Step 3: Implement api/projects.py**

```python
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.project import Project, GameGenre
from storage.database import Database

router = APIRouter(prefix="/api/projects", tags=["projects"])

_db: Database | None = None


def init_routes(db: Database):
    global _db
    _db = db


class CreateProjectRequest(BaseModel):
    name: str
    genre: str
    sub_genres: list[str] = []
    target_audience: str = ""
    tone: str = ""
    themes: list[str] = []


@router.get("")
async def list_projects():
    projects = await _db.list_projects()
    return [p.model_dump(mode="json") for p in projects]


@router.get("/{project_id}")
async def get_project(project_id: str):
    project = await _db.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.model_dump(mode="json")


@router.post("")
async def create_project(req: CreateProjectRequest):
    project = Project(
        name=req.name,
        genre=GameGenre(req.genre),
        sub_genres=req.sub_genres,
        target_audience=req.target_audience,
        tone=req.tone,
        themes=req.themes,
    )
    await _db.create_project(project)
    return project.model_dump(mode="json")


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    project = await _db.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await _db.delete_project(project_id)
    return {"deleted": project_id}
```

- [ ] **Step 4: Implement api/generation.py**

```python
from __future__ import annotations

import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.project import Project
from models.story_bible import StoryBible
from memory.graph_store import NarrativeGraph
from agents.base import AgentContext
from pipeline.orchestrator import PipelineOrchestrator
from ai_providers.base import AIProvider

router = APIRouter(prefix="/api/generate", tags=["generation"])

_orchestrator: PipelineOrchestrator | None = None
_project_getter = None


def init_routes(provider: AIProvider, project_getter):
    global _orchestrator, _project_getter
    _orchestrator = PipelineOrchestrator(provider)
    _project_getter = project_getter


class GenerateRequest(BaseModel):
    project_id: str
    request: str
    temperature: float = 0.7


@router.post("")
async def generate(req: GenerateRequest):
    project = await _project_getter(req.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    sb = StoryBible(project_id=project.id)
    graph = NarrativeGraph.from_story_bible(sb)

    context = AgentContext(
        project=project,
        story_bible=sb,
        graph=graph,
        user_request=req.request,
        generation_params={"temperature": req.temperature},
        previous_results=[],
        locked_elements=set(),
    )

    result = await _orchestrator.run(context)

    return {
        "content": result.content,
        "stages": result.stages_completed,
        "metadata": result.metadata,
    }
```

- [ ] **Step 5: Update main.py to register routes**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from api.projects import router as projects_router, init_routes as init_project_routes
from api.generation import router as generation_router, init_routes as init_generation_routes
from storage.database import Database
from ai_providers.openai_compatible import OpenAICompatibleProvider

app = FastAPI(
    title="NarrativeForge Engine",
    version="0.1.0",
    description="AI-powered narrative engine for game development",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(generation_router)


@app.on_event("startup")
async def startup():
    db = Database(config.database_url)
    await db.init()
    app.state.db = db
    init_project_routes(db)

    provider = OpenAICompatibleProvider(
        base_url="http://localhost:11434",
        model=config.default_model,
    )
    init_generation_routes(provider, db.get_project)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 6: Create api/__init__.py**

```python
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
cd src/NarrativeForge.Engine
pytest tests/unit/test_api.py -v
# Expected: 5 passed
```

- [ ] **Step 8: Commit**

```bash
git add src/NarrativeForge.Engine/api/ src/NarrativeForge.Engine/main.py tests/unit/test_api.py
git commit -m "feat: add FastAPI routes for project CRUD and generation pipeline"
```

---

## Task 9: C# Project Scaffolding + Shared DTOs

**Covers:** [S3, S4, S12]

**Files:**
- Create: `src/NarrativeForge/NarrativeForge.sln`
- Create: `src/NarrativeForge/NarrativeForge.Core/NarrativeForge.Core.csproj`
- Create: `src/NarrativeForge/NarrativeForge.Core/DTOs/ProjectDto.cs`
- Create: `src/NarrativeForge/NarrativeForge.Core/DTOs/CharacterDto.cs`
- Create: `src/NarrativeForge/NarrativeForge.Core/DTOs/GenerationDto.cs`
- Create: `src/NarrativeForge/NarrativeForge.Core/Enums/GameGenre.cs`

**Interfaces:**
- Produces: Shared C# types matching Python Pydantic models

- [ ] **Step 1: Create solution and Core project**

```bash
cd src/NarrativeForge
dotnet new sln -n NarrativeForge
dotnet new classlib -n NarrativeForge.Core -f net8.0
dotnet sln add NarrativeForge.Core/NarrativeForge.Core.csproj
```

- [ ] **Step 2: Remove default Class1.cs**

```bash
rm src/NarrativeForge/NarrativeForge.Core/Class1.cs
```

- [ ] **Step 3: Implement Enums/GameGenre.cs**

```csharp
namespace NarrativeForge.Core.Enums;

public enum GameGenre
{
    RPG,
    JRPG,
    OpenWorld,
    Horror,
    SciFi,
    Fantasy,
    Medieval,
    Cyberpunk,
    Detective,
    Zombie,
    Psychological,
    Survival,
    Romance,
    Comedy,
    DarkFantasy,
    Steampunk,
    Historical,
    Mythology,
    Lovecraftian,
    Noir,
    Military,
    PostApocalypse,
    Vampire,
    Werewolf,
    Mystery,
    Thriller,
    Superhero,
    Crime,
    School,
    Anime
}
```

- [ ] **Step 4: Implement DTOs/ProjectDto.cs**

```csharp
namespace NarrativeForge.Core.DTOs;

using NarrativeForge.Core.Enums;

public class ProjectDto
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public string Name { get; set; } = string.Empty;
    public GameGenre Genre { get; set; }
    public List<string> SubGenres { get; set; } = new();
    public string TargetAudience { get; set; } = string.Empty;
    public string Tone { get; set; } = string.Empty;
    public List<string> Themes { get; set; } = new();
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}

public class CreateProjectRequest
{
    public string Name { get; set; } = string.Empty;
    public string Genre { get; set; } = string.Empty;
    public List<string> SubGenres { get; set; } = new();
    public string TargetAudience { get; set; } = string.Empty;
    public string Tone { get; set; } = string.Empty;
    public List<string> Themes { get; set; } = new();
}
```

- [ ] **Step 5: Implement DTOs/CharacterDto.cs**

```csharp
namespace NarrativeForge.Core.DTOs;

public class CharacterDto
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public string Name { get; set; } = string.Empty;
    public List<string> Alias { get; set; } = new();
    public string Role { get; set; } = "npc";
    public PersonalityDto Personality { get; set; } = new();
    public string Backstory { get; set; } = string.Empty;
    public string Motivation { get; set; } = string.Empty;
    public List<string> Goals { get; set; } = new();
    public List<string> Fears { get; set; } = new();
    public bool IsAlive { get; set; } = true;
    public bool IsLocked { get; set; } = false;
}

public class PersonalityDto
{
    public List<string> Traits { get; set; } = new();
    public List<string> Values { get; set; } = new();
    public List<string> Fears { get; set; } = new();
    public List<string> Desires { get; set; } = new();
}
```

- [ ] **Step 6: Implement DTOs/GenerationDto.cs**

```csharp
namespace NarrativeForge.Core.DTOs;

public class GenerateRequestDto
{
    public string ProjectId { get; set; } = string.Empty;
    public string Request { get; set; } = string.Empty;
    public double Temperature { get; set; } = 0.7;
}

public class GenerateResponseDto
{
    public string Content { get; set; } = string.Empty;
    public List<string> Stages { get; set; } = new();
    public GenerationMetadata Metadata { get; set; } = new();
}

public class GenerationMetadata
{
    public int ConsistencyScore { get; set; }
    public List<ConsistencyIssue> Issues { get; set; } = new();
}

public class ConsistencyIssue
{
    public string Severity { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Location { get; set; } = string.Empty;
}
```

- [ ] **Step 7: Build Core project**

```bash
cd src/NarrativeForge
dotnet build NarrativeForge.Core/NarrativeForge.Core.csproj
# Expected: Build succeeded
```

- [ ] **Step 8: Commit**

```bash
git add src/NarrativeForge/
git commit -m "feat: scaffold C# solution with shared DTOs and enums"
```

---

## Task 10: WPF Desktop Application

**Covers:** [S11]

**Files:**
- Create: `src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj`
- Create: `src/NarrativeForge/NarrativeForge.App/App.xaml`
- Create: `src/NarrativeForge/NarrativeForge.App/App.xaml.cs`
- Create: `src/NarrativeForge/NarrativeForge.App/MainWindow.xaml`
- Create: `src/NarrativeForge/NarrativeForge.App/MainWindow.xaml.cs`
- Create: `src/NarrativeForge/NarrativeForge.App/ViewModels/MainViewModel.cs`
- Create: `src/NarrativeForge/NarrativeForge.App/Services/ApiClient.cs`
- Modify: `src/NarrativeForge/NarrativeForge.sln`

**Interfaces:**
- Consumes: DTOs from Task 9
- Produces: Working WPF desktop shell

- [ ] **Step 1: Create WPF project**

```bash
cd src/NarrativeForge
dotnet new wpf -n NarrativeForge.App -f net8.0-windows
dotnet sln add NarrativeForge.App/NarrativeForge.App.csproj
cd NarrativeForge.App
dotnet add reference ../NarrativeForge.Core/NarrativeForge.Core.csproj
dotnet add package CommunityToolkit.Mvvm --version 8.2.2
```

- [ ] **Step 2: Remove default files**

```bash
rm src/NarrativeForge/NarrativeForge.App/MainWindow.xaml
rm src/NarrativeForge/NarrativeForge.App/MainWindow.xaml.cs
```

- [ ] **Step 3: Implement Services/ApiClient.cs**

```csharp
using System.Net.Http.Json;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Services;

public class ApiClient
{
    private readonly HttpClient _http;

    public ApiClient(string baseUrl = "http://127.0.0.1:8000")
    {
        _http = new HttpClient { BaseAddress = new Uri(baseUrl) };
    }

    public async Task<bool> HealthCheckAsync()
    {
        try
        {
            var response = await _http.GetAsync("/health");
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public async Task<List<ProjectDto>> GetProjectsAsync()
    {
        return await _http.GetFromJsonAsync<List<ProjectDto>>("/api/projects") ?? new();
    }

    public async Task<ProjectDto?> GetProjectAsync(string id)
    {
        return await _http.GetFromJsonAsync<ProjectDto>($"/api/projects/{id}");
    }

    public async Task<ProjectDto> CreateProjectAsync(CreateProjectRequest request)
    {
        var response = await _http.PostAsJsonAsync("/api/projects", request);
        response.EnsureSuccessStatusCode();
        return (await response.Content.ReadFromJsonAsync<ProjectDto>())!;
    }

    public async Task DeleteProjectAsync(string id)
    {
        var response = await _http.DeleteAsync($"/api/projects/{id}");
        response.EnsureSuccessStatusCode();
    }

    public async Task<GenerateResponseDto> GenerateAsync(GenerateRequestDto request)
    {
        var response = await _http.PostAsJsonAsync("/api/generate", request);
        response.EnsureSuccessStatusCode();
        return (await response.Content.ReadFromJsonAsync<GenerateResponseDto>())!;
    }
}
```

- [ ] **Step 4: Implement ViewModels/MainViewModel.cs**

```csharp
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using NarrativeForge.App.Services;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.ViewModels;

public partial class MainViewModel : ObservableObject
{
    private readonly ApiClient _api;

    [ObservableProperty]
    private string _statusText = "Disconnected";

    [ObservableProperty]
    private string _generationInput = string.Empty;

    [ObservableProperty]
    private string _generatedContent = string.Empty;

    [ObservableProperty]
    private bool _isGenerating;

    [ObservableProperty]
    private ProjectDto? _currentProject;

    public MainViewModel()
    {
        _api = new ApiClient();
    }

    [RelayCommand]
    private async Task ConnectAsync()
    {
        var healthy = await _api.HealthCheckAsync();
        StatusText = healthy ? "Connected" : "Connection failed";
    }

    [RelayCommand]
    private async Task GenerateAsync()
    {
        if (string.IsNullOrWhiteSpace(GenerationInput) || CurrentProject is null)
            return;

        IsGenerating = true;
        GeneratedContent = "Generating...";

        try
        {
            var response = await _api.GenerateAsync(new GenerateRequestDto
            {
                ProjectId = CurrentProject.Id,
                Request = GenerationInput,
                Temperature = 0.7,
            });

            GeneratedContent = response.Content;
            StatusText = $"Score: {response.Metadata.ConsistencyScore}/10 | Stages: {string.Join(" → ", response.Stages)}";
        }
        catch (Exception ex)
        {
            GeneratedContent = $"Error: {ex.Message}";
        }
        finally
        {
            IsGenerating = false;
        }
    }

    [RelayCommand]
    private async Task NewProjectAsync()
    {
        var project = await _api.CreateProjectAsync(new CreateProjectRequest
        {
            Name = "New Game",
            Genre = "fantasy",
        });
        CurrentProject = project;
        StatusText = $"Project: {project.Name}";
    }
}
```

- [ ] **Step 5: Implement MainWindow.xaml**

```xml
<Window x:Class="NarrativeForge.App.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:vm="clr-namespace:NarrativeForge.App.ViewModels"
        Title="NarrativeForge" Height="700" Width="1100"
        Background="#1E1E2E">

    <Window.DataContext>
        <vm:MainViewModel />
    </Window.DataContext>

    <Grid>
        <Grid.RowDefinitions>
            <RowDefinition Height="40" />
            <RowDefinition Height="*" />
            <RowDefinition Height="30" />
        </Grid.RowDefinitions>

        <!-- Menu Bar -->
        <Menu Grid.Row="0" Background="#181825">
            <MenuItem Header="_Project">
                <MenuItem Header="_New Project" Command="{Binding NewProjectCommand}" />
                <MenuItem Header="_Connect to Engine" Command="{Binding ConnectCommand}" />
            </MenuItem>
            <MenuItem Header="_Generate">
                <MenuItem Header="_Generate Content" Command="{Binding GenerateCommand}" />
            </MenuItem>
        </Menu>

        <!-- Main Content -->
        <Grid Grid.Row="1" Margin="8">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="250" />
                <ColumnDefinition Width="*" />
                <ColumnDefinition Width="300" />
            </Grid.ColumnDefinitions>

            <!-- Left Panel: Project Info -->
            <Border Grid.Column="0" Background="#181825" CornerRadius="4" Margin="0,0,4,0">
                <StackPanel Margin="12">
                    <TextBlock Text="PROJECT" Foreground="#6C7086" FontWeight="Bold" Margin="0,0,0,8" />
                    <TextBlock Text="{Binding CurrentProject.Name, FallbackValue='No project'}"
                               Foreground="#CDD6F4" FontSize="16" FontWeight="SemiBold" />
                    <TextBlock Text="{Binding CurrentProject.Genre, FallbackValue=''}"
                               Foreground="#A6ADC8" Margin="0,4,0,0" />
                    <Separator Background="#313244" Margin="0,12" />
                    <TextBlock Text="Story Bible" Foreground="#6C7086" FontWeight="Bold" Margin="0,0,0,4" />
                    <TextBlock Text="Characters: 0" Foreground="#A6ADC8" />
                    <TextBlock Text="Locations: 0" Foreground="#A6ADC8" />
                    <TextBlock Text="Timeline Events: 0" Foreground="#A6ADC8" />
                </StackPanel>
            </Border>

            <!-- Center: Generation Area -->
            <Grid Grid.Column="1" Margin="4,0">
                <Grid.RowDefinitions>
                    <RowDefinition Height="*" />
                    <RowDefinition Height="Auto" />
                    <RowDefinition Height="*" />
                </Grid.RowDefinitions>

                <!-- Output -->
                <Border Grid.Row="0" Background="#181825" CornerRadius="4" Margin="0,0,0,4">
                    <ScrollViewer Margin="12">
                        <TextBlock Text="{Binding GeneratedContent}"
                                   Foreground="#CDD6F4"
                                   TextWrapping="Wrap"
                                   FontFamily="Consolas"
                                   FontSize="14" />
                    </ScrollViewer>
                </Border>

                <!-- Input -->
                <Grid Grid.Row="2">
                    <TextBox Text="{Binding GenerationInput, UpdateSourceTrigger=PropertyChanged}"
                             Background="#1E1E2E"
                             Foreground="#CDD6F4"
                             BorderBrush="#313244"
                             AcceptsReturn="True"
                             TextWrapping="Wrap"
                             VerticalScrollBarVisibility="Auto"
                             Padding="12"
                             FontSize="14" />
                    <Button Content="GENERATE"
                            Command="{Binding GenerateCommand}"
                            HorizontalAlignment="Right"
                            VerticalAlignment="Bottom"
                            Margin="0,0,8,8"
                            Padding="16,8"
                            Background="#89B4FA"
                            Foreground="#1E1E2E"
                            FontWeight="Bold"
                            BorderThickness="0"
                            IsEnabled="{Binding IsGenerating, Converter={StaticResource InvertBool}}" />
                </Grid>
            </Grid>

            <!-- Right Panel: Status -->
            <Border Grid.Column="2" Background="#181825" CornerRadius="4" Margin="4,0,0,0">
                <StackPanel Margin="12">
                    <TextBlock Text="AI PIPELINE" Foreground="#6C7086" FontWeight="Bold" Margin="0,0,0,8" />
                    <TextBlock Text="Director → Story → Consistency"
                               Foreground="#A6ADC8"
                               TextWrapping="Wrap" />
                    <Separator Background="#313244" Margin="0,12" />
                    <TextBlock Text="PROVIDER" Foreground="#6C7086" FontWeight="Bold" Margin="0,0,0,4" />
                    <TextBlock Text="Local LLM (Ollama)" Foreground="#A6ADC8" />
                    <Separator Background="#313244" Margin="0,12" />
                    <TextBlock Text="HISTORY" Foreground="#6C7086" FontWeight="Bold" Margin="0,0,0,4" />
                    <TextBlock Text="No generations yet" Foreground="#A6ADC8" />
                </StackPanel>
            </Border>
        </Grid>

        <!-- Status Bar -->
        <Border Grid.Row="2" Background="#181825">
            <TextBlock Text="{Binding StatusText}"
                       Foreground="#6C7086"
                       VerticalAlignment="Center"
                       Margin="12,0" />
        </Border>
    </Grid>
</Window>
```

- [ ] **Step 6: Implement MainWindow.xaml.cs**

```csharp
using System.Windows;

namespace NarrativeForge.App;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
    }
}
```

- [ ] **Step 7: Update App.xaml**

```xml
<Application x:Class="NarrativeForge.App.App"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             StartupUri="MainWindow.xaml">
    <Application.Resources>
        <BooleanToVisibilityConverter x:Key="BoolToVis" />
        <local:InvertBoolConverter x:Key="InvertBool"
                                   xmlns:local="clr-namespace:NarrativeForge.App" />
    </Application.Resources>
</Application>
```

- [ ] **Step 8: Add InvertBoolConverter to App.xaml.cs**

```csharp
using System.Globalization;
using System.Windows.Data;

namespace NarrativeForge.App;

public class InvertBoolConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is bool b) return !b;
        return false;
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is bool b) return !b;
        return false;
    }
}
```

- [ ] **Step 9: Build WPF project**

```bash
cd src/NarrativeForge
dotnet build NarrativeForge.App/NarrativeForge.App.csproj
# Expected: Build succeeded
```

- [ ] **Step 10: Commit**

```bash
git add src/NarrativeForge/
git commit -m "feat: add WPF desktop application with IDE-like layout and API client"
```

---

## Task 11: End-to-End Integration

**Covers:** [S3, S13, S14]

**Files:**
- Modify: `src/NarrativeForge.Engine/main.py` (final wiring)
- Create: `tests/integration/test_e2e.py`

**Interfaces:**
- Consumes: All previous tasks
- Produces: Verified end-to-end flow

- [ ] **Step 1: Write integration test**

```python
# tests/integration/test_e2e.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_full_workflow(client):
    # 1. Health check
    health = await client.get("/health")
    assert health.status_code == 200

    # 2. Create project
    project = await client.post("/api/projects", json={
        "name": "Dragon Quest",
        "genre": "fantasy",
        "tone": "epic",
    })
    assert project.status_code == 200
    pid = project.json()["id"]

    # 3. Verify project exists
    get_resp = await client.get(f"/api/projects/{pid}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Dragon Quest"

    # 4. List projects
    list_resp = await client.get("/api/projects")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 5. Generate content
    gen_resp = await client.post("/api/generate", json={
        "project_id": pid,
        "request": "Write a prologue for an epic fantasy game",
    })
    assert gen_resp.status_code == 200
    data = gen_resp.json()
    assert len(data["content"]) > 0
    assert len(data["stages"]) > 0

    # 6. Cleanup
    del_resp = await client.delete(f"/api/projects/{pid}")
    assert del_resp.status_code == 200
```

- [ ] **Step 2: Run integration test**

```bash
cd src/NarrativeForge.Engine
pytest tests/integration/test_e2e.py -v
# Expected: 1 passed
```

- [ ] **Step 3: Run full test suite**

```bash
cd src/NarrativeForge.Engine
pytest -v
# Expected: All tests pass
```

- [ ] **Step 4: Run linter**

```bash
cd src/NarrativeForge.Engine
ruff check .
# Expected: No errors
```

- [ ] **Step 5: Build WPF project one final time**

```bash
cd src/NarrativeForge
dotnet build
# Expected: Build succeeded
```

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "feat: Phase 1 complete — core engine with AI pipeline, storage, and WPF desktop shell"
```
