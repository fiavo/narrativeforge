import json
from dataclasses import dataclass, field
from enum import Enum

from NarrativeForge.Engine.ai_providers.base import CompletionOptions, Message

from .base import AgentContext, AgentResult, BaseAgent


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ConsistencyIssue:
    severity: IssueSeverity
    category: str
    description: str
    suggestion: str = ""


@dataclass
class ConsistencyReport:
    score: float
    issues: list[ConsistencyIssue] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "category": issue.category,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                }
                for issue in self.issues
            ],
            "summary": self.summary,
        }


CHECKER_SYSTEM_PROMPT = (
    "You are a narrative consistency checker for an AI-powered story generation system. "
    "Your job is to validate generated content against the story bible and detect "
    "plot holes, character contradictions, timeline inconsistencies, and lore violations.\n\n"
    "Analyze the provided content and return a JSON object with:\n"
    '- "score": a float 0.0-1.0 (1.0 = perfectly consistent)\n'
    '- "issues": an array of objects with "severity" (critical/warning/info), '
    '"category" (plot/character/timeline/lore/setting), "description", and "suggestion"\n'
    '- "summary": a one-line overall assessment\n\n'
    "Always return valid JSON with no surrounding text."
)


class ConsistencyChecker(BaseAgent):
    @property
    def name(self) -> str:
        return "ConsistencyChecker"

    def build_system_prompt(self, context: AgentContext) -> str:
        parts = [CHECKER_SYSTEM_PROMPT]

        if context.story_bible:
            parts.append(self._build_bible_context(context))

        if context.locked_elements:
            parts.append(
                f"Locked elements (must NOT be changed): "
                f"{len(context.locked_elements)} element(s)."
            )

        return "\n".join(parts)

    async def execute(self, context: AgentContext) -> AgentResult:
        system_prompt = self.build_system_prompt(context)

        content_to_check = self._extract_content_to_check(context)

        messages = [
            Message.system(system_prompt),
            Message.user(
                f"Validate the following content for consistency:\n\n{content_to_check}"
            ),
        ]

        options = context.generation_params or CompletionOptions(
            temperature=0.2, max_tokens=2048
        )

        raw_response = await self._provider.complete(messages, options)
        report = self._parse_report(raw_response)

        return AgentResult(
            agent_name=self.name,
            content=report.to_dict(),
            metadata={
                "score": report.score,
                "issue_count": len(report.issues),
                "critical_count": sum(
                    1 for i in report.issues if i.severity == IssueSeverity.CRITICAL
                ),
            },
        )

    def _extract_content_to_check(self, context: AgentContext) -> str:
        if "content" in context.previous_results:
            result = context.previous_results["content"]
            if isinstance(result, dict):
                return json.dumps(result, indent=2)
            return str(result)

        return context.user_request

    def _build_bible_context(self, context: AgentContext) -> str:
        bible = context.story_bible
        parts = ["Story Bible constraints:"]

        if bible.characters:
            for char in bible.characters.values():
                parts.append(
                    f"  Character: {char.name} (role: {char.role.value}) "
                    f"- motivation: {char.motivation or 'none'}"
                )

        if bible.locations:
            for loc in bible.locations.values():
                parts.append(f"  Location: {loc.name} - {loc.description[:100] or 'no desc'}")

        if bible.timeline:
            for event in bible.timeline:
                parts.append(f"  Timeline: {event.title} (order: {event.order})")

        if bible.locked_elements:
            parts.append(f"  Locked elements: {len(bible.locked_elements)} (must not change)")

        return "\n".join(parts)

    def _parse_report(self, raw: str) -> ConsistencyReport:
        try:
            data = json.loads(raw)
            issues = [
                ConsistencyIssue(
                    severity=IssueSeverity(issue.get("severity", "info")),
                    category=issue.get("category", "unknown"),
                    description=issue.get("description", ""),
                    suggestion=issue.get("suggestion", ""),
                )
                for issue in data.get("issues", [])
            ]
            return ConsistencyReport(
                score=float(data.get("score", 1.0)),
                issues=issues,
                summary=data.get("summary", ""),
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            return ConsistencyReport(
                score=0.0,
                summary="Failed to parse consistency check response",
            )
