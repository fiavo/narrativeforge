from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    role: Role
    content: str

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> "Message":
        return cls(role=Role.ASSISTANT, content=content)


@dataclass
class CompletionOptions:
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    stop: list[str] = field(default_factory=list)


class AIProvider(ABC):
    @abstractmethod
    async def complete(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> str:
        ...

    @abstractmethod
    async def stream(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> AsyncIterator[str]:
        ...
