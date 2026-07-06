from NarrativeForge.Engine.models.dialogue_tree import (
    DialogueNodeType,
    DialogueNode,
    DialogueChoice,
    DialogueCondition,
    DialogueEdge,
    DialogueTree,
)


def test_dialogue_node_types():
    assert DialogueNodeType.TEXT == "text"
    assert DialogueNodeType.CHOICE == "choice"
    assert DialogueNodeType.END == "end"


def test_dialogue_node_creation():
    node = DialogueNode(id="n1", type=DialogueNodeType.TEXT, content="Hello!")
    assert node.id == "n1"
    assert node.content == "Hello!"


def test_dialogue_choice_creation():
    choice = DialogueChoice(text="Tell me more", next_node_id="n2")
    assert choice.text == "Tell me more"
    assert choice.condition == ""


def test_dialogue_condition_creation():
    cond = DialogueCondition(expression="has_key == true", true_node_id="n3")
    assert cond.expression == "has_key == true"
    assert cond.false_node_id == ""


def test_dialogue_edge_creation():
    edge = DialogueEdge(source_id="n1", target_id="n2")
    assert edge.source_id == "n1"
    assert edge.target_id == "n2"


def test_dialogue_tree_creation():
    tree = DialogueTree(start_node_id="n1")
    assert tree.start_node_id == "n1"
    assert tree.nodes == {}


def test_dialogue_tree_add_node():
    tree = DialogueTree(start_node_id="n1")
    node = DialogueNode(id="n1", type=DialogueNodeType.TEXT, content="Hi")
    tree.nodes["n1"] = node
    assert "n1" in tree.nodes


def test_dialogue_tree_has_variables():
    tree = DialogueTree(start_node_id="n1")
    assert tree.variables is not None
    tree.variables.set("flag", True)
    assert tree.variables.get("flag") is True
