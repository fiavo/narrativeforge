from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class TimelineEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str = ""
    timestamp: str = ""
    participants: list[UUID] = Field(default_factory=list)
    location_id: Optional[UUID] = None
    consequences: list[str] = Field(default_factory=list)
    order: int = 0
