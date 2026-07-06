import json
from enum import Enum
from typing import Any

from NarrativeForge.Engine.ai_providers.base import CompletionOptions, Message
from NarrativeForge.Engine.models.project import GameGenre
from NarrativeForge.Engine.models.story_bible import StoryBible

from .base import AgentContext, AgentResult, BaseAgent


class DialogueType(str, Enum):
    CONVERSATION = "conversation"
    MONOLOGUE = "monologue"
    CONFRONTATION = "confrontation"
    NEGOTIATION = "negotiation"
    EXPOSITION = "exposition"


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
    GameGenre.Zombie: "Desperate, survival horror, with decaying civilization.",
}

DIALOGUE_TYPE_INSTRUCTIONS: dict[DialogueType, str] = {
    DialogueType.CONVERSATION: (
        "Write a natural back-and-forth conversation between characters. "
        "Each line should feel organic, with characters responding to each other's points."
    ),
    DialogueType.MONOLOGUE: (
        "Write a monologue delivered by a single character. "
        "This should reveal inner thoughts, motivations, or key information."
    ),
    DialogueType.CONFRONTATION: (
        "Write a tense confrontation between characters. "
        "Include escalating conflict, strong emotions, and dramatic tension."
    ),
    DialogueType.NEGOTIATION: (
        "Write a negotiation dialogue where characters are bargaining or trying to reach agreement. "
        "Show tactics, concessions, and shifting power dynamics."
    ),
    DialogueType.EXPOSITION: (
        "Write exposition-heavy dialogue where a character explains lore, backstory, or world details. "
        "Keep it natural and avoid info-dumping."
    ),
}

SYSTEM_PROMPT_BASE = (
    "You are a masterful dialogue writer for interactive fiction and games. "
    "Your dialogue should feel authentic to each character's voice, "
    "capture emotional subtext, and advance the narrative.\n\n"
    "Always return your response as valid JSON with the following structure:\n"
    '{\n'
    '  "dialogue_type": "<type>",\n'
    '  "exchanges": [\n'
    '    {\n'
    '      "speaker": "<character name>",\n'
    '      "line": "<dialogue line>",\n'
    '      "emotion": "<optional emotion>",\n'
    '      "action": "<optional stage direction>"\n'
    '    }\n'
    '  ],\n'
    '  "narrative_context": "<optional brief context setting>"\n'
    '}\n\n'
    "Do not include any text outside the JSON."
)


class DialogueAgent(BaseAgent):
    def __init__(self, provider: Any) -> None:
        super().__init__(provider)

    @property
    def name(self) -> str:
        return "DialogueAgent"

    def build_system_prompt(self, context: AgentContext) -> str:
        prompt_parts = [SYSTEM_PROMPT_BASE]

        genre = context.project.genre
        tone_hint = GENRE_TONE_HINTS.get(genre, "Adapt the tone to fit the genre.")
        prompt_parts.append(f"Genre: {genre.value}")
        prompt_parts.append(f"Tone guidance: {tone_hint}")

        if context.project.tone:
            prompt_parts.append(f"Additional tone notes: {context.project.tone}")

        if context.story_bible:
            prompt_parts.append(self._summarize_characters(context.story_bible))

        dialogue_type = self._classify_dialogue_type(context.user_request)
        prompt_parts.append(f"\nDialogue type: {dialogue_type.value}")
        prompt_parts.append(DIALOGUE_TYPE_INSTRUCTIONS[dialogue_type])

        return "\n".join(prompt_parts)

    async def execute(self, context: AgentContext) -> AgentResult:
        format_param = context.previous_results.get("format", "structured")

        system_prompt = self.build_system_prompt(context)
        user_prompt = self._build_user_prompt(context, format_param)

        messages = [
            Message.system(system_prompt),
            Message.user(user_prompt),
        ]

        options = context.generation_params or CompletionOptions(
            temperature=0.75, max_tokens=4096
        )

        raw_response = await self._provider.complete(messages, options)
        content = self._parse_response(raw_response)

        return AgentResult(
            agent_name=self.name,
            content=content,
            metadata={
                "dialogue_type": content.get("dialogue_type", "conversation"),
                "exchange_count": len(content.get("exchanges", [])),
                "format": format_param,
            },
        )

    def _build_user_prompt(self, context: AgentContext, format_param: str) -> str:
        prompt_parts = [f"User request: {context.user_request}"]

        if format_param == "formatted":
            prompt_parts.append(
                "Format: Return the dialogue in a readable script format with "
                "character names in brackets and stage directions in parentheses."
            )
        else:
            prompt_parts.append("Format: Return structured JSON as specified.")

        if context.previous_results:
            relevant = {k: v for k, v in context.previous_results.items() if k != "format"}
            if relevant:
                prompt_parts.append(f"Additional context from previous steps: {json.dumps(relevant)}")

        return "\n".join(prompt_parts)

    def _classify_dialogue_type(self, request: str) -> DialogueType:
        lower = request.lower()
        if "monologue" in lower or "speech" in lower:
            return DialogueType.MONOLOGUE
        if "confront" in lower or "argue" in lower or "fight" in lower or "battle" in lower:
            return DialogueType.CONFRONTATION
        if "negoti" in lower or "bargain" in lower or "deal" in lower or "trade" in lower:
            return DialogueType.NEGOTIATION
        if "explain" in lower or "lore" in lower or "tell me" in lower or "history" in lower:
            return DialogueType.EXPOSITION
        return DialogueType.CONVERSATION

    def _parse_response(self, raw: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw)
            if "dialogue_type" not in parsed:
                parsed["dialogue_type"] = DialogueType.CONVERSATION.value
            if "exchanges" not in parsed:
                parsed["exchanges"] = []
            return parsed
        except (json.JSONDecodeError, TypeError):
            return {
                "dialogue_type": DialogueType.CONVERSATION.value,
                "exchanges": [],
                "narrative_context": "",
                "raw": raw,
                "error": "Failed to parse response",
            }

    def _summarize_characters(self, bible: StoryBible) -> str:
        if not bible.characters:
            return ""

        parts = ["\nAvailable characters from Story Bible:"]
        for char in bible.characters.values():
            char_info = f"  - {char.name} ({char.role.value})"
            if char.personality and char.personality.traits:
                char_info += f": traits={', '.join(char.personality.traits)}"
            if char.dialogue_style:
                char_info += f", dialogue_style={char.dialogue_style}"
            if char.backstory:
                char_info += f", backstory={char.backstory[:100]}"
            if char.motivation:
                char_info += f", motivation={char.motivation}"
            parts.append(char_info)

        return "\n".join(parts)
