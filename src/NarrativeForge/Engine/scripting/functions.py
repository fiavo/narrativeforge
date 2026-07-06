from __future__ import annotations

import random
from typing import Any, Callable


class InkFunctionRegistry:
    """Registers and calls named functions, including built-ins."""

    def __init__(self) -> None:
        self._functions: dict[str, Callable[..., Any]] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        self._functions["RANDOM"] = self._builtin_random
        self._functions["CONTAINS"] = self._builtin_contains
        self._functions["LENGTH"] = self._builtin_length

    @staticmethod
    def _builtin_random(*args: Any) -> Any:
        if len(args) == 2:
            low, high = args
            return random.randint(int(low), int(high))
        if len(args) == 1:
            return random.choice(args[0])
        raise ValueError("RANDOM expects 1 or 2 arguments")

    @staticmethod
    def _builtin_contains(collection: Any, item: Any) -> bool:
        return item in collection

    @staticmethod
    def _builtin_length(collection: Any) -> int:
        return len(collection)

    def register(self, name: str, func: Callable[..., Any]) -> None:
        self._functions[name.upper()] = func

    def call(self, name: str, *args: Any) -> Any:
        func = self._functions.get(name.upper())
        if func is None:
            raise KeyError(f"Unknown function: {name}")
        return func(*args)

    def has(self, name: str) -> bool:
        return name.upper() in self._functions

    def list_functions(self) -> list[str]:
        return sorted(self._functions.keys())
