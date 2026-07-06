from __future__ import annotations

import operator
from typing import Any

from NarrativeForge.Engine.scripting.variables import InkVariableStore

_OPERATORS = {
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
}


class InkConditionEvaluator:
    """Evaluates simple boolean expressions against a variable store."""

    def __init__(self, variables: InkVariableStore) -> None:
        self._variables = variables

    def evaluate(self, expression: str) -> bool:
        expr = expression.strip()

        if expr.startswith("!"):
            return not self.evaluate(expr[1:])

        if "||" in expr:
            parts = expr.split("||", 1)
            return self.evaluate(parts[0]) or self.evaluate(parts[1])

        if "&&" in expr:
            parts = expr.split("&&", 1)
            return self.evaluate(parts[0]) and self.evaluate(parts[1])

        for op_str, op_func in _OPERATORS.items():
            if op_str in expr:
                left_str, right_str = expr.split(op_str, 1)
                left = self._resolve(left_str.strip())
                right = self._resolve(right_str.strip())
                return op_func(left, right)

        val = self._resolve(expr)
        return bool(val)

    def _resolve(self, token: str) -> Any:
        token = token.strip()

        if token.startswith('"') and token.endswith('"'):
            return token[1:-1]
        if token.startswith("'") and token.endswith("'"):
            return token[1:-1]

        if token.lower() == "true":
            return True
        if token.lower() == "false":
            return False

        try:
            return int(token)
        except ValueError:
            pass
        try:
            return float(token)
        except ValueError:
            pass

        return self._variables.get(token)
