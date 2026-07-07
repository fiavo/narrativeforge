import json
from typing import AsyncIterator
from uuid import UUID, uuid4

import pytest

from NarrativeForge.Engine.ai_providers.base import (
    AIProvider,
    CompletionOptions,
    Message,
)
from NarrativeForge.Engine.agents.base import AgentContext, AgentResult
from NarrativeForge.Engine.agents.timeline_agent import TimelineAgent
from NarrativeForge.Engine.models.project import GameGenre, Project
from NarrativeForge.Engine.models.story_bible import StoryBible
from NarrativeForge.Engine.models.timeline import TimelineEvent


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
    return Project(name="Test Project", genre=genre, themes=["war", "prophecy"])


def _make_timeline_response() -> str:
    return json.dumps({
        "title": "The Fall of Eldoria",
        "timestamp": "Year 1247 of the Third Age",
        "description": (
            "The ancient kingdom of Eldoria fell when the Obsidian Tower collapsed, "
            "releasing a wave of dark magic that corrupted the surrounding lands."
        ),
        "participants": ["King Aldric", "The Shadow Covenant"],
        "location": "Eldoria",
        "consequences": [
            "The Great Schism among the mages",
            "Refugees fled to the Northern Reaches",
        ],
    })


def _make_existing_event(title: str = "The Founding of Eldoria") -> TimelineEvent:
    return TimelineEvent(
        title=title,
        description="The great kingdom was established.",
        timestamp="Year 800 of the Third Age",
    )


def _make_bible(project_id: UUID | None = None) -> StoryBible:
    pid = project_id or uuid4()
    event = _make_existing_event()
    return StoryBible(
        project_id=pid,
        timeline=[event],
    )


class TestTimelineAgent:
    @pytest.mark.asyncio
    async def test_timeline_agent_returns_result(self):
        provider = FakeProvider(_make_timeline_response())
        agent = TimelineAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate a timeline event about the fall of a kingdom",
        )

        result = await agent.execute(ctx)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "TimelineAgent"

    @pytest.mark.asyncio
    async def test_timeline_agent_uses_temperature_06(self):
        provider = FakeProvider("{}")
        agent = TimelineAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate timeline events",
        )

        await agent.execute(ctx)

        assert provider.last_options is not None
        assert provider.last_options.temperature == 0.6

    @pytest.mark.asyncio
    async def test_timeline_agent_returns_changes(self):
        provider = FakeProvider(_make_timeline_response())
        agent = TimelineAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate a timeline event",
        )

        result = await agent.execute(ctx)

        assert len(result.changes) == 1
        change = result.changes[0]
        assert "timeline" in change
        assert len(change["timeline"]["new"]) == 1
        assert change["timeline"]["new"][0]["title"] == "The Fall of Eldoria"
        assert change["timeline"]["new"][0]["timestamp"] == "Year 1247 of the Third Age"
        assert change["timeline"]["updated"] == []

    @pytest.mark.asyncio
    async def test_timeline_agent_system_prompt_includes_existing_events(self):
        provider = FakeProvider("{}")
        agent = TimelineAgent(provider)
        bible = _make_bible()
        ctx = AgentContext(
            project=_make_project(),
            story_bible=bible,
            user_request="Generate timeline events",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "The Founding of Eldoria" in prompt
        assert "Existing timeline entries:" in prompt
