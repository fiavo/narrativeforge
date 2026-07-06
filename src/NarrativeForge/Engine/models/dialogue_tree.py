from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field

from NarrativeForge.Engine.scripting.variables import InkVariableStore


class DialogueNodeType(str, Enum):
    TEXT = "text"
    CHOICE = "choice"
    CONDITION = "condition"
    FUNCTION = "function"
    VARIABLE = "variable"
    JUMP = "jump"
    END = "end"


class DialogueChoice(BaseModel):
    text: str
    next_node_id: str
    condition: str = ""
    variables_set: dict[str, str] = Field(default_factory=dict)


class DialogueCondition(BaseModel):
    expression: str
    true_node_id: str
    false_node_id: str = ""


class DialogueNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: DialogueNodeType
    content: str = ""
    choices: list[DialogueChoice] = Field(default_factory=list)
    conditions: list[DialogueCondition] = Field(default_factory=list)
    variables_set: dict[str, str] = Field(default_factory=dict)
    next_node_id: str = ""


class DialogueEdge(BaseModel):
    source_id: str
    target_id: str
    label: str = ""


class DialogueTree(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    start_node_id: str
    nodes: dict[str, DialogueNode] = Field(default_factory=dict)
    edges: list[DialogueEdge] = Field(default_factory=list)
    variables: InkVariableStore = Field(default_factory=InkVariableStore)

    model_config = {"arbitrary_types_allowed": True}
