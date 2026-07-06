from uuid import uuid4

import pytest

from NarrativeForge.Engine.models import (
    Character,
    CharacterRole,
    GameGenre,
    Project,
    StoryBible,
)
from NarrativeForge.Engine.storage.database import Database
from NarrativeForge.Engine.storage.json_store import JsonStore


@pytest.fixture
def sample_project():
    return Project(name="Test Game", genre=GameGenre.RPG)


@pytest.fixture
def sample_character():
    return Character(name="Hero", role=CharacterRole.Protagonist)


@pytest.fixture
def sample_story_bible(sample_project):
    return StoryBible(project_id=sample_project.id)


class TestDatabase:
    @pytest.fixture
    def db(self):
        return Database("sqlite+aiosqlite:///:memory:")

    @pytest.fixture
    def project(self):
        return Project(name="Test Game", genre=GameGenre.RPG)

    @pytest.fixture
    def character(self):
        return Character(name="Hero", role=CharacterRole.Protagonist)

    async def test_create_and_get_project(self, db, project):
        await db.create_project(project)
        retrieved = await db.get_project(project.id)
        assert retrieved is not None
        assert retrieved.name == "Test Game"
        assert retrieved.genre == GameGenre.RPG

    async def test_list_projects_empty(self, db):
        projects = await db.list_projects()
        assert projects == []

    async def test_list_projects_multiple(self, db):
        p1 = Project(name="Game 1", genre=GameGenre.RPG)
        p2 = Project(name="Game 2", genre=GameGenre.Fantasy)
        await db.create_project(p1)
        await db.create_project(p2)
        projects = await db.list_projects()
        assert len(projects) == 2
        names = {p.name for p in projects}
        assert names == {"Game 1", "Game 2"}

    async def test_delete_project(self, db, project):
        await db.create_project(project)
        result = await db.delete_project(project.id)
        assert result is True
        retrieved = await db.get_project(project.id)
        assert retrieved is None

    async def test_delete_nonexistent_project(self, db):
        result = await db.delete_project(uuid4())
        assert result is False

    async def test_get_nonexistent_project(self, db):
        retrieved = await db.get_project(uuid4())
        assert retrieved is None

    async def test_create_and_get_character(self, db, project, character):
        await db.create_project(project)
        await db.create_character(project.id, character)
        retrieved = await db.get_character(character.id)
        assert retrieved is not None
        assert retrieved.name == "Hero"
        assert retrieved.role == CharacterRole.Protagonist

    async def test_list_characters(self, db, project):
        await db.create_project(project)
        c1 = Character(name="Hero", role=CharacterRole.Protagonist)
        c2 = Character(name="Villain", role=CharacterRole.Antagonist)
        await db.create_character(project.id, c1)
        await db.create_character(project.id, c2)
        chars = await db.list_characters(project.id)
        assert len(chars) == 2
        names = {c.name for c in chars}
        assert names == {"Hero", "Villain"}

    async def test_delete_character(self, db, project, character):
        await db.create_project(project)
        await db.create_character(project.id, character)
        result = await db.delete_character(character.id)
        assert result is True
        retrieved = await db.get_character(character.id)
        assert retrieved is None

    async def test_character_personality_preserved(self, db, project):
        await db.create_project(project)
        char = Character(
            name="Complex Hero",
            role=CharacterRole.Protagonist,
            personality={
                "traits": ["brave", "loyal"],
                "values": ["justice"],
                "fears": ["failure"],
                "desires": ["freedom"],
            },
            arc={
                "start_state": "naive",
                "end_state": "wise",
                "turning_points": ["betrayal"],
            },
        )
        await db.create_character(project.id, char)
        retrieved = await db.get_character(char.id)
        assert retrieved.personality.traits == ["brave", "loyal"]
        assert retrieved.arc.start_state == "naive"

    async def test_project_fields_roundtrip(self, db):
        project = Project(
            name="Complex Game",
            genre=GameGenre.Cyberpunk,
            sub_genres=[GameGenre.SciFi, GameGenre.Noir],
            target_audience="Adults",
            tone="Dark",
            themes=["identity", "technology"],
            settings={"difficulty": "hard"},
        )
        await db.create_project(project)
        retrieved = await db.get_project(project.id)
        assert retrieved.sub_genres == [GameGenre.SciFi, GameGenre.Noir]
        assert retrieved.target_audience == "Adults"
        assert retrieved.themes == ["identity", "technology"]
        assert retrieved.settings == {"difficulty": "hard"}


class TestJsonStore:
    @pytest.fixture
    def store(self, tmp_path):
        return JsonStore(tmp_path)

    @pytest.fixture
    def project(self):
        return Project(name="Test Game", genre=GameGenre.RPG)

    @pytest.fixture
    def story_bible(self, project):
        return StoryBible(project_id=project.id)

    def test_save_and_load_project(self, store, project, story_bible):
        path = store.save_project(project, story_bible)
        assert path.exists()
        assert path.suffix == ".nforge"

        loaded_project, loaded_bible = store.load_project(path)
        assert loaded_project.name == project.name
        assert loaded_project.genre == project.genre
        assert loaded_bible.project_id == project.id

    def test_list_projects_empty(self, store):
        projects = store.list_projects()
        assert projects == []

    def test_list_projects(self, store):
        p1 = Project(name="Game 1", genre=GameGenre.RPG)
        p2 = Project(name="Game 2", genre=GameGenre.Fantasy)
        sb1 = StoryBible(project_id=p1.id)
        sb2 = StoryBible(project_id=p2.id)
        store.save_project(p1, sb1)
        store.save_project(p2, sb2)
        projects = store.list_projects()
        assert len(projects) == 2

    def test_delete_project(self, store, project, story_bible):
        store.save_project(project, story_bible)
        result = store.delete_project(project.id)
        assert result is True
        assert store.list_projects() == []

    def test_delete_nonexistent_project(self, store):
        result = store.delete_project(uuid4())
        assert result is False

    def test_nforge_file_is_json(self, store, project, story_bible):
        path = store.save_project(project, story_bible)
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "project" in data
        assert "story_bible" in data
        assert data["project"]["name"] == "Test Game"

    def test_story_bible_preserved(self, store, project):
        from NarrativeForge.Engine.models import Character, Location, TimelineEvent
        c = Character(name="Hero")
        loc = Location(name="Castle")
        event = TimelineEvent(title="War", order=1)
        bible = StoryBible(
            project_id=project.id,
            characters={c.id: c},
            locations={loc.id: loc},
            timeline=[event],
        )
        path = store.save_project(project, bible)
        loaded_project, loaded_bible = store.load_project(path)
        assert len(loaded_bible.characters) == 1
        assert len(loaded_bible.locations) == 1
        assert len(loaded_bible.timeline) == 1
