import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from NarrativeForge.Engine.plugins.plugin_info import PluginInfo, PluginType
from NarrativeForge.Engine.plugins.plugin_manager import PluginManager


def test_plugin_info_defaults():
    info = PluginInfo(name="test")
    assert info.name == "test"
    assert info.version == "0.1.0"
    assert info.enabled is True
    assert info.plugin_type == PluginType.MISC


def test_register_and_get_plugins():
    pm = PluginManager()
    pm.register(PluginInfo(name="a"))
    pm.register(PluginInfo(name="b"))
    plugins = pm.get_plugins()
    assert set(plugins.keys()) == {"a", "b"}


def test_load_disabled_plugin_raises():
    pm = PluginManager()
    pm.register(PluginInfo(name="disabled", enabled=False))
    with pytest.raises(ValueError, match="disabled"):
        pm.load("disabled")


def test_discover_file_based(tmp_path):
    plugin_dir = tmp_path / "plugins" / "sample"
    plugin_dir.mkdir(parents=True)
    manifest = {
        "name": "sample",
        "version": "1.0.0",
        "description": "A sample plugin",
        "author": "Tester",
        "plugin_type": "agent",
        "entry_point": "sample.module",
    }
    (plugin_dir / "plugin.json").write_text(json.dumps(manifest))
    pm = PluginManager(plugins_dir=tmp_path / "plugins")
    discovered = pm.discover()
    assert any(p.name == "sample" for p in discovered)
    sample = next(p for p in discovered if p.name == "sample")
    assert sample.version == "1.0.0"
    assert sample.plugin_type == PluginType.AGENT


def test_discover_entry_points():
    pm = PluginManager()
    with patch(
        "importlib.metadata.distributions", return_value=[]
    ):
        discovered = pm._discover_entry_points()
    assert discovered == []


def test_load_nonexistent_plugin_raises():
    pm = PluginManager()
    with pytest.raises(KeyError, match="not registered"):
        pm.load("nonexistent")
