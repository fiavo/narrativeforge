import json
from typing import AsyncIterator
from uuid import uuid4

import pytest

from NarrativeForge.Engine.ai_providers.base import (
    AIProvider,
    CompletionOptions,
    Message,
)
from NarrativeForge.Engine.agents.base import AgentContext, AgentResult
from NarrativeForge.Engine.agents.dialogue_agent import DialogueAgent
from NarrativeForge.Engine.agents.quest_agent import QuestAgent
from NarrativeForge.Engine.models.project import GameGenre, Project
from NarrativeForge.Engine.models.story_bible import StoryBible


class FakeProvider(AIProvider):
    def __init__(self, response: str = "{}"):
        self._response = response
        self.last_messages: list[Message] | None = None
        self.last_options: CompletionOptions | None = None

    async def complete(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> str:
        self.last_messages = messages
        self.last_options = options
        return self._response

    async def stream(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> AsyncIterator[str]:
        self.last_messages = messages
        self.last_options = options
        for word in self._response.split():
            yield word + " "


def _make_project(genre: GameGenre = GameGenre.Fantasy) -> Project:
    return Project(name="Test Project", genre=genre, themes=["redemption", "power"])


def _make_dialogue_node_response() -> str:
    return json.dumps({
        "speaker": "Aria",
        "line": "I won't let you take the artifact!",
        "emotion": "determined",
        "action": "draws sword",
        "node_type": "dialogue",
    })


def _make_quest_node_response() -> str:
    return json.dumps({
        "title": "Find the Map",
        "description": "Search the ancient library for the treasure map.",
        "node_type": "quest_step",
        "objective": {
            "description": "Find the treasure map in the library",
            "type": "explore",
            "target": "Ancient Library",
            "quantity": 1,
            "is_required": True,
        },
        "completion_hint": "Check the restricted section behind the desk.",
    })


class TestDialogueNodeGeneration:
    @pytest.mark.asyncio
    async def test_generate_next_node_returns_agent_result(self):
        provider = FakeProvider(_make_dialogue_node_response())
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write a dialogue between Aria and Malakar",
        )

        result = await agent.generate_next_node(ctx)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "DialogueAgent"
        assert result.metadata["node_type"] == "dialogue"

    @pytest.mark.asyncio
    async def test_generate_next_node_returns_node_with_speaker(self):
        provider = FakeProvider(_make_dialogue_node_response())
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write a dialogue between Aria and Malakar",
        )

        result = await agent.generate_next_node(ctx)

        assert isinstance(result.content, dict)
        assert result.content["speaker"] == "Aria"
        assert result.content["line"] == "I won't let you take the artifact!"
        assert result.content["emotion"] == "determined"
        assert result.content["action"] == "draws sword"
        assert result.metadata["speaker"] == "Aria"


class TestQuestNodeGeneration:
    @pytest.mark.asyncio
    async def test_generate_next_node_returns_agent_result(self):
        provider = FakeProvider(_make_quest_node_response())
        agent = QuestAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create a quest about finding treasure",
        )

        result = await agent.generate_next_node(ctx)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "QuestAgent"
        assert result.metadata["node_type"] == "quest_step"

    @pytest.mark.asyncio
    async def test_generate_next_node_returns_node_with_objective(self):
        provider = FakeProvider(_make_quest_node_response())
        agent = QuestAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create a quest about finding treasure",
        )

        result = await agent.generate_next_node(ctx)

        assert isinstance(result.content, dict)
        assert result.content["title"] == "Find the Map"
        assert result.content["description"] == "Search the ancient library for the treasure map."
        assert result.content["objective"]["type"] == "explore"
        assert result.content["objective"]["target"] == "Ancient Library"
        assert result.metadata["has_objective"] is True
