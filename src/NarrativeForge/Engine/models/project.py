from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone


class GameGenre(str, Enum):
    RPG = "RPG"
    JRPG = "JRPG"
    OpenWorld = "OpenWorld"
    Horror = "Horror"
    SciFi = "SciFi"
    Fantasy = "Fantasy"
    Medieval = "Medieval"
    Cyberpunk = "Cyberpunk"
    Detective = "Detective"
    Zombie = "Zombie"
    Psychological = "Psychological"
    Survival = "Survival"
    Romance = "Romance"
    Comedy = "Comedy"
    DarkFantasy = "DarkFantasy"
    Steampunk = "Steampunk"
    Historical = "Historical"
    Mythology = "Mythology"
    Lovecraftian = "Lovecraftian"
    Noir = "Noir"
    Military = "Military"
    PostApocalypse = "PostApocalypse"
    Vampire = "Vampire"
    Werewolf = "Werewolf"
    Mystery = "Mystery"
    Thriller = "Thriller"
    Superhero = "Superhero"
    Crime = "Crime"
    School = "School"
    Anime = "Anime"


class Project(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    genre: GameGenre
    sub_genres: list[GameGenre] = Field(default_factory=list)
    target_audience: str = ""
    tone: str = ""
    themes: list[str] = Field(default_factory=list)
    story_bible_id: Optional[UUID] = None
    settings: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
