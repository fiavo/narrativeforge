import json
from typing import Any

from NarrativeForge.Engine.ai_providers.base import CompletionOptions, Message
from NarrativeForge.Engine.models.project import GameGenre

from .base import AgentContext, AgentResult, BaseAgent

GENRE_TONE_HINTS: dict[GameGenre, str] = {
    GameGenre.Horror: "Tense, atmospheric, with dread building steadily.",
    GameGenre.Romance: "Warm, emotionally intimate, with romantic tension.",
    GameGenre.Comedy: "Light-hearted, witty, with humorous misunderstandings.",
    GameGenre.SciFi: "Technically grounded, speculative, with a sense of wonder.",
    GameGenre.Fantasy: "Epic, mythic, with rich world-building details.",
    GameGenre.Cyberpunk: "Gritty, neon-lit, with corporate dystopia undertones.",
    GameGenre.Detective: "Suspenseful, analytical, with clues woven throughout.",
    GameGenre.Noir: "Hard-boiled, cynical, with morally grey characters.",
    GameGenre.Military: "Disciplined, tactical, with camaraderie under fire.",
    GameGenre.PostApocalypse: "Desolate, survival-focused, with flickers of hope.",
    GameGenre.DarkFantasy: "Grim, morally complex, with corrupt power.",
    GameGenre.Lovecraftian: "Cosmic dread, sanity-fraying, with the unknowable.",
    GameGenre.Thriller: "Fast-paced, high-stakes, with constant tension.",
    GameGenre.Mystery: "Puzzling, layered, with revelations at each turn.",
    GameGenre.Steampunk: "Victorian-industrial, inventive, with brass-and-steam aesthetics.",
    GameGenre.Historical: "Grounded in real events, period-accurate, with cultural texture.",
    GameGenre.Mythology: "Legendary, archetypal, with divine forces at play.",
    GameGenre.Superhero: "Larger-than-life, with secret identities and moral dilemmas.",
    GameGenre.Crime: "Underworld-focused, with schemes and betrayals.",
    GameGenre.School: "Youthful, campus dynamics, with coming-of-age themes.",
    GameGenre.Anime: "Expressive, dramatic, with trope-aware storytelling.",
    GameGenre.Vampire: "Gothic, seductive, with immortality's curse.",
    GameGenre.Werewolf: "Feral, primal, with the beast within.",
    GameGenre.RPG: "Choice-driven, branching, with player agency themes.",
    GameGenre.JRPG: "Character-driven, emotional, with ensemble casts.",
    GameGenre.OpenWorld: "Exploratory, sandbox-like, with emergent stories.",
    GameGenre.Survival: "Resource-scarce, desperate, with every choice mattering.",
    GameGenre.Psychological: "Introspective, unreliable, with minds unraveling.",
    GameGenre.Medieval: "Feudal, chivalric, with political intrigue.",
}

TASK_PROMPTS: dict[str, str] = {
    "story_beat": (
        "Generate a sequence of story beats (key plot points) for a narrative segment. "
        "Return a JSON array of objects with 'title' and 'description' fields."
    ),
    "chapter": (
        "Write a full chapter of narrative prose. "
        "Include scene descriptions, character actions, and dialogue. "
        "Return a JSON object with 'title' and 'content' fields."
    ),
    "dialogue": (
        "Write a dialogue exchange between characters. "
        "Return a JSON array of objects with 'speaker' and 'line' fields."
    ),
}


class StoryAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "StoryAgent"

    def build_system_prompt(self, context: AgentContext) -> str:
        genre = context.project.genre
        tone_hint = GENRE_TONE_HINTS.get(genre, "Adapt the tone to fit the genre.")
        prompt_parts = [
            "You are a masterful narrative writer for interactive fiction and games.",
            f"Genre: {genre.value}",
            f"Tone guidance: {tone_hint}",
        ]

        if context.project.themes:
            prompt_parts.append(f"Themes: {', '.join(context.project.themes)}")

        if context.project.tone:
            prompt_parts.append(f"Additional tone notes: {context.project.tone}")

        if context.story_bible:
            prompt_parts.append(self._summarize_story_bible(context))

        prompt_parts.append(
            "Always return your response as valid JSON. "
            "Do not include any text outside the JSON."
        )

        return "\n".join(prompt_parts)

    async def execute(self, context: AgentContext) -> AgentResult:
        task_type = self._detect_task_type(context.user_request)
        task_prompt = TASK_PROMPTS.get(task_type, TASK_PROMPTS["story_beat"])

        system_prompt = self.build_system_prompt(context)
        messages = [
            Message.system(system_prompt),
            Message.user(f"{task_prompt}\n\nUser request: {context.user_request}"),
        ]

        options = context.generation_params or CompletionOptions(
            temperature=0.8, max_tokens=4096
        )

        raw_response = await self._provider.complete(messages, options)
        content = self._parse_response(raw_response, task_type)

        return AgentResult(
            agent_name=self.name,
            content=content,
            metadata={"task_type": task_type, "genre": context.project.genre.value},
        )

    def _detect_task_type(self, request: str) -> str:
        lower = request.lower()
        if "dialogue" in lower or "dialog" in lower:
            return "dialogue"
        if "chapter" in lower or "scene" in lower or "prose" in lower:
            return "chapter"
        return "story_beat"

    def _parse_response(self, raw: str, task_type: str) -> Any:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {"raw": raw, "task_type": task_type}

    def _summarize_story_bible(self, context: AgentContext) -> str:
        bible = context.story_bible
        parts = ["Story Bible summary:"]

        if bible.characters:
            char_names = [c.name for c in bible.characters.values()]
            parts.append(f"Characters: {', '.join(char_names)}")

        if bible.locations:
            loc_names = [loc.name for loc in bible.locations.values()]
            parts.append(f"Locations: {', '.join(loc_names)}")

        if bible.factions:
            faction_names = [f.name for f in bible.factions.values()]
            parts.append(f"Factions: {', '.join(faction_names)}")

        if bible.lore_entries:
            lore_titles = [e.title for e in bible.lore_entries.values()]
            parts.append(f"Lore entries: {', '.join(lore_titles)}")

        if bible.timeline:
            event_titles = [e.title for e in bible.timeline]
            parts.append(f"Timeline events: {', '.join(event_titles)}")

        return "\n".join(parts)
