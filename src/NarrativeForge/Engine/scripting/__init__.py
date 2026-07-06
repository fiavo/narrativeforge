from NarrativeForge.Engine.scripting.variables import InkVariableStore
from NarrativeForge.Engine.scripting.conditions import InkConditionEvaluator
from NarrativeForge.Engine.scripting.functions import InkFunctionRegistry

__all__ = [
    "InkVariableStore",
    "InkConditionEvaluator",
    "InkFunctionRegistry",
]


def __getattr__(name: str):
    if name == "InkParser":
        from NarrativeForge.Engine.scripting.ink_parser import InkParser
        return InkParser
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
