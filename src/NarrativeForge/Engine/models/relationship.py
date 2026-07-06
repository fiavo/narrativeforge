from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class RelationshipType(str, Enum):
    Ally = "Ally"
    Enemy = "Enemy"
    Family = "Family"
    Friend = "Friend"
    Romantic = "Romantic"
    Rival = "Rival"
    Mentor = "Mentor"
    Servant = "Servant"
    Leader = "Leader"
    Follower = "Follower"


class Relationship(BaseModel):
    source_id: UUID = Field(default_factory=uuid4)
    target_id: UUID = Field(default_factory=uuid4)
    type: RelationshipType = RelationshipType.Friend
    strength: int = Field(default=50, ge=0, le=100)
    is_bidirectional: bool = False
    notes: str = ""
