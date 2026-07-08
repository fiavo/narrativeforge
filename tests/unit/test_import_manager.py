from pathlib import Path

import pytest

from NarrativeForge.Engine.importing import ImportManager


INK_CONTENT = """\
=== greeting ===
Hello there.
-> END
"""

YARN_CONTENT = """\
title: Greeting
---
Hello there.
===
"""


class TestDetectFormat:
    def test_ink_extension(self):
        assert ImportManager.detect_format("dialogue.ink") == "ink"

    def test_yarn_extension(self):
        assert ImportManager.detect_format("dialogue.yarn") == "yarn"

    def test_unsupported_extension_raises(self):
        with pytest.raises(ValueError, match="Unsupported extension"):
            ImportManager.detect_format("dialogue.txt")


class TestImportFile:
    def test_import_ink(self, tmp_path: Path):
        f = tmp_path / "test.ink"
        f.write_text(INK_CONTENT, encoding="utf-8")
        mgr = ImportManager()
        tree = mgr.import_file(f)
        assert tree.name == "test"
        assert len(tree.nodes) >= 1

    def test_import_yarn(self, tmp_path: Path):
        f = tmp_path / "test.yarn"
        f.write_text(YARN_CONTENT, encoding="utf-8")
        mgr = ImportManager()
        tree = mgr.import_file(f)
        assert tree.name == "test"
        assert len(tree.nodes) >= 1

    def test_import_unknown_extension_raises(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        mgr = ImportManager()
        with pytest.raises(ValueError, match="Unsupported extension"):
            mgr.import_file(f)
