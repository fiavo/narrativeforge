"""YarnSpinner-compatible parser for dialogue trees.

Supports: title headers, options/shortcuts, variables, commands, inline links.
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
from NarrativeForge.Engine.scripting.variables import InkVariableStore

_TITLE_RE = re.compile(r"^title:\s*(.+)$")
_SEPARATOR_RE = re.compile(r"^---\s*$")
_END_RE = re.compile(r"^===\s*$")
_SHORTCUT_RE = re.compile(r"^->\s*(.+)$")
_INLINE_LINK_RE = re.compile(r"\[\[(.+?)\|(.+?)\]\]")
_COMMAND_RE = re.compile(r"^<<(.+?)>>$")
_IF_RE = re.compile(r"^<<if\s+(.+?)>>$")
_ELSE_RE = re.compile(r"^<<else>>$")
_ENDIF_RE = re.compile(r"^<<endif>>$")
_SET_RE = re.compile(r"^<<set\s+(\w+)\s*=\s*(.+?)>>$")
_DECLARE_RE = re.compile(r"^<<declare\s+(\w+)\s*=\s*(.+?)>>$")
_COMMENT_RE = re.compile(r"^\s*//")
_BLANK_RE = re.compile(r"^\s*$")


def _uuid() -> str:
    return str(uuid.uuid4())


class YarnParser:
    """Parses YarnSpinner-format scripts into DialogueTree structures."""

    def parse(self, script: str) -> DialogueTree:
        nodes_raw = self._parse_nodes(script)
        if not nodes_raw:
            return DialogueTree(start_node_id="", name="")

        node_ids: dict[str, str] = {name: _uuid() for name in nodes_raw}
        nodes: dict[str, DialogueNode] = {}
        edges: list[DialogueEdge] = []
        variables = InkVariableStore()

        for name, lines in nodes_raw.items():
            node_id = node_ids[name]
            i = 0

            while i < len(lines):
                line = lines[i].rstrip()

                if _COMMENT_RE.match(line) or _BLANK_RE.match(line):
                    i += 1
                    continue

                m = _DECLARE_RE.match(line)
                if m:
                    var_name = m.group(1)
                    var_val = self._coerce(m.group(2).strip())
                    variables.set(var_name, var_val)
                    i += 1
                    continue

                m = _SET_RE.match(line)
                if m:
                    var_name = m.group(1)
                    var_val = self._coerce(m.group(2).strip())
                    variables.set(var_name, var_val)
                    i += 1
                    continue

                m = _SHORTCUT_RE.match(line)
                if m:
                    target = m.group(1).strip()
                    if node_id not in nodes:
                        nodes[node_id] = DialogueNode(id=node_id, type=DialogueNodeType.CHOICE)
                    target_id = node_ids.get(target, target)
                    nodes[node_id].choices.append(
                        DialogueChoice(text=target, next_node_id=target_id)
                    )
                    edges.append(
                        DialogueEdge(source_id=node_id, target_id=target_id, label=target)
                    )
                    i += 1
                    continue

                inline_match = _INLINE_LINK_RE.search(line)
                if inline_match:
                    text = inline_match.group(1)
                    target = inline_match.group(2)
                    if node_id not in nodes:
                        nodes[node_id] = DialogueNode(id=node_id, type=DialogueNodeType.CHOICE)
                    target_id = node_ids.get(target, target)
                    nodes[node_id].choices.append(
                        DialogueChoice(text=text, next_node_id=target_id)
                    )
                    edges.append(
                        DialogueEdge(source_id=node_id, target_id=target_id, label=text)
                    )
                    i += 1
                    continue

                if_line = _IF_RE.match(line)
                if if_line:
                    if node_id not in nodes:
                        nodes[node_id] = DialogueNode(id=node_id, type=DialogueNodeType.TEXT)
                    expr = if_line.group(1)
                    true_id = _uuid()
                    false_id = _uuid()
                    nodes[node_id].conditions.append(
                        DialogueCondition(
                            expression=expr,
                            true_node_id=true_id,
                            false_node_id=false_id,
                        )
                    )
                    nodes[node_id].type = DialogueNodeType.CONDITION

                    i += 1
                    true_lines: list[str] = []
                    while i < len(lines):
                        tl = lines[i].rstrip()
                        if _ELSE_RE.match(tl) or _ENDIF_RE.match(tl) or _TITLE_RE.match(tl):
                            break
                        if not _COMMENT_RE.match(tl) and not _BLANK_RE.match(tl):
                            true_lines.append(tl)
                        i += 1

                    nodes[true_id] = DialogueNode(
                        id=true_id,
                        type=DialogueNodeType.TEXT,
                        content="\n".join(true_lines) if true_lines else "",
                    )

                    if i < len(lines) and _ELSE_RE.match(lines[i].rstrip()):
                        i += 1
                        false_lines: list[str] = []
                        while i < len(lines):
                            fl = lines[i].rstrip()
                            if _ENDIF_RE.match(fl) or _TITLE_RE.match(fl):
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
                        nodes[false_id] = DialogueNode(id=false_id, type=DialogueNodeType.END)

                    if i < len(lines) and _ENDIF_RE.match(lines[i].rstrip()):
                        i += 1
                    continue

                m = _COMMAND_RE.match(line)
                if m:
                    cmd = m.group(1).strip()
                    if node_id not in nodes:
                        nodes[node_id] = DialogueNode(id=node_id, type=DialogueNodeType.TEXT)
                    if not nodes[node_id].content:
                        nodes[node_id].content = f"<<{cmd}>>"
                    i += 1
                    continue

                if node_id not in nodes:
                    nodes[node_id] = DialogueNode(id=node_id, type=DialogueNodeType.TEXT)
                node = nodes[node_id]
                if node.content:
                    node.content += "\n" + line
                else:
                    node.content = line
                i += 1

            if node_id not in nodes:
                nodes[node_id] = DialogueNode(id=node_id, type=DialogueNodeType.TEXT, content="")

        first_name = next(iter(nodes_raw))
        start_id = node_ids[first_name]

        return DialogueTree(
            start_node_id=start_id,
            nodes=nodes,
            edges=edges,
            variables=variables,
        )

    @staticmethod
    def _parse_nodes(script: str) -> dict[str, list[str]]:
        """Split script into ``{title: [lines]}`` preserving order."""
        nodes: dict[str, list[str]] = {}
        current_title: str | None = None
        in_body = False
        body_lines: list[str] = []

        for raw_line in script.splitlines():
            tm = _TITLE_RE.match(raw_line)
            if tm:
                if current_title and body_lines is not None:
                    nodes[current_title] = body_lines
                current_title = tm.group(1).strip()
                body_lines = []
                in_body = False
                continue

            if current_title is not None:
                if _SEPARATOR_RE.match(raw_line):
                    in_body = True
                    continue
                if _END_RE.match(raw_line):
                    nodes[current_title] = body_lines
                    current_title = None
                    in_body = False
                    body_lines = []
                    continue

                if in_body:
                    body_lines.append(raw_line)

        if current_title and body_lines is not None:
            nodes[current_title] = body_lines

        return nodes

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
