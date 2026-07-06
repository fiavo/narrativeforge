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
from NarrativeForge.Engine.agents.dialogue_agent import DialogueAgent, DialogueType
from NarrativeForge.Engine.models.project import GameGenre, Project
from NarrativeForge.Engine.models.character import Character, CharacterRole, PersonalityProfile
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


def _make_character(name: str = "Aria", role: CharacterRole = CharacterRole.Protagonist) -> Character:
    return Character(
        name=name,
        role=role,
        backstory="A warrior seeking redemption",
        motivation="Find the lost artifact",
        personality=PersonalityProfile(traits=["brave", "impulsive"], values=["honor", "loyalty"]),
        dialogue_style="Direct and passionate",
    )


def _make_bible(project_id: UUID | None = None) -> StoryBible:
    pid = project_id or uuid4()
    aria = _make_character("Aria", CharacterRole.Protagonist)
    villain = _make_character("Malakar", CharacterRole.Antagonist)
    return StoryBible(
        project_id=pid,
        characters={aria.id: aria, villain.id: villain},
    )


def _make_dialogue_response() -> str:
    return json.dumps({
        "dialogue_type": "conversation",
        "exchanges": [
            {"speaker": "Aria", "line": "I won't let you take the artifact!", "emotion": "determined", "action": "draws sword"},
            {"speaker": "Malakar", "line": "You're too late, warrior.", "emotion": "smug", "action": "holds up the relic"},
        ],
        "narrative_context": "Aria confronts Malakar in the ancient temple.",
    })


class TestDialogueAgent:
    @pytest.mark.asyncio
    async def test_dialogue_agent_returns_result(self):
        provider = FakeProvider(_make_dialogue_response())
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write a dialogue between Aria and the villain",
        )

        result = await agent.execute(ctx)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "DialogueAgent"
        assert isinstance(result.content, dict)
        assert "dialogue_type" in result.content
        assert "exchanges" in result.content

    @pytest.mark.asyncio
    async def test_dialogue_agent_has_exchanges(self):
        provider = FakeProvider(_make_dialogue_response())
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write a dialogue between Aria and Malakar",
        )

        result = await agent.execute(ctx)

        assert len(result.content["exchanges"]) == 2
        assert result.content["exchanges"][0]["speaker"] == "Aria"
        assert result.content["exchanges"][0]["line"] == "I won't let you take the artifact!"
        assert result.content["exchanges"][1]["speaker"] == "Malakar"
        assert result.metadata["exchange_count"] == 2

    @pytest.mark.asyncio
    async def test_dialogue_agent_system_prompt_includes_characters(self):
        provider = FakeProvider("{}")
        agent = DialogueAgent(provider)
        bible = _make_bible()
        ctx = AgentContext(
            project=_make_project(),
            story_bible=bible,
            user_request="Write dialogue",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "Aria" in prompt
        assert "Malakar" in prompt
        assert "Protagonist" in prompt
        assert "Antagonist" in prompt

    @pytest.mark.asyncio
    async def test_dialogue_agent_uses_format_parameter(self):
        provider = FakeProvider(_make_dialogue_response())
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write dialogue",
            previous_results={"format": "formatted"},
        )

        result = await agent.execute(ctx)

        assert result.metadata["format"] == "formatted"
        user_msg = provider.last_messages[1].content
        assert "readable script format" in user_msg.lower()

    @pytest.mark.asyncio
    async def test_dialogue_agent_includes_emotions_and_actions(self):
        provider = FakeProvider(_make_dialogue_response())
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write dialogue between Aria and Malakar",
        )

        result = await agent.execute(ctx)

        exchange = result.content["exchanges"][0]
        assert exchange["emotion"] == "determined"
        assert exchange["action"] == "draws sword"

    @pytest.mark.asyncio
    async def test_dialogue_agent_classifies_confrontation(self):
        provider = FakeProvider(_make_dialogue_response())
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write a confrontation dialogue where Aria argues with Malakar",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "confrontation" in prompt.lower()

    @pytest.mark.asyncio
    async def test_dialogue_agent_classifies_monologue(self):
        provider = FakeProvider(_make_dialogue_response())
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write a monologue for Aria about her past",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "monologue" in prompt.lower()

    @pytest.mark.asyncio
    async def test_dialogue_agent_invalid_json_fallback(self):
        provider = FakeProvider("This is not valid JSON at all")
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write dialogue",
        )

        result = await agent.execute(ctx)

        assert result.content["dialogue_type"] == DialogueType.CONVERSATION.value
        assert result.content["exchanges"] == []
        assert "error" in result.content

    @pytest.mark.asyncio
    async def test_dialogue_agent_uses_temperature_075(self):
        provider = FakeProvider("{}")
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write dialogue",
        )

        await agent.execute(ctx)

        assert provider.last_options is not None
        assert provider.last_options.temperature == 0.75

    @pytest.mark.asyncio
    async def test_dialogue_agent_system_prompt_includes_genre(self):
        provider = FakeProvider("{}")
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(GameGenre.Horror),
            user_request="Write dialogue",
        )

        prompt = agent.build_system_prompt(ctx)

        assert "Horror" in prompt
        assert "Tense, atmospheric" in prompt

    @pytest.mark.asyncio
    async def test_dialogue_agent_sends_system_and_user_messages(self):
        provider = FakeProvider("{}")
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write dialogue between characters",
        )

        await agent.execute(ctx)

        assert provider.last_messages is not None
        assert provider.last_messages[0].role.value == "system"
        assert provider.last_messages[1].role.value == "user"

    @pytest.mark.asyncio
    async def test_dialogue_agent_metadata_includes_dialogue_type(self):
        provider = FakeProvider(_make_dialogue_response())
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write dialogue",
        )

        result = await agent.execute(ctx)

        assert result.metadata["dialogue_type"] == "conversation"

    @pytest.mark.asyncio
    async def test_dialogue_agent_handles_empty_exchanges(self):
        empty_response = json.dumps({
            "dialogue_type": "monologue",
            "exchanges": [],
        })
        provider = FakeProvider(empty_response)
        agent = DialogueAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write a monologue",
        )

        result = await agent.execute(ctx)

        assert result.content["dialogue_type"] == "monologue"
        assert result.content["exchanges"] == []
        assert result.metadata["exchange_count"] == 0


class TestDialogueType:
    def test_all_types(self):
        assert DialogueType.CONVERSATION.value == "conversation"
        assert DialogueType.MONOLOGUE.value == "monologue"
        assert DialogueType.CONFRONTATION.value == "confrontation"
        assert DialogueType.NEGOTIATION.value == "negotiation"
        assert DialogueType.EXPOSITION.value == "exposition"
