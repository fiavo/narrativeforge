import json
from typing import Any

from NarrativeForge.Engine.ai_providers.base import CompletionOptions, Message
from NarrativeForge.Engine.models.story_bible import StoryBible

from .base import AgentContext, AgentResult, BaseAgent


class LoreCategory:
    HISTORY = "history"
    RELIGION = "religion"
    ECONOMY = "economy"
    CULTURE = "culture"
    CREATURE = "creature"
    ITEM = "item"
    GEOGRAPHY = "geography"
    POLITICS = "politics"


LORE_CATEGORY_INSTRUCTIONS: dict[str, str] = {
    LoreCategory.HISTORY: (
        "Create historical lore about past events, eras, wars, dynasties, or "
        "significant moments that shaped the world."
    ),
    LoreCategory.RELIGION: (
        "Create religious lore about deities, belief systems, creation myths, "
        "sacred rituals, or religious institutions."
    ),
    LoreCategory.ECONOMY: (
        "Create economic lore about trade routes, currencies, guilds, resources, "
        "markets, or economic systems."
    ),
    LoreCategory.CULTURE: (
        "Create cultural lore about customs, traditions, festivals, art forms, "
        "languages, or social practices."
    ),
    LoreCategory.CREATURE: (
        "Create creature lore about monsters, beasts, mythical animals, "
        "their habitats, behaviors, and significance."
    ),
    LoreCategory.ITEM: (
        "Create item lore about artifacts, weapons, tools, relics, "
        "their origins, powers, and history."
    ),
    LoreCategory.GEOGRAPHY: (
        "Create geographical lore about regions, landmarks, natural wonders, "
        "climates, or terrain features."
    ),
    LoreCategory.POLITICS: (
        "Create political lore about governments, laws, treaties, power struggles, "
        "or political movements."
    ),
}


class LoreAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "LoreAgent"

    def build_system_prompt(self, context: AgentContext) -> str:
        prompt_parts = [
            "You are a masterful world-builder and lore keeper for interactive "
            "fiction and games. Your task is to create rich, detailed world lore "
            "entries that deepen the setting and provide context for the story.",
        ]

        genre = context.project.genre
        prompt_parts.append(f"Genre: {genre.value}")

        if context.project.themes:
            prompt_parts.append(f"Themes: {', '.join(context.project.themes)}")

        if context.project.tone:
            prompt_parts.append(f"Tone: {context.project.tone}")

        prompt_parts.append("\nLore categories you can generate:")
        for category, instruction in LORE_CATEGORY_INSTRUCTIONS.items():
            prompt_parts.append(f"  - {category}: {instruction}")

        if context.story_bible:
            prompt_parts.append(self._summarize_story_bible(context.story_bible))

        prompt_parts.append(
            "\nAlways return your response as valid JSON matching this schema:\n"
            "{\n"
            '  "title": "string",\n'
            '  "category": "history|religion|economy|culture|creature|item|geography|politics",\n'
            '  "content": "string (detailed lore entry)",\n'
            '  "tags": ["string"],\n'
            '  "related_entries": ["string (titles of related lore entries)"]\n'
            "}\n"
            "Do not include any text outside the JSON."
        )

        return "\n".join(prompt_parts)

    def _build_user_prompt(self, context: AgentContext) -> str:
        prompt_parts = [f"User request: {context.user_request}"]

        existing_titles = self._get_existing_titles(context.story_bible)
        if existing_titles:
            prompt_parts.append(
                f"\nExisting lore entries to avoid duplicating:\n"
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
            temperature=0.7, max_tokens=4096
        )

        raw_response = await self._provider.complete(messages, options)
        content = self._parse_response(raw_response)

        changes: list[dict[str, Any]] = []
        if content.get("title") and content.get("content"):
            changes.append({
                "lore_entries": {
                    "new": [{
                        "title": content["title"],
                        "category": content.get("category", ""),
                        "content": content.get("content", ""),
                        "tags": content.get("tags", []),
                    }],
                    "updated": [],
                }
            })

        return AgentResult(
            agent_name=self.name,
            content=content,
            metadata={
                "category": content.get("category", ""),
                "has_title": bool(content.get("title")),
                "has_content": bool(content.get("content")),
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
                "category": "",
                "content": raw if isinstance(raw, str) else "",
                "tags": [],
                "related_entries": [],
                "error": "Failed to parse JSON response",
            }

    def _get_existing_titles(self, bible: StoryBible | None) -> list[str]:
        if not bible or not bible.lore_entries:
            return []
        return [entry.title for entry in bible.lore_entries.values()]

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

        existing_titles = self._get_existing_titles(bible)
        if existing_titles:
            parts.append(f"Existing lore entries: {', '.join(existing_titles)}")

        return "\n".join(parts)
