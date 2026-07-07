import json
from pathlib import Path
from unittest.mock import patch

from NarrativeForge.Engine.ai_providers import discover_plugin_providers
from NarrativeForge.Engine.plugins.plugin_info import PluginInfo, PluginType


def test_plugin_provider_registers(tmp_path):
    plugin_dir = tmp_path / "plugins" / "my_provider"
    plugin_dir.mkdir(parents=True)
    manifest = {
        "name": "my_provider",
        "version": "1.0.0",
        "description": "A test provider plugin",
        "author": "Tester",
        "plugin_type": "provider",
        "entry_point": "my_provider.module:MyProvider",
    }
    (plugin_dir / "plugin.json").write_text(json.dumps(manifest))
    providers = discover_plugin_providers(plugins_dir=str(tmp_path / "plugins"))
    assert len(providers) == 1
    assert providers[0].name == "my_provider"
    assert providers[0].plugin_type == PluginType.PROVIDER
    assert providers[0].version == "1.0.0"


def test_plugin_provider_filters_non_providers(tmp_path):
    plugin_dir_agent = tmp_path / "plugins" / "agent_plugin"
    plugin_dir_agent.mkdir(parents=True)
    (plugin_dir_agent / "plugin.json").write_text(json.dumps({
        "name": "agent_plugin",
        "plugin_type": "agent",
        "entry_point": "agent_mod",
    }))
    plugin_dir_provider = tmp_path / "plugins" / "prov_plugin"
    plugin_dir_provider.mkdir(parents=True)
    (plugin_dir_provider / "plugin.json").write_text(json.dumps({
        "name": "prov_plugin",
        "plugin_type": "provider",
        "entry_point": "prov_mod",
    }))
    providers = discover_plugin_providers(plugins_dir=str(tmp_path / "plugins"))
    assert len(providers) == 1
    assert providers[0].name == "prov_plugin"
