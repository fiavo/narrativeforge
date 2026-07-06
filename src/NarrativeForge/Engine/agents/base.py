from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID

from NarrativeForge.Engine.ai_providers.base import AIProvider, CompletionOptions
from NarrativeForge.Engine.memory.graph_store import NarrativeGraph
from NarrativeForge.Engine.models.project import Project
from NarrativeForge.Engine.models.story_bible import StoryBible


class AgentRole(str, Enum):
    DIRECTOR = "director"
    STORY = "story"
    CONSISTENCY = "consistency"


@dataclass
class AgentContext:
    project: Project
    story_bible: StoryBible | None = None
    graph: NarrativeGraph | None = None
    user_request: str = ""
    generation_params: CompletionOptions | None = None
    previous_results: dict[str, Any] = field(default_factory=dict)
    locked_elements: set[UUID] = field(default_factory=set)


@dataclass
class AgentResult:
    agent_name: str
    content: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    changes: list[dict[str, Any]] = field(default_factory=list)


class BaseAgent(ABC):
    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult: ...

    @abstractmethod
    def build_system_prompt(self, context: AgentContext) -> str: ...
