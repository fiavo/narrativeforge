import json
from typing import AsyncIterator
from unittest.mock import patch, MagicMock

import pytest

from NarrativeForge.Engine.ai_providers.base import AIProvider, CompletionOptions, Message
from NarrativeForge.Engine.agents.base import AgentContext, AgentResult, BaseAgent
from NarrativeForge.Engine.plugins.plugin_info import PluginInfo, PluginType
from NarrativeForge.Engine.pipeline.orchestrator import PipelineOrchestrator
from NarrativeForge.Engine.models.project import GameGenre, Project


class FakeProvider(AIProvider):
    def __init__(self, responses: dict[str, str] | None = None, response: str = "{}"):
        self._responses = responses or {}
        self._fallback = response

    async def complete(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> str:
        system_msg = messages[0].content if messages else ""
        for key, resp in self._responses.items():
            if key.lower() in system_msg.lower():
                return resp
        return self._fallback

    async def stream(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> AsyncIterator[str]:
        for word in self._fallback.split():
            yield word + " "


class FakePluginAgent(BaseAgent):
    def __init__(self, provider: AIProvider, name: str = "CustomPluginAgent") -> None:
        super().__init__(provider)
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def build_system_prompt(self, context: AgentContext) -> str:
        return "You are a custom plugin agent."

    async def execute(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            content={"source": "plugin", "message": "Hello from plugin"},
            metadata={"plugin": True},
        )


def _make_project(genre: GameGenre = GameGenre.Fantasy) -> Project:
    return Project(name="Test Project", genre=genre, themes=["redemption"])


def _make_plugin_info(name: str = "custom", plugin_type: PluginType = PluginType.AGENT) -> PluginInfo:
    return PluginInfo(
        name=name,
        version="1.0.0",
        description="Test plugin agent",
        plugin_type=plugin_type,
        entry_point="test_module:FakePluginAgent",
    )


class TestPluginAgentRegistration:
    @pytest.mark.asyncio
    async def test_plugin_agent_registers(self):
        provider = FakeProvider()
        plugin_agent = FakePluginAgent(provider, name="custom")
        plugin_info = _make_plugin_info(name="custom")

        with patch(
            "NarrativeForge.Engine.plugins.plugin_manager.PluginManager.discover",
            return_value=[plugin_info],
        ), patch(
            "NarrativeForge.Engine.plugins.plugin_manager.PluginManager.load",
            return_value=plugin_agent,
        ):
            orchestrator = PipelineOrchestrator(provider)

        assert "custom" in orchestrator.plugin_agents
        assert orchestrator.plugin_agents["custom"] is plugin_agent

    @pytest.mark.asyncio
    async def test_plugin_agent_not_registered_when_disabled(self):
        provider = FakeProvider()
        plugin_info = _make_plugin_info(name="disabled_plugin")
        plugin_info.enabled = False

        with patch(
            "NarrativeForge.Engine.plugins.plugin_manager.PluginManager.discover",
            return_value=[plugin_info],
        ):
            orchestrator = PipelineOrchestrator(provider)

        assert "disabled_plugin" not in orchestrator.plugin_agents

    @pytest.mark.asyncio
    async def test_non_agent_plugin_not_registered(self):
        provider = FakeProvider()
        plugin_info = _make_plugin_info(name="provider_plugin", plugin_type=PluginType.PROVIDER)

        with patch(
            "NarrativeForge.Engine.plugins.plugin_manager.PluginManager.discover",
            return_value=[plugin_info],
        ):
            orchestrator = PipelineOrchestrator(provider)

        assert "provider_plugin" not in orchestrator.plugin_agents

    @pytest.mark.asyncio
    async def test_non_base_agent_instance_not_registered(self):
        provider = FakeProvider()
        plugin_info = _make_plugin_info(name="bad_plugin")

        with patch(
            "NarrativeForge.Engine.plugins.plugin_manager.PluginManager.discover",
            return_value=[plugin_info],
        ), patch(
            "NarrativeForge.Engine.plugins.plugin_manager.PluginManager.load",
            return_value="not an agent",
        ):
            orchestrator = PipelineOrchestrator(provider)

        assert "bad_plugin" not in orchestrator.plugin_agents


class TestPluginAgentExecution:
    @pytest.mark.asyncio
    async def test_plugin_agent_can_execute(self):
        provider = FakeProvider(
            responses={
                "narrative director": json.dumps({
                    "request_type": "generate",
                    "classification": "custom",
                    "sub_tasks": [],
                    "summary": "Use custom plugin",
                }),
                "consistency checker": json.dumps({"score": 1.0, "issues": [], "summary": "OK"}),
            }
        )
        plugin_agent = FakePluginAgent(provider, name="custom")
        plugin_info = _make_plugin_info(name="custom")

        with patch(
            "NarrativeForge.Engine.plugins.plugin_manager.PluginManager.discover",
            return_value=[plugin_info],
        ), patch(
            "NarrativeForge.Engine.plugins.plugin_manager.PluginManager.load",
            return_value=plugin_agent,
        ):
            orchestrator = PipelineOrchestrator(provider)

        ctx = AgentContext(
            project=_make_project(),
            user_request="Use the custom plugin agent",
        )

        result = await orchestrator.run(ctx)

        assert result.stages_completed[0] == "Director"
        assert "Consistency" in result.stages_completed
        assert result.content == {"source": "plugin", "message": "Hello from plugin"}
        assert result.metadata["classification"] == "custom"
