from __future__ import annotations

from typing import Any

from NarrativeForge.Engine.agents.base import AgentContext, AgentResult, BaseAgent
from NarrativeForge.Engine.ai_providers.base import AIProvider


class ExampleAgent(BaseAgent):
    """Example plugin agent demonstrating the NarrativeForge plugin pattern.

    This agent returns a static test response without calling any AI provider,
    serving as a template for building custom agents.
    """

    def __init__(self, provider: AIProvider | None = None) -> None:
        super().__init__(provider)  # type: ignore[arg-type]

    @property
    def name(self) -> str:
        return "ExampleAgent"

    def build_system_prompt(self, context: AgentContext) -> str:
        return (
            "You are an example agent plugin for NarrativeForge. "
            "This is a template showing how to implement a custom agent."
        )

    async def execute(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            content={
                "message": "Hello from ExampleAgent plugin!",
                "user_request": context.user_request,
                "project_genre": context.project.genre.value if context.project.genre else "unknown",
            },
            metadata={"plugin": "example-agent", "version": "1.0.0"},
        )
