from NarrativeForge.Engine.models.quest_graph import (
    QuestNodeType,
    QuestNode,
    QuestCondition,
    QuestEdge,
    QuestStateTracker,
    QuestGraph,
)


def test_quest_node_type_enum():
    assert QuestNodeType.START == "start"
    assert QuestNodeType.OBJECTIVE == "objective"
    assert QuestNodeType.BRANCH == "branch"
    assert QuestNodeType.CONDITION == "condition"
    assert QuestNodeType.REWARD == "reward"
    assert QuestNodeType.FAIL == "fail"
    assert QuestNodeType.END == "end"


def test_quest_node_creation():
    node = QuestNode(id="n1", type=QuestNodeType.START, name="Quest Start")
    assert node.id == "n1"
    assert node.type == QuestNodeType.START
    assert node.name == "Quest Start"
    assert node.objectives == []
    assert node.rewards == {}


def test_quest_condition_creation():
    cond = QuestCondition(expression="has_sword == true", true_node_id="n2")
    assert cond.expression == "has_sword == true"
    assert cond.true_node_id == "n2"
    assert cond.false_node_id == ""


def test_quest_edge_creation():
    edge = QuestEdge(source_id="n1", target_id="n2", weight=0.5)
    assert edge.source_id == "n1"
    assert edge.target_id == "n2"
    assert edge.condition == ""
    assert edge.weight == 0.5


def test_quest_state_tracker():
    tracker = QuestStateTracker()
    assert tracker.get("status") is None
    tracker.set("status", "active")
    assert tracker.get("status") == "active"
    assert tracker.get("missing", default="none") == "none"


def test_quest_state_tracker_is_complete():
    tracker = QuestStateTracker()
    assert tracker.is_complete() is False
    tracker.set("step1", True)
    assert tracker.is_complete() is True
    tracker.set("step2", False)
    assert tracker.is_complete() is False
    tracker.set("step2", True)
    assert tracker.is_complete() is True


def test_quest_graph_creation():
    graph = QuestGraph(name="Main Quest", start_node_id="n1")
    assert graph.name == "Main Quest"
    assert graph.start_node_id == "n1"
    assert graph.nodes == {}
    assert graph.edges == []


def test_quest_graph_add_node_and_edge():
    graph = QuestGraph(name="Test Quest", start_node_id="n1")
    node1 = QuestNode(id="n1", type=QuestNodeType.START, name="Start")
    node2 = QuestNode(id="n2", type=QuestNodeType.END, name="Finish")
    graph.nodes["n1"] = node1
    graph.nodes["n2"] = node2
    edge = QuestEdge(source_id="n1", target_id="n2")
    graph.edges.append(edge)

    assert "n1" in graph.nodes
    assert "n2" in graph.nodes
    assert len(graph.edges) == 1
    assert graph.edges[0].source_id == "n1"
    assert graph.edges[0].target_id == "n2"
