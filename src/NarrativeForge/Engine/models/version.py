from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone


class Version(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    version_number: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: str = ""
    author: str = ""
    snapshot: dict = Field(default_factory=dict)
    size_bytes: int = 0
