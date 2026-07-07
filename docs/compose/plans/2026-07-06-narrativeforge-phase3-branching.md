# NarrativeForge Phase 3: Branching Dialogue Trees & Quest Graphs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Ink-compatible branching dialogue trees and dynamic quest graphs with iterative AI generation.

**Architecture:** Build an Ink parser that produces DialogueTree and QuestGraph objects. A shared scripting DSL (variable store, condition evaluator, function registry) powers both. AI generates nodes iteratively with user review. SQLite stores trees/graphs; REST API exposes CRUD + generation.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy, existing BaseAgent framework

## Global Constraints

- All models use Pydantic v2 BaseModel
- All agents catch JSON parse errors and return safe fallbacks
- Tests use FakeProvider (no real LLM calls)
- Every task ends with a commit
- TDD: write failing test first, then implement

---

## Task 1: Scripting Engine Core

**Covers:** [S4]

**Files:**
- Create: `src/NarrativeForge/Engine/scripting/__init__.py`
- Create: `src/NarrativeForge/Engine/scripting/variables.py`
- Create: `src/NarrativeForge/Engine/scripting/conditions.py`
- Create: `src/NarrativeForge/Engine/scripting/functions.py`
- Create: `tests/unit/test_scripting.py`

**Interfaces:**
- Produces: InkVariableStore, InkConditionEvaluator, InkFunctionRegistry

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_scripting.py
import pytest
from scripting.variables import InkVariableStore
from scripting.conditions import InkConditionEvaluator
from scripting.functions import InkFunctionRegistry


def test_variable_store_set_get():
    store = InkVariableStore()
    store.set("health", 100)
    assert store.get("health") == 100


def test_variable_store_default():
    store = InkVariableStore()
    assert store.get("missing", 0) == 0


def test_variable_store_observe():
    store = InkVariableStore()
    changes = []
    store.observe("health", lambda v: changes.append(v))
    store.set("health", 50)
    assert changes == [50]


def test_condition_evaluator_equals():
    evaluator = InkConditionEvaluator()
    store = InkVariableStore()
    store.set("x", 5)
    assert evaluator.evaluate("x == 5", store) is True
    assert evaluator.evaluate("x == 6", store) is False


def test_condition_evaluator_and():
    evaluator = InkConditionEvaluator()
    store = InkVariableStore()
    store.set("a", True)
    store.set("b", False)
    assert evaluator.evaluate("a && b", store) is False
    store.set("b", True)
    assert evaluator.evaluate("a && b", store) is True


def test_condition_evaluator_not():
    evaluator = InkConditionEvaluator()
    store = InkVariableStore()
    store.set("flag", False)
    assert evaluator.evaluate("!flag", store) is True


def test_function_registry():
    registry = InkFunctionRegistry()
    registry.register("double", lambda x: x * 2)
    assert registry.call("double", [5]) == 10


def test_function_registry_builtin_random():
    registry = InkFunctionRegistry()
    result = registry.call("RANDOM", [1, 10])
    assert 1 <= result <= 10


def test_function_registry_builtin_contains():
    registry = InkFunctionRegistry()
    assert registry.call("CONTAINS", [[1, 2, 3], 2]) is True
    assert registry.call("CONTAINS", [[1, 2, 3], 4]) is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_scripting.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement scripting/variables.py**

```python
from __future__ import annotations

from typing import Any, Callable


class InkVariableStore:
    def __init__(self):
        self._variables: dict[str, Any] = {}
        self._observers: dict[str, list[Callable[[Any], None]]] = {}

    def set(self, name: str, value: Any) -> None:
        self._variables[name] = value
        for callback in self._observers.get(name, []):
            callback(value)

    def get(self, name: str, default: Any = None) -> Any:
        return self._variables.get(name, default)

    def observe(self, name: str, callback: Callable[[Any], None]) -> None:
        if name not in self._observers:
            self._observers[name] = []
        self._observers[name].append(callback)

    def to_dict(self) -> dict[str, Any]:
        return dict(self._variables)

    def from_dict(self, data: dict[str, Any]) -> None:
        self._variables = dict(data)
```

- [ ] **Step 4: Implement scripting/conditions.py**

```python
from __future__ import annotations

import operator
from typing import Any

from scripting.variables import InkVariableStore


OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
}


class InkConditionEvaluator:
    def evaluate(self, expression: str, store: InkVariableStore) -> bool:
        expression = expression.strip()

        if not expression:
            return True

        if expression.startswith("!"):
            return not self.evaluate(expression[1:], store)

        for op_str, op_func in OPERATORS.items():
            parts = expression.split(op_str, 1)
            if len(parts) == 2:
                left = self._resolve(parts[0].strip(), store)
                right = self._resolve(parts[1].strip(), store)
                return op_func(left, right)

        if "&&" in expression:
            left, right = expression.split("&&", 1)
            return self.evaluate(left, store) and self.evaluate(right, store)

        if "||" in expression:
            left, right = expression.split("||", 1)
            return self.evaluate(left, store) or self.evaluate(right, store)

        return bool(self._resolve(expression, store))

    def _resolve(self, value: str, store: InkVariableStore) -> Any:
        value = value.strip()

        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False

        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]

        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            pass

        return store.get(value, value)
```

- [ ] **Step 5: Implement scripting/functions.py**

```python
from __future__ import annotations

import random
from typing import Any, Callable


class InkFunctionRegistry:
    def __init__(self):
        self._functions: dict[str, Callable] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        self.register("RANDOM", lambda *args: random.randint(int(args[0]), int(args[1])))
        self.register("CONTAINS", lambda lst, item: item in lst)
        self.register("LENGTH", lambda lst: len(lst))

    def register(self, name: str, func: Callable) -> None:
        self._functions[name] = func

    def call(self, name: str, args: list[Any]) -> Any:
        if name not in self._functions:
            raise ValueError(f"Unknown function: {name}")
        return self._functions[name](*args)
```

- [ ] **Step 6: Create scripting/__init__.py**

```python
from scripting.variables import InkVariableStore
from scripting.conditions import InkConditionEvaluator
from scripting.functions import InkFunctionRegistry

__all__ = ["InkVariableStore", "InkConditionEvaluator", "InkFunctionRegistry"]
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_scripting.py -v
# Expected: 9 passed
```

- [ ] **Step 8: Commit**

```bash
git add src/NarrativeForge/Engine/scripting/ tests/unit/test_scripting.py
git commit -m "feat: add scripting engine core (variable store, condition evaluator, function registry)"
```

---

## Task 2: Dialogue Tree Data Model

**Covers:** [S5]

**Files:**
- Create: `src/NarrativeForge/Engine/models/dialogue_tree.py`
- Modify: `src/NarrativeForge/Engine/models/__init__.py`
- Create: `tests/unit/test_dialogue_tree.py`

**Interfaces:**
- Consumes: InkVariableStore from Task 1
- Produces: DialogueNodeType, DialogueNode, DialogueChoice, DialogueCondition, DialogueEdge, DialogueTree

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_dialogue_tree.py
import pytest
from models.dialogue_tree import (
    DialogueNodeType, DialogueNode, DialogueChoice,
    DialogueCondition, DialogueEdge, DialogueTree,
)


def test_dialogue_node_types():
    assert DialogueNodeType.TEXT == "text"
    assert DialogueNodeType.CHOICE == "choice"
    assert DialogueNodeType.END == "end"


def test_dialogue_node_creation():
    node = DialogueNode(id="n1", type=DialogueNodeType.TEXT, content="Hello!")
    assert node.id == "n1"
    assert node.content == "Hello!"


def test_dialogue_choice_creation():
    choice = DialogueChoice(text="Tell me more", next_node_id="n2")
    assert choice.text == "Tell me more"
    assert choice.condition == ""


def test_dialogue_condition_creation():
    cond = DialogueCondition(expression="has_key == true", true_node_id="n3")
    assert cond.expression == "has_key == true"
    assert cond.false_node_id == ""


def test_dialogue_edge_creation():
    edge = DialogueEdge(source_id="n1", target_id="n2")
    assert edge.source_id == "n1"
    assert edge.target_id == "n2"


def test_dialogue_tree_creation():
    tree = DialogueTree(start_node_id="n1")
    assert tree.start_node_id == "n1"
    assert tree.nodes == {}


def test_dialogue_tree_add_node():
    tree = DialogueTree(start_node_id="n1")
    node = DialogueNode(id="n1", type=DialogueNodeType.TEXT, content="Hi")
    tree.nodes["n1"] = node
    assert "n1" in tree.nodes


def test_dialogue_tree_has_variables():
    tree = DialogueTree(start_node_id="n1")
    assert tree.variables is not None
    tree.variables.set("flag", True)
    assert tree.variables.get("flag") is True
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_dialogue_tree.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement models/dialogue_tree.py**

```python
from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field

from scripting.variables import InkVariableStore


class DialogueNodeType(str, Enum):
    TEXT = "text"
    CHOICE = "choice"
    CONDITION = "condition"
    FUNCTION = "function"
    VARIABLE = "variable"
    JUMP = "jump"
    END = "end"


class DialogueChoice(BaseModel):
    text: str
    next_node_id: str
    condition: str = ""
    variables_set: dict[str, str] = Field(default_factory=dict)


class DialogueCondition(BaseModel):
    expression: str
    true_node_id: str
    false_node_id: str = ""


class DialogueNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: DialogueNodeType
    content: str = ""
    choices: list[DialogueChoice] = Field(default_factory=list)
    conditions: list[DialogueCondition] = Field(default_factory=list)
    variables_set: dict[str, str] = Field(default_factory=dict)
    next_node_id: str = ""


class DialogueEdge(BaseModel):
    source_id: str
    target_id: str
    label: str = ""


class DialogueTree(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    start_node_id: str
    nodes: dict[str, DialogueNode] = Field(default_factory=dict)
    edges: list[DialogueEdge] = Field(default_factory=list)
    variables: InkVariableStore = Field(default_factory=InkVariableStore)

    model_config = {"arbitrary_types_allowed": True}
```

- [ ] **Step 4: Update models/__init__.py**

Add imports for all new dialogue tree models.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_dialogue_tree.py -v
# Expected: 8 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/NarrativeForge/Engine/models/dialogue_tree.py src/NarrativeForge/Engine/models/__init__.py tests/unit/test_dialogue_tree.py
git commit -m "feat: add dialogue tree data model with branching node types"
```

---

## Task 3: Quest Graph Data Model

**Covers:** [S6]

**Files:**
- Create: `src/NarrativeForge/Engine/models/quest_graph.py`
- Modify: `src/NarrativeForge/Engine/models/__init__.py`
- Create: `tests/unit/test_quest_graph.py`

**Interfaces:**
- Consumes: InkVariableStore from Task 1
- Produces: QuestNodeType, QuestNode, QuestCondition, QuestEdge, QuestStateTracker, QuestGraph

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_quest_graph.py
import pytest
from models.quest_graph import (
    QuestNodeType, QuestNode, QuestCondition,
    QuestEdge, QuestStateTracker, QuestGraph,
)


def test_quest_node_types():
    assert QuestNodeType.START == "start"
    assert QuestNodeType.OBJECTIVE == "objective"
    assert QuestNodeType.BRANCH == "branch"
    assert QuestNodeType.FAIL == "fail"


def test_quest_node_creation():
    node = QuestNode(id="n1", type=QuestNodeType.START, name="Quest Start")
    assert node.id == "n1"
    assert node.name == "Quest Start"


def test_quest_condition_creation():
    cond = QuestCondition(expression="reputation > 50", true_node_id="n2")
    assert cond.expression == "reputation > 50"


def test_quest_edge_creation():
    edge = QuestEdge(source_id="n1", target_id="n2", condition="has_key == true")
    assert edge.source_id == "n1"
    assert edge.condition == "has_key == true"


def test_quest_state_tracker():
    tracker = QuestStateTracker()
    tracker.set("dragons_killed", 3)
    assert tracker.get("dragons_killed") == 3
    assert tracker.is_complete() is False


def test_quest_state_tracker_complete():
    tracker = QuestStateTracker()
    tracker.set("objectives_complete", True)
    assert tracker.is_complete() is True


def test_quest_graph_creation():
    graph = QuestGraph(start_node_id="n1")
    assert graph.start_node_id == "n1"
    assert graph.nodes == {}


def test_quest_graph_has_variables():
    graph = QuestGraph(start_node_id="n1")
    assert graph.variables is not None
    graph.variables.set("quest_level", 5)
    assert graph.variables.get("quest_level") == 5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_quest_graph.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement models/quest_graph.py**

```python
from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field

from scripting.variables import InkVariableStore


class QuestNodeType(str, Enum):
    START = "start"
    OBJECTIVE = "objective"
    BRANCH = "branch"
    CONDITION = "condition"
    REWARD = "reward"
    FAIL = "fail"
    END = "end"


class QuestCondition(BaseModel):
    expression: str
    true_node_id: str
    false_node_id: str = ""


class QuestNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: QuestNodeType
    name: str = ""
    description: str = ""
    objectives: list[dict] = Field(default_factory=list)
    rewards: dict = Field(default_factory=dict)
    conditions: list[QuestCondition] = Field(default_factory=list)
    next_node_ids: list[str] = Field(default_factory=list)


class QuestEdge(BaseModel):
    source_id: str
    target_id: str
    condition: str = ""
    weight: float = 1.0


class QuestStateTracker(BaseModel):
    state: dict[str, any] = Field(default_factory=dict)

    def set(self, key: str, value: any) -> None:
        self.state[key] = value

    def get(self, key: str, default: any = None) -> any:
        return self.state.get(key, default)

    def is_complete(self) -> bool:
        return self.state.get("objectives_complete", False)


class QuestGraph(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    start_node_id: str
    nodes: dict[str, QuestNode] = Field(default_factory=dict)
    edges: list[QuestEdge] = Field(default_factory=list)
    variables: InkVariableStore = Field(default_factory=InkVariableStore)
    state: QuestStateTracker = Field(default_factory=QuestStateTracker)

    model_config = {"arbitrary_types_allowed": True}
```

- [ ] **Step 4: Update models/__init__.py**

Add imports for all new quest graph models.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_quest_graph.py -v
# Expected: 8 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/NarrativeForge/Engine/models/quest_graph.py src/NarrativeForge/Engine/models/__init__.py tests/unit/test_quest_graph.py
git commit -m "feat: add quest graph data model with branching node types"
```

---

## Task 4: Ink Parser

**Covers:** [S7]

**Files:**
- Create: `src/NarrativeForge/Engine/scripting/ink_parser.py`
- Modify: `src/NarrativeForge/Engine/scripting/__init__.py`
- Create: `tests/unit/test_ink_parser.py`

**Interfaces:**
- Consumes: DialogueTree, QuestGraph from Tasks 2-3
- Produces: InkParser with parse_dialogue() and parse_quest() methods

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_ink_parser.py
import pytest
from scripting.ink_parser import InkParser


def test_parse_simple_dialogue():
    script = """
=== start ===
NPC: Hello there!
+ [Hi] -> greeting
+ [Goodbye] -> END

=== greeting ===
NPC: Nice to meet you!
-> END
"""
    parser = InkParser()
    tree = parser.parse_dialogue(script)
    assert tree.start_node_id != ""
    assert len(tree.nodes) >= 2


def test_parse_variable_assignment():
    script = """
=== start ===
~ has_key = true
NPC: You got the key!
-> END
"""
    parser = InkParser()
    tree = parser.parse_dialogue(script)
    assert tree.variables.get("has_key") is True


def test_parse_choice_with_condition():
    script = """
=== start ===
NPC: Want to enter?
+ [Enter] (has_key == true) -> inside
+ [Leave] -> END

=== inside ===
NPC: Welcome inside!
-> END
"""
    parser = InkParser()
    tree = parser.parse_dialogue(script)
    assert len(tree.nodes) >= 2


def test_parse_quest():
    script = """
=== start ===
# name: Dragon Hunt
# description: Defeat the ancient dragon
-> objective_1

=== objective_1 ===
# objective: Travel to the cave
-> objective_2

=== objective_2 ===
# objective: Defeat the dragon
-> reward

=== reward ===
# xp: 500
# gold: 200
-> END
"""
    parser = InkParser()
    graph = parser.parse_quest(script)
    assert graph.start_node_id != ""
    assert len(graph.nodes) >= 3


def test_parse_jump():
    script = """
=== start ===
-> middle

=== middle ===
NPC: Middle!
-> END
"""
    parser = InkParser()
    tree = parser.parse_dialogue(script)
    assert len(tree.nodes) >= 2


def test_parse_empty_script():
    parser = InkParser()
    tree = parser.parse_dialogue("")
    assert tree.start_node_id != ""


def test_parse_tag():
    script = """
=== start ===
# mood: tense
NPC: Something is wrong...
-> END
"""
    parser = InkParser()
    tree = parser.parse_dialogue(script)
    assert len(tree.nodes) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_ink_parser.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement scripting/ink_parser.py**

```python
from __future__ import annotations

import re
import uuid
from typing import Any

from models.dialogue_tree import (
    DialogueTree, DialogueNode, DialogueNodeType,
    DialogueChoice, DialogueCondition, DialogueEdge,
)
from models.quest_graph import (
    QuestGraph, QuestNode, QuestNodeType, QuestCondition, QuestEdge,
)
from scripting.variables import InkVariableStore


class InkParser:
    def __init__(self):
        self._knots: dict[str, list[str]] = {}
        self._variables: dict[str, Any] = {}

    def parse_dialogue(self, script: str) -> DialogueTree:
        self._knots = self._extract_knots(script)
        self._variables = {}

        tree = DialogueTree(start_node_id="", name="Untitled Dialogue")
        tree.variables = InkVariableStore()

        for knot_name, lines in self._knots.items():
            nodes = self._parse_knot(lines, knot_name)
            for node in nodes:
                tree.nodes[node.id] = node

        if self._knots:
            first_knot = list(self._knots.keys())[0]
            first_nodes = [n for n in tree.nodes.values()
                          if any(e.source_id == n.id for e in tree.edges
                                if e.label == f"knot:{first_knot}")]
            if first_nodes:
                tree.start_node_id = first_nodes[0].id
            elif tree.nodes:
                tree.start_node_id = list(tree.nodes.keys())[0]

        for var_name, var_value in self._variables.items():
            tree.variables.set(var_name, var_value)

        return tree

    def parse_quest(self, script: str) -> QuestGraph:
        self._knots = self._extract_knots(script)
        self._variables = {}

        graph = QuestGraph(start_node_id="", name="Untitled Quest")
        graph.variables = InkVariableStore()

        for knot_name, lines in self._knots.items():
            nodes = self._parse_quest_knot(lines, knot_name)
            for node in nodes:
                graph.nodes[node.id] = node

        if self._knots:
            first_knot = list(self._knots.keys())[0]
            first_nodes = [n for n in graph.nodes.values()
                          if any(e.source_id == n.id for e in graph.edges
                                if e.label == f"knot:{first_knot}")]
            if first_nodes:
                graph.start_node_id = first_nodes[0].id
            elif graph.nodes:
                graph.start_node_id = list(graph.nodes.keys())[0]

        for var_name, var_value in self._variables.items():
            graph.variables.set(var_name, var_value)

        return graph

    def _extract_knots(self, script: str) -> dict[str, list[str]]:
        knots: dict[str, list[str]] = {}
        current_knot = "__header__"
        knots[current_knot] = []

        for line in script.split("\n"):
            stripped = line.strip()
            match = re.match(r"^===\s+(\w+)\s+===$", stripped)
            if match:
                current_knot = match.group(1)
                knots[current_knot] = []
            else:
                knots[current_knot].append(line)

        return {k: v for k, v in knots.items() if v or k != "__header__"}

    def _parse_knot(self, lines: list[str], knot_name: str) -> list[DialogueNode]:
        nodes: list[DialogueNode] = []
        pending_choices: list[DialogueChoice] = []
        last_node_id = ""

        for line in lines:
            stripped = line.strip()

            if not stripped or stripped.startswith("//"):
                continue

            if stripped.startswith("~"):
                self._parse_variable_line(stripped)
                continue

            if stripped.startswith("->"):
                target = stripped[2:].strip()
                if target == "END":
                    end_node = DialogueNode(
                        id=str(uuid.uuid4()),
                        type=DialogueNodeType.END,
                    )
                    nodes.append(end_node)
                    if last_node_id:
                        nodes[-1].next_node_id = end_node.id
                elif target in self._knots:
                    jump_node = DialogueNode(
                        id=str(uuid.uuid4()),
                        type=DialogueNodeType.JUMP,
                        content=target,
                    )
                    nodes.append(jump_node)
                continue

            if stripped.startswith("+"):
                choice = self._parse_choice_line(stripped)
                pending_choices.append(choice)
                continue

            if stripped.startswith("#"):
                continue

            if pending_choices:
                choice_node = DialogueNode(
                    id=str(uuid.uuid4()),
                    type=DialogueNodeType.CHOICE,
                    choices=pending_choices,
                )
                nodes.append(choice_node)
                pending_choices = []

            text = stripped
            if ":" in text:
                parts = text.split(":", 1)
                text = parts[1].strip() if len(parts) > 1 else text

            node = DialogueNode(
                id=str(uuid.uuid4()),
                type=DialogueNodeType.TEXT,
                content=text,
            )
            nodes.append(node)
            last_node_id = node.id

        if pending_choices:
            choice_node = DialogueNode(
                id=str(uuid.uuid4()),
                type=DialogueNodeType.CHOICE,
                choices=pending_choices,
            )
            nodes.append(choice_node)

        return nodes

    def _parse_quest_knot(self, lines: list[str], knot_name: str) -> list[QuestNode]:
        nodes: list[QuestNode] = []
        tags: dict[str, str] = {}

        for line in lines:
            stripped = line.strip()

            if not stripped or stripped.startswith("//"):
                continue

            if stripped.startswith("~"):
                self._parse_variable_line(stripped)
                continue

            if stripped.startswith("#"):
                key, _, value = stripped[1:].strip().partition(":")
                tags[key.strip()] = value.strip()
                continue

            if stripped.startswith("->"):
                target = stripped[2:].strip()
                if target == "END":
                    continue
                continue

        if tags:
            node_type = QuestNodeType.OBJECTIVE
            if "name" in tags:
                node_type = QuestNodeType.START
            elif "xp" in tags or "gold" in tags:
                node_type = QuestNodeType.REWARD

            node = QuestNode(
                id=str(uuid.uuid4()),
                type=node_type,
                name=tags.get("name", ""),
                description=tags.get("description", ""),
            )

            if "objective" in tags:
                node.objectives = [{"description": tags["objective"]}]

            if "xp" in tags or "gold" in tags:
                node.rewards = {
                    "xp": int(tags.get("xp", 0)),
                    "gold": int(tags.get("gold", 0)),
                }

            nodes.append(node)

        return nodes

    def _parse_variable_line(self, line: str) -> None:
        match = re.match(r"~\s+(\w+)\s*=\s*(.+)", line)
        if match:
            var_name = match.group(1)
            var_value = match.group(2).strip()
            if var_value.lower() == "true":
                self._variables[var_name] = True
            elif var_value.lower() == "false":
                self._variables[var_name] = False
            else:
                try:
                    self._variables[var_name] = int(var_value)
                except ValueError:
                    try:
                        self._variables[var_name] = float(var_value)
                    except ValueError:
                        self._variables[var_name] = var_value.strip("\"'")

    def _parse_choice_line(self, line: str) -> DialogueChoice:
        match = re.match(r"\+\s*\[(.+?)\](?:\s*\((.+?)\))?\s*(?:->\s*(\w+))?", line)
        if match:
            text = match.group(1)
            condition = match.group(2) or ""
            target = match.group(3) or ""
            return DialogueChoice(text=text, next_node_id=target, condition=condition)
        return DialogueChoice(text=line, next_node_id="")
```

- [ ] **Step 4: Update scripting/__init__.py**

Add InkParser to exports.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_ink_parser.py -v
# Expected: 7 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/NarrativeForge/Engine/scripting/ink_parser.py src/NarrativeForge/Engine/scripting/__init__.py tests/unit/test_ink_parser.py
git commit -m "feat: add Ink-compatible parser for dialogue trees and quest graphs"
```

---

## Task 5: Dialogue & Quest Storage

**Covers:** [S9]

**Files:**
- Modify: `src/NarrativeForge/Engine/storage/database.py`
- Modify: `tests/unit/test_storage.py`

**Interfaces:**
- Consumes: DialogueTree, QuestGraph from Tasks 2-3
- Produces: DialogueTreeStore, QuestGraphStore CRUD methods

- [ ] **Step 1: Write failing tests**

Add to existing `tests/unit/test_storage.py`:

```python
async def test_create_and_get_dialogue_tree(db):
    project = Project(name="Test", genre=GameGenre.RPG)
    await db.create_project(project)
    from models.dialogue_tree import DialogueTree, DialogueNode, DialogueNodeType
    tree = DialogueTree(name="Test Dialogue", start_node_id="n1",
                       nodes={"n1": DialogueNode(id="n1", type=DialogueNodeType.TEXT, content="Hi")})
    await db.create_dialogue_tree(project.id, tree)
    trees = await db.list_dialogue_trees(project.id)
    assert len(trees) == 1
    assert trees[0].name == "Test Dialogue"


async def test_create_and_get_quest_graph(db):
    project = Project(name="Test", genre=GameGenre.RPG)
    await db.create_project(project)
    from models.quest_graph import QuestGraph, QuestNode, QuestNodeType
    graph = QuestGraph(name="Test Quest", start_node_id="n1",
                      nodes={"n1": QuestNode(id="n1", type=QuestNodeType.START, name="Start")})
    await db.create_quest_graph(project.id, graph)
    graphs = await db.list_quest_graphs(project.id)
    assert len(graphs) == 1
    assert graphs[0].name == "Test Quest"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_storage.py -v
# Expected: NEW tests FAIL
```

- [ ] **Step 3: Add DialogueTreeRow and QuestGraphRow to database.py**

Add SQLAlchemy models and CRUD methods for dialogue trees and quest graphs.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_storage.py -v
# Expected: all passed
```

- [ ] **Step 5: Commit**

```bash
git add src/NarrativeForge/Engine/storage/database.py tests/unit/test_storage.py
git commit -m "feat: add dialogue tree and quest graph storage CRUD"
```

---

## Task 6: Dialogue & Quest API Endpoints

**Covers:** [S10]

**Files:**
- Create: `src/NarrativeForge/Engine/api/dialogues.py`
- Create: `src/NarrativeForge/Engine/api/quests.py`
- Modify: `src/NarrativeForge/Engine/main.py`
- Modify: `tests/unit/test_api.py`

**Interfaces:**
- Consumes: DialogueTree, QuestGraph, InkParser from previous tasks
- Produces: REST endpoints for dialogue tree and quest graph CRUD + generation

- [ ] **Step 1: Write failing tests**

Add to existing `tests/unit/test_api.py`:

```python
async def test_create_dialogue_tree(client):
    proj = await client.post("/api/projects", json={"name": "Test", "genre": "fantasy"})
    pid = proj.json()["id"]
    response = await client.post(f"/api/projects/{pid}/dialogues", json={
        "name": "Village Elder Dialogue",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Village Elder Dialogue"
    assert "id" in data


async def test_list_dialogue_trees(client):
    proj = await client.post("/api/projects", json={"name": "Test", "genre": "fantasy"})
    pid = proj.json()["id"]
    await client.post(f"/api/projects/{pid}/dialogues", json={"name": "Dialogue 1"})
    await client.post(f"/api/projects/{pid}/dialogues", json={"name": "Dialogue 2"})
    response = await client.get(f"/api/projects/{pid}/dialogues")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_parse_ink_dialogue(client):
    script = """=== start ===
NPC: Hello!
+ [Hi] -> END
"""
    response = await client.post("/api/dialogues/parse", json={
        "script": script,
        "type": "dialogue",
    })
    assert response.status_code == 200
    data = response.json()
    assert "tree" in data


async def test_create_quest_graph(client):
    proj = await client.post("/api/projects", json={"name": "Test", "genre": "fantasy"})
    pid = proj.json()["id"]
    response = await client.post(f"/api/projects/{pid}/quests", json={
        "name": "Dragon Hunt",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Dragon Hunt"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_api.py -v
# Expected: NEW tests FAIL — 404
```

- [ ] **Step 3: Implement api/dialogues.py**

Create router with CRUD endpoints for dialogue trees and Ink parse endpoint.

- [ ] **Step 4: Implement api/quests.py**

Create router with CRUD endpoints for quest graphs and Ink parse endpoint.

- [ ] **Step 5: Update main.py to register new routers**

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_api.py -v
# Expected: all passed
```

- [ ] **Step 7: Commit**

```bash
git add src/NarrativeForge/Engine/api/dialogues.py src/NarrativeForge/Engine/api/quests.py src/NarrativeForge/Engine/main.py tests/unit/test_api.py
git commit -m "feat: add dialogue tree and quest graph API endpoints with Ink parsing"
```

---

## Task 7: AI Node Generation

**Covers:** [S8]

**Files:**
- Modify: `src/NarrativeForge/Engine/agents/dialogue_agent.py`
- Modify: `src/NarrativeForge/Engine/agents/quest_agent.py`
- Create: `tests/unit/test_node_generation.py`

**Interfaces:**
- Consumes: DialogueTree, QuestGraph, BaseAgent framework
- Produces: generate_next_node() methods on agents

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_node_generation.py
import pytest
from agents.dialogue_agent import DialogueAgent
from agents.quest_agent import QuestAgent
from agents.base import AgentContext, AgentResult
from ai_providers.base import AIProvider
from models.project import Project, GameGenre
from models.story_bible import StoryBible
from models.dialogue_tree import DialogueTree
from models.quest_graph import QuestGraph
from memory.graph_store import NarrativeGraph


class FakeProvider(AIProvider):
    def __init__(self):
        self.name = "fake"

    async def complete(self, messages, temperature=0.7, max_tokens=4096):
        import json
        return json.dumps({
            "id": "new_node",
            "type": "text",
            "content": "Generated text",
            "next_node_id": "",
        })

    async def stream(self, messages, temperature=0.7, max_tokens=4096):
        yield "test"


def make_dialogue_context():
    project = Project(name="Test", genre=GameGenre.FANTASY)
    sb = StoryBible(project_id=project.id)
    graph = NarrativeGraph.from_story_bible(sb)
    tree = DialogueTree(start_node_id="n1")
    return AgentContext(
        project=project, story_bible=sb, graph=graph,
        user_request="Generate next dialogue node",
        generation_params={"tree": tree.model_dump()},
        previous_results=[], locked_elements=set(),
    )


def make_quest_context():
    project = Project(name="Test", genre=GameGenre.FANTASY)
    sb = StoryBible(project_id=project.id)
    graph = NarrativeGraph.from_story_bible(sb)
    quest_graph = QuestGraph(start_node_id="n1")
    return AgentContext(
        project=project, story_bible=sb, graph=graph,
        user_request="Generate next quest node",
        generation_params={"quest_graph": quest_graph.model_dump()},
        previous_results=[], locked_elements=set(),
    )


async def test_dialogue_agent_generates_node():
    agent = DialogueAgent(FakeProvider())
    result = await agent.generate_next_node(make_dialogue_context())
    assert isinstance(result, AgentResult)
    assert "node" in result.metadata


async def test_quest_agent_generates_node():
    agent = QuestAgent(FakeProvider())
    result = await agent.generate_next_node(make_quest_context())
    assert isinstance(result, AgentResult)
    assert "node" in result.metadata
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_node_generation.py -v
# Expected: FAIL — AttributeError
```

- [ ] **Step 3: Add generate_next_node() to DialogueAgent**

Add method that builds a prompt for single node generation, calls provider, parses response.

- [ ] **Step 4: Add generate_next_node() to QuestAgent**

Add method that builds a prompt for single quest node generation, calls provider, parses response.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/unit/test_node_generation.py -v
# Expected: 2 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/NarrativeForge/Engine/agents/dialogue_agent.py src/NarrativeForge/Engine/agents/quest_agent.py tests/unit/test_node_generation.py
git commit -m "feat: add iterative node generation to DialogueAgent and QuestAgent"
```

---

## Task 8: E2E Integration Tests

**Covers:** [S11]

**Files:**
- Modify: `tests/integration/test_e2e.py`

**Interfaces:**
- Consumes: All previous tasks
- Produces: Extended E2E tests for dialogue trees and quest graphs

- [ ] **Step 1: Add E2E tests**

```python
async def test_dialogue_tree_workflow(client):
    # Create project
    proj = await client.post("/api/projects", json={"name": "Dialogue Test", "genre": "fantasy"})
    pid = proj.json()["id"]

    # Create dialogue tree
    tree_resp = await client.post(f"/api/projects/{pid}/dialogues", json={"name": "Village Elder"})
    tree_id = tree_resp.json()["id"]

    # Parse Ink script
    script = """=== start ===
NPC: Welcome, adventurer!
+ [Tell me about quests] -> quests
+ [Goodbye] -> END

=== quests ===
NPC: We need help with the dragon!
-> END
"""
    parse_resp = await client.post("/api/dialogues/parse", json={"script": script, "type": "dialogue"})
    assert parse_resp.status_code == 200

    # Cleanup
    await client.delete(f"/api/dialogues/{tree_id}")
    await client.delete(f"/api/projects/{pid}")


async def test_quest_graph_workflow(client):
    proj = await client.post("/api/projects", json={"name": "Quest Test", "genre": "rpg"})
    pid = proj.json()["id"]

    # Create quest graph
    graph_resp = await client.post(f"/api/projects/{pid}/quests", json={"name": "Dragon Hunt"})
    graph_id = graph_resp.json()["id"]

    # Parse Ink quest script
    script = """=== start ===
# name: Dragon Hunt
# description: Defeat the dragon
-> objective

=== objective ===
# objective: Travel to the cave
-> reward

=== reward ===
# xp: 500
# gold: 200
-> END
"""
    parse_resp = await client.post("/api/quests/parse", json={"script": script, "type": "quest"})
    assert parse_resp.status_code == 200

    # Cleanup
    await client.delete(f"/api/quests/{graph_id}")
    await client.delete(f"/api/projects/{pid}")
```

- [ ] **Step 2: Run full test suite**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/ -v
# Expected: ~200 tests pass
```

- [ ] **Step 3: Run linter**

```bash
python -m ruff check .
# Expected: no errors
```

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_e2e.py
git commit -m "feat: add E2E tests for dialogue tree and quest graph workflows"
```
