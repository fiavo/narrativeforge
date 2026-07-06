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
from NarrativeForge.Engine.agents.lore_agent import LoreAgent
from NarrativeForge.Engine.models.project import GameGenre, Project
from NarrativeForge.Engine.models.story_bible import StoryBible, Faction
from NarrativeForge.Engine.models.location import Location
from NarrativeForge.Engine.models.character import Character, CharacterRole
from NarrativeForge.Engine.models.lore import LoreEntry


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


def _make_location(name: str = "Dark Forest", loc_type: str = "wilderness") -> Location:
    return Location(name=name, type=loc_type, description="A dark and eerie place")


def _make_faction(name: str = "Shadow Covenant") -> Faction:
    return Faction(name=name, description="A secretive organization")


def _make_existing_lore(title: str = "The Ancient War", category: str = "history") -> LoreEntry:
    return LoreEntry(
        title=title,
        category=category,
        content="A thousand years ago, the great war began...",
        tags=["war", "ancient"],
    )


def _make_bible(project_id: UUID | None = None) -> StoryBible:
    pid = project_id or uuid4()
    loc = _make_location()
    faction = _make_faction()
    lore = _make_existing_lore()
    return StoryBible(
        project_id=pid,
        locations={loc.id: loc},
        factions={faction.id: faction},
        lore_entries={lore.id: lore},
    )


def _make_lore_response() -> str:
    return json.dumps({
        "title": "The Dragon Cult",
        "category": "religion",
        "content": (
            "The Dragon Cult is an ancient religious order that worships the "
            "primordial dragons as divine beings. Founded during the Age of Scales, "
            "the cult believes dragons are the architects of the world and that "
            "their return will bring about a golden age."
        ),
        "tags": ["religion", "dragons", "cult", "ancient"],
        "related_entries": ["The Ancient War"],
    })


class TestLoreAgent:
    @pytest.mark.asyncio
    async def test_lore_agent_returns_result(self):
        provider = FakeProvider(_make_lore_response())
        agent = LoreAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create lore about the Dragon Cult religion",
        )

        result = await agent.execute(ctx)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "LoreAgent"

    @pytest.mark.asyncio
    async def test_lore_agent_has_entries(self):
        provider = FakeProvider(_make_lore_response())
        agent = LoreAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create lore about the Dragon Cult religion",
        )

        result = await agent.execute(ctx)

        assert isinstance(result.content, dict)
        assert result.content["title"] == "The Dragon Cult"
        assert result.content["category"] == "religion"
        assert "Dragon Cult" in result.content["content"]
        assert len(result.content["tags"]) == 4
        assert "religion" in result.content["tags"]

    @pytest.mark.asyncio
    async def test_lore_agent_returns_changes(self):
        provider = FakeProvider(_make_lore_response())
        agent = LoreAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create lore about the Dragon Cult religion",
        )

        result = await agent.execute(ctx)

        assert len(result.changes) == 1
        change = result.changes[0]
        assert "lore_entries" in change
        assert len(change["lore_entries"]["new"]) == 1
        assert change["lore_entries"]["new"][0]["title"] == "The Dragon Cult"
        assert change["lore_entries"]["new"][0]["category"] == "religion"
        assert change["lore_entries"]["updated"] == []

    @pytest.mark.asyncio
    async def test_lore_agent_system_prompt_includes_existing(self):
        provider = FakeProvider("{}")
        agent = LoreAgent(provider)
        bible = _make_bible()
        ctx = AgentContext(
            project=_make_project(),
            story_bible=bible,
            user_request="Create lore",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "Dark Forest" in prompt
        assert "Shadow Covenant" in prompt
        assert "The Ancient War" in prompt
        assert "Existing lore entries:" in prompt

    @pytest.mark.asyncio
    async def test_lore_agent_avoids_duplicates(self):
        provider = FakeProvider(_make_lore_response())
        agent = LoreAgent(provider)
        bible = _make_bible()
        ctx = AgentContext(
            project=_make_project(),
            story_bible=bible,
            user_request="Create lore about ancient history",
        )

        user_prompt = agent._build_user_prompt(ctx)

        assert "Existing lore entries to avoid duplicating:" in user_prompt
        assert "The Ancient War" in user_prompt

    @pytest.mark.asyncio
    async def test_lore_agent_uses_temperature_07(self):
        provider = FakeProvider("{}")
        agent = LoreAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create lore",
        )

        await agent.execute(ctx)

        assert provider.last_options is not None
        assert provider.last_options.temperature == 0.7

    @pytest.mark.asyncio
    async def test_lore_agent_sends_system_and_user_messages(self):
        provider = FakeProvider("{}")
        agent = LoreAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create lore",
        )

        await agent.execute(ctx)

        assert provider.last_messages is not None
        assert provider.last_messages[0].role.value == "system"
        assert provider.last_messages[1].role.value == "user"

    @pytest.mark.asyncio
    async def test_lore_agent_invalid_json_fallback(self):
        provider = FakeProvider("This is not valid JSON")
        agent = LoreAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create lore",
        )

        result = await agent.execute(ctx)

        assert result.content["title"] == ""
        assert result.content["content"] == "This is not valid JSON"
        assert "error" in result.content
        assert result.changes == []

    @pytest.mark.asyncio
    async def test_lore_agent_metadata_includes_category(self):
        provider = FakeProvider(_make_lore_response())
        agent = LoreAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create lore",
        )

        result = await agent.execute(ctx)

        assert result.metadata["category"] == "religion"
        assert result.metadata["has_title"] is True
        assert result.metadata["has_content"] is True
        assert result.metadata["genre"] == "Fantasy"

    @pytest.mark.asyncio
    async def test_lore_agent_system_prompt_includes_genre(self):
        provider = FakeProvider("{}")
        agent = LoreAgent(provider)
        ctx = AgentContext(
            project=_make_project(GameGenre.Horror),
            user_request="Create lore",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "Horror" in prompt

    @pytest.mark.asyncio
    async def test_lore_agent_system_prompt_includes_themes(self):
        provider = FakeProvider("{}")
        agent = LoreAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create lore",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "redemption" in prompt
        assert "power" in prompt

    @pytest.mark.asyncio
    async def test_lore_agent_no_existing_lore(self):
        provider = FakeProvider(_make_lore_response())
        agent = LoreAgent(provider)
        pid = uuid4()
        bible = StoryBible(project_id=pid)
        ctx = AgentContext(
            project=_make_project(),
            story_bible=bible,
            user_request="Create lore",
        )

        user_prompt = agent._build_user_prompt(ctx)

        assert "avoid duplicating" not in user_prompt

    @pytest.mark.asyncio
    async def test_lore_agent_with_previous_results(self):
        provider = FakeProvider(_make_lore_response())
        agent = LoreAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create lore",
            previous_results={"director_notes": "Focus on dark themes"},
        )

        user_prompt = agent._build_user_prompt(ctx)

        assert "director_notes" in user_prompt
        assert "dark themes" in user_prompt

    @pytest.mark.asyncio
    async def test_lore_agent_empty_content_no_changes(self):
        empty_response = json.dumps({
            "title": "",
            "category": "",
            "content": "",
            "tags": [],
            "related_entries": [],
        })
        provider = FakeProvider(empty_response)
        agent = LoreAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create lore",
        )

        result = await agent.execute(ctx)

        assert result.changes == []
