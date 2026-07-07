from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PluginType(str, Enum):
    AGENT = "agent"
    PROVIDER = "provider"
    TOOL = "tool"
    MISC = "misc"


@dataclass
class PluginInfo:
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    plugin_type: PluginType = PluginType.MISC
    entry_point: str = ""
    instance: Any = None
    enabled: bool = True
