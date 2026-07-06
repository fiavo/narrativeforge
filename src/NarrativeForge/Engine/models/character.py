from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class CharacterRole(str, Enum):
    Protagonist = "Protagonist"
    Antagonist = "Antagonist"
    Deuteragonist = "Deuteragonist"
    Sidekick = "Sidekick"
    Mentor = "Mentor"
    LoveInterest = "LoveInterest"
    ComicRelief = "ComicRelief"
    Trickster = "Trickster"
    Supporting = "Supporting"
    Background = "Background"


class PersonalityProfile(BaseModel):
    traits: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    fears: list[str] = Field(default_factory=list)
    desires: list[str] = Field(default_factory=list)


class CharacterArc(BaseModel):
    start_state: str = ""
    end_state: str = ""
    turning_points: list[str] = Field(default_factory=list)


class Character(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    alias: str = ""
    role: CharacterRole = CharacterRole.Supporting
    personality: PersonalityProfile = Field(default_factory=PersonalityProfile)
    backstory: str = ""
    motivation: str = ""
    goals: list[str] = Field(default_factory=list)
    fears: list[str] = Field(default_factory=list)
    relationships: dict[UUID, str] = Field(default_factory=dict)
    arc: CharacterArc = Field(default_factory=CharacterArc)
    dialogue_style: str = ""
    appearance: str = ""
    is_alive: bool = True
    is_locked: bool = False
