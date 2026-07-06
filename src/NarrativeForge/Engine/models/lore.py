from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class LoreEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    content: str = ""
    category: str = ""
    tags: list[str] = Field(default_factory=list)
    related_entries: list[UUID] = Field(default_factory=list)
    is_locked: bool = False
