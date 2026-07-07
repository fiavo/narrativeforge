import json
from pathlib import Path
from typing import Optional


class PluginConfig:
    def __init__(self, config_path: Optional[Path] = None):
        self._config_path = config_path or Path("plugin_config.json")
        self._disabled: set[str] = set()
        self.load()

    def load(self) -> None:
        if self._config_path.exists():
            with open(self._config_path) as f:
                data = json.load(f)
            self._disabled = set(data.get("disabled", []))

    def save(self) -> None:
        with open(self._config_path, "w") as f:
            json.dump({"disabled": sorted(self._disabled)}, f, indent=2)

    def is_enabled(self, plugin_name: str) -> bool:
        return plugin_name not in self._disabled

    def set_enabled(self, plugin_name: str, enabled: bool) -> None:
        if enabled:
            self._disabled.discard(plugin_name)
        else:
            self._disabled.add(plugin_name)

    def get_disabled(self) -> list[str]:
        return sorted(self._disabled)
