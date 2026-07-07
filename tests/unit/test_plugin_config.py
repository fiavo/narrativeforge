import json

import pytest

from NarrativeForge.Engine.plugins.plugin_config import PluginConfig


def test_plugin_config_enable_disable():
    config = PluginConfig()
    config.set_enabled("test-plugin", False)
    assert config.is_enabled("test-plugin") is False
    assert config.is_enabled("other-plugin") is True


def test_plugin_config_save_load(tmp_path):
    config_path = tmp_path / "plugins.json"
    config = PluginConfig(config_path)
    config.set_enabled("test", False)
    config.save()

    loaded = PluginConfig(config_path)
    loaded.load()
    assert loaded.is_enabled("test") is False


def test_plugin_config_list_disabled():
    config = PluginConfig()
    config.set_enabled("a", False)
    config.set_enabled("b", True)
    config.set_enabled("c", False)

    disabled = config.get_disabled()
    assert "a" in disabled
    assert "c" in disabled
    assert "b" not in disabled
