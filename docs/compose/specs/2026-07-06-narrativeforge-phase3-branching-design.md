# NarrativeForge Phase 3: Branching Dialogue Trees & Quest Graphs — Design Spec

## [S1] Problem Statement

Phase 2 delivered flat dialogue exchanges and linear quests. Game developers need branching dialogue trees with player choices, conditions, and variable state — the backbone of RPG and visual novel narratives. Quests need dynamic chains with branching paths, fail states, and world-state triggers. Without these, the system cannot support the non-linear storytelling that defines modern game narratives.

## [S2] Solution Overview

Build an Ink-compatible scripting engine with a parser, variable store, and condition evaluator. Create `DialogueTree` and `QuestGraph` classes as separate graph structures. The AI generates nodes iteratively (one at a time), with user review at each step. Support Ink script import/export for compatibility with existing tools.

## [S3] Architecture Approach

**Ink-Compatible Parser with Separate Graph Classes.** Build a parser for a subset of Ink syntax that produces `DialogueTree` and `QuestGraph` objects. A shared scripting DSL (variable store, condition evaluator, function registry) works with both. The AI generates one node at a time; the user reviews and wires it.

## [S4] Scripting Engine Components

### Variable Store
```python
class InkVariableStore:
    variables: dict[str, Any]
    set(name, value)
    get(name) -> Any
    observe(name, callback)  # Variable change listeners
```

### Condition Evaluator
```python
class InkConditionEvaluator:
    evaluate(expression: str) -> bool
    # Supports: ==, !=, >, <, >=, <=, &&, ||, !
    # Supports: variable references, literal values
```

### Function Registry
```python
class InkFunctionRegistry:
    register(name, callable)
    call(name, args) -> Any
    # Built-in: RANDOM(min, max), CONTAINS(list, item), LENGTH(list)
```

## [S5] Dialogue Tree Data Model

### Node Types
- `TEXT` — NPC speaks text
- `CHOICE` — Player picks from 2-4 options
- `CONDITION` — Branch based on variable
- `FUNCTION` — Call a registered function
- `VARIABLE` — Set a variable
- `JUMP` — Jump to another node
- `END` — End dialogue

### DialogueNode
```python
class DialogueNode(BaseModel):
    id: str
    type: DialogueNodeType
    content: str = ""
    choices: list[DialogueChoice] = []
    conditions: list[DialogueCondition] = []
    variables_set: dict[str, Any] = {}
    next_node_id: str = ""
```

### DialogueChoice
```python
class DialogueChoice(BaseModel):
    text: str
    next_node_id: str
    condition: str = ""
    variables_set: dict[str, Any] = {}
```

### DialogueTree
```python
class DialogueTree:
    nodes: dict[str, DialogueNode]
    edges: list[DialogueEdge]
    start_node_id: str
    variables: InkVariableStore
```

## [S6] Quest Graph Data Model

### Node Types
- `START` — Quest entry point
- `OBJECTIVE` — Quest objective
- `BRANCH` — Decision point
- `CONDITION` — State check
- `REWARD` — Quest completion reward
- `FAIL` — Quest failure state
- `END` — Quest end

### QuestNode
```python
class QuestNode(BaseModel):
    id: str
    type: QuestNodeType
    name: str = ""
    description: str = ""
    objectives: list[QuestObjective] = []
    rewards: QuestReward = {}
    conditions: list[QuestCondition] = []
    next_node_ids: list[str] = []
```

### QuestEdge
```python
class QuestEdge(BaseModel):
    source_id: str
    target_id: str
    condition: str = ""
    weight: float = 1.0
```

### QuestGraph
```python
class QuestGraph:
    nodes: dict[str, QuestNode]
    edges: list[QuestEdge]
    start_node_id: str
    variables: InkVariableStore
    state: QuestStateTracker
```

## [S7] Ink-Compatible Parser

### Supported Ink Syntax
- Knots: `=== name ===`
- Choices: `+ [text]` or `+ text`
- Diverts: `-> knot_name`
- Variables: `~ variable = value`
- Conditions: `{ condition ? true : false }`
- Tags: `# key: value`
- Comments: `// comment`
- End: `-> END`

### Parser Implementation
```python
class InkParser:
    def parse_dialogue(self, script: str) -> DialogueTree
    def parse_quest(self, script: str) -> QuestGraph
    def _parse_knot(self, lines) -> list[DialogueNode]
    def _parse_choice(self, line) -> DialogueChoice
    def _parse_divert(self, line) -> str
    def _parse_variable(self, line) -> dict
    def _parse_tag(self, line) -> dict
```

## [S8] AI Generation Design

### Iterative Node-by-Node Flow

1. User requests dialogue/quest generation
2. AI generates first node (START or initial TEXT)
3. User reviews → approves/rejects/modifies
4. AI generates next node based on context
5. Repeat until END node

### AI Prompts
- Dialogue prompt includes: genre, existing nodes, variables, last node content
- Quest prompt includes: genre, quest name, existing nodes, objectives so far
- Both return structured JSON matching node schemas

## [S9] Storage Design

### SQLite Schema
```sql
CREATE TABLE dialogue_trees (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    name TEXT NOT NULL,
    start_node_id TEXT,
    data_json TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE quest_graphs (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    name TEXT NOT NULL,
    start_node_id TEXT,
    data_json TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Store Classes
- `DialogueTreeStore`: save, load, list, delete, add/update/delete nodes
- `QuestGraphStore`: save, load, list, delete, add/update/delete nodes, add edges

## [S10] API Design

### Dialogue Endpoints
- `POST /api/projects/{id}/dialogues` — Create tree
- `GET /api/projects/{id}/dialogues` — List trees
- `GET /api/dialogues/{tree_id}` — Get tree
- `DELETE /api/dialogues/{tree_id}` — Delete tree
- `POST /api/dialogues/{tree_id}/nodes` — Add node
- `PUT /api/dialogues/{tree_id}/nodes/{node_id}` — Update node
- `DELETE /api/dialogues/{tree_id}/nodes/{node_id}` — Delete node
- `POST /api/dialogues/{tree_id}/generate` — Generate next node (AI)
- `POST /api/dialogues/parse` — Parse Ink script

### Quest Endpoints
- `POST /api/projects/{id}/quests` — Create graph
- `GET /api/projects/{id}/quests` — List graphs
- `GET /api/quests/{graph_id}` — Get graph
- `DELETE /api/quests/{graph_id}` — Delete graph
- `POST /api/quests/{graph_id}/nodes` — Add node
- `PUT /api/quests/{graph_id}/nodes/{node_id}` — Update node
- `DELETE /api/quests/{graph_id}/nodes/{node_id}` — Delete node
- `POST /api/quests/{graph_id}/edges` — Add edge
- `POST /api/quests/{graph_id}/generate` — Generate next node (AI)
- `POST /api/quests/parse` — Parse Ink script

## [S11] Scope Boundaries

### Included
- Ink-compatible parser (knots, choices, diverts, variables, tags, conditions)
- Variable store with observe/callback
- Condition evaluator (==, !=, >, <, >=, <=, &&, ||, !)
- DialogueTree and QuestGraph classes
- 7 DialogueNode types, 7 QuestNode types
- Iterative AI node generation
- SQLite storage for trees and graphs
- Full CRUD API
- Ink script import/export
- Unit tests

### Deferred to Phase 4+
- Visual graph editor in WPF
- Dialogue playback/preview
- Quest state simulation
- Game engine export
- Variable synchronization
- Plugin system
