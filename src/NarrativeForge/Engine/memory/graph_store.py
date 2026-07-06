from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from uuid import UUID


@dataclass
class GraphNode:
    id: UUID
    type: str
    name: str
    properties: dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    target_id: UUID
    relationship: str
    weight: float = 1.0


class NarrativeGraph:
    def __init__(self) -> None:
        self._nodes: dict[UUID, GraphNode] = {}
        self._adjacency: dict[UUID, list[GraphEdge]] = {}

    @classmethod
    def from_story_bible(cls, sb) -> NarrativeGraph:
        from NarrativeForge.Engine.models.story_bible import StoryBible
        from NarrativeForge.Engine.models.character import Character
        from NarrativeForge.Engine.models.location import Location
        from NarrativeForge.Engine.models.story_bible import Faction
        from NarrativeForge.Engine.models.timeline import TimelineEvent
        from NarrativeForge.Engine.models.story_bible import LoreEntry

        assert isinstance(sb, StoryBible)
        graph = cls()

        for char_id, char in sb.characters.items():
            graph.add_node(GraphNode(
                id=char_id,
                type="character",
                name=char.name,
                properties={"role": char.role.value, "alive": char.is_alive},
            ))

        for loc_id, loc in sb.locations.items():
            graph.add_node(GraphNode(
                id=loc_id,
                type="location",
                name=loc.name,
                properties={"type": loc.type},
            ))

        for faction_id, faction in sb.factions.items():
            graph.add_node(GraphNode(
                id=faction_id,
                type="faction",
                name=faction.name,
                properties={"goals": faction.goals},
            ))

        for event in sb.timeline:
            graph.add_node(GraphNode(
                id=event.id,
                type="event",
                name=event.title,
                properties={"timestamp": event.timestamp, "order": event.order},
            ))

        for lore_id, lore in sb.lore_entries.items():
            graph.add_node(GraphNode(
                id=lore_id,
                type="lore",
                name=lore.title,
                properties={"category": lore.category},
            ))

        for rel in sb.relationships:
            source_id = UUID(rel.source_id)
            target_id = UUID(rel.target_id)
            graph.add_edge(source_id, GraphEdge(
                target_id=target_id,
                relationship=rel.type.value,
                weight=rel.strength / 100.0,
            ))
            if rel.is_bidirectional:
                graph.add_edge(target_id, GraphEdge(
                    target_id=source_id,
                    relationship=rel.type.value,
                    weight=rel.strength / 100.0,
                ))

        for char_id, char in sb.characters.items():
            for peer_id, label in char.relationships.items():
                if peer_id in sb.characters:
                    graph.add_edge(char_id, GraphEdge(
                        target_id=peer_id,
                        relationship=label,
                        weight=1.0,
                    ))

        for loc_id, loc in sb.locations.items():
            for connected_id in loc.connected_to:
                if connected_id in sb.locations:
                    graph.add_edge(loc_id, GraphEdge(
                        target_id=connected_id,
                        relationship="connected_to",
                        weight=1.0,
                    ))

        for faction_id, faction in sb.factions.items():
            for member_id in faction.members:
                if member_id in sb.characters:
                    graph.add_edge(faction_id, GraphEdge(
                        target_id=member_id,
                        relationship="member",
                        weight=1.0,
                    ))
            for ally_id in faction.allies:
                graph.add_edge(faction_id, GraphEdge(
                    target_id=ally_id,
                    relationship="ally",
                    weight=0.8,
                ))
            for enemy_id in faction.enemies:
                graph.add_edge(faction_id, GraphEdge(
                    target_id=enemy_id,
                    relationship="enemy",
                    weight=0.8,
                ))

        for event in sb.timeline:
            for participant_id in event.participants:
                graph.add_edge(event.id, GraphEdge(
                    target_id=participant_id,
                    relationship="participant",
                    weight=1.0,
                ))
            if event.location_id and event.location_id in sb.locations:
                graph.add_edge(event.id, GraphEdge(
                    target_id=event.location_id,
                    relationship="occurred_at",
                    weight=1.0,
                ))

        return graph

    def add_node(self, node: GraphNode) -> None:
        self._nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = []

    def add_edge(self, source_id: UUID, edge: GraphEdge) -> None:
        if source_id not in self._adjacency:
            self._adjacency[source_id] = []
        self._adjacency[source_id].append(edge)

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return sum(len(edges) for edges in self._adjacency.values())

    def get_node(self, node_id: UUID) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: UUID) -> list[GraphNode]:
        neighbors = []
        for edge in self._adjacency.get(node_id, []):
            node = self._nodes.get(edge.target_id)
            if node:
                neighbors.append(node)
        return neighbors

    def get_relationships(self, node_id: UUID) -> list[GraphEdge]:
        return list(self._adjacency.get(node_id, []))

    def find_path(self, start_id: UUID, end_id: UUID) -> Optional[list[UUID]]:
        if start_id == end_id:
            return [start_id]
        if start_id not in self._nodes or end_id not in self._nodes:
            return None

        visited: set[UUID] = {start_id}
        queue: deque[list[UUID]] = deque([[start_id]])

        while queue:
            path = queue.popleft()
            current = path[-1]

            for edge in self._adjacency.get(current, []):
                if edge.target_id == end_id:
                    return path + [end_id]
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append(path + [edge.target_id])

        return None
