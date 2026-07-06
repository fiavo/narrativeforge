"""Ink-compatible parser for dialogue trees and quest graphs.

Supports: knots, choices, diverts, variables, conditions, tags, comments, end.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from NarrativeForge.Engine.models.dialogue_tree import (
    DialogueChoice,
    DialogueCondition,
    DialogueEdge,
    DialogueNode,
    DialogueNodeType,
    DialogueTree,
)
from NarrativeForge.Engine.models.quest_graph import (
    QuestCondition,
    QuestEdge,
    QuestNode,
    QuestNodeType,
    QuestGraph,
)
from NarrativeForge.Engine.scripting.variables import InkVariableStore

_KNOT_RE = re.compile(r"^===\s*(\w+)\s*===\s*$")
_CHOICE_RE = re.compile(r"^[+*]\s*\[(.+?)\](?:\s*\{(.+?)\})?(?:\s*->\s*(\w+))?\s*$")
_DIVERT_RE = re.compile(r"^->\s*(\w+)\s*$")
_VAR_RE = re.compile(r"^~\s*(\w+)\s*=\s*(.+)$")
_TAG_RE = re.compile(r"^#\s*(.+)$")
_IF_RE = re.compile(r"^~?\s*if\s*\{(.+?)\}\s*$")
_ELSE_RE = re.compile(r"^~?\s*else\s*$")
_COMMENT_RE = re.compile(r"^\s*//")
_BLANK_RE = re.compile(r"^\s*$")


def _uuid() -> str:
    return str(uuid.uuid4())


class InkParser:
    """Parses Ink-format scripts into DialogueTree or QuestGraph structures."""

    # ── public API ──────────────────────────────────────────────────────

    def parse_dialogue(self, script: str) -> DialogueTree:
        knots = self._parse_script(script)
        if not knots:
            return DialogueTree(start_node_id="", name="")

        nodes: dict[str, DialogueNode] = {}
        edges: list[DialogueEdge] = []
        variables = InkVariableStore()

        knot_ids: dict[str, str] = {name: _uuid() for name in knots}

        for name, lines in knots.items():
            node_id = knot_ids[name]
            current_id = node_id
            pending_choices: list[DialogueChoice] = []
            content_lines: list[str] = []
            pending_divert: str = ""
            i = 0

            while i < len(lines):
                line = lines[i].rstrip()

                if _COMMENT_RE.match(line) or _BLANK_RE.match(line):
                    i += 1
                    continue

                m = _VAR_RE.match(line)
                if m:
                    var_name, var_val = m.group(1), m.group(2).strip()
                    variables.set(var_name, self._coerce(var_val))
                    i += 1
                    continue

                m = _CHOICE_RE.match(line)
                if m:
                    if content_lines:
                        self._ensure_node(nodes, current_id, content_lines, pending_divert)
                        if pending_divert and pending_divert in knot_ids:
                            edges.append(
                                DialogueEdge(
                                    source_id=current_id,
                                    target_id=knot_ids[pending_divert],
                                    label="",
                                )
                            )
                        current_id = _uuid()
                        content_lines = []
                        pending_divert = ""

                    text = m.group(1)
                    condition = m.group(2) or ""
                    inline_divert = m.group(3) or ""
                    next_id = _uuid()
                    pending_choices.append(
                        DialogueChoice(
                            text=text,
                            next_node_id=next_id,
                            condition=condition,
                        )
                    )
                    i += 1

                    choice_lines: list[str] = []
                    while i < len(lines):
                        cl = lines[i].rstrip()
                        if _CHOICE_RE.match(cl) or _KNOT_RE.match(cl) or _IF_RE.match(cl):
                            break
                        if not _COMMENT_RE.match(cl) and not _BLANK_RE.match(cl):
                            choice_lines.append(cl)
                        i += 1

                    choice_divert = inline_divert
                    filtered_choice: list[str] = []
                    for cline in choice_lines:
                        dm = _DIVERT_RE.match(cline)
                        if dm:
                            choice_divert = dm.group(1)
                        else:
                            filtered_choice.append(cline)

                    choice_node = DialogueNode(
                        id=next_id,
                        type=DialogueNodeType.TEXT,
                        content="\n".join(filtered_choice) if filtered_choice else text,
                    )
                    if choice_divert and choice_divert in knot_ids:
                        choice_node.next_node_id = knot_ids[choice_divert]
                        edges.append(
                            DialogueEdge(
                                source_id=next_id,
                                target_id=knot_ids[choice_divert],
                                label="",
                            )
                        )
                    nodes[next_id] = choice_node
                    continue

                m = _IF_RE.match(line)
                if m:
                    self._ensure_node(nodes, current_id, content_lines, pending_divert)
                    if pending_divert and pending_divert in knot_ids:
                        edges.append(
                            DialogueEdge(
                                source_id=current_id,
                                target_id=knot_ids[pending_divert],
                                label="",
                            )
                        )

                    expr = m.group(1)
                    true_id = _uuid()
                    false_id = _uuid()
                    nodes[current_id].conditions.append(
                        DialogueCondition(
                            expression=expr,
                            true_node_id=true_id,
                            false_node_id=false_id,
                        )
                    )
                    nodes[current_id].type = DialogueNodeType.CONDITION

                    i += 1
                    true_lines: list[str] = []
                    while i < len(lines):
                        tl = lines[i].rstrip()
                        if _ELSE_RE.match(tl) or _KNOT_RE.match(tl):
                            break
                        if not _COMMENT_RE.match(tl) and not _BLANK_RE.match(tl):
                            true_lines.append(tl)
                        i += 1

                    nodes[true_id] = DialogueNode(
                        id=true_id,
                        type=DialogueNodeType.TEXT,
                        content="\n".join(true_lines) if true_lines else "",
                    )

                    if _ELSE_RE.match(lines[i].rstrip()) if i < len(lines) else False:
                        i += 1
                        false_lines: list[str] = []
                        while i < len(lines):
                            fl = lines[i].rstrip()
                            if _KNOT_RE.match(fl) or _CHOICE_RE.match(fl):
                                break
                            if not _COMMENT_RE.match(fl) and not _BLANK_RE.match(fl):
                                false_lines.append(fl)
                            i += 1
                        nodes[false_id] = DialogueNode(
                            id=false_id,
                            type=DialogueNodeType.TEXT,
                            content="\n".join(false_lines) if false_lines else "",
                        )
                    else:
                        nodes[false_id] = DialogueNode(
                            id=false_id,
                            type=DialogueNodeType.END,
                        )

                    content_lines = []
                    pending_divert = ""
                    current_id = _uuid()
                    continue

                m = _DIVERT_RE.match(line)
                if m:
                    pending_divert = m.group(1)
                    i += 1
                    continue

                m = _TAG_RE.match(line)
                if m:
                    i += 1
                    continue

                content_lines.append(line)
                i += 1

            if pending_choices:
                self._ensure_node(nodes, current_id, content_lines, pending_divert)
                if pending_divert and pending_divert in knot_ids:
                    edges.append(
                        DialogueEdge(
                            source_id=current_id,
                            target_id=knot_ids[pending_divert],
                            label="",
                        )
                    )
                nodes[node_id].type = DialogueNodeType.CHOICE
                nodes[node_id].choices = pending_choices
            else:
                self._ensure_node(nodes, current_id, content_lines, pending_divert)
                if pending_divert and pending_divert in knot_ids:
                    edges.append(
                        DialogueEdge(
                            source_id=current_id,
                            target_id=knot_ids[pending_divert],
                            label="",
                        )
                    )

        first_knot = next(iter(knots))
        start_id = knot_ids[first_knot]

        tree = DialogueTree(
            start_node_id=start_id,
            nodes=nodes,
            edges=edges,
            variables=variables,
        )
        return tree

    def parse_quest(self, script: str) -> QuestGraph:
        knots = self._parse_script(script)
        if not knots:
            return QuestGraph(start_node_id="", name="")

        nodes: dict[str, QuestNode] = {}
        edges: list[QuestEdge] = []
        variables = InkVariableStore()

        knot_ids: dict[str, str] = {name: _uuid() for name in knots}
        knot_names = list(knots.keys())

        for name, lines in knots.items():
            node_id = knot_ids[name]
            is_start = name == knot_names[0]

            quest_type = QuestNodeType.START if is_start else QuestNodeType.OBJECTIVE
            next_ids: list[str] = []
            description_lines: list[str] = []
            conditions: list[QuestCondition] = []
            pending_divert: str = ""
            rewards: dict[str, str] = {}

            i = 0
            while i < len(lines):
                line = lines[i].rstrip()

                if _COMMENT_RE.match(line) or _BLANK_RE.match(line):
                    i += 1
                    continue

                m = _VAR_RE.match(line)
                if m:
                    var_name, var_val = m.group(1), m.group(2).strip()
                    variables.set(var_name, self._coerce(var_val))
                    i += 1
                    continue

                m = _IF_RE.match(line)
                if m:
                    expr = m.group(1)
                    true_id = _uuid()
                    false_id = _uuid()
                    conditions.append(
                        QuestCondition(
                            expression=expr,
                            true_node_id=true_id,
                            false_node_id=false_id,
                        )
                    )
                    nodes[true_id] = QuestNode(
                        id=true_id,
                        type=QuestNodeType.OBJECTIVE,
                        name=f"{name}_true",
                    )
                    nodes[false_id] = QuestNode(
                        id=false_id,
                        type=QuestNodeType.FAIL,
                        name=f"{name}_false",
                    )
                    i += 1
                    continue

                m = _CHOICE_RE.match(line)
                if m:
                    choice_text = m.group(1)
                    if choice_text.lower() in ("reward", "完成", "complete"):
                        quest_type = QuestNodeType.REWARD
                        rewards["description"] = choice_text
                    else:
                        quest_type = QuestNodeType.BRANCH
                    i += 1
                    continue

                m = _DIVERT_RE.match(line)
                if m:
                    pending_divert = m.group(1)
                    i += 1
                    continue

                m = _TAG_RE.match(line)
                if m:
                    i += 1
                    continue

                description_lines.append(line)
                i += 1

            if pending_divert:
                if pending_divert.upper() == "END" and quest_type != QuestNodeType.START:
                    quest_type = QuestNodeType.END
                elif pending_divert in knot_ids:
                    next_ids.append(knot_ids[pending_divert])

            nodes[node_id] = QuestNode(
                id=node_id,
                type=quest_type,
                name=name,
                description="\n".join(description_lines),
                rewards=rewards,
                conditions=conditions,
                next_node_ids=next_ids,
            )

            for nid in next_ids:
                edges.append(
                    QuestEdge(
                        source_id=node_id,
                        target_id=nid,
                    )
                )

            for cond in conditions:
                edges.append(
                    QuestEdge(
                        source_id=node_id,
                        target_id=cond.true_node_id,
                        condition=cond.expression,
                    )
                )

        first_knot = knot_names[0]
        start_id = knot_ids[first_knot]

        return QuestGraph(
            name="",
            start_node_id=start_id,
            nodes=nodes,
            edges=edges,
            variables=variables,
        )

    # ── internals ───────────────────────────────────────────────────────

    @staticmethod
    def _parse_script(script: str) -> dict[str, list[str]]:
        """Split script into ``{knot_name: [lines]}`` preserving order."""
        knots: dict[str, list[str]] = {}
        current_knot = "_preamble"
        knots[current_knot] = []

        for raw_line in script.splitlines():
            m = _KNOT_RE.match(raw_line)
            if m:
                current_knot = m.group(1)
                knots[current_knot] = []
            else:
                knots[current_knot].append(raw_line)

        if not knots["_preamble"]:
            del knots["_preamble"]
        return knots

    @staticmethod
    def _ensure_node(
        nodes: dict[str, DialogueNode],
        node_id: str,
        content_lines: list[str],
        divert: str,
    ) -> None:
        if node_id not in nodes:
            nodes[node_id] = DialogueNode(id=node_id, type=DialogueNodeType.TEXT)
        node = nodes[node_id]
        if content_lines:
            node.content = "\n".join(content_lines)
        if divert and divert.upper() == "END":
            node.type = DialogueNodeType.END
            node.next_node_id = ""
        elif divert:
            node.next_node_id = divert

    @staticmethod
    def _coerce(value: str) -> Any:
        v = value.strip()
        if v.lower() == "true":
            return True
        if v.lower() == "false":
            return False
        try:
            return int(v)
        except ValueError:
            pass
        try:
            return float(v)
        except ValueError:
            pass
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            return v[1:-1]
        return v
