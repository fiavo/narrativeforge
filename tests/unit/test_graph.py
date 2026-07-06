from uuid import uuid4

from NarrativeForge.Engine.models import (
    Character,
    CharacterRole,
    Location,
    StoryBible,
    Relationship,
    RelationshipType,
    Faction,
    TimelineEvent,
)
from NarrativeForge.Engine.memory import GraphNode, GraphEdge, NarrativeGraph


def _make_character(name: str, role=CharacterRole.Supporting) -> Character:
    return Character(name=name, role=role)


def _make_bible() -> tuple[StoryBible, dict]:
    hero_id = uuid4()
    villain_id = uuid4()
    castle_id = uuid4()
    forest_id = uuid4()
    guild_id = uuid4()
    war_id = uuid4()

    hero = _make_character("Hero", CharacterRole.Protagonist)
    villain = _make_character("Villain", CharacterRole.Antagonist)
    castle = Location(name="Castle", type="Structure")
    forest = Location(name="Dark Forest", type="Natural", connected_to=[castle_id])
    guild = Faction(name="Thieves Guild", members=[hero_id], allies=[], enemies=[villain_id])
    war = TimelineEvent(title="The Great War", participants=[hero_id, villain_id], location_id=castle_id)

    rel = Relationship(
        source_id=str(hero_id),
        target_id=str(villain_id),
        type=RelationshipType.Enemy,
        strength=80,
        is_bidirectional=True,
    )

    bible = StoryBible(
        project_id=uuid4(),
        characters={hero_id: hero, villain_id: villain},
        locations={castle_id: castle, forest_id: forest},
        factions={guild_id: guild},
        timeline=[war],
        relationships=[rel],
    )

    refs = {
        "hero_id": hero_id,
        "villain_id": villain_id,
        "castle_id": castle_id,
        "forest_id": forest_id,
        "guild_id": guild_id,
        "war_id": war.id,
    }
    return bible, refs


class TestBuildGraphFromBible:
    def test_builds_nodes_from_characters(self):
        bible, refs = _make_bible()
        graph = NarrativeGraph.from_story_bible(bible)

        hero = graph.get_node(refs["hero_id"])
        assert hero is not None
        assert hero.type == "character"
        assert hero.name == "Hero"
        assert hero.properties["role"] == "Protagonist"

    def test_builds_nodes_from_locations(self):
        bible, refs = _make_bible()
        graph = NarrativeGraph.from_story_bible(bible)

        castle = graph.get_node(refs["castle_id"])
        assert castle is not None
        assert castle.type == "location"
        assert castle.name == "Castle"

    def test_builds_nodes_from_factions(self):
        bible, refs = _make_bible()
        graph = NarrativeGraph.from_story_bible(bible)

        guild = graph.get_node(refs["guild_id"])
        assert guild is not None
        assert guild.type == "faction"
        assert guild.name == "Thieves Guild"

    def test_builds_edges_from_relationships(self):
        bible, refs = _make_bible()
        graph = NarrativeGraph.from_story_bible(bible)

        hero_edges = graph.get_relationships(refs["hero_id"])
        assert len(hero_edges) >= 1
        target_ids = [e.target_id for e in hero_edges]
        assert refs["villain_id"] in target_ids

    def test_bidirectional_relationship(self):
        bible, refs = _make_bible()
        graph = NarrativeGraph.from_story_bible(bible)

        villain_edges = graph.get_relationships(refs["villain_id"])
        target_ids = [e.target_id for e in villain_edges]
        assert refs["hero_id"] in target_ids


class TestNodeAndEdgeCounts:
    def test_node_count(self):
        bible, refs = _make_bible()
        graph = NarrativeGraph.from_story_bible(bible)
        assert graph.node_count() == 6

    def test_edge_count(self):
        bible, refs = _make_bible()
        graph = NarrativeGraph.from_story_bible(bible)
        assert graph.edge_count() > 0


class TestGetNeighbors:
    def test_hero_neighbors_include_villain(self):
        bible, refs = _make_bible()
        graph = NarrativeGraph.from_story_bible(bible)

        neighbors = graph.get_neighbors(refs["hero_id"])
        names = [n.name for n in neighbors]
        assert "Villain" in names

    def test_forest_connected_to_castle(self):
        bible, refs = _make_bible()
        graph = NarrativeGraph.from_story_bible(bible)

        neighbors = graph.get_neighbors(refs["forest_id"])
        names = [n.name for n in neighbors]
        assert "Castle" in names

    def test_nonexistent_node_returns_empty(self):
        graph = NarrativeGraph()
        assert graph.get_neighbors(uuid4()) == []


class TestFindPath:
    def test_path_between_connected_nodes(self):
        bible, refs = _make_bible()
        graph = NarrativeGraph.from_story_bible(bible)

        path = graph.find_path(refs["hero_id"], refs["villain_id"])
        assert path is not None
        assert path[0] == refs["hero_id"]
        assert path[-1] == refs["villain_id"]

    def test_path_returns_none_for_disconnected(self):
        graph = NarrativeGraph()
        a = uuid4()
        b = uuid4()
        graph.add_node(GraphNode(id=a, type="character", name="A"))
        graph.add_node(GraphNode(id=b, type="character", name="B"))
        assert graph.find_path(a, b) is None

    def test_path_same_node(self):
        node_id = uuid4()
        graph = NarrativeGraph()
        graph.add_node(GraphNode(id=node_id, type="character", name="Solo"))
        path = graph.find_path(node_id, node_id)
        assert path == [node_id]

    def test_path_through_intermediate(self):
        a, b, c = uuid4(), uuid4(), uuid4()
        graph = NarrativeGraph()
        graph.add_node(GraphNode(id=a, type="character", name="A"))
        graph.add_node(GraphNode(id=b, type="character", name="B"))
        graph.add_node(GraphNode(id=c, type="character", name="C"))
        graph.add_edge(a, GraphEdge(target_id=b, relationship="knows"))
        graph.add_edge(b, GraphEdge(target_id=c, relationship="knows"))

        path = graph.find_path(a, c)
        assert path is not None
        assert path == [a, b, c]

    def test_path_nonexistent_start(self):
        graph = NarrativeGraph()
        graph.add_node(GraphNode(id=uuid4(), type="x", name="X"))
        assert graph.find_path(uuid4(), uuid4()) is None
