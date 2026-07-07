import json
from typing import Any

from NarrativeForge.Engine.ai_providers.base import CompletionOptions, Message
from NarrativeForge.Engine.models.story_bible import StoryBible

from .base import AgentContext, AgentResult, BaseAgent


class WorldAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "WorldAgent"

    def build_system_prompt(self, context: AgentContext) -> str:
        prompt_parts = [
            "You are a masterful world-builder for interactive fiction and games. "
            "Your task is to generate a comprehensive world setting including "
            "geography, cultures, religions, economies, and political systems.",
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
            '  "locations": [\n'
            "    {\n"
            '      "name": "string",\n'
            '      "type": "city|region|landmark|wilderness|dungeon|other",\n'
            '      "description": "string",\n'
            '      "significance": "string"\n'
            "    }\n"
            "  ],\n"
            '  "factions": [\n'
            "    {\n"
            '      "name": "string",\n'
            '      "description": "string",\n'
            '      "goals": ["string"],\n'
            '      "allies": ["string (faction names)"],\n'
            '      "enemies": ["string (faction names)"]\n'
            "    }\n"
            "  ],\n"
            '  "lore_entries": [\n'
            "    {\n"
            '      "title": "string",\n'
            '      "category": "culture|religion|economy|politics|geography",\n'
            '      "content": "string (detailed description)",\n'
            '      "tags": ["string"]\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Do not include any text outside the JSON."
        )

        return "\n".join(prompt_parts)

    def _build_user_prompt(self, context: AgentContext) -> str:
        prompt_parts = [f"User request: {context.user_request}"]

        existing_names = self._get_existing_names(context.story_bible)
        if existing_names:
            prompt_parts.append(
                f"\nExisting world elements to avoid duplicating:\n"
                f"{chr(10).join(f'  - {n}' for n in existing_names)}"
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
            temperature=0.7, max_tokens=4096
        )

        raw_response = await self._provider.complete(messages, options)
        content = self._parse_response(raw_response)

        changes: list[dict[str, Any]] = []
        if content.get("locations") or content.get("factions") or content.get("lore_entries"):
            changes.append({
                "locations": {
                    "new": [
                        {
                            "name": loc.get("name", ""),
                            "type": loc.get("type", ""),
                            "description": loc.get("description", ""),
                            "significance": loc.get("significance", ""),
                        }
                        for loc in content.get("locations", [])
                    ],
                    "updated": [],
                },
                "factions": {
                    "new": [
                        {
                            "name": f.get("name", ""),
                            "description": f.get("description", ""),
                            "goals": f.get("goals", []),
                            "allies": f.get("allies", []),
                            "enemies": f.get("enemies", []),
                        }
                        for f in content.get("factions", [])
                    ],
                    "updated": [],
                },
                "lore_entries": {
                    "new": [
                        {
                            "title": e.get("title", ""),
                            "category": e.get("category", ""),
                            "content": e.get("content", ""),
                            "tags": e.get("tags", []),
                        }
                        for e in content.get("lore_entries", [])
                    ],
                    "updated": [],
                },
            })

        return AgentResult(
            agent_name=self.name,
            content=content,
            metadata={
                "location_count": len(content.get("locations", [])),
                "faction_count": len(content.get("factions", [])),
                "lore_entry_count": len(content.get("lore_entries", [])),
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
                "locations": [],
                "factions": [],
                "lore_entries": [],
                "error": "Failed to parse JSON response",
                "raw": raw if isinstance(raw, str) else "",
            }

    def _get_existing_names(self, bible: StoryBible | None) -> list[str]:
        if not bible:
            return []
        names: list[str] = []
        for loc in (bible.locations or {}).values():
            names.append(loc.name)
        for faction in (bible.factions or {}).values():
            names.append(faction.name)
        for entry in (bible.lore_entries or {}).values():
            names.append(entry.title)
        return names

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

        existing_names = self._get_existing_names(bible)
        if existing_names:
            parts.append(f"Existing elements: {', '.join(existing_names)}")

        return "\n".join(parts)
