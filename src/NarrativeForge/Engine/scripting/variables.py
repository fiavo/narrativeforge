from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


class InkVariableStore:
    """Manages story variables with set/get/observe pattern."""

    def __init__(self) -> None:
        self._variables: dict[str, Any] = {}
        self._observers: dict[str, list[Callable[[str, Any, Any], None]]] = defaultdict(list)

    def set(self, name: str, value: Any) -> None:
        old = self._variables.get(name)
        self._variables[name] = value
        if old != value:
            for callback in self._observers.get(name, []):
                callback(name, old, value)

    def get(self, name: str, default: Any = None) -> Any:
        return self._variables.get(name, default)

    def observe(self, name: str, callback: Callable[[str, Any, Any], None]) -> None:
        self._observers[name].append(callback)

    def has(self, name: str) -> bool:
        return name in self._variables

    def delete(self, name: str) -> None:
        self._variables.pop(name, None)

    def clear(self) -> None:
        self._variables.clear()
        self._observers.clear()

    def all_names(self) -> list[str]:
        return list(self._variables.keys())

    def to_dict(self) -> dict[str, Any]:
        return dict(self._variables)
