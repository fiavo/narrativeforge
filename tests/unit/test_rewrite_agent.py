import json
from typing import AsyncIterator

import pytest

from NarrativeForge.Engine.ai_providers.base import (
    AIProvider,
    CompletionOptions,
    Message,
)
from NarrativeForge.Engine.agents.base import AgentContext, AgentResult
from NarrativeForge.Engine.agents.rewrite_agent import RewriteAgent, RewriteMode
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


def _make_project() -> Project:
    return Project(name="Test Project", genre=GameGenre.Fantasy, themes=["redemption"])


def _make_polish_response() -> str:
    return json.dumps({
        "rewritten_text": "The brave warrior drew her sword, its gleaming blade reflecting the temple torchlight.",
        "mode": "polish",
        "changes_summary": "Improved grammar, enhanced description, tightened prose.",
    })


def _make_style_response() -> str:
    return json.dumps({
        "rewritten_text": "In the hallowed hall, the warrior's steel sang forth, a silver tongue whispering of fate.",
        "mode": "style_transfer",
        "changes_summary": "Transformed to poetic style with vivid imagery and figurative language.",
    })


class TestRewriteAgent:
    @pytest.mark.asyncio
    async def test_returns_agent_result(self):
        provider = FakeProvider(_make_polish_response())
        agent = RewriteAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Polish this: The warrior drew her sword.",
        )

        result = await agent.execute(ctx)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "RewriteAgent"
        assert isinstance(result.content, dict)

    @pytest.mark.asyncio
    async def test_polish_mode_uses_temperature_07(self):
        provider = FakeProvider(_make_polish_response())
        agent = RewriteAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Polish this: The warrior drew her sword.",
        )

        await agent.execute(ctx)

        assert provider.last_options is not None
        assert provider.last_options.temperature == 0.7

    @pytest.mark.asyncio
    async def test_style_transfer_mode_uses_temperature_08(self):
        provider = FakeProvider(_make_style_response())
        agent = RewriteAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Convert this to poetic style: The warrior drew her sword.",
        )

        await agent.execute(ctx)

        assert provider.last_options is not None
        assert provider.last_options.temperature == 0.8

    @pytest.mark.asyncio
    async def test_style_transfer_poetic_detected(self):
        provider = FakeProvider(_make_style_response())
        agent = RewriteAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Rewrite this in a poetic tone: The warrior drew her sword.",
        )

        result = await agent.execute(ctx)

        assert result.metadata["mode"] == "style_transfer"
        user_msg = provider.last_messages[1].content
        assert "poetic" in user_msg.lower()
