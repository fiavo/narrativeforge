from NarrativeForge.Engine.scripting.ink_parser import InkParser


class TestInkParserKnots:
    def test_single_knot(self):
        parser = InkParser()
        script = """\
=== greeting ===
Hello there.
"""
        tree = parser.parse_dialogue(script)
        assert len(tree.nodes) >= 1
        first = tree.nodes[tree.start_node_id]
        assert "Hello there." in first.content

    def test_multiple_knots(self):
        parser = InkParser()
        script = """\
=== intro ===
Welcome to the world.

=== farewell ===
Goodbye, friend.
"""
        tree = parser.parse_dialogue(script)
        assert len(tree.nodes) >= 2
        ids = set(tree.nodes.keys())
        assert tree.start_node_id in ids


class TestInkParserChoices:
    def test_choices_create_choice_node(self):
        parser = InkParser()
        script = """\
=== start ===
Choose wisely.
+ [Go left] -> left_room
+ [Go right] -> right_room

=== left_room ===
You went left.

=== right_room ===
You went right.
"""
        tree = parser.parse_dialogue(script)
        start_node = tree.nodes[tree.start_node_id]
        assert start_node.type.value == "choice"
        assert len(start_node.choices) == 2
        assert start_node.choices[0].text == "Go left"
        assert start_node.choices[1].text == "Go right"

    def test_choices_with_condition(self):
        parser = InkParser()
        script = """\
=== start ===
What do you do?
+ [Attack] {has_sword}
+ [Run]
"""
        tree = parser.parse_dialogue(script)
        start_node = tree.nodes[tree.start_node_id]
        assert len(start_node.choices) == 2
        assert start_node.choices[0].condition == "has_sword"
        assert start_node.choices[1].condition == ""


class TestInkParserDiverts:
    def test_divert_creates_edge(self):
        parser = InkParser()
        script = """\
=== start ===
You enter the cave.
-> cave_inside

=== cave_inside ===
It's dark inside.
"""
        tree = parser.parse_dialogue(script)
        assert len(tree.edges) >= 1
        edge = tree.edges[0]
        assert edge.source_id in tree.nodes
        assert edge.target_id in tree.nodes

    def test_divert_to_end(self):
        parser = InkParser()
        script = """\
=== finale ===
The story concludes here.
-> END
"""
        tree = parser.parse_dialogue(script)
        finale_id = [k for k, v in tree.nodes.items() if v.content == "The story concludes here."][
            0
        ]
        assert tree.nodes[finale_id].type.value == "end"


class TestInkParserVariables:
    def test_variables_parsed(self):
        parser = InkParser()
        script = """\
=== start ===
~ health = 100
~ name = "Hero"
~ alive = true
Your adventure begins.
"""
        tree = parser.parse_dialogue(script)
        assert tree.variables.get("health") == 100
        assert tree.variables.get("name") == "Hero"
        assert tree.variables.get("alive") is True


class TestInkParserCommentsAndTags:
    def test_comments_ignored(self):
        parser = InkParser()
        script = """\
=== start ===
// This is a comment
Real text here.
// Another comment
"""
        tree = parser.parse_dialogue(script)
        node = tree.nodes[tree.start_node_id]
        assert "comment" not in node.content.lower()
        assert "Real text here." in node.content

    def test_tags_ignored(self):
        parser = InkParser()
        script = """\
=== start ===
# speaker: Narrator
# mood: calm
Some dialogue.
"""
        tree = parser.parse_dialogue(script)
        node = tree.nodes[tree.start_node_id]
        assert "speaker" not in node.content
        assert "Some dialogue." in node.content


class TestInkParserConditions:
    def test_if_condition_creates_condition_node(self):
        parser = InkParser()
        script = """\
=== start ===
~ has_key = true
if {has_key}
  The door opens.
  -> victory
else
  The door is locked.

=== victory ===
You win!
"""
        tree = parser.parse_dialogue(script)
        cond_nodes = [n for n in tree.nodes.values() if n.type.value == "condition"]
        assert len(cond_nodes) >= 1
        assert cond_nodes[0].conditions[0].expression == "has_key"


class TestInkParserQuestGraph:
    def test_parse_quest_basic(self):
        parser = InkParser()
        script = """\
=== rescue_princess ===
Find and rescue the princess.
-> END
"""
        graph = parser.parse_quest(script)
        assert graph.start_node_id in graph.nodes
        start = graph.nodes[graph.start_node_id]
        assert start.type.value == "start"
        assert "Find and rescue the princess." in start.description

    def test_parse_quest_with_divert(self):
        parser = InkParser()
        script = """\
=== collect_herbs ===
Gather 5 herbs from the forest.
-> deliver_herbs

=== deliver_herbs ===
Bring herbs to the alchemist.
-> END
"""
        graph = parser.parse_quest(script)
        assert len(graph.edges) >= 1
        deliver_id = [k for k, v in graph.nodes.items() if v.name == "deliver_herbs"][0]
        assert graph.nodes[deliver_id].type.value == "end"
