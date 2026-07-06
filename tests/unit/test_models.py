from uuid import uuid4
import pytest
from pydantic import ValidationError
from NarrativeForge.Engine.models import (
    GameGenre,
    Project,
    CharacterRole,
    PersonalityProfile,
    CharacterArc,
    Character,
    Location,
    TimelineEvent,
    RelationshipType,
    Relationship,
    LoreEntry,
    Faction,
    StoryBible,
)


class TestProject:
    def test_project_creation(self):
        project = Project(name="Test Game", genre=GameGenre.RPG)
        assert project.name == "Test Game"
        assert project.genre == GameGenre.RPG
        assert project.id is not None

    def test_project_defaults(self):
        project = Project(name="Test", genre=GameGenre.Fantasy)
        assert project.sub_genres == []
        assert project.target_audience == ""
        assert project.tone == ""
        assert project.themes == []
        assert project.story_bible_id is None
        assert project.settings == {}


class TestCharacter:
    def test_character_creation(self):
        char = Character(name="Hero", role=CharacterRole.Protagonist)
        assert char.name == "Hero"
        assert char.role == CharacterRole.Protagonist
        assert char.is_alive is True
        assert char.is_locked is False

    def test_personality_profile(self):
        profile = PersonalityProfile(
            traits=["brave", "loyal"], fears=["darkness"], desires=["justice"]
        )
        assert len(profile.traits) == 2
        assert "darkness" in profile.fears

    def test_character_arc(self):
        arc = CharacterArc(
            start_state="naive",
            end_state="wise",
            turning_points=["betrayal", "redemption"],
        )
        assert arc.start_state == "naive"
        assert len(arc.turning_points) == 2


class TestLocation:
    def test_location_creation(self):
        loc = Location(name="Forest", type="Natural")
        assert loc.name == "Forest"
        assert loc.type == "Natural"
        assert loc.connected_to == []

    def test_location_defaults(self):
        loc = Location(name="City")
        assert loc.inhabitants == []
        assert loc.factions_present == []
        assert loc.is_locked is False


class TestTimelineEvent:
    def test_event_creation(self):
        event = TimelineEvent(title="Great War", order=1)
        assert event.title == "Great War"
        assert event.order == 1
        assert event.participants == []

    def test_event_with_location(self):
        loc_id = uuid4()
        event = TimelineEvent(
            title="Battle", location_id=loc_id, consequences=["peace"]
        )
        assert event.location_id == loc_id
        assert "peace" in event.consequences


class TestRelationship:
    def test_relationship_creation(self):
        src = str(uuid4())
        tgt = str(uuid4())
        rel = Relationship(source_id=src, target_id=tgt, type=RelationshipType.Enemy, strength=80)
        assert rel.source_id == src
        assert rel.target_id == tgt
        assert rel.type == RelationshipType.Enemy
        assert rel.strength == 80
        assert rel.is_bidirectional is False

    def test_relationship_strength_bounds(self):
        src = str(uuid4())
        tgt = str(uuid4())
        rel = Relationship(source_id=src, target_id=tgt, strength=0)
        assert rel.strength == 0
        rel = Relationship(source_id=src, target_id=tgt, strength=100)
        assert rel.strength == 100


class TestStoryBible:
    def test_story_bible_creation(self):
        project_id = uuid4()
        bible = StoryBible(project_id=project_id)
        assert bible.project_id == project_id
        assert bible.characters == {}
        assert bible.locations == {}

    def test_lore_entry(self):
        entry = LoreEntry(title="Ancient Magic", content="Mysterious forces")
        assert entry.title == "Ancient Magic"
        assert entry.is_locked is False

    def test_faction(self):
        faction = Faction(name="Guardians", goals=["protect"])
        assert faction.name == "Guardians"
        assert "protect" in faction.goals

    def test_story_bible_with_data(self):
        project_id = uuid4()
        char_id = uuid4()
        loc_id = uuid4()
        char = Character(name="Hero")
        loc = Location(name="Castle")
        bible = StoryBible(
            project_id=project_id,
            characters={char_id: char},
            locations={loc_id: loc},
        )
        assert char_id in bible.characters
        assert loc_id in bible.locations
        assert bible.characters[char_id].name == "Hero"
        assert bible.locations[loc_id].name == "Castle"


class TestValidation:
    def test_project_missing_name_raises(self):
        with pytest.raises(ValidationError):
            Project(genre=GameGenre.RPG)

    def test_relationship_strength_over_100_raises(self):
        src = str(uuid4())
        tgt = str(uuid4())
        with pytest.raises(ValidationError):
            Relationship(source_id=src, target_id=tgt, strength=101)

    def test_invalid_genre_string_raises(self):
        with pytest.raises(ValidationError):
            Project(name="Test", genre="InvalidGenre")
