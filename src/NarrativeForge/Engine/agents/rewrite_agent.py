import json
from enum import Enum
from typing import Any

from NarrativeForge.Engine.ai_providers.base import CompletionOptions, Message

from .base import AgentContext, AgentResult, BaseAgent


class RewriteMode(str, Enum):
    POLISH = "polish"
    STYLE_TRANSFER = "style_transfer"


STYLE_TARGETS = {
    "formal": "Rewrite in a formal, professional tone with precise vocabulary and structured sentences.",
    "informal": "Rewrite in a casual, conversational tone with relaxed language and contractions.",
    "poetic": "Rewrite in a poetic, lyrical style with vivid imagery, rhythm, and figurative language.",
}

MODE_TEMPERATURE: dict[RewriteMode, float] = {
    RewriteMode.POLISH: 0.7,
    RewriteMode.STYLE_TRANSFER: 0.8,
}

SYSTEM_PROMPT_TEMPLATE = (
    "You are an expert text rewriter for interactive fiction and games.\n"
    "{mode_instructions}\n\n"
    "Always return your response as valid JSON with the following structure:\n"
    '{{\n'
    '  "rewritten_text": "<the rewritten text>",\n'
    '  "mode": "<polish or style_transfer>",\n'
    '  "changes_summary": "<brief summary of what was changed>"\n'
    '}}\n\n'
    "Do not include any text outside the JSON."
)


class RewriteAgent(BaseAgent):
    def __init__(self, provider: Any) -> None:
        super().__init__(provider)

    @property
    def name(self) -> str:
        return "RewriteAgent"

    def build_system_prompt(self, context: AgentContext) -> str:
        mode = self._classify_mode(context)
        mode_instructions = self._get_mode_instructions(mode, context)
        return SYSTEM_PROMPT_TEMPLATE.format(mode_instructions=mode_instructions)

    async def execute(self, context: AgentContext) -> AgentResult:
        mode = self._classify_mode(context)
        temperature = MODE_TEMPERATURE[mode]

        system_prompt = self.build_system_prompt(context)
        user_prompt = self._build_user_prompt(context, mode)

        messages = [
            Message.system(system_prompt),
            Message.user(user_prompt),
        ]

        options = context.generation_params or CompletionOptions(
            temperature=temperature, max_tokens=4096
        )
        options.temperature = temperature

        raw_response = await self._provider.complete(messages, options)
        content = self._parse_response(raw_response)

        return AgentResult(
            agent_name=self.name,
            content=content,
            metadata={
                "mode": mode.value,
                "temperature": temperature,
                "changes_summary": content.get("changes_summary", ""),
            },
            changes=[],
        )

    def _classify_mode(self, context: AgentContext) -> RewriteMode:
        request_lower = context.user_request.lower()
        for keyword in ("formal", "informal", "poetic", "style", "tone", "convert", "transform"):
            if keyword in request_lower:
                return RewriteMode.STYLE_TRANSFER
        return RewriteMode.POLISH

    def _get_mode_instructions(self, mode: RewriteMode, context: AgentContext) -> str:
        if mode == RewriteMode.POLISH:
            return (
                "Polish the provided text: fix grammar, improve flow, "
                "enhance descriptions, and tighten prose while preserving "
                "the original meaning and voice."
            )

        style_target = "formal"
        request_lower = context.user_request.lower()
        for target in STYLE_TARGETS:
            if target in request_lower:
                style_target = target
                break

        return STYLE_TARGETS[style_target]

    def _build_user_prompt(self, context: AgentContext, mode: RewriteMode) -> str:
        parts = [f"Mode: {mode.value}"]
        parts.append(f"Text to rewrite:\n{context.user_request}")

        if context.previous_results:
            original = context.previous_results.get("original_text", "")
            if original:
                parts.append(f"Original text:\n{original}")

        return "\n".join(parts)

    def _parse_response(self, raw: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw)
            return {
                "rewritten_text": parsed.get("rewritten_text", ""),
                "mode": parsed.get("mode", "polish"),
                "changes_summary": parsed.get("changes_summary", ""),
            }
        except (json.JSONDecodeError, TypeError):
            return {
                "rewritten_text": raw if isinstance(raw, str) else "",
                "mode": "polish",
                "changes_summary": "",
                "error": "Failed to parse response",
            }
