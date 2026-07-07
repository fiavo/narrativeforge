import json
from typing import AsyncIterator
from uuid import UUID, uuid4

import pytest

from NarrativeForge.Engine.ai_providers.base import (
    AIProvider,
    CompletionOptions,
    Message,
)
from NarrativeForge.Engine.agents.base import AgentContext, AgentResult, AgentRole
from NarrativeForge.Engine.agents.story_agent import StoryAgent
from NarrativeForge.Engine.agents.director_agent import DirectorAgent, RequestType
from NarrativeForge.Engine.agents.consistency_checker import (
    ConsistencyChecker,
    ConsistencyIssue,
    ConsistencyReport,
    IssueSeverity,
)
from NarrativeForge.Engine.models.project import GameGenre, Project
from NarrativeForge.Engine.models.character import Character, CharacterRole
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
    return StoryBible(
        project_id=pid,
        characters={char.id: char},
    )


class TestAgentContext:
    def test_defaults(self):
        project = _make_project()
        ctx = AgentContext(project=project)
        assert ctx.project is project
        assert ctx.story_bible is None
        assert ctx.graph is None
        assert ctx.user_request == ""
        assert ctx.generation_params is None
        assert ctx.previous_results == {}
        assert ctx.locked_elements == set()

    def test_with_all_fields(self):
        project = _make_project()
        bible = _make_bible()
        ctx = AgentContext(
            project=project,
            story_bible=bible,
            user_request="Write a chapter",
            previous_results={"StoryAgent": {"title": "Ch1"}},
            locked_elements={uuid4()},
        )
        assert ctx.story_bible is bible
        assert ctx.user_request == "Write a chapter"
        assert len(ctx.locked_elements) == 1


class TestAgentResult:
    def test_basic(self):
        result = AgentResult(agent_name="test", content={"key": "value"})
        assert result.agent_name == "test"
        assert result.content == {"key": "value"}
        assert result.metadata == {}
        assert result.changes == []

    def test_with_metadata(self):
        result = AgentResult(
            agent_name="test",
            content="text",
            metadata={"task_type": "chapter"},
            changes=[{"type": "add", "field": "title"}],
        )
        assert result.metadata["task_type"] == "chapter"
        assert len(result.changes) == 1


class TestStoryAgent:
    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        json_response = json.dumps([{"title": "Beat 1", "description": "Inciting incident"}])
        provider = FakeProvider(json_response)
        agent = StoryAgent(provider)
        project = _make_project()
        ctx = AgentContext(project=project, user_request="Generate story beats")

        result = await agent.execute(ctx)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "StoryAgent"
        assert isinstance(result.content, list)
        assert result.content[0]["title"] == "Beat 1"

    @pytest.mark.asyncio
    async def test_execute_dialogue_detection(self):
        json_response = json.dumps([{"speaker": "Aria", "line": "Hello!"}])
        provider = FakeProvider(json_response)
        agent = StoryAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Write dialogue between Aria and enemy")

        result = await agent.execute(ctx)

        assert result.metadata["task_type"] == "dialogue"

    @pytest.mark.asyncio
    async def test_execute_chapter_detection(self):
        json_response = json.dumps({"title": "Chapter 1", "content": "The story begins..."})
        provider = FakeProvider(json_response)
        agent = StoryAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Write a scene about the battle")

        result = await agent.execute(ctx)

        assert result.metadata["task_type"] == "chapter"

    @pytest.mark.asyncio
    async def test_execute_invalid_json_fallback(self):
        provider = FakeProvider("not json at all")
        agent = StoryAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Generate story beats")

        result = await agent.execute(ctx)

        assert result.content == {"raw": "not json at all", "task_type": "story_beat"}

    @pytest.mark.asyncio
    async def test_system_prompt_includes_genre(self):
        provider = FakeProvider("{}")
        agent = StoryAgent(provider)
        ctx = AgentContext(project=_make_project(GameGenre.Horror), user_request="test")

        prompt = agent.build_system_prompt(ctx)

        assert "Horror" in prompt
        assert "Tense, atmospheric" in prompt

    @pytest.mark.asyncio
    async def test_system_prompt_includes_themes(self):
        provider = FakeProvider("{}")
        agent = StoryAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="test")

        prompt = agent.build_system_prompt(ctx)

        assert "redemption" in prompt
        assert "power" in prompt

    @pytest.mark.asyncio
    async def test_system_prompt_includes_story_bible(self):
        provider = FakeProvider("{}")
        agent = StoryAgent(provider)
        bible = _make_bible()
        ctx = AgentContext(project=_make_project(), story_bible=bible, user_request="test")

        prompt = agent.build_system_prompt(ctx)

        assert "Aria" in prompt

    @pytest.mark.asyncio
    async def test_uses_custom_generation_params(self):
        provider = FakeProvider("{}")
        agent = StoryAgent(provider)
        opts = CompletionOptions(temperature=0.2, max_tokens=1024)
        ctx = AgentContext(
            project=_make_project(),
            user_request="test",
            generation_params=opts,
        )

        await agent.execute(ctx)

        assert provider.last_options is opts

    @pytest.mark.asyncio
    async def test_sends_system_and_user_messages(self):
        provider = FakeProvider("{}")
        agent = StoryAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Generate beats")

        await agent.execute(ctx)

        assert provider.last_messages is not None
        assert provider.last_messages[0].role.value == "system"
        assert provider.last_messages[1].role.value == "user"
        assert "Generate beats" in provider.last_messages[1].content


class TestDirectorAgent:
    @pytest.mark.asyncio
    async def test_execute_returns_plan(self):
        plan = {
            "request_type": "generate",
            "sub_tasks": [
                {"agent": "story", "instruction": "Write opening scene"},
                {"agent": "consistency", "instruction": "Check for plot holes"},
            ],
            "summary": "Generate a new chapter with consistency check",
            "context_notes": "",
        }
        provider = FakeProvider(json.dumps(plan))
        agent = DirectorAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Write chapter 1")

        result = await agent.execute(ctx)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "DirectorAgent"
        assert result.content["request_type"] == "generate"
        assert len(result.content["sub_tasks"]) == 2
        assert result.metadata["sub_task_count"] == 2

    @pytest.mark.asyncio
    async def test_execute_revise_request(self):
        plan = {"request_type": "revise", "sub_tasks": [], "summary": "Revise dialogue"}
        provider = FakeProvider(json.dumps(plan))
        agent = DirectorAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Revise the dialogue in chapter 2")

        result = await agent.execute(ctx)

        assert result.content["request_type"] == "revise"

    @pytest.mark.asyncio
    async def test_execute_invalid_json_fallback(self):
        provider = FakeProvider("This is a plan to generate content.")
        agent = DirectorAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="test")

        result = await agent.execute(ctx)

        assert result.content["request_type"] == RequestType.GENERATE.value
        assert result.content["summary"] == "This is a plan to generate content."

    @pytest.mark.asyncio
    async def test_system_prompt_includes_project_info(self):
        provider = FakeProvider("{}")
        agent = DirectorAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="test")

        prompt = agent.build_system_prompt(ctx)

        assert "Test Project" in prompt
        assert "Fantasy" in prompt

    @pytest.mark.asyncio
    async def test_system_prompt_includes_previous_results(self):
        provider = FakeProvider("{}")
        agent = DirectorAgent(provider)
        ctx = AgentContext(
            project=_make_project(),
            user_request="test",
            previous_results={"StoryAgent": {"title": "Ch1"}},
        )

        prompt = agent.build_system_prompt(ctx)

        assert "StoryAgent" in prompt

    @pytest.mark.asyncio
    async def test_uses_low_temperature(self):
        provider = FakeProvider("{}")
        agent = DirectorAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="test")

        await agent.execute(ctx)

        assert provider.last_options is not None
        assert provider.last_options.temperature == 0.3

    @pytest.mark.asyncio
    async def test_director_classifies_dialogue(self):
        plan = {
            "request_type": "generate",
            "classification": "dialogue",
            "sub_tasks": [{"agent": "story", "instruction": "Write dialogue between Aria and the villain"}],
            "summary": "Generate dialogue scene",
        }
        provider = FakeProvider(json.dumps(plan))
        agent = DirectorAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Write a conversation between Aria and the villain")

        result = await agent.execute(ctx)

        assert result.content["classification"] == "dialogue"
        assert result.metadata["classification"] == "dialogue"

    @pytest.mark.asyncio
    async def test_director_classifies_quest(self):
        plan = {
            "request_type": "generate",
            "classification": "quest",
            "sub_tasks": [{"agent": "story", "instruction": "Create a fetch quest for the artifact"}],
            "summary": "Generate quest content",
        }
        provider = FakeProvider(json.dumps(plan))
        agent = DirectorAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Design a quest to find the lost artifact")

        result = await agent.execute(ctx)

        assert result.content["classification"] == "quest"
        assert result.metadata["classification"] == "quest"

    @pytest.mark.asyncio
    async def test_director_classifies_lore(self):
        plan = {
            "request_type": "generate",
            "classification": "lore",
            "sub_tasks": [{"agent": "story", "instruction": "Write the history of the ancient kingdom"}],
            "summary": "Generate lore content",
        }
        provider = FakeProvider(json.dumps(plan))
        agent = DirectorAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Explain the history of the ancient kingdom")

        result = await agent.execute(ctx)

        assert result.content["classification"] == "lore"
        assert result.metadata["classification"] == "lore"

    @pytest.mark.asyncio
    async def test_director_classifies_world(self):
        plan = {
            "request_type": "generate",
            "classification": "world",
            "sub_tasks": [{"agent": "story", "instruction": "Describe the kingdom of Eldoria and its geography"}],
            "summary": "Generate world-building content",
        }
        provider = FakeProvider(json.dumps(plan))
        agent = DirectorAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Describe the world of Eldoria")

        result = await agent.execute(ctx)

        assert result.content["classification"] == "world"
        assert result.metadata["classification"] == "world"

    @pytest.mark.asyncio
    async def test_director_classifies_timeline(self):
        plan = {
            "request_type": "generate",
            "classification": "timeline",
            "sub_tasks": [{"agent": "story", "instruction": "Create a chronological history of the kingdom"}],
            "summary": "Generate timeline content",
        }
        provider = FakeProvider(json.dumps(plan))
        agent = DirectorAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Create a timeline of events in the kingdom")

        result = await agent.execute(ctx)

        assert result.content["classification"] == "timeline"
        assert result.metadata["classification"] == "timeline"

    @pytest.mark.asyncio
    async def test_director_classifies_critique(self):
        plan = {
            "request_type": "analyze",
            "classification": "critique",
            "sub_tasks": [{"agent": "story", "instruction": "Provide critical analysis of the chapter"}],
            "summary": "Critique the written content",
        }
        provider = FakeProvider(json.dumps(plan))
        agent = DirectorAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Critique the chapter I just wrote")

        result = await agent.execute(ctx)

        assert result.content["classification"] == "critique"
        assert result.metadata["classification"] == "critique"

    @pytest.mark.asyncio
    async def test_director_classifies_rewrite(self):
        plan = {
            "request_type": "revise",
            "classification": "rewrite",
            "sub_tasks": [{"agent": "story", "instruction": "Rewrite the opening scene with more tension"}],
            "summary": "Rewrite content with improvements",
        }
        provider = FakeProvider(json.dumps(plan))
        agent = DirectorAgent(provider)
        ctx = AgentContext(project=_make_project(), user_request="Rewrite the opening scene to be more engaging")

        result = await agent.execute(ctx)

        assert result.content["classification"] == "rewrite"
        assert result.metadata["classification"] == "rewrite"


class TestConsistencyChecker:
    @pytest.mark.asyncio
    async def test_execute_returns_report(self):
        report = {
            "score": 0.85,
            "issues": [
                {
                    "severity": "warning",
                    "category": "character",
                    "description": "Aria's motivation contradicts earlier statement",
                    "suggestion": "Align motivation with chapter 1 backstory",
                }
            ],
            "summary": "Mostly consistent with one character issue",
        }
        provider = FakeProvider(json.dumps(report))
        checker = ConsistencyChecker(provider)
        ctx = AgentContext(
            project=_make_project(),
            story_bible=_make_bible(),
            user_request="Validate this content",
            previous_results={"content": {"title": "Chapter 1", "text": "Story content..."}},
        )

        result = await checker.execute(ctx)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "ConsistencyChecker"
        assert result.content["score"] == 0.85
        assert len(result.content["issues"]) == 1
        assert result.content["issues"][0]["severity"] == "warning"
        assert result.metadata["issue_count"] == 1
        assert result.metadata["critical_count"] == 0

    @pytest.mark.asyncio
    async def test_execute_with_critical_issues(self):
        report = {
            "score": 0.3,
            "issues": [
                {"severity": "critical", "category": "timeline", "description": "Event ordering wrong"},
                {"severity": "critical", "category": "plot", "description": "Major plot hole"},
                {"severity": "info", "category": "lore", "description": "Minor lore inconsistency"},
            ],
            "summary": "Multiple critical issues found",
        }
        provider = FakeProvider(json.dumps(report))
        checker = ConsistencyChecker(provider)
        ctx = AgentContext(project=_make_project(), user_request="check")

        result = await checker.execute(ctx)

        assert result.content["score"] == 0.3
        assert result.metadata["critical_count"] == 2
        assert result.metadata["issue_count"] == 3

    @pytest.mark.asyncio
    async def test_execute_invalid_json_fallback(self):
        provider = FakeProvider("The content looks good overall.")
        checker = ConsistencyChecker(provider)
        ctx = AgentContext(project=_make_project(), user_request="check this")

        result = await checker.execute(ctx)

        assert result.content["score"] == 0.0
        assert "Failed to parse" in result.content["summary"]

    @pytest.mark.asyncio
    async def test_system_prompt_includes_bible(self):
        provider = FakeProvider("{}")
        checker = ConsistencyChecker(provider)
        bible = _make_bible()
        ctx = AgentContext(project=_make_project(), story_bible=bible, user_request="test")

        prompt = checker.build_system_prompt(ctx)

        assert "Aria" in prompt
        assert "Protagonist" in prompt

    @pytest.mark.asyncio
    async def test_system_prompt_includes_locked_elements(self):
        provider = FakeProvider("{}")
        checker = ConsistencyChecker(provider)
        locked = {uuid4(), uuid4()}
        ctx = AgentContext(project=_make_project(), user_request="test", locked_elements=locked)

        prompt = checker.build_system_prompt(ctx)

        assert "Locked elements" in prompt
        assert "2" in prompt

    @pytest.mark.asyncio
    async def test_extracts_content_from_previous_results(self):
        provider = FakeProvider("{}")
        checker = ConsistencyChecker(provider)
        content = {"chapter": 1, "text": "The hero entered the cave..."}
        ctx = AgentContext(
            project=_make_project(),
            user_request="check",
            previous_results={"content": content},
        )

        await checker.execute(ctx)

        user_msg = provider.last_messages[1].content
        assert "hero entered the cave" in user_msg

    @pytest.mark.asyncio
    async def test_uses_low_temperature(self):
        provider = FakeProvider("{}")
        checker = ConsistencyChecker(provider)
        ctx = AgentContext(project=_make_project(), user_request="check")

        await checker.execute(ctx)

        assert provider.last_options is not None
        assert provider.last_options.temperature == 0.2


class TestConsistencyReport:
    def test_to_dict(self):
        report = ConsistencyReport(
            score=0.75,
            issues=[
                ConsistencyIssue(
                    severity=IssueSeverity.WARNING,
                    category="character",
                    description="Motivation mismatch",
                    suggestion="Fix backstory",
                )
            ],
            summary="One issue found",
        )
        d = report.to_dict()
        assert d["score"] == 0.75
        assert len(d["issues"]) == 1
        assert d["issues"][0]["severity"] == "warning"
        assert d["summary"] == "One issue found"

    def test_empty_report(self):
        report = ConsistencyReport(score=1.0)
        d = report.to_dict()
        assert d["score"] == 1.0
        assert d["issues"] == []


class TestAgentRole:
    def test_roles(self):
        assert AgentRole.DIRECTOR.value == "director"
        assert AgentRole.STORY.value == "story"
        assert AgentRole.CONSISTENCY.value == "consistency"
