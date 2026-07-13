"""Tests for storage and database module."""
import pytest
from uuid import uuid4
from datetime import datetime

from NarrativeForge.Engine.models import Project, GameGenre, Character, CharacterRole, PersonalityProfile


@pytest.mark.unit
class TestDatabase:
    """Test database operations."""

    @pytest.mark.asyncio
    async def test_create_and_get_project(self, test_db):
        """Test creating and retrieving a project."""
        project = Project(
            id=uuid4(),
            name="Test Game",
            genre=GameGenre.Fantasy,
            sub_genres=[],
            target_audience="Adult",
            tone="Dark",
            themes=["Redemption"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        created = await test_db.create_project(project)
        assert created.id == project.id
        assert created.name == "Test Game"

        retrieved = await test_db.get_project(project.id)
        assert retrieved is not None
        assert retrieved.name == "Test Game"
        assert retrieved.genre == GameGenre.Fantasy

    @pytest.mark.asyncio
    async def test_list_projects(self, test_db):
        """Test listing projects."""
        project1 = Project(
            id=uuid4(),
            name="Game 1",
            genre=GameGenre.Fantasy,
            sub_genres=[],
            target_audience="Adult",
            tone="Epic",
            themes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        project2 = Project(
            id=uuid4(),
            name="Game 2",
            genre=GameGenre.SciFi,
            sub_genres=[],
            target_audience="Teen",
            tone="Noir",
            themes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        await test_db.create_project(project1)
        await test_db.create_project(project2)

        projects = await test_db.list_projects()
        assert len(projects) == 2
        assert any(p.name == "Game 1" for p in projects)
        assert any(p.name == "Game 2" for p in projects)

    @pytest.mark.asyncio
    async def test_delete_project(self, test_db):
        """Test deleting a project."""
        project = Project(
            id=uuid4(),
            name="Temp Game",
            genre=GameGenre.Fantasy,
            sub_genres=[],
            target_audience="Adult",
            tone="Dark",
            themes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        await test_db.create_project(project)
        deleted = await test_db.delete_project(project.id)
        assert deleted is True

        retrieved = await test_db.get_project(project.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_create_and_get_character(self, test_db):
        """Test creating and retrieving a character."""
        project = Project(
            id=uuid4(),
            name="Test Game",
            genre=GameGenre.Fantasy,
            sub_genres=[],
            target_audience="Adult",
            tone="Dark",
            themes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await test_db.create_project(project)

        character = Character(
            id=uuid4(),
            name="Hero",
            alias="The Chosen One",
            role=CharacterRole.Protagonist,
            personality=PersonalityProfile(
                traits=["Brave", "Honorable"],
                strengths=["Leadership"],
                weaknesses=["Stubborn"],
                quirks=["Hums when thinking"],
            ),
            backstory="A humble farmer turned hero.",
            motivation="Saving the kingdom",
            goals=["Defeat the dark lord"],
            fears=["Losing loved ones"],
            relationships={},
        )

        created = await test_db.create_character(project.id, character)
        assert created.id == character.id
        assert created.name == "Hero"

        retrieved = await test_db.get_character(character.id)
        assert retrieved is not None
        assert retrieved.role == CharacterRole.Protagonist
