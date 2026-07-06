from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class QuestObjectiveType(str, Enum):
    Kill = "kill"
    Collect = "collect"
    Explore = "explore"
    Escort = "escort"
    Talk = "talk"
    Solve = "solve"


class QuestObjective(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    description: str
    type: QuestObjectiveType = QuestObjectiveType.Talk
    target: str = ""
    quantity: int = 1
    is_required: bool = True


class QuestPrerequisite(BaseModel):
    quest_id: UUID
    relationship: str = ""


class QuestReward(BaseModel):
    xp: int = 0
    gold: int = 0
    items: list[str] = Field(default_factory=list)
    reputation: int = 0


class Quest(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    objectives: list[QuestObjective] = Field(default_factory=list)
    prerequisites: list[QuestPrerequisite] = Field(default_factory=list)
    rewards: QuestReward = Field(default_factory=QuestReward)
    faction_id: UUID | None = None
    is_main_quest: bool = False
