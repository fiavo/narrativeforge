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
from NarrativeForge.Engine.agents.quest_agent import QuestAgent
from NarrativeForge.Engine.models.project import GameGenre, Project
from NarrativeForge.Engine.models.story_bible import StoryBible, Faction
from NarrativeForge.Engine.models.location import Location
from NarrativeForge.Engine.models.character import Character, CharacterRole, PersonalityProfile


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


def _make_bible(project_id: UUID | None = None) -> StoryBible:
    pid = project_id or uuid4()
    loc = _make_location()
    faction = _make_faction()
    return StoryBible(
        project_id=pid,
        locations={loc.id: loc},
        factions={faction.id: faction},
    )


def _make_quest_response() -> str:
    return json.dumps({
        "name": "The Lost Relic",
        "description": "Recover the ancient relic from the Dark Forest.",
        "is_main_quest": True,
        "objectives": [
            {
                "description": "Travel to the Dark Forest",
                "type": "explore",
                "target": "Dark Forest",
                "quantity": 1,
                "is_required": True,
            },
            {
                "description": "Defeat the forest guardian",
                "type": "kill",
                "target": "Forest Guardian",
                "quantity": 1,
                "is_required": True,
            },
            {
                "description": "Collect the relic",
                "type": "collect",
                "target": "Ancient Relic",
                "quantity": 1,
                "is_required": True,
            },
        ],
        "prerequisites": [],
        "rewards": {
            "xp": 500,
            "gold": 200,
            "items": ["Ancient Relic", "Guardian's Blade"],
            "reputation": 50,
        },
    })


class TestQuestAgent:
    @pytest.mark.asyncio
    async def test_quest_agent_returns_result(self):
        provider = FakeProvider(_make_quest_response())
        agent = QuestAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create a main quest about finding a lost relic",
        )

        result = await agent.execute(ctx)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "QuestAgent"

    @pytest.mark.asyncio
    async def test_quest_agent_has_quest_data(self):
        provider = FakeProvider(_make_quest_response())
        agent = QuestAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create a main quest about finding a lost relic",
        )

        result = await agent.execute(ctx)

        assert isinstance(result.content, dict)
        assert result.content["name"] == "The Lost Relic"
        assert result.content["is_main_quest"] is True
        assert len(result.content["objectives"]) == 3
        assert result.content["objectives"][0]["type"] == "explore"
        assert result.content["objectives"][1]["type"] == "kill"
        assert result.content["objectives"][2]["type"] == "collect"

    @pytest.mark.asyncio
    async def test_quest_agent_system_prompt_includes_locations(self):
        provider = FakeProvider("{}")
        agent = QuestAgent(provider)
        bible = _make_bible()
        ctx = AgentContext(
            project=_make_project(),
            story_bible=bible,
            user_request="Create a quest",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "Dark Forest" in prompt
        assert "wilderness" in prompt
        assert "Shadow Covenant" in prompt

    @pytest.mark.asyncio
    async def test_quest_agent_includes_rewards(self):
        provider = FakeProvider(_make_quest_response())
        agent = QuestAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create a main quest about finding a lost relic",
        )

        result = await agent.execute(ctx)

        rewards = result.content["rewards"]
        assert rewards["xp"] == 500
        assert rewards["gold"] == 200
        assert "Ancient Relic" in rewards["items"]
        assert "Guardian's Blade" in rewards["items"]
        assert rewards["reputation"] == 50
        assert result.metadata["has_rewards"] is True

    @pytest.mark.asyncio
    async def test_quest_agent_uses_temperature_06(self):
        provider = FakeProvider("{}")
        agent = QuestAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create a quest",
        )

        await agent.execute(ctx)

        assert provider.last_options is not None
        assert provider.last_options.temperature == 0.6

    @pytest.mark.asyncio
    async def test_quest_agent_invalid_json_fallback(self):
        provider = FakeProvider("This is not valid JSON")
        agent = QuestAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create a quest",
        )

        result = await agent.execute(ctx)

        assert result.content["name"] == "Unnamed Quest"
        assert result.content["objectives"] == []
        assert result.content["rewards"]["xp"] == 0
        assert "error" in result.content

    @pytest.mark.asyncio
    async def test_quest_agent_sends_system_and_user_messages(self):
        provider = FakeProvider("{}")
        agent = QuestAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create a quest",
        )

        await agent.execute(ctx)

        assert provider.last_messages is not None
        assert provider.last_messages[0].role.value == "system"
        assert provider.last_messages[1].role.value == "user"

    @pytest.mark.asyncio
    async def test_quest_agent_metadata_includes_genre(self):
        provider = FakeProvider(_make_quest_response())
        agent = QuestAgent(provider)
        ctx = AgentContext(
            project=_make_project(GameGenre.Horror),
            user_request="Create a quest",
        )

        result = await agent.execute(ctx)

        assert result.metadata["genre"] == "Horror"
        assert result.metadata["is_main_quest"] is True
        assert result.metadata["has_objectives"] is True

    @pytest.mark.asyncio
    async def test_quest_agent_system_prompt_includes_genre_hint(self):
        provider = FakeProvider("{}")
        agent = QuestAgent(provider)
        ctx = AgentContext(
            project=_make_project(GameGenre.Horror),
            user_request="Create a quest",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "Horror" in prompt
        assert "Survival, escape" in prompt
