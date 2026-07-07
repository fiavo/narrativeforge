import json
from typing import AsyncIterator

import pytest

from NarrativeForge.Engine.ai_providers.base import (
    AIProvider,
    CompletionOptions,
    Message,
)
from NarrativeForge.Engine.agents.base import AgentContext, AgentResult
from NarrativeForge.Engine.agents.critic_agent import (
    CRITERIA,
    CriticAgent,
    CriticReport,
)
from NarrativeForge.Engine.models.project import GameGenre, Project


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


def _make_critic_response() -> str:
    return json.dumps({
        "overall_score": 0.85,
        "scores": {
            "coherence": 0.9,
            "character_depth": 0.8,
            "pacing": 0.85,
            "dialogue_quality": 0.8,
            "creativity": 0.9,
            "emotional_impact": 0.85,
        },
        "summary": "Strong narrative with good character development.",
        "strengths": ["Good pacing", "Creative world-building"],
        "weaknesses": ["Dialogue could be more natural"],
    })


class TestCriticAgent:
    @pytest.mark.asyncio
    async def test_critic_agent_returns_result(self):
        provider = FakeProvider(_make_critic_response())
        agent = CriticAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Evaluate this story content",
            previous_results={"content": "The hero journeyed through the dark forest..."},
        )

        result = await agent.execute(ctx)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "CriticAgent"

    @pytest.mark.asyncio
    async def test_critic_agent_has_all_criteria_scores(self):
        provider = FakeProvider(_make_critic_response())
        agent = CriticAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Evaluate this story content",
            previous_results={"content": "The hero journeyed through the dark forest..."},
        )

        result = await agent.execute(ctx)

        assert isinstance(result.content, dict)
        assert "overall_score" in result.content
        assert "scores" in result.content
        for criterion in CRITERIA:
            assert criterion in result.content["scores"]
        assert result.content["overall_score"] == 0.85
        assert result.content["scores"]["coherence"] == 0.9

    @pytest.mark.asyncio
    async def test_critic_agent_uses_temperature_03(self):
        provider = FakeProvider("{}")
        agent = CriticAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Evaluate",
        )

        await agent.execute(ctx)

        assert provider.last_options is not None
        assert provider.last_options.temperature == 0.3

    @pytest.mark.asyncio
    async def test_critic_agent_returns_no_changes(self):
        provider = FakeProvider(_make_critic_response())
        agent = CriticAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Evaluate this story content",
            previous_results={"content": "The hero journeyed through the dark forest..."},
        )

        result = await agent.execute(ctx)

        assert result.changes == []
