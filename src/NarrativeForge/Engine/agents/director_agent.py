import json
from enum import Enum

from NarrativeForge.Engine.ai_providers.base import CompletionOptions, Message

from .base import AgentContext, AgentResult, BaseAgent


class RequestType(str, Enum):
    GENERATE = "generate"
    EXPAND = "expand"
    REVISE = "revise"
    ANALYZE = "analyze"
    QUERY = "query"


DIRECTOR_SYSTEM_PROMPT = (
    "You are a narrative director for an AI-powered story generation system. "
    "Your job is to analyze user requests, classify their intent, and decompose "
    "them into structured sub-tasks for specialized agents.\n\n"
    "For each request, produce a JSON object with:\n"
    '- "request_type": one of "generate", "expand", "revise", "analyze", "query"\n'
    '- "sub_tasks": an array of objects with "agent" (one of "story", "consistency") '
    'and "instruction" fields\n'
    '- "summary": a one-line description of the plan\n'
    '- "context_notes": any relevant context to pass along\n\n'
    "Always return valid JSON with no surrounding text."
)


class DirectorAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "DirectorAgent"

    def build_system_prompt(self, context: AgentContext) -> str:
        parts = [DIRECTOR_SYSTEM_PROMPT]

        if context.project:
            parts.append(
                f"Current project: {context.project.name} "
                f"(genre: {context.project.genre.value})"
            )

        if context.story_bible:
            char_count = len(context.story_bible.characters)
            parts.append(f"Story bible has {char_count} character(s) defined.")

        if context.previous_results:
            agent_names = list(context.previous_results.keys())
            parts.append(f"Previous agent results from: {', '.join(agent_names)}")

        return "\n".join(parts)

    async def execute(self, context: AgentContext) -> AgentResult:
        system_prompt = self.build_system_prompt(context)
        messages = [
            Message.system(system_prompt),
            Message.user(context.user_request),
        ]

        options = context.generation_params or CompletionOptions(
            temperature=0.3, max_tokens=2048
        )

        raw_response = await self._provider.complete(messages, options)
        plan = self._parse_plan(raw_response)

        return AgentResult(
            agent_name=self.name,
            content=plan,
            metadata={
                "request_type": plan.get("request_type", "unknown"),
                "sub_task_count": len(plan.get("sub_tasks", [])),
            },
        )

    def _parse_plan(self, raw: str) -> dict:
        try:
            plan = json.loads(raw)
            if "request_type" not in plan:
                plan["request_type"] = RequestType.GENERATE.value
            if "sub_tasks" not in plan:
                plan["sub_tasks"] = []
            return plan
        except (json.JSONDecodeError, TypeError):
            return {
                "request_type": RequestType.GENERATE.value,
                "sub_tasks": [],
                "summary": raw,
                "context_notes": "",
            }
