import json
from typing import Any

from NarrativeForge.Engine.ai_providers.base import CompletionOptions, Message
from NarrativeForge.Engine.models.story_bible import StoryBible

from .base import AgentContext, AgentResult, BaseAgent


class TimelineAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "TimelineAgent"

    def build_system_prompt(self, context: AgentContext) -> str:
        prompt_parts = [
            "You are a meticulous chronologist and historian for interactive "
            "fiction and games. Your task is to generate chronologies, historical "
            "events, and timeline entries that fit coherently within the world.",
        ]

        genre = context.project.genre
        prompt_parts.append(f"Genre: {genre.value}")

        if context.project.themes:
            prompt_parts.append(f"Themes: {', '.join(context.project.themes)}")

        if context.project.tone:
            prompt_parts.append(f"Tone: {context.project.tone}")

        if context.story_bible:
            prompt_parts.append(self._summarize_story_bible(context.story_bible))

        prompt_parts.append(
            "\nAlways return your response as valid JSON matching this schema:\n"
            "{\n"
            '  "title": "string",\n'
            '  "timestamp": "string (e.g. year, era, or relative date)",\n'
            '  "description": "string (detailed description of the event)",\n'
            '  "participants": ["string (names of involved characters/factions)"],\n'
            '  "location": "string (name of location where event occurs)",\n'
            '  "consequences": ["string (outcomes or impacts of this event)"]\n'
            "}\n"
            "Do not include any text outside the JSON."
        )

        return "\n".join(prompt_parts)

    def _build_user_prompt(self, context: AgentContext) -> str:
        prompt_parts = [f"User request: {context.user_request}"]

        existing_titles = self._get_existing_event_titles(context.story_bible)
        if existing_titles:
            prompt_parts.append(
                f"\nExisting timeline events to avoid duplicating:\n"
                f"{chr(10).join(f'  - {t}' for t in existing_titles)}"
            )

        if context.previous_results:
            relevant = {
                k: v for k, v in context.previous_results.items()
                if k not in ("format",)
            }
            if relevant:
                prompt_parts.append(
                    f"\nAdditional context from previous steps:\n{json.dumps(relevant, indent=2)}"
                )

        return "\n".join(prompt_parts)

    async def execute(self, context: AgentContext) -> AgentResult:
        system_prompt = self.build_system_prompt(context)
        user_prompt = self._build_user_prompt(context)

        messages = [
            Message.system(system_prompt),
            Message.user(user_prompt),
        ]

        options = context.generation_params or CompletionOptions(
            temperature=0.6, max_tokens=4096
        )

        raw_response = await self._provider.complete(messages, options)
        content = self._parse_response(raw_response)

        changes: list[dict[str, Any]] = []
        if content.get("title") and content.get("description"):
            changes.append({
                "timeline": {
                    "new": [{
                        "title": content["title"],
                        "timestamp": content.get("timestamp", ""),
                        "description": content.get("description", ""),
                        "participants": content.get("participants", []),
                        "location": content.get("location", ""),
                        "consequences": content.get("consequences", []),
                    }],
                    "updated": [],
                }
            })

        return AgentResult(
            agent_name=self.name,
            content=content,
            metadata={
                "has_title": bool(content.get("title")),
                "has_description": bool(content.get("description")),
                "genre": context.project.genre.value,
            },
            changes=changes,
        )

    def _parse_response(self, raw: str) -> dict[str, Any]:
        try:
            data = json.loads(raw)
            return data
        except (json.JSONDecodeError, TypeError):
            return {
                "title": "",
                "timestamp": "",
                "description": raw if isinstance(raw, str) else "",
                "participants": [],
                "location": "",
                "consequences": [],
                "error": "Failed to parse JSON response",
            }

    def _get_existing_event_titles(self, bible: StoryBible | None) -> list[str]:
        if not bible or not bible.timeline:
            return []
        return [event.title for event in bible.timeline]

    def _summarize_story_bible(self, bible: StoryBible) -> str:
        parts = ["Story Bible summary:"]

        if bible.characters:
            char_entries = [
                f"{c.name} ({c.role.value})" for c in bible.characters.values()
            ]
            parts.append(f"Characters: {', '.join(char_entries)}")

        if bible.locations:
            loc_entries = [
                f"{loc.name} ({loc.type})" if loc.type else loc.name
                for loc in bible.locations.values()
            ]
            parts.append(f"Locations: {', '.join(loc_entries)}")

        if bible.factions:
            faction_entries = [
                f"{f.name}: {f.description}" if f.description else f.name
                for f in bible.factions.values()
            ]
            parts.append(f"Factions: {', '.join(faction_entries)}")

        if bible.timeline:
            event_entries = [e.title for e in bible.timeline]
            parts.append(f"Timeline events: {', '.join(event_entries)}")

        existing_titles = self._get_existing_event_titles(bible)
        if existing_titles:
            parts.append(f"Existing timeline entries: {', '.join(existing_titles)}")

        return "\n".join(parts)
