from NarrativeForge.Engine.scripting.yarn_parser import YarnParser


class TestYarnParserNodes:
    def test_single_node(self):
        parser = YarnParser()
        script = """\
title: Greeting
---
Hello there.
===
"""
        tree = parser.parse(script)
        assert len(tree.nodes) >= 1
        first = tree.nodes[tree.start_node_id]
        assert "Hello there." in first.content

    def test_multiple_nodes(self):
        parser = YarnParser()
        script = """\
title: Intro
---
Welcome to the world.
===
title: Farewell
---
Goodbye, friend.
===
"""
        tree = parser.parse(script)
        assert len(tree.nodes) >= 2
        ids = set(tree.nodes.keys())
        assert tree.start_node_id in ids


class TestYarnParserOptions:
    def test_shortcut_options(self):
        parser = YarnParser()
        script = """\
title: Start
---
-> Left
-> Right
===
title: Left
---
You went left.
===
title: Right
---
You went right.
===
"""
        tree = parser.parse(script)
        start_node = tree.nodes[tree.start_node_id]
        assert start_node.type.value == "choice"
        assert len(start_node.choices) == 2
        assert start_node.choices[0].text == "Left"
        assert start_node.choices[1].text == "Right"

    def test_inline_links(self):
        parser = YarnParser()
        script = """\
title: Start
---
[[Go to cave|Cave]]
[[Go to forest|Forest]]
===
title: Cave
---
It is dark.
===
title: Forest
---
The trees are tall.
===
"""
        tree = parser.parse(script)
        start_node = tree.nodes[tree.start_node_id]
        assert start_node.type.value == "choice"
        assert len(start_node.choices) == 2
        assert start_node.choices[0].text == "Go to cave"
        assert start_node.choices[1].text == "Go to forest"


class TestYarnParserVariables:
    def test_declare_and_set(self):
        parser = YarnParser()
        script = """\
title: Start
---
<<declare gold = 100>>
<<set name = "Hero">>
<<set alive = true>>
Your adventure begins.
===
"""
        tree = parser.parse(script)
        assert tree.variables.get("gold") == 100
        assert tree.variables.get("name") == "Hero"
        assert tree.variables.get("alive") is True


class TestYarnParserCommands:
    def test_if_condition(self):
        parser = YarnParser()
        script = """\
title: Start
---
<<declare has_key = true>>
<<if has_key>>
The door opens.
<<else>>
The door is locked.
<<endif>>
===
"""
        tree = parser.parse(script)
        cond_nodes = [n for n in tree.nodes.values() if n.type.value == "condition"]
        assert len(cond_nodes) >= 1
        assert cond_nodes[0].conditions[0].expression == "has_key"
