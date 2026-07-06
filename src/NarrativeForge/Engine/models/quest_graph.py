from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field

from NarrativeForge.Engine.scripting.variables import InkVariableStore


class QuestNodeType(str, Enum):
    START = "start"
    OBJECTIVE = "objective"
    BRANCH = "branch"
    CONDITION = "condition"
    REWARD = "reward"
    FAIL = "fail"
    END = "end"


class QuestCondition(BaseModel):
    expression: str
    true_node_id: str
    false_node_id: str = ""


class QuestNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: QuestNodeType
    name: str = ""
    description: str = ""
    objectives: list[str] = Field(default_factory=list)
    rewards: dict[str, str] = Field(default_factory=dict)
    conditions: list[QuestCondition] = Field(default_factory=list)
    next_node_ids: list[str] = Field(default_factory=list)


class QuestEdge(BaseModel):
    source_id: str
    target_id: str
    condition: str = ""
    weight: float = 1.0


class QuestStateTracker:
    def __init__(self, initial_state: dict | None = None) -> None:
        self._state: dict[str, str | int | float | bool] = dict(initial_state or {})

    def set(self, key: str, value: str | int | float | bool) -> None:
        self._state[key] = value

    def get(self, key: str, default: str | int | float | bool | None = None) -> str | int | float | bool | None:
        return self._state.get(key, default)

    def is_complete(self) -> bool:
        return len(self._state) > 0 and all(
            self._state.get(k) is True for k in list(self._state.keys())
        )


class QuestGraph(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    start_node_id: str = ""
    nodes: dict[str, QuestNode] = Field(default_factory=dict)
    edges: list[QuestEdge] = Field(default_factory=list)
    variables: InkVariableStore = Field(default_factory=InkVariableStore)
    state: QuestStateTracker = Field(default_factory=QuestStateTracker)

    model_config = {"arbitrary_types_allowed": True}
