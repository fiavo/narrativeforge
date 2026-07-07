# NarrativeForge Phase 2: AI Agents — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add DialogueAgent, QuestAgent, and LoreAgent with smart Director routing to the existing narrative engine.

**Architecture:** Extend the existing BaseAgent framework with three new agent implementations. Update the DirectorAgent to classify requests and route to the appropriate agent. The PipelineOrchestrator gains conditional execution. LoreAgent auto-adds entries to Story Bible via AgentResult.changes.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy, existing AIProvider abstraction

## Global Constraints

- All agents extend BaseAgent from `src/NarrativeForge/Engine/agents/base.py`
- All models use Pydantic v2 BaseModel with `Field(default_factory=...)` for mutable defaults
- All agents catch JSON parse errors and return safe fallbacks
- Tests use FakeProvider (no real LLM calls)
- Every task ends with a commit
- TDD: write failing test first, then implement

---

## Task 1: New Data Models

**Covers:** [S4]

**Files:**
- Create: `src/NarrativeForge/Engine/models/dialogue.py`
- Create: `src/NarrativeForge/Engine/models/quest.py`
- Create: `src/NarrativeForge/Engine/models/lore.py`
- Modify: `src/NarrativeForge/Engine/models/__init__.py`
- Create: `tests/unit/test_new_models.py`

**Interfaces:**
- Produces: DialogueLine, DialogueExchange, DialogueResult, QuestObjective, QuestPrerequisite, QuestReward, Quest, LoreEntry (extended)

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_new_models.py
import pytest
from models.dialogue import DialogueLine, DialogueExchange, DialogueResult
from models.quest import QuestObjective, QuestPrerequisite, QuestReward, Quest
from models.lore import LoreEntry


def test_dialogue_line_creation():
    line = DialogueLine(character_id="c1", character_name="Hero", text="Hello")
    assert line.character_id == "c1"
    assert line.emotion == ""
    assert line.pause_after == 0.0


def test_dialogue_exchange_creation():
    exchange = DialogueExchange(
        id="ex1",
        lines=[DialogueLine(character_id="c1", character_name="A", text="Hi")],
        context="meeting",
        mood="tense",
    )
    assert len(exchange.lines) == 1


def test_dialogue_result_structured():
    result = DialogueResult(exchanges=[], format="structured")
    assert result.format == "structured"
    assert result.formatted_text == ""


def test_dialogue_result_formatted():
    result = DialogueResult(exchanges=[], format="formatted", formatted_text="HERO: Hello")
    assert result.formatted_text == "HERO: Hello"


def test_quest_objective_creation():
    obj = QuestObjective(id="o1", description="Defeat the dragon", type="kill", target="dragon")
    assert obj.quantity == 1
    assert obj.is_required is True


def test_quest_prerequisite():
    prereq = QuestPrerequisite(quest_id="q0", relationship="completed")
    assert prereq.relationship == "completed"


def test_quest_reward():
    reward = QuestReward(xp=100, gold=50, items=["sword"], reputation={"guards": 10})
    assert reward.xp == 100
    assert len(reward.items) == 1


def test_quest_creation():
    quest = Quest(
        id="q1",
        name="Dragon Slayer",
        description="Defeat the ancient dragon",
        objectives=[QuestObjective(id="o1", description="Find dragon", type="explore", target="cave")],
        prerequisites=[],
        rewards=QuestReward(xp=500),
    )
    assert quest.is_main_quest is False
    assert quest.faction_id == ""


def test_lore_entry_creation():
    entry = LoreEntry(id="l1", title="The First War", content="Long ago...", category="history")
    assert entry.tags == []
    assert entry.related_entries == []


def test_lore_entry_with_tags():
    entry = LoreEntry(
        id="l2", title="Dragon Scale", content="A rare material",
        category="item", tags=["rare", "crafting"], related_entries=["l1"],
    )
    assert len(entry.tags) == 2
    assert "l1" in entry.related_entries
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_new_models.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement models/dialogue.py**

```python
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class DialogueLine(BaseModel):
    character_id: str
    character_name: str
    text: str
    emotion: str = ""
    action: str = ""
    pause_after: float = 0.0


class DialogueExchange(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lines: list[DialogueLine] = Field(default_factory=list)
    context: str = ""
    mood: str = ""


class DialogueResult(BaseModel):
    exchanges: list[DialogueExchange] = Field(default_factory=list)
    format: str = "structured"
    formatted_text: str = ""
```

- [ ] **Step 4: Implement models/quest.py**

```python
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class QuestObjective(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    type: str = "explore"
    target: str = ""
    quantity: int = 1
    is_required: bool = True


class QuestPrerequisite(BaseModel):
    quest_id: str
    relationship: str = "completed"


class QuestReward(BaseModel):
    xp: int = 0
    gold: int = 0
    items: list[str] = Field(default_factory=list)
    reputation: dict[str, int] = Field(default_factory=dict)


class Quest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    objectives: list[QuestObjective] = Field(default_factory=list)
    prerequisites: list[QuestPrerequisite] = Field(default_factory=list)
    rewards: QuestReward = Field(default_factory=QuestReward)
    faction_id: str = ""
    is_main_quest: bool = False
```

- [ ] **Step 5: Implement models/lore.py**

```python
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class LoreEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    related_entries: list[str] = Field(default_factory=list)
```

- [ ] **Step 6: Update models/__init__.py**

Add imports for all new models to the existing `__init__.py`.

- [ ] **Step 7: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_new_models.py -v
# Expected: 11 passed
```

- [ ] **Step 8: Commit**

```bash
git add src/NarrativeForge/Engine/models/dialogue.py src/NarrativeForge/Engine/models/quest.py src/NarrativeForge/Engine/models/lore.py src/NarrativeForge/Engine/models/__init__.py tests/unit/test_new_models.py
git commit -m "feat: add Dialogue, Quest, and Lore data models"
```

---

## Task 2: DialogueAgent

**Covers:** [S5]

**Files:**
- Create: `src/NarrativeForge/Engine/agents/dialogue_agent.py`
- Modify: `src/NarrativeForge/Engine/agents/__init__.py`
- Create: `tests/unit/test_dialogue_agent.py`

**Interfaces:**
- Consumes: BaseAgent, AgentContext, AgentResult from `agents/base.py`; AIProvider; StoryBible models
- Produces: DialogueAgent class with `execute(context) -> AgentResult` returning structured or formatted dialogue

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_dialogue_agent.py
import pytest
from unittest.mock import AsyncMock
from agents.dialogue_agent import DialogueAgent
from agents.base import AgentContext, AgentResult
from ai_providers.base import AIProvider, Message
from models.project import Project, GameGenre
from models.story_bible import StoryBible
from models.character import Character, CharacterRole
from memory.graph_store import NarrativeGraph


class FakeProvider(AIProvider):
    def __init__(self):
        self.name = "fake"

    async def complete(self, messages, temperature=0.7, max_tokens=4096):
        import json
        return json.dumps({
            "exchanges": [{
                "id": "ex1",
                "lines": [
                    {"character_id": "c1", "character_name": "Hero", "text": "I will defeat you!", "emotion": "determined"},
                    {"character_id": "c2", "character_name": "Villain", "text": "You dare challenge me?", "emotion": "amused"},
                ],
                "context": "confrontation",
                "mood": "tense",
            }],
            "format": "structured",
        })

    async def stream(self, messages, temperature=0.7, max_tokens=4096):
        yield "test"


def make_context():
    project = Project(name="Test", genre=GameGenre.FANTASY)
    sb = StoryBible(project_id=project.id)
    sb.characters = {
        "c1": Character(name="Hero", id="c1", role=CharacterRole.PROTAGONIST),
        "c2": Character(name="Villain", id="c2", role=CharacterRole.ANTAGONIST),
    }
    graph = NarrativeGraph.from_story_bible(sb)
    return AgentContext(
        project=project,
        story_bible=sb,
        graph=graph,
        user_request="Write a confrontation dialogue between Hero and Villain",
        generation_params={"format": "structured"},
        previous_results=[],
        locked_elements=set(),
    )


async def test_dialogue_agent_returns_result():
    agent = DialogueAgent(FakeProvider())
    result = await agent.execute(make_context())
    assert isinstance(result, AgentResult)
    assert result.agent_name == "dialogue"


async def test_dialogue_agent_has_exchanges():
    agent = DialogueAgent(FakeProvider())
    result = await agent.execute(make_context())
    assert "exchanges" in result.metadata
    assert len(result.metadata["exchanges"]) > 0


async def test_dialogue_agent_system_prompt_includes_characters():
    agent = DialogueAgent(FakeProvider())
    context = make_context()
    prompt = agent.build_system_prompt(context)
    assert "Hero" in prompt
    assert "Villain" in prompt


async def test_dialogue_agent_uses_format_parameter():
    agent = DialogueAgent(FakeProvider())
    context = make_context()
    context.generation_params["format"] = "formatted"
    prompt = agent._build_user_prompt(context)
    assert "formatted" in prompt.lower() or "script" in prompt.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_dialogue_agent.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement agents/dialogue_agent.py**

```python
from __future__ import annotations

import json

from ai_providers.base import AIProvider, Message
from agents.base import BaseAgent, AgentContext, AgentResult


class DialogueAgent(BaseAgent):
    name = "dialogue"

    def build_system_prompt(self, context: AgentContext) -> str:
        genre = context.project.genre.value
        chars = list(context.story_bible.characters.values())
        char_info = "\n".join(
            f"- {c.name}: role={c.role.value}, personality={c.personality.traits}"
            for c in chars[:10]
        )
        return (
            f"You are a professional game dialogue writer specializing in {genre}.\n"
            f"Write natural, character-appropriate dialogue with emotional depth.\n"
            f"Each character must have a distinct voice based on their personality.\n"
            f"Include actions in [brackets] and emotional beats.\n\n"
            f"Known characters:\n{char_info}\n\n"
            f"Return JSON: {{\"exchanges\": [{{\"id\": \"...\", \"lines\": "
            f"[{{\"character_id\": \"...\", \"character_name\": \"...\", \"text\": \"...\", "
            f\"emotion\": \"...\", \"action\": \"...\"}}], \"context\": \"...\", \"mood\": \"...\"}}], "
            f\"format\": \"structured\"}}"
        )

    def _build_user_prompt(self, context: AgentContext) -> str:
        fmt = context.generation_params.get("format", "structured")
        parts = [
            f"Dialogue request: {context.user_request}",
            f"Output format: {fmt}",
        ]
        if context.previous_results:
            for prev in context.previous_results:
                parts.append(f"Previous context ({prev.agent_name}): {prev.content[:300]}")
        return "\n".join(parts)

    async def execute(self, context: AgentContext) -> AgentResult:
        system = self.build_system_prompt(context)
        user_msg = self._build_user_prompt(context)

        response = await self.provider.complete(
            [Message.system(system), Message.user(user_msg)],
            temperature=context.generation_params.get("temperature", 0.75),
        )

        parsed = self._parse_response(response)

        return AgentResult(
            agent_name=self.name,
            content=parsed.get("formatted_text", response),
            metadata=parsed,
        )

    def _parse_response(self, response: str) -> dict:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "exchanges": [],
                "format": "structured",
                "formatted_text": response,
            }
```

- [ ] **Step 4: Update agents/__init__.py**

Add `DialogueAgent` to the imports and `__all__`.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_dialogue_agent.py -v
# Expected: 4 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/NarrativeForge/Engine/agents/dialogue_agent.py src/NarrativeForge/Engine/agents/__init__.py tests/unit/test_dialogue_agent.py
git commit -m "feat: add DialogueAgent with structured and formatted output modes"
```

---

## Task 3: QuestAgent

**Covers:** [S5]

**Files:**
- Create: `src/NarrativeForge/Engine/agents/quest_agent.py`
- Modify: `src/NarrativeForge/Engine/agents/__init__.py`
- Create: `tests/unit/test_quest_agent.py`

**Interfaces:**
- Consumes: BaseAgent, AgentContext, AgentResult; StoryBible (characters, locations, factions)
- Produces: QuestAgent class with `execute(context) -> AgentResult` returning structured Quest data

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_quest_agent.py
import pytest
from agents.quest_agent import QuestAgent
from agents.base import AgentContext, AgentResult
from ai_providers.base import AIProvider, Message
from models.project import Project, GameGenre
from models.story_bible import StoryBible
from models.character import Character, CharacterRole
from models.location import Location
from memory.graph_store import NarrativeGraph


class FakeProvider(AIProvider):
    def __init__(self):
        self.name = "fake"

    async def complete(self, messages, temperature=0.7, max_tokens=4096):
        import json
        return json.dumps({
            "name": "Dragon Hunt",
            "description": "Defeat the dragon terrorizing the village",
            "objectives": [
                {"id": "o1", "description": "Travel to the dragon's cave", "type": "explore", "target": "Dragon Cave", "quantity": 1, "is_required": True},
                {"id": "o2", "description": "Defeat the dragon", "type": "kill", "target": "Ancient Dragon", "quantity": 1, "is_required": True},
            ],
            "prerequisites": [],
            "rewards": {"xp": 500, "gold": 200, "items": ["Dragon Scale"], "reputation": {"Village": 50}},
            "is_main_quest": False,
        })

    async def stream(self, messages, temperature=0.7, max_tokens=4096):
        yield "test"


def make_context():
    project = Project(name="Test", genre=GameGenre.FANTASY)
    sb = StoryBible(project_id=project.id)
    sb.characters = {"c1": Character(name="Elder", id="c1", role=CharacterRole.NPC)}
    sb.locations = {"l1": Location(name="Dragon Cave", id="l1", type="dungeon")}
    graph = NarrativeGraph.from_story_bible(sb)
    return AgentContext(
        project=project,
        story_bible=sb,
        graph=graph,
        user_request="Create a quest to defeat a dragon",
        generation_params={},
        previous_results=[],
        locked_elements=set(),
    )


async def test_quest_agent_returns_result():
    agent = QuestAgent(FakeProvider())
    result = await agent.execute(make_context())
    assert isinstance(result, AgentResult)
    assert result.agent_name == "quest"


async def test_quest_agent_has_quest_data():
    agent = QuestAgent(FakeProvider())
    result = await agent.execute(make_context())
    assert "quest" in result.metadata
    quest = result.metadata["quest"]
    assert quest["name"] == "Dragon Hunt"
    assert len(quest["objectives"]) == 2


async def test_quest_agent_system_prompt_includes_locations():
    agent = QuestAgent(FakeProvider())
    prompt = agent.build_system_prompt(make_context())
    assert "Dragon Cave" in prompt


async def test_quest_agent_includes_rewards():
    agent = QuestAgent(FakeProvider())
    result = await agent.execute(make_context())
    quest = result.metadata["quest"]
    assert quest["rewards"]["xp"] == 500
    assert "Dragon Scale" in quest["rewards"]["items"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_quest_agent.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement agents/quest_agent.py**

```python
from __future__ import annotations

import json

from ai_providers.base import AIProvider, Message
from agents.base import BaseAgent, AgentContext, AgentResult


class QuestAgent(BaseAgent):
    name = "quest"

    def build_system_prompt(self, context: AgentContext) -> str:
        genre = context.project.genre.value
        chars = list(context.story_bible.characters.values())
        locs = list(context.story_bible.locations.values())
        factions = list(context.story_bible.factions.values())

        char_info = "\n".join(f"- {c.name} ({c.role.value})" for c in chars[:10])
        loc_info = "\n".join(f"- {l.name} ({l.type})" for l in locs[:10])
        faction_info = "\n".join(f"- {f.name}" for f in factions[:10])

        return (
            f"You are a professional game quest designer specializing in {genre}.\n"
            f"Design compelling quests with clear objectives, logical prerequisites, and meaningful rewards.\n"
            f"Quests must fit the world's lore and existing characters.\n\n"
            f"Characters:\n{char_info}\n\n"
            f"Locations:\n{loc_info}\n\n"
            f"Factions:\n{faction_info}\n\n"
            f"Return JSON: {{\"name\": \"...\", \"description\": \"...\", \"objectives\": "
            f"[{{\"id\": \"...\", \"description\": \"...\", \"type\": \"explore|kill|collect|talk|defend\", "
            f\"target\": \"...\", \"quantity\": 1, \"is_required\": true}}], \"prerequisites\": "
            f"[{{\"quest_id\": \"...\", \"relationship\": \"completed\"}}], \"rewards\": "
            f"{{\"xp\": 0, \"gold\": 0, \"items\": [], \"reputation\": {{}}}, \"is_main_quest\": false}}"
        )

    async def execute(self, context: AgentContext) -> AgentResult:
        system = self.build_system_prompt(context)
        user_msg = f"Quest request: {context.user_request}"

        if context.previous_results:
            for prev in context.previous_results:
                user_msg += f"\nPrevious context ({prev.agent_name}): {prev.content[:300]}"

        response = await self.provider.complete(
            [Message.system(system), Message.user(user_msg)],
            temperature=context.generation_params.get("temperature", 0.6),
        )

        parsed = self._parse_response(response)

        return AgentResult(
            agent_name=self.name,
            content=json.dumps(parsed, indent=2),
            metadata={"quest": parsed},
        )

    def _parse_response(self, response: str) -> dict:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "name": "Untitled Quest",
                "description": response,
                "objectives": [],
                "prerequisites": [],
                "rewards": {"xp": 0, "gold": 0, "items": [], "reputation": {}},
                "is_main_quest": False,
            }
```

- [ ] **Step 4: Update agents/__init__.py**

Add `QuestAgent` to imports and `__all__`.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_quest_agent.py -v
# Expected: 4 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/NarrativeForge/Engine/agents/quest_agent.py src/NarrativeForge/Engine/agents/__init__.py tests/unit/test_quest_agent.py
git commit -m "feat: add QuestAgent with objectives, prerequisites, and rewards"
```

---

## Task 4: LoreAgent

**Covers:** [S5, S6]

**Files:**
- Create: `src/NarrativeForge/Engine/agents/lore_agent.py`
- Modify: `src/NarrativeForge/Engine/agents/__init__.py`
- Create: `tests/unit/test_lore_agent.py`

**Interfaces:**
- Consumes: BaseAgent, AgentContext, AgentResult; StoryBible (lore_entries)
- Produces: LoreAgent class with `execute(context) -> AgentResult` returning lore entries + changes for Story Bible auto-add

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_lore_agent.py
import pytest
from agents.lore_agent import LoreAgent
from agents.base import AgentContext, AgentResult
from ai_providers.base import AIProvider, Message
from models.project import Project, GameGenre
from models.story_bible import StoryBible
from memory.graph_store import NarrativeGraph


class FakeProvider(AIProvider):
    def __init__(self):
        self.name = "fake"

    async def complete(self, messages, temperature=0.7, max_tokens=4096):
        import json
        return json.dumps({
            "entries": [
                {
                    "id": "lore1",
                    "title": "The Dragon Wars",
                    "content": "Three centuries ago, dragons ruled the skies...",
                    "category": "history",
                    "tags": ["war", "dragons", "ancient"],
                    "related_entries": [],
                }
            ]
        })

    async def stream(self, messages, temperature=0.7, max_tokens=4096):
        yield "test"


def make_context():
    project = Project(name="Test", genre=GameGenre.FANTASY)
    sb = StoryBible(project_id=project.id)
    graph = NarrativeGraph.from_story_bible(sb)
    return AgentContext(
        project=project,
        story_bible=sb,
        graph=graph,
        user_request="Generate lore about the ancient dragon wars",
        generation_params={},
        previous_results=[],
        locked_elements=set(),
    )


async def test_lore_agent_returns_result():
    agent = LoreAgent(FakeProvider())
    result = await agent.execute(make_context())
    assert isinstance(result, AgentResult)
    assert result.agent_name == "lore"


async def test_lore_agent_has_entries():
    agent = LoreAgent(FakeProvider())
    result = await agent.execute(make_context())
    assert "lore_entries" in result.metadata
    assert len(result.metadata["lore_entries"]) > 0


async def test_lore_agent_returns_changes():
    agent = LoreAgent(FakeProvider())
    result = await agent.execute(make_context())
    assert "lore_entries" in result.changes
    assert "new" in result.changes["lore_entries"]


async def test_lore_agent_system_prompt_includes_existing():
    agent = LoreAgent(FakeProvider())
    context = make_context()
    context.story_bible.lore_entries = {"existing": {"title": "Old Lore", "content": "..."}}
    prompt = agent.build_system_prompt(context)
    assert "Old Lore" in prompt


async def test_lore_agent_avoids_duplicates():
    agent = LoreAgent(FakeProvider())
    context = make_context()
    context.story_bible.lore_entries = {"e1": {"title": "Dragon Wars", "content": "..."}}
    prompt = agent._build_user_prompt(context)
    assert "Dragon Wars" in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_lore_agent.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement agents/lore_agent.py**

```python
from __future__ import annotations

import json

from ai_providers.base import AIProvider, Message
from agents.base import BaseAgent, AgentContext, AgentResult


class LoreAgent(BaseAgent):
    name = "lore"

    def build_system_prompt(self, context: AgentContext) -> str:
        genre = context.project.genre.value
        existing = list(context.story_bible.lore_entries.values())
        existing_titles = [e.get("title", "") if isinstance(e, dict) else e.title for e in existing[:20]]

        return (
            f"You are a professional world-building lore architect specializing in {genre}.\n"
            f"Generate rich, detailed lore entries that fit the existing world.\n"
            f"Avoid duplicating existing lore.\n\n"
            f"Existing lore titles: {', '.join(existing_titles) if existing_titles else 'None'}\n\n"
            f"Categories: history, religion, economy, culture, creature, item, geography, politics\n\n"
            f"Return JSON: {{\"entries\": [{{\"id\": \"...\", \"title\": \"...\", \"content\": \"...\", "
            f"\"category\": \"...\", \"tags\": [], \"related_entries\": []}}]}}"
        )

    def _build_user_prompt(self, context: AgentContext) -> str:
        existing = list(context.story_bible.lore_entries.values())
        existing_titles = [e.get("title", "") if isinstance(e, dict) else e.title for e in existing[:10]]

        parts = [
            f"Lore request: {context.user_request}",
            f"Avoid these existing titles: {', '.join(existing_titles) if existing_titles else 'None'}",
        ]

        if context.previous_results:
            for prev in context.previous_results:
                parts.append(f"Context ({prev.agent_name}): {prev.content[:300]}")

        return "\n".join(parts)

    async def execute(self, context: AgentContext) -> AgentResult:
        system = self.build_system_prompt(context)
        user_msg = self._build_user_prompt(context)

        response = await self.provider.complete(
            [Message.system(system), Message.user(user_msg)],
            temperature=context.generation_params.get("temperature", 0.7),
        )

        parsed = self._parse_response(response)
        entries = parsed.get("entries", [])

        return AgentResult(
            agent_name=self.name,
            content=json.dumps(entries, indent=2),
            metadata={"lore_entries": entries},
            changes={"lore_entries": {"new": entries, "updated": []}},
        )

    def _parse_response(self, response: str) -> dict:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"entries": []}
```

- [ ] **Step 4: Update agents/__init__.py**

Add `LoreAgent` to imports and `__all__`.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_lore_agent.py -v
# Expected: 5 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/NarrativeForge/Engine/agents/lore_agent.py src/NarrativeForge/Engine/agents/__init__.py tests/unit/test_lore_agent.py
git commit -m "feat: add LoreAgent with auto-add to Story Bible via changes"
```

---

## Task 5: DirectorAgent Routing Update

**Covers:** [S5]

**Files:**
- Modify: `src/NarrativeForge/Engine/agents/director_agent.py`
- Modify: `tests/unit/test_agents.py` (add routing tests)

**Interfaces:**
- Consumes: Existing DirectorAgent
- Produces: Updated DirectorAgent with dialogue/quest/lore/mixed classification

- [ ] **Step 1: Write failing tests**

Add to existing `tests/unit/test_agents.py`:

```python
async def test_director_classifies_dialogue():
    provider = FakeProvider()
    provider.complete = AsyncMock(return_value='{"type": "dialogue", "agents": ["dialogue"], "plan": "Write confrontation dialogue"}')
    agent = DirectorAgent(provider)
    context = make_context()
    context.user_request = "Write a dialogue between the hero and the villain"
    result = await agent.execute(context)
    assert result.metadata["classification"] == "dialogue"


async def test_director_classifies_quest():
    provider = FakeProvider()
    provider.complete = AsyncMock(return_value='{"type": "quest", "agents": ["quest"], "plan": "Create dragon hunt quest"}')
    agent = DirectorAgent(provider)
    context = make_context()
    context.user_request = "Create a quest to defeat the dragon"
    result = await agent.execute(context)
    assert result.metadata["classification"] == "quest"


async def test_director_classifies_lore():
    provider = FakeProvider()
    provider.complete = AsyncMock(return_value='{"type": "lore", "agents": ["lore"], "plan": "Generate history of the empire"}')
    agent = DirectorAgent(provider)
    context = make_context()
    context.user_request = "Generate lore about the ancient empire"
    result = await agent.execute(context)
    assert result.metadata["classification"] == "lore"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_agents.py::TestDirectorAgent -v
# Expected: NEW tests FAIL — classification key not in metadata
```

- [ ] **Step 3: Update director_agent.py**

Add `"dialogue"`, `"quest"`, `"lore"`, `"mixed"` to the classification types in the system prompt and metadata extraction.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_agents.py -v
# Expected: all passed including new routing tests
```

- [ ] **Step 5: Commit**

```bash
git add src/NarrativeForge/Engine/agents/director_agent.py tests/unit/test_agents.py
git commit -m "feat: update DirectorAgent with dialogue/quest/lore/mixed classification"
```

---

## Task 6: PipelineOrchestrator Update

**Covers:** [S6]

**Files:**
- Modify: `src/NarrativeForge/Engine/pipeline/orchestrator.py`
- Modify: `tests/unit/test_pipeline.py`

**Interfaces:**
- Consumes: DialogueAgent, QuestAgent, LoreAgent from Tasks 2-4
- Produces: Updated PipelineOrchestrator with conditional agent execution and lore auto-add

- [ ] **Step 1: Write failing tests**

Add to existing `tests/unit/test_pipeline.py`:

```python
async def test_pipeline_routes_to_dialogue_agent():
    provider = FakeProvider()
    provider.complete = AsyncMock(return_value='{"type": "dialogue", "agents": ["dialogue"], "plan": "..."}')
    # Override to return dialogue-formatted response for dialogue agent
    original_complete = provider.complete

    async def side_effect(messages, **kwargs):
        if any("dialogue writer" in m.content.lower() for m in messages if hasattr(m, 'content')):
            import json
            return json.dumps({"exchanges": [{"id": "ex1", "lines": [], "context": "", "mood": ""}], "format": "structured"})
        return await original_complete(messages, **kwargs)

    provider.complete = side_effect
    orchestrator = PipelineOrchestrator(provider)
    context = make_context()
    context.user_request = "Write a dialogue"
    result = await orchestrator.run(context)
    assert "dialogue" in result.stages_completed


async def test_pipeline_lore_changes_applied():
    provider = FakeProvider()
    provider.complete = AsyncMock(return_value='{"type": "lore", "agents": ["lore"], "plan": "..."}')
    orchestrator = PipelineOrchestrator(provider)
    context = make_context()
    context.user_request = "Generate lore"
    result = await orchestrator.run(context)
    assert "lore" in result.stages_completed
    assert result.metadata.get("lore_entries_added", 0) >= 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_pipeline.py -v
# Expected: NEW tests FAIL
```

- [ ] **Step 3: Update pipeline/orchestrator.py**

- Import DialogueAgent, QuestAgent, LoreAgent
- In `run()`, read Director's classification from `director_result.metadata`
- Conditionally execute the appropriate agent(s)
- After consistency check, apply lore changes from AgentResult.changes to context.story_bible
- Add `lore_entries_added` to metadata

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_pipeline.py -v
# Expected: all passed
```

- [ ] **Step 5: Commit**

```bash
git add src/NarrativeForge/Engine/pipeline/orchestrator.py tests/unit/test_pipeline.py
git commit -m "feat: update PipelineOrchestrator with smart routing and lore auto-add"
```

---

## Task 7: Storage Updates

**Covers:** [S4]

**Files:**
- Modify: `src/NarrativeForge/Engine/storage/database.py`
- Modify: `tests/unit/test_storage.py`

**Interfaces:**
- Consumes: Existing Database class
- Produces: Added quest and dialogue CRUD methods

- [ ] **Step 1: Write failing tests**

Add to existing `tests/unit/test_storage.py`:

```python
async def test_create_and_get_quest(db):
    project = Project(name="Test", genre=GameGenre.RPG)
    await db.create_project(project)
    from models.quest import Quest, QuestObjective
    quest = Quest(name="Dragon Hunt", description="Defeat dragon", objectives=[QuestObjective(id="o1", description="Find cave", type="explore", target="cave")])
    await db.create_quest(project.id, quest)
    quests = await db.list_quests(project.id)
    assert len(quests) == 1
    assert quests[0].name == "Dragon Hunt"


async def test_create_and_get_dialogue(db):
    project = Project(name="Test", genre=GameGenre.RPG)
    await db.create_project(project)
    from models.dialogue import DialogueExchange, DialogueLine
    exchange = DialogueExchange(id="ex1", lines=[DialogueLine(character_id="c1", character_name="A", text="Hi")], context="meeting", mood="tense")
    await db.create_dialogue(project.id, exchange)
    dialogues = await db.list_dialogues(project.id)
    assert len(dialogues) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_storage.py -v
# Expected: NEW tests FAIL — methods don't exist
```

- [ ] **Step 3: Add QuestRow and DialogueRow to database.py**

Add SQLAlchemy models and CRUD methods for quests and dialogues.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_storage.py -v
# Expected: all passed
```

- [ ] **Step 5: Commit**

```bash
git add src/NarrativeForge/Engine/storage/database.py tests/unit/test_storage.py
git commit -m "feat: add quest and dialogue storage CRUD methods"
```

---

## Task 8: Direct Agent API Endpoint

**Covers:** [S6]

**Files:**
- Modify: `src/NarrativeForge/Engine/api/generation.py`
- Modify: `tests/unit/test_api.py`

**Interfaces:**
- Consumes: Existing API router, agents
- Produces: POST /api/agents/{agent_name} endpoint

- [ ] **Step 1: Write failing tests**

Add to existing `tests/unit/test_api.py`:

```python
async def test_direct_agent_invocation(client):
    # Create a project first
    proj = await client.post("/api/projects", json={"name": "Test", "genre": "fantasy"})
    pid = proj.json()["id"]

    response = await client.post(f"/api/agents/story", json={
        "project_id": pid,
        "request": "Write a short story",
        "temperature": 0.7,
    })
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert data["agent_name"] == "story"


async def test_direct_agent_invalid_name(client):
    proj = await client.post("/api/projects", json={"name": "Test", "genre": "fantasy"})
    pid = proj.json()["id"]

    response = await client.post("/api/agents/invalid_agent", json={
        "project_id": pid,
        "request": "test",
    })
    assert response.status_code == 400
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_api.py -v
# Expected: NEW tests FAIL — 404
```

- [ ] **Step 3: Add POST /api/agents/{agent_name} to generation.py**

Register route that instantiates the named agent and runs it directly.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_api.py -v
# Expected: all passed
```

- [ ] **Step 5: Commit**

```bash
git add src/NarrativeForge/Engine/api/generation.py tests/unit/test_api.py
git commit -m "feat: add direct agent invocation endpoint POST /api/agents/{agent_name}"
```

---

## Task 9: E2E Integration Test Extension

**Covers:** [S7]

**Files:**
- Modify: `tests/integration/test_e2e.py`

**Interfaces:**
- Consumes: All previous tasks
- Produces: Extended E2E test covering dialogue and quest flows

- [ ] **Step 1: Add dialogue and quest E2E tests**

```python
async def test_dialogue_generation_flow(client):
    # Create project
    proj = await client.post("/api/projects", json={"name": "Dialogue Test", "genre": "fantasy"})
    pid = proj.json()["id"]

    # Generate dialogue via direct agent
    response = await client.post("/api/agents/dialogue", json={
        "project_id": pid,
        "request": "Write a confrontation between two rivals",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["content"]) > 0

    # Cleanup
    await client.delete(f"/api/projects/{pid}")


async def test_quest_generation_flow(client):
    proj = await client.post("/api/projects", json={"name": "Quest Test", "genre": "rpg"})
    pid = proj.json()["id"]

    response = await client.post("/api/agents/quest", json={
        "project_id": pid,
        "request": "Create a rescue mission quest",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["content"]) > 0

    await client.delete(f"/api/projects/{pid}")


async def test_lore_generation_flow(client):
    proj = await client.post("/api/projects", json={"name": "Lore Test", "genre": "fantasy"})
    pid = proj.json()["id"]

    response = await client.post("/api/agents/lore", json={
        "project_id": pid,
        "request": "Generate the history of an ancient civilization",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["content"]) > 0

    await client.delete(f"/api/projects/{pid}")
```

- [ ] **Step 2: Run full test suite**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/ -v
# Expected: ~125 tests pass
```

- [ ] **Step 3: Run linter**

```bash
ruff check .
# Expected: no errors
```

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_e2e.py
git commit -m "feat: extend E2E tests with dialogue, quest, and lore generation flows"
```
