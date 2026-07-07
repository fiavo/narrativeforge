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
from NarrativeForge.Engine.agents.world_agent import WorldAgent
from NarrativeForge.Engine.models.project import GameGenre, Project
from NarrativeForge.Engine.models.story_bible import StoryBible, Faction
from NarrativeForge.Engine.models.location import Location


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
    return Project(name="Test Project", genre=genre, themes=["magic", "war"])


def _make_location(name: str = "Old Town", loc_type: str = "city") -> Location:
    return Location(name=name, type=loc_type, description="A bustling old town")


def _make_faction(name: str = "Crown Guard") -> Faction:
    return Faction(name=name, description="The king's elite guard")


def _make_bible(project_id: UUID | None = None) -> StoryBible:
    pid = project_id or uuid4()
    loc = _make_location()
    faction = _make_faction()
    return StoryBible(
        project_id=pid,
        locations={loc.id: loc},
        factions={faction.id: faction},
    )


def _make_world_response() -> str:
    return json.dumps({
        "locations": [
            {
                "name": "Ironhold",
                "type": "city",
                "description": "A massive fortress-city built into a mountain.",
                "significance": "Capital of the dwarven kingdom.",
            }
        ],
        "factions": [
            {
                "name": "Dwarven Forge Council",
                "description": "The ruling body of the dwarven smiths.",
                "goals": ["Protect ancient forges", "Expand mining rights"],
                "allies": ["Ironhold"],
                "enemies": ["Goblin Wastes"],
            }
        ],
        "lore_entries": [
            {
                "title": "The Great Forging",
                "category": "culture",
                "content": "A sacred ritual where master smiths create legendary weapons.",
                "tags": ["culture", "smithing", "ritual"],
            }
        ],
    })


class TestWorldAgent:
    @pytest.mark.asyncio
    async def test_world_agent_returns_result(self):
        provider = FakeProvider(_make_world_response())
        agent = WorldAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate the starting world for a dwarven kingdom",
        )

        result = await agent.execute(ctx)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "WorldAgent"

    @pytest.mark.asyncio
    async def test_world_agent_has_content(self):
        provider = FakeProvider(_make_world_response())
        agent = WorldAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate the starting world",
        )

        result = await agent.execute(ctx)

        assert isinstance(result.content, dict)
        assert len(result.content["locations"]) == 1
        assert result.content["locations"][0]["name"] == "Ironhold"
        assert len(result.content["factions"]) == 1
        assert result.content["factions"][0]["name"] == "Dwarven Forge Council"
        assert len(result.content["lore_entries"]) == 1
        assert result.content["lore_entries"][0]["title"] == "The Great Forging"

    @pytest.mark.asyncio
    async def test_world_agent_returns_changes(self):
        provider = FakeProvider(_make_world_response())
        agent = WorldAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate the starting world",
        )

        result = await agent.execute(ctx)

        assert len(result.changes) == 1
        change = result.changes[0]
        assert "locations" in change
        assert "factions" in change
        assert "lore_entries" in change
        assert len(change["locations"]["new"]) == 1
        assert change["locations"]["new"][0]["name"] == "Ironhold"
        assert len(change["factions"]["new"]) == 1
        assert change["factions"]["new"][0]["name"] == "Dwarven Forge Council"
        assert len(change["lore_entries"]["new"]) == 1
        assert change["lore_entries"]["new"][0]["title"] == "The Great Forging"

    @pytest.mark.asyncio
    async def test_world_agent_system_prompt_includes_genre(self):
        provider = FakeProvider("{}")
        agent = WorldAgent(provider)
        ctx = AgentContext(
            project=_make_project(GameGenre.SciFi),
            user_request="Generate world",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "SciFi" in prompt

    @pytest.mark.asyncio
    async def test_world_agent_system_prompt_includes_themes(self):
        provider = FakeProvider("{}")
        agent = WorldAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate world",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "magic" in prompt
        assert "war" in prompt

    @pytest.mark.asyncio
    async def test_world_agent_system_prompt_includes_story_bible(self):
        provider = FakeProvider("{}")
        agent = WorldAgent(provider)
        bible = _make_bible()
        ctx = AgentContext(
            project=_make_project(),
            story_bible=bible,
            user_request="Generate world",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "Old Town" in prompt
        assert "Crown Guard" in prompt

    @pytest.mark.asyncio
    async def test_world_agent_avoids_duplicates(self):
        provider = FakeProvider(_make_world_response())
        agent = WorldAgent(provider)
        bible = _make_bible()
        ctx = AgentContext(
            project=_make_project(),
            story_bible=bible,
            user_request="Generate world",
        )

        user_prompt = agent._build_user_prompt(ctx)

        assert "avoid duplicating" in user_prompt
        assert "Old Town" in user_prompt
        assert "Crown Guard" in user_prompt

    @pytest.mark.asyncio
    async def test_world_agent_uses_temperature_07(self):
        provider = FakeProvider("{}")
        agent = WorldAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate world",
        )

        await agent.execute(ctx)

        assert provider.last_options is not None
        assert provider.last_options.temperature == 0.7

    @pytest.mark.asyncio
    async def test_world_agent_sends_system_and_user_messages(self):
        provider = FakeProvider("{}")
        agent = WorldAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate world",
        )

        await agent.execute(ctx)

        assert provider.last_messages is not None
        assert provider.last_messages[0].role.value == "system"
        assert provider.last_messages[1].role.value == "user"

    @pytest.mark.asyncio
    async def test_world_agent_invalid_json_fallback(self):
        provider = FakeProvider("This is not valid JSON")
        agent = WorldAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate world",
        )

        result = await agent.execute(ctx)

        assert result.content["locations"] == []
        assert result.content["factions"] == []
        assert result.content["lore_entries"] == []
        assert "error" in result.content
        assert result.changes == []

    @pytest.mark.asyncio
    async def test_world_agent_metadata(self):
        provider = FakeProvider(_make_world_response())
        agent = WorldAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate world",
        )

        result = await agent.execute(ctx)

        assert result.metadata["location_count"] == 1
        assert result.metadata["faction_count"] == 1
        assert result.metadata["lore_entry_count"] == 1
        assert result.metadata["genre"] == "Fantasy"

    @pytest.mark.asyncio
    async def test_world_agent_with_previous_results(self):
        provider = FakeProvider(_make_world_response())
        agent = WorldAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate world",
            previous_results={"DirectorAgent": {"notes": "Focus on dwarven lore"}},
        )

        user_prompt = agent._build_user_prompt(ctx)

        assert "DirectorAgent" in user_prompt

    @pytest.mark.asyncio
    async def test_world_agent_empty_response_no_changes(self):
        empty_response = json.dumps({
            "locations": [],
            "factions": [],
            "lore_entries": [],
        })
        provider = FakeProvider(empty_response)
        agent = WorldAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Generate world",
        )

        result = await agent.execute(ctx)

        assert result.changes == []
