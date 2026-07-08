"""ImportManager: detect file format and import Ink/Yarn content into DialogueTree."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from NarrativeForge.Engine.models.dialogue_tree import DialogueTree
from NarrativeForge.Engine.scripting.ink_parser import InkParser
from NarrativeForge.Engine.scripting.yarn_parser import YarnParser

_FORMAT_MAP: dict[str, Literal["ink", "yarn"]] = {
    ".ink": "ink",
    ".yarn": "yarn",
}

SUPPORTED_EXTENSIONS = tuple(_FORMAT_MAP.keys())


class ImportManager:
    """Detects dialogue format from a file extension and parses content into a DialogueTree."""

    def __init__(self) -> None:
        self._ink = InkParser()
        self._yarn = YarnParser()

    @staticmethod
    def detect_format(path: str | Path) -> Literal["ink", "yarn"]:
        """Return ``"ink"`` or ``"yarn"`` based on file extension.

        Raises ``ValueError`` for unsupported extensions.
        """
        ext = Path(path).suffix.lower()
        fmt = _FORMAT_MAP.get(ext)
        if fmt is None:
            raise ValueError(
                f"Unsupported extension {ext!r}. Expected one of: {SUPPORTED_EXTENSIONS}"
            )
        return fmt

    def import_file(self, path: str | Path) -> DialogueTree:
        """Read a file, detect its format, parse it, and return the DialogueTree."""
        p = Path(path)
        fmt = self.detect_format(p)
        content = p.read_text(encoding="utf-8")
        if fmt == "ink":
            tree = self._ink.parse_dialogue(content)
        else:
            tree = self._yarn.parse(content)
        tree.name = p.stem
        return tree
