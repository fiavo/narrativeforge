from NarrativeForge.Engine.scripting.variables import InkVariableStore
from NarrativeForge.Engine.scripting.conditions import InkConditionEvaluator
from NarrativeForge.Engine.scripting.functions import InkFunctionRegistry


class TestInkVariableStore:
    def test_set_get_and_observer(self):
        store = InkVariableStore()
        observed: list[tuple] = []
        store.observe("hp", lambda n, o, v: observed.append((n, o, v)))

        store.set("hp", 100)
        assert store.get("hp") == 100
        assert observed == [("hp", None, 100)]

        store.set("hp", 80)
        assert store.get("hp") == 80
        assert len(observed) == 2

    def test_no_observer_on_same_value(self):
        store = InkVariableStore()
        observed: list[tuple] = []
        store.observe("x", lambda n, o, v: observed.append((n, o, v)))
        store.set("x", 5)
        store.set("x", 5)
        assert len(observed) == 1

    def test_delete_and_clear(self):
        store = InkVariableStore()
        store.set("a", 1)
        store.set("b", 2)
        store.delete("a")
        assert store.get("a") is None
        assert store.get("b") == 2
        store.clear()
        assert store.all_names() == []


class TestInkConditionEvaluator:
    def test_equality_and_comparison(self):
        store = InkVariableStore()
        store.set("score", 50)
        ev = InkConditionEvaluator(store)

        assert ev.evaluate("score == 50") is True
        assert ev.evaluate("score != 50") is False
        assert ev.evaluate("score > 40") is True
        assert ev.evaluate("score < 40") is False
        assert ev.evaluate("score >= 50") is True
        assert ev.evaluate("score <= 30") is False

    def test_logical_operators(self):
        store = InkVariableStore()
        store.set("a", True)
        store.set("b", False)
        ev = InkConditionEvaluator(store)

        assert ev.evaluate("a && a") is True
        assert ev.evaluate("a && b") is False
        assert ev.evaluate("b || a") is True
        assert ev.evaluate("b || b") is False

    def test_negation_and_literal(self):
        store = InkVariableStore()
        store.set("flag", False)
        ev = InkConditionEvaluator(store)

        assert ev.evaluate("!flag") is True
        assert ev.evaluate("true") is True
        assert ev.evaluate("false") is False
        assert ev.evaluate('"hello" == "hello"') is True


class TestInkFunctionRegistry:
    def test_builtin_random_range(self):
        reg = InkFunctionRegistry()
        for _ in range(50):
            result = reg.call("RANDOM", 1, 10)
            assert 1 <= result <= 10

    def test_builtin_contains_and_length(self):
        reg = InkFunctionRegistry()
        assert reg.call("CONTAINS", [1, 2, 3], 2) is True
        assert reg.call("CONTAINS", [1, 2, 3], 5) is False
        assert reg.call("LENGTH", "hello") == 5
        assert reg.call("LENGTH", [1, 2, 3]) == 3

    def test_custom_function_registration(self):
        reg = InkFunctionRegistry()
        reg.register("double", lambda x: x * 2)
        assert reg.call("double", 5) == 10
        assert reg.has("DOUBLE") is True
        assert "DOUBLE" in reg.list_functions()
