import json
from dataclasses import dataclass, field
from typing import Any

from NarrativeForge.Engine.ai_providers.base import CompletionOptions, Message

from .base import AgentContext, AgentResult, BaseAgent


CRITERIA = [
    "coherence",
    "character_depth",
    "pacing",
    "dialogue_quality",
    "creativity",
    "emotional_impact",
]


CRITIC_SYSTEM_PROMPT = (
    "You are a narrative quality critic for an AI-powered story generation system. "
    "Your job is to evaluate the quality of generated narrative content.\n\n"
    "Score the content on these 6 criteria, each on a scale of 0.0 to 1.0:\n"
    "  - coherence: How logically consistent and well-structured the narrative is\n"
    "  - character_depth: How well-developed, believable, and distinct the characters are\n"
    "  - pacing: How well the narrative flow and timing work\n"
    "  - dialogue_quality: How natural, purposeful, and character-appropriate the dialogue is\n"
    "  - creativity: How original, surprising, and inventive the content is\n"
    "  - emotional_impact: How effectively the narrative evokes emotional response\n\n"
    "Return a JSON object with:\n"
    '- "overall_score": a float 0.0-1.0 (weighted average of all criteria)\n'
    '- "scores": an object with each criterion and its score\n'
    '- "summary": a brief overall assessment\n'
    '- "strengths": an array of strengths identified\n'
    '- "weaknesses": an array of areas for improvement\n\n'
    "Always return valid JSON with no surrounding text."
)


@dataclass
class CriticReport:
    overall_score: float
    scores: dict[str, float] = field(default_factory=dict)
    summary: str = ""
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "scores": self.scores,
            "summary": self.summary,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }


class CriticAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "CriticAgent"

    def build_system_prompt(self, context: AgentContext) -> str:
        parts = [CRITIC_SYSTEM_PROMPT]

        genre = context.project.genre
        parts.append(f"\nGenre: {genre.value}")

        if context.project.themes:
            parts.append(f"Themes: {', '.join(context.project.themes)}")

        if context.project.tone:
            parts.append(f"Tone: {context.project.tone}")

        return "\n".join(parts)

    async def execute(self, context: AgentContext) -> AgentResult:
        system_prompt = self.build_system_prompt(context)

        content_to_evaluate = self._extract_content(context)

        messages = [
            Message.system(system_prompt),
            Message.user(
                f"Evaluate the following narrative content for quality:\n\n{content_to_evaluate}"
            ),
        ]

        options = context.generation_params or CompletionOptions(
            temperature=0.3, max_tokens=2048
        )

        raw_response = await self._provider.complete(messages, options)
        report = self._parse_report(raw_response)

        return AgentResult(
            agent_name=self.name,
            content=report.to_dict(),
            metadata={
                "overall_score": report.overall_score,
                "criterion_count": len(report.scores),
                "genre": context.project.genre.value,
            },
            changes=[],
        )

    def _extract_content(self, context: AgentContext) -> str:
        if "content" in context.previous_results:
            result = context.previous_results["content"]
            if isinstance(result, dict):
                return json.dumps(result, indent=2)
            return str(result)

        return context.user_request

    def _parse_report(self, raw: str) -> CriticReport:
        try:
            data = json.loads(raw)
            scores = {}
            for criterion in CRITERIA:
                scores[criterion] = float(data.get("scores", {}).get(criterion, 0.0))

            return CriticReport(
                overall_score=float(data.get("overall_score", 0.0)),
                scores=scores,
                summary=data.get("summary", ""),
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            return CriticReport(
                overall_score=0.0,
                summary="Failed to parse critic response",
            )
