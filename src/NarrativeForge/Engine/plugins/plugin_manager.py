import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any

from NarrativeForge.Engine.plugins.plugin_info import PluginInfo, PluginType


class PluginManager:
    def __init__(self, plugins_dir: str | Path | None = None) -> None:
        self._plugins: dict[str, PluginInfo] = {}
        self._plugins_dir = Path(plugins_dir) if plugins_dir else Path("plugins")

    def discover(self) -> list[PluginInfo]:
        discovered: list[PluginInfo] = []
        discovered.extend(self._discover_entry_points())
        discovered.extend(self._discover_file_based())
        return discovered

    def _discover_entry_points(self) -> list[PluginInfo]:
        results: list[PluginInfo] = []
        try:
            for dist in importlib.metadata.distributions():
                eps = dist.entry_points
                for ep in eps:
                    if ep.group == "narrativeforge.plugins":
                        try:
                            plugin_cls = ep.load()
                            info = PluginInfo(
                                name=ep.name,
                                description=getattr(plugin_cls, "__doc__", "") or "",
                                entry_point=f"{ep.group}:{ep.name}",
                            )
                            results.append(info)
                        except Exception:
                            continue
        except Exception:
            pass
        return results

    def _discover_file_based(self) -> list[PluginInfo]:
        results: list[PluginInfo] = []
        if not self._plugins_dir.is_dir():
            return results
        for child in self._plugins_dir.iterdir():
            if not child.is_dir():
                continue
            manifest = child / "plugin.json"
            if not manifest.is_file():
                continue
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                info = PluginInfo(
                    name=data.get("name", child.name),
                    version=data.get("version", "0.1.0"),
                    description=data.get("description", ""),
                    author=data.get("author", ""),
                    plugin_type=PluginType(data.get("plugin_type", "misc")),
                    entry_point=data.get("entry_point", ""),
                )
                results.append(info)
            except (json.JSONDecodeError, ValueError):
                continue
        return results

    def register(self, plugin: PluginInfo) -> None:
        self._plugins[plugin.name] = plugin

    def load(self, plugin_name: str) -> Any:
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise KeyError(f"Plugin '{plugin_name}' not registered")
        if not plugin.enabled:
            raise ValueError(f"Plugin '{plugin_name}' is disabled")
        if plugin.instance is not None:
            return plugin.instance
        if plugin.entry_point:
            module_path, _, attr = plugin.entry_point.partition(":")
            mod = importlib.import_module(module_path)
            if attr:
                plugin.instance = getattr(mod, attr)()
            else:
                plugin.instance = mod
        return plugin.instance

    def validate(self, plugin: PluginInfo) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not plugin.name or not plugin.name.strip():
            errors.append("Plugin name is required")
        if not plugin.entry_point or not plugin.entry_point.strip():
            errors.append("Plugin entry_point is required")
        if not isinstance(plugin.plugin_type, PluginType):
            errors.append("Invalid plugin_type")
        if not plugin.version or not plugin.version.strip():
            errors.append("Plugin version is required")
        return len(errors) == 0, errors

    def get_plugins(self) -> dict[str, PluginInfo]:
        return dict(self._plugins)
