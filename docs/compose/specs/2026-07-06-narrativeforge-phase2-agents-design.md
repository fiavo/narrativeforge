# NarrativeForge Phase 2: AI Agents — Design Spec

## [S1] Problem Statement

Phase 1 delivered a working narrative engine with three agents (Story, Director, Consistency Checker). Game developers need specialized agents for dialogue writing, quest design, and lore generation — the three most labor-intensive aspects of game narrative. Without these, the system only handles prose generation and must be augmented with manual work for core game writing tasks.

## [S2] Solution Overview

Add three new specialized AI agents (DialogueAgent, QuestAgent, LoreAgent) to the existing agent framework. Update the Director Agent to classify requests and route to the appropriate agent. The PipelineOrchestrator gains conditional execution paths. LoreAgent automatically adds generated entries to the Story Bible. All new agents follow the established BaseAgent pattern and integrate with the existing pipeline.

## [S3] Architecture Approach

**Extend Existing Pipeline with Smart Director Routing.** The Director already classifies requests — extending it to route to Dialogue/Quest/Lore agents is natural. The Consistency Checker already validates against the Story Bible, so it catches cross-domain issues automatically. No new structural patterns needed.

## [S4] New Data Models

### Dialogue Models

```python
class DialogueLine(BaseModel):
    character_id: str
    character_name: str
    text: str
    emotion: str = ""
    action: str = ""
    pause_after: float = 0.0

class DialogueExchange(BaseModel):
    id: str
    lines: list[DialogueLine]
    context: str
    mood: str

class DialogueResult(BaseModel):
    exchanges: list[DialogueExchange]
    format: str                # "structured" or "formatted"
    formatted_text: str = ""
```

### Quest Models

```python
class QuestObjective(BaseModel):
    id: str
    description: str
    type: str                  # "kill", "collect", "talk", "explore", "defend"
    target: str
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
    id: str
    name: str
    description: str
    objectives: list[QuestObjective]
    prerequisites: list[QuestPrerequisite]
    rewards: QuestReward
    faction_id: str = ""
    is_main_quest: bool = False
```

### Lore Model (Extended)

```python
class LoreEntry(BaseModel):
    id: str
    title: str
    content: str
    category: str              # "history", "religion", "economy", "culture", "creature", "item"
    tags: list[str] = Field(default_factory=list)
    related_entries: list[str] = Field(default_factory=list)
```

## [S5] Agent Designs

### DialogueAgent

Extends BaseAgent. Classifies dialogue request into: conversation, monologue, confrontation, negotiation, exposition. Generates structured JSON with character lines, emotions, and actions. Supports both structured and formatted output modes via a `format` parameter.

**System prompt includes:** Genre, tone, character personalities/relationships from Story Bible, dialogue history from previous results.

**Temperature:** 0.75

### QuestAgent

Extends BaseAgent. Generates complete quest structures with objectives, prerequisites, and rewards. Cross-references Story Bible for characters, locations, and factions involved.

**System prompt includes:** Genre conventions for quests, existing characters/locations/factions, active timeline events, locked elements.

**Temperature:** 0.6

### LoreAgent

Extends BaseAgent. Generates world lore entries across categories. Automatically adds generated entries to Story Bible via the `changes` field in AgentResult.

**System prompt includes:** Existing lore entries (to avoid duplicates), world geography, faction relationships, timeline events.

**Temperature:** 0.7

### DirectorAgent Update

The existing DirectorAgent gains new classification categories:
- `"dialogue"` → routes to DialogueAgent
- `"quest"` → routes to QuestAgent
- `"lore"` → routes to LoreAgent
- `"story"` → routes to StoryAgent (existing)
- `"mixed"` → routes to multiple agents sequentially

## [S6] Pipeline Integration

### Updated Flow

```
User Request → Director (classify + route) → [Selected Agent(s)] → Consistency Checker → Output
```

The PipelineOrchestrator inspects the Director's classification and conditionally invokes the appropriate agent(s). The Consistency Checker always runs last.

### Lore Auto-Add

LoreAgent returns changes in `AgentResult.changes`:
```python
{"lore_entries": {"new": [LoreEntry(...)], "updated": [LoreEntry(...)]}}
```

The PipelineOrchestrator applies these to the Story Bible after pipeline completion.

### Direct Agent Endpoint

New API endpoint for power users bypassing Director:
```
POST /api/agents/{agent_name}
Body: { project_id, request, temperature }
```

## [S7] Testing Strategy

### Unit Tests (~10 new)
- DialogueAgent: structured output, formatted mode, emotion detection
- QuestAgent: objectives generation, prerequisite handling, reward calculation
- LoreAgent: entry generation, category detection, change tracking

### Integration Tests (~5 new)
- Director routing to each new agent
- Mixed routing (multiple agents)
- Lore changes applied to Story Bible

### E2E Test (extend existing)
- Dialogue generation flow
- Quest generation flow

### Target: ~120 total tests (110 existing + ~10 new)

## [S8] Scope Boundaries

### Included
- DialogueAgent with structured + formatted output
- QuestAgent with objectives, prerequisites, rewards
- LoreAgent with auto-add to Story Bible
- DirectorAgent routing update
- PipelineOrchestrator conditional execution
- New data models
- Storage updates for quest/dialogue persistence
- Direct agent invocation API endpoint
- Full test coverage

### Deferred to Phase 3+
- Branching dialogue trees
- Quest graphs with multiple endings
- Dialogue playback/preview in WPF
- Quest visual editor
- Game engine export
- Plugin system
