from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class Location(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: str = ""
    description: str = ""
    connected_to: list[UUID] = Field(default_factory=list)
    inhabitants: list[UUID] = Field(default_factory=list)
    factions_present: list[UUID] = Field(default_factory=list)
    significance: str = ""
    is_locked: bool = False
