import json

from NarrativeForge.Engine.ai_providers.base import CompletionOptions, Message
from NarrativeForge.Engine.models.project import GameGenre

from .base import AgentContext, AgentResult, BaseAgent

GENRE_QUEST_HINTS: dict[GameGenre, str] = {
    GameGenre.Horror: "Survival, escape, investigation of dark mysteries.",
    GameGenre.Romance: "Relationship-building, trust tests, shared vulnerability.",
    GameGenre.Comedy: "Misunderstandings, absurd fetch tasks, escalating chaos.",
    GameGenre.SciFi: "Exploration, tech heists, diplomatic crises.",
    GameGenre.Fantasy: "Heroic journeys, dungeon crawls, political intrigue.",
    GameGenre.Cyberpunk: "Corporate espionage, data heists, street-level survival.",
    GameGenre.Detective: "Clue gathering, witness interviews, solving cases.",
    GameGenre.Noir: "Moral dilemmas, backroom deals, unraveling conspiracies.",
    GameGenre.Military: "Tactical objectives, squad coordination, sabotage.",
    GameGenre.PostApocalypse: "Scavenging, escort, fortification, trade routes.",
    GameGenre.DarkFantasy: "Cursed artifacts, morally grey choices, impossible odds.",
    GameGenre.Lovecraftian: "Investigation of the unknowable, sanity tests, ritual prevention.",
    GameGenre.Thriller: "Race against time, stealth, disarming threats.",
    GameGenre.Mystery: "Evidence collection, interrogations, reconstructing events.",
    GameGenre.Steampunk: "Engineering challenges, factory infiltration, invention quests.",
    GameGenre.Historical: "Diplomatic missions, battles, espionage in period settings.",
    GameGenre.Mythology: "Divine trials, artifact recovery, prophecy fulfillment.",
    GameGenre.Superhero: "Villain thwarting, rescue missions, identity protection.",
    GameGenre.Crime: "Undercover operations, evidence planting, heist planning.",
    GameGenre.School: "Social quests, club activities, academic challenges.",
    GameGenre.Anime: "Tournament arcs, training montages, friendship tests.",
    GameGenre.Vampire: "Blood hunts, political maneuvering, clan loyalty.",
    GameGenre.Werewolf: "Territory defense, pack hunts, moon-cycle crises.",
    GameGenre.RPG: "Choice-driven branches, faction reputation, skill checks.",
    GameGenre.JRPG: "Party recruitment, elemental trials, boss encounters.",
    GameGenre.OpenWorld: "Exploration discovery, side quests, faction warfare.",
    GameGenre.Survival: "Resource gathering, base building, predator avoidance.",
    GameGenre.Psychological: "Reality-bending puzzles, trust tests, identity quests.",
    GameGenre.Medieval: "Feudal duties, jousts, siege preparation.",
}


class QuestAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "QuestAgent"

    def build_system_prompt(self, context: AgentContext) -> str:
        genre = context.project.genre
        quest_hint = GENRE_QUEST_HINTS.get(genre, "Adapt quest design to fit the genre.")
        prompt_parts = [
            "You are a masterful quest designer for interactive fiction and games.",
            f"Genre: {genre.value}",
            f"Genre quest conventions: {quest_hint}",
        ]

        if context.project.themes:
            prompt_parts.append(f"Themes: {', '.join(context.project.themes)}")

        if context.project.tone:
            prompt_parts.append(f"Additional tone notes: {context.project.tone}")

        if context.story_bible:
            prompt_parts.append(self._summarize_story_bible(context))

        prompt_parts.append(
            "Always return your response as valid JSON matching this schema:\n"
            "{\n"
            '  "name": "string",\n'
            '  "description": "string",\n'
            '  "is_main_quest": boolean,\n'
            '  "objectives": [{"description": "string", "type": "kill|collect|explore|escort|talk|solve", "target": "string", "quantity": 1, "is_required": true}],\n'
            '  "prerequisites": [{"quest_id": "uuid-string", "relationship": "string"}],\n'
            '  "rewards": {"xp": 0, "gold": 0, "items": [], "reputation": 0}\n'
            "}\n"
            "Do not include any text outside the JSON."
        )

        return "\n".join(prompt_parts)

    async def execute(self, context: AgentContext) -> AgentResult:
        system_prompt = self.build_system_prompt(context)
        messages = [
            Message.system(system_prompt),
            Message.user(context.user_request),
        ]

        options = context.generation_params or CompletionOptions(
            temperature=0.6, max_tokens=4096
        )

        raw_response = await self._provider.complete(messages, options)
        content = self._parse_response(raw_response)

        return AgentResult(
            agent_name=self.name,
            content=content,
            metadata={
                "genre": context.project.genre.value,
                "has_objectives": bool(content.get("objectives")),
                "has_rewards": bool(content.get("rewards")),
                "is_main_quest": content.get("is_main_quest", False),
            },
        )

    def _parse_response(self, raw: str) -> dict:
        try:
            data = json.loads(raw)
            return data
        except (json.JSONDecodeError, TypeError):
            return {
                "name": "Unnamed Quest",
                "description": raw if isinstance(raw, str) else "",
                "objectives": [],
                "prerequisites": [],
                "rewards": {"xp": 0, "gold": 0, "items": [], "reputation": 0},
                "is_main_quest": False,
                "error": "Failed to parse JSON response",
            }

    def _summarize_story_bible(self, context: AgentContext) -> str:
        bible = context.story_bible
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

        return "\n".join(parts)
