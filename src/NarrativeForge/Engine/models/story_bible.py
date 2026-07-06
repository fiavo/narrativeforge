from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from .character import Character
from .location import Location
from .timeline import TimelineEvent
from .relationship import Relationship
from .lore import LoreEntry


class Faction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    goals: list[str] = Field(default_factory=list)
    members: list[UUID] = Field(default_factory=list)
    allies: list[UUID] = Field(default_factory=list)
    enemies: list[UUID] = Field(default_factory=list)


class StoryBible(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    characters: dict[UUID, Character] = Field(default_factory=dict)
    locations: dict[UUID, Location] = Field(default_factory=dict)
    factions: dict[UUID, Faction] = Field(default_factory=dict)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    lore_entries: dict[UUID, LoreEntry] = Field(default_factory=dict)
    relationships: list[Relationship] = Field(default_factory=list)
    locked_elements: set[UUID] = Field(default_factory=set)
