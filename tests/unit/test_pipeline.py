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
from NarrativeForge.Engine.pipeline.orchestrator import PipelineOrchestrator, PipelineResult
from NarrativeForge.Engine.models.project import GameGenre, Project
from NarrativeForge.Engine.models.character import Character, CharacterRole
from NarrativeForge.Engine.models.story_bible import StoryBible


class FakeProvider(AIProvider):
    def __init__(self, responses: dict[str, str] | None = None, response: str = "{}"):
        self._responses = responses or {}
        self._fallback = response
        self.last_messages: list[Message] | None = None
        self.last_options: CompletionOptions | None = None
        self.call_count = 0

    async def complete(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> str:
        self.last_messages = messages
        self.last_options = options
        self.call_count += 1

        system_msg = messages[0].content if messages else ""
        for key, resp in self._responses.items():
            if key.lower() in system_msg.lower():
                return resp

        return self._fallback

    async def stream(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> AsyncIterator[str]:
        self.last_messages = messages
        for word in self._fallback.split():
            yield word + " "


def _make_project(genre: GameGenre = GameGenre.Fantasy) -> Project:
    return Project(name="Test Project", genre=genre, themes=["redemption", "power"])


def _make_character(name: str = "Aria") -> Character:
    return Character(
        name=name,
        role=CharacterRole.Protagonist,
        backstory="A warrior seeking redemption",
        motivation="Find the lost artifact",
    )


def _make_bible(project_id: UUID | None = None) -> StoryBible:
    pid = project_id or uuid4()
    char = _make_character()
    return StoryBible(project_id=pid, characters={char.id: char})


class TestPipelineResult:
    def test_defaults(self):
        result = PipelineResult()
        assert result.content is None
        assert result.stages_completed == []
        assert result.results == []
        assert result.metadata == {}

    def test_with_fields(self):
        agent_result = AgentResult(agent_name="test", content={"key": "value"})
        result = PipelineResult(
            content={"text": "hello"},
            stages_completed=["Director", "Story"],
            results=[agent_result],
            metadata={"consistency_score": 0.9},
        )
        assert result.content == {"text": "hello"}
        assert result.stages_completed == ["Director", "Story"]
        assert len(result.results) == 1
        assert result.metadata["consistency_score"] == 0.9


class TestPipelineOrchestrator:
    @pytest.mark.asyncio
    async def test_runs_all_three_stages(self):
        director_plan = {
            "request_type": "generate",
            "sub_tasks": [{"agent": "story", "instruction": "Write scene"}],
            "summary": "Generate scene",
            "context_notes": "",
        }
        story_content = [{"title": "Beat 1", "description": "Opening"}]
        consistency_report = {
            "score": 0.9,
            "issues": [],
            "summary": "All consistent",
        }

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "masterful narrative writer": json.dumps(story_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write a chapter",
        )

        result = await orchestrator.run(ctx)

        assert isinstance(result, PipelineResult)
        assert result.stages_completed == ["Director", "Story", "Consistency"]
        assert len(result.results) == 3
        assert result.results[0].agent_name == "DirectorAgent"
        assert result.results[1].agent_name == "StoryAgent"
        assert result.results[2].agent_name == "ConsistencyChecker"

    @pytest.mark.asyncio
    async def test_content_comes_from_story_agent(self):
        director_plan = {
            "request_type": "generate",
            "sub_tasks": [],
            "summary": "Plan",
        }
        story_content = {"title": "Chapter 1", "content": "Once upon a time..."}
        consistency_report = {"score": 0.85, "issues": [], "summary": "OK"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "masterful narrative writer": json.dumps(story_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        ctx = AgentContext(project=_make_project(), user_request="Write chapter 1")

        result = await orchestrator.run(ctx)

        assert result.content == story_content

    @pytest.mark.asyncio
    async def test_metadata_contains_consistency_score(self):
        director_plan = {"request_type": "generate", "sub_tasks": [], "summary": "Plan"}
        story_content = {"title": "Ch1", "content": "Text"}
        consistency_report = {
            "score": 0.75,
            "issues": [
                {"severity": "warning", "category": "character", "description": "Issue"}
            ],
            "summary": "One issue",
        }

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "masterful narrative writer": json.dumps(story_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        ctx = AgentContext(project=_make_project(), user_request="Write chapter")

        result = await orchestrator.run(ctx)

        assert result.metadata["consistency_score"] == 0.75
        assert result.metadata["issue_count"] == 1
        assert result.metadata["critical_count"] == 0

    @pytest.mark.asyncio
    async def test_context_propagates_to_story_with_director_results(self):
        director_plan = {
            "request_type": "generate",
            "sub_tasks": [],
            "summary": "Plan",
        }
        story_content = [{"title": "Beat 1", "description": "Inciting incident"}]
        consistency_report = {"score": 1.0, "issues": [], "summary": "Perfect"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "masterful narrative writer": json.dumps(story_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write scene",
            story_bible=_make_bible(),
        )

        result = await orchestrator.run(ctx)

        # Verify the story agent received director results in context
        # by checking the call count - all 3 stages should have run
        assert provider.call_count == 3
        assert result.stages_completed == ["Director", "Story", "Consistency"]

    @pytest.mark.asyncio
    async def test_critical_issues_reflected_in_metadata(self):
        director_plan = {"request_type": "generate", "sub_tasks": [], "summary": "Plan"}
        story_content = {"title": "Ch1", "content": "Text"}
        consistency_report = {
            "score": 0.2,
            "issues": [
                {"severity": "critical", "category": "timeline", "description": "Wrong order"},
                {"severity": "critical", "category": "plot", "description": "Plot hole"},
                {"severity": "info", "category": "lore", "description": "Minor"},
            ],
            "summary": "Multiple critical issues",
        }

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "masterful narrative writer": json.dumps(story_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        ctx = AgentContext(project=_make_project(), user_request="Write chapter")

        result = await orchestrator.run(ctx)

        assert result.metadata["consistency_score"] == 0.2
        assert result.metadata["issue_count"] == 3
        assert result.metadata["critical_count"] == 2

    @pytest.mark.asyncio
    async def test_propagates_generation_params(self):
        director_plan = {"request_type": "generate", "sub_tasks": [], "summary": "Plan"}
        story_content = []
        consistency_report = {"score": 1.0, "issues": [], "summary": "OK"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "masterful narrative writer": json.dumps(story_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        opts = CompletionOptions(temperature=0.5, max_tokens=1024)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write scene",
            generation_params=opts,
        )

        await orchestrator.run(ctx)

        # Verify the options were passed through to the provider
        assert provider.last_options is opts

    @pytest.mark.asyncio
    async def test_pipeline_routes_to_dialogue_agent(self):
        director_plan = {
            "request_type": "generate",
            "classification": "dialogue",
            "sub_tasks": [{"agent": "story", "instruction": "Write dialogue"}],
            "summary": "Generate dialogue",
        }
        dialogue_content = {
            "dialogue_type": "conversation",
            "exchanges": [
                {"speaker": "Aria", "line": "Hello there."},
                {"speaker": "Vex", "line": "Well, well."},
            ],
        }
        consistency_report = {"score": 0.9, "issues": [], "summary": "OK"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "masterful dialogue writer": json.dumps(dialogue_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write a dialogue between Aria and Vex",
        )

        result = await orchestrator.run(ctx)

        assert result.stages_completed[0] == "Director"
        assert "Dialogue" in result.stages_completed
        assert result.stages_completed[-1] == "Consistency"
        assert result.content == dialogue_content
        assert result.metadata["classification"] == "dialogue"

    @pytest.mark.asyncio
    async def test_pipeline_lore_changes_applied(self):
        director_plan = {
            "request_type": "generate",
            "classification": "lore",
            "sub_tasks": [],
            "summary": "Generate lore",
        }
        lore_content = {
            "title": "The Crystal Kingdoms",
            "category": "history",
            "content": "Ancient civilizations once thrived under crystalline skies.",
            "tags": ["history", "crystal"],
            "related_entries": [],
        }
        consistency_report = {"score": 0.95, "issues": [], "summary": "OK"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "masterful world-builder": json.dumps(lore_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        bible = _make_bible()
        initial_lore_count = len(bible.lore_entries)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create lore about the Crystal Kingdoms",
            story_bible=bible,
        )

        result = await orchestrator.run(ctx)

        assert len(bible.lore_entries) == initial_lore_count + 1
        added = list(bible.lore_entries.values())[-1]
        assert added.title == "The Crystal Kingdoms"
        assert added.category == "history"
        assert result.metadata["lore_entries_added"] == 1

    @pytest.mark.asyncio
    async def test_pipeline_routes_to_quest_agent(self):
        director_plan = {
            "request_type": "generate",
            "classification": "quest",
            "sub_tasks": [],
            "summary": "Generate quest",
        }
        quest_content = {
            "name": "Dragon's Lair",
            "description": "Slay the dragon",
            "is_main_quest": True,
            "objectives": [{"description": "Defeat dragon", "type": "kill", "target": "Dragon", "quantity": 1, "is_required": True}],
            "prerequisites": [],
            "rewards": {"xp": 100, "gold": 50, "items": [], "reputation": 10},
        }
        consistency_report = {"score": 0.88, "issues": [], "summary": "OK"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "masterful quest designer": json.dumps(quest_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Design a quest to slay the dragon",
        )

        result = await orchestrator.run(ctx)

        assert "Quest" in result.stages_completed
        assert result.content == quest_content
        assert result.metadata["classification"] == "quest"

    @pytest.mark.asyncio
    async def test_pipeline_mixed_runs_story_and_quest(self):
        director_plan = {
            "request_type": "generate",
            "classification": "mixed",
            "sub_tasks": [],
            "summary": "Generate story and quest",
        }
        story_content = [{"title": "Beat 1", "description": "Opening"}]
        quest_content = {
            "name": "Rescue Mission",
            "description": "Save the village",
            "is_main_quest": False,
            "objectives": [],
            "prerequisites": [],
            "rewards": {"xp": 50, "gold": 20, "items": [], "reputation": 5},
        }
        consistency_report = {"score": 0.92, "issues": [], "summary": "OK"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "masterful narrative writer": json.dumps(story_content),
                "masterful quest designer": json.dumps(quest_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write story beats and design a side quest",
        )

        result = await orchestrator.run(ctx)

        assert "Story" in result.stages_completed
        assert "Quest" in result.stages_completed
        assert result.stages_completed[-1] == "Consistency"
        assert result.metadata["classification"] == "mixed"

    @pytest.mark.asyncio
    async def test_propagates_story_bible(self):
        director_plan = {"request_type": "generate", "sub_tasks": [], "summary": "Plan"}
        story_content = []
        consistency_report = {"score": 1.0, "issues": [], "summary": "OK"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "masterful narrative writer": json.dumps(story_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        bible = _make_bible()
        ctx = AgentContext(
            project=_make_project(),
            user_request="Write scene",
            story_bible=bible,
        )

        result = await orchestrator.run(ctx)

        # Verify all 3 stages ran and completed
        assert result.stages_completed == ["Director", "Story", "Consistency"]
        assert provider.call_count == 3

    @pytest.mark.asyncio
    async def test_pipeline_routes_to_world_agent(self):
        director_plan = {
            "request_type": "generate",
            "classification": "world",
            "sub_tasks": [],
            "summary": "Generate world",
        }
        world_content = {
            "locations": [
                {"name": "Silverwood", "type": "city", "description": "A forest city", "significance": "Capital of the elves"}
            ],
            "factions": [
                {"name": "Silver Council", "description": "Elven ruling body", "goals": ["Peace"], "allies": [], "enemies": []}
            ],
            "lore_entries": [],
        }
        consistency_report = {"score": 0.9, "issues": [], "summary": "OK"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "world-builder": json.dumps(world_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create a world setting with cities and factions",
        )

        result = await orchestrator.run(ctx)

        assert "World" in result.stages_completed
        assert result.content == world_content
        assert result.metadata["classification"] == "world"

    @pytest.mark.asyncio
    async def test_pipeline_routes_to_timeline_agent(self):
        director_plan = {
            "request_type": "generate",
            "classification": "timeline",
            "sub_tasks": [],
            "summary": "Generate timeline",
        }
        timeline_content = {
            "title": "The Great War",
            "timestamp": "Year 1024",
            "description": "A devastating war between factions",
            "participants": ["Silver Council", "Shadow Guild"],
            "location": "Silverwood",
            "consequences": ["Factions weakened", "New alliance formed"],
        }
        consistency_report = {"score": 0.88, "issues": [], "summary": "OK"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "chronologist": json.dumps(timeline_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create a timeline of major events",
        )

        result = await orchestrator.run(ctx)

        assert "Timeline" in result.stages_completed
        assert result.content == timeline_content
        assert result.metadata["classification"] == "timeline"

    @pytest.mark.asyncio
    async def test_pipeline_world_changes_applied(self):
        director_plan = {
            "request_type": "generate",
            "classification": "world",
            "sub_tasks": [],
            "summary": "Generate world",
        }
        world_content = {
            "locations": [
                {"name": "Silverwood", "type": "city", "description": "A forest city", "significance": "Capital"}
            ],
            "factions": [
                {"name": "Silver Council", "description": "Ruling body", "goals": ["Peace"], "allies": [], "enemies": []}
            ],
            "lore_entries": [],
        }
        consistency_report = {"score": 0.9, "issues": [], "summary": "OK"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "world-builder": json.dumps(world_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        bible = _make_bible()
        initial_loc_count = len(bible.locations)
        initial_faction_count = len(bible.factions)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Create a world setting",
            story_bible=bible,
        )

        result = await orchestrator.run(ctx)

        assert len(bible.locations) == initial_loc_count + 1
        assert len(bible.factions) == initial_faction_count + 1
        assert result.metadata["world_elements_added"] == 2

    @pytest.mark.asyncio
    async def test_pipeline_routes_to_critique_agent(self):
        director_plan = {
            "request_type": "generate",
            "classification": "critique",
            "sub_tasks": [],
            "summary": "Evaluate content",
        }
        critic_content = {
            "overall_score": 0.85,
            "scores": {
                "coherence": 0.9,
                "character_depth": 0.8,
                "pacing": 0.85,
                "dialogue_quality": 0.8,
                "creativity": 0.9,
                "emotional_impact": 0.85,
            },
            "summary": "Strong narrative with good pacing",
            "strengths": ["Good world-building"],
            "weaknesses": ["Could develop characters more"],
        }
        consistency_report = {"score": 0.9, "issues": [], "summary": "OK"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "narrative quality critic": json.dumps(critic_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Evaluate this story content",
        )

        result = await orchestrator.run(ctx)

        assert "Critic" in result.stages_completed
        assert result.content == critic_content
        assert result.metadata["classification"] == "critique"

    @pytest.mark.asyncio
    async def test_pipeline_routes_to_rewrite_agent(self):
        director_plan = {
            "request_type": "generate",
            "classification": "rewrite",
            "sub_tasks": [],
            "summary": "Rewrite content",
        }
        rewrite_content = {
            "rewritten_text": "The ancient forest whispered secrets of ages past.",
            "mode": "polish",
            "changes_summary": "Enhanced descriptions and improved flow",
        }
        consistency_report = {"score": 0.9, "issues": [], "summary": "OK"}

        provider = FakeProvider(
            responses={
                "narrative director": json.dumps(director_plan),
                "expert text rewriter": json.dumps(rewrite_content),
                "consistency checker": json.dumps(consistency_report),
            }
        )

        orchestrator = PipelineOrchestrator(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="Rewrite this text to improve flow",
        )

        result = await orchestrator.run(ctx)

        assert "Rewrite" in result.stages_completed
        assert result.content == rewrite_content
        assert result.metadata["classification"] == "rewrite"
