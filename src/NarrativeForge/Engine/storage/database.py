import json
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    delete as sql_delete,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from NarrativeForge.Engine.models import (
    Character,
    CharacterRole,
    CharacterArc,
    DialogueExchange,
    DialogueLine,
    DialogueTree,
    DialogueNode,
    DialogueNodeType,
    DialogueEdge,
    DialogueChoice,
    DialogueCondition,
    Faction,
    GameGenre,
    Location,
    LoreEntry,
    PersonalityProfile,
    Project,
    Quest,
    QuestObjective,
    QuestPrerequisite,
    QuestReward,
    QuestGraph,
    QuestNode,
    QuestNodeType,
    QuestEdge,
    QuestCondition,
    StoryBible,
    TimelineEvent,
)


class Base(DeclarativeBase):
    pass


class ProjectRow(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    sub_genres = Column(Text, default="[]")
    target_audience = Column(String, default="")
    tone = Column(String, default="")
    themes = Column(Text, default="[]")
    story_bible_id = Column(String, nullable=True)
    settings = Column(Text, default="{}")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    characters = relationship("CharacterRow", back_populates="project", cascade="all, delete-orphan")
    locations = relationship("LocationRow", back_populates="project", cascade="all, delete-orphan")
    factions = relationship("FactionRow", back_populates="project", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEventRow", back_populates="project", cascade="all, delete-orphan")
    lore_entries = relationship("LoreEntryRow", back_populates="project", cascade="all, delete-orphan")

    def to_model(self) -> Project:
        return Project(
            id=UUID(self.id),
            name=self.name,
            genre=GameGenre(self.genre),
            sub_genres=[GameGenre(g) for g in json.loads(self.sub_genres)],
            target_audience=self.target_audience,
            tone=self.tone,
            themes=json.loads(self.themes),
            story_bible_id=UUID(self.story_bible_id) if self.story_bible_id else None,
            settings=json.loads(self.settings),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_model(cls, project: Project) -> "ProjectRow":
        return cls(
            id=str(project.id),
            name=project.name,
            genre=project.genre.value,
            sub_genres=json.dumps([g.value for g in project.sub_genres]),
            target_audience=project.target_audience,
            tone=project.tone,
            themes=json.dumps(project.themes),
            story_bible_id=str(project.story_bible_id) if project.story_bible_id else None,
            settings=json.dumps(project.settings),
            created_at=project.created_at,
            updated_at=project.updated_at,
        )


class CharacterRow(Base):
    __tablename__ = "characters"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    alias = Column(String, default="")
    role = Column(String, default=CharacterRole.Supporting.value)
    personality = Column(Text, default="{}")
    backstory = Column(String, default="")
    motivation = Column(String, default="")
    goals = Column(Text, default="[]")
    fears = Column(Text, default="[]")
    relationships = Column(Text, default="{}")
    arc = Column(Text, default="{}")
    dialogue_style = Column(String, default="")
    appearance = Column(String, default="")
    is_alive = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)

    project = relationship("ProjectRow", back_populates="characters")

    def to_model(self) -> Character:
        personality_data = json.loads(self.personality)
        arc_data = json.loads(self.arc)
        relationships_raw = json.loads(self.relationships)
        relationships = {UUID(k): v for k, v in relationships_raw.items()}

        return Character(
            id=UUID(self.id),
            name=self.name,
            alias=self.alias,
            role=CharacterRole(self.role),
            personality=PersonalityProfile(**personality_data),
            backstory=self.backstory,
            motivation=self.motivation,
            goals=json.loads(self.goals),
            fears=json.loads(self.fears),
            relationships=relationships,
            arc=CharacterArc(**arc_data),
            dialogue_style=self.dialogue_style,
            appearance=self.appearance,
            is_alive=self.is_alive,
            is_locked=self.is_locked,
        )

    @classmethod
    def from_model(cls, character: Character, project_id: UUID) -> "CharacterRow":
        return cls(
            id=str(character.id),
            project_id=str(project_id),
            name=character.name,
            alias=character.alias,
            role=character.role.value,
            personality=character.personality.model_dump_json(),
            backstory=character.backstory,
            motivation=character.motivation,
            goals=json.dumps(character.goals),
            fears=json.dumps(character.fears),
            relationships=json.dumps({str(k): v for k, v in character.relationships.items()}),
            arc=character.arc.model_dump_json(),
            dialogue_style=character.dialogue_style,
            appearance=character.appearance,
            is_alive=character.is_alive,
            is_locked=character.is_locked,
        )


class LocationRow(Base):
    __tablename__ = "locations"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, default="")
    description = Column(String, default="")
    connected_to = Column(Text, default="[]")
    inhabitants = Column(Text, default="[]")
    factions_present = Column(Text, default="[]")
    significance = Column(String, default="")
    is_locked = Column(Boolean, default=False)

    project = relationship("ProjectRow", back_populates="locations")

    def to_model(self) -> Location:
        return Location(
            id=UUID(self.id),
            name=self.name,
            type=self.type,
            description=self.description,
            connected_to=[UUID(u) for u in json.loads(self.connected_to)],
            inhabitants=[UUID(u) for u in json.loads(self.inhabitants)],
            factions_present=[UUID(u) for u in json.loads(self.factions_present)],
            significance=self.significance,
            is_locked=self.is_locked,
        )

    @classmethod
    def from_model(cls, location: Location, project_id: UUID) -> "LocationRow":
        return cls(
            id=str(location.id),
            project_id=str(project_id),
            name=location.name,
            type=location.type,
            description=location.description,
            connected_to=json.dumps([str(u) for u in location.connected_to]),
            inhabitants=json.dumps([str(u) for u in location.inhabitants]),
            factions_present=json.dumps([str(u) for u in location.factions_present]),
            significance=location.significance,
            is_locked=location.is_locked,
        )


class FactionRow(Base):
    __tablename__ = "factions"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    goals = Column(Text, default="[]")
    members = Column(Text, default="[]")
    allies = Column(Text, default="[]")
    enemies = Column(Text, default="[]")

    project = relationship("ProjectRow", back_populates="factions")

    def to_model(self) -> Faction:
        return Faction(
            id=UUID(self.id),
            name=self.name,
            description=self.description,
            goals=json.loads(self.goals),
            members=[UUID(u) for u in json.loads(self.members)],
            allies=[UUID(u) for u in json.loads(self.allies)],
            enemies=[UUID(u) for u in json.loads(self.enemies)],
        )

    @classmethod
    def from_model(cls, faction: Faction, project_id: UUID) -> "FactionRow":
        return cls(
            id=str(faction.id),
            project_id=str(project_id),
            name=faction.name,
            description=faction.description,
            goals=json.dumps(faction.goals),
            members=json.dumps([str(u) for u in faction.members]),
            allies=json.dumps([str(u) for u in faction.allies]),
            enemies=json.dumps([str(u) for u in faction.enemies]),
        )


class TimelineEventRow(Base):
    __tablename__ = "timeline_events"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    timestamp = Column(String, default="")
    participants = Column(Text, default="[]")
    location_id = Column(String, nullable=True)
    consequences = Column(Text, default="[]")
    order = Column(String, default="0")

    project = relationship("ProjectRow", back_populates="timeline_events")

    def to_model(self) -> TimelineEvent:
        from typing import Optional as Opt
        return TimelineEvent(
            id=UUID(self.id),
            title=self.title,
            description=self.description,
            timestamp=self.timestamp,
            participants=[UUID(u) for u in json.loads(self.participants)],
            location_id=UUID(self.location_id) if self.location_id else None,
            consequences=json.loads(self.consequences),
            order=int(self.order),
        )

    @classmethod
    def from_model(cls, event: TimelineEvent, project_id: UUID) -> "TimelineEventRow":
        return cls(
            id=str(event.id),
            project_id=str(project_id),
            title=event.title,
            description=event.description,
            timestamp=event.timestamp,
            participants=json.dumps([str(u) for u in event.participants]),
            location_id=str(event.location_id) if event.location_id else None,
            consequences=json.dumps(event.consequences),
            order=str(event.order),
        )


class LoreEntryRow(Base):
    __tablename__ = "lore_entries"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, default="")
    category = Column(String, default="")
    tags = Column(Text, default="[]")
    related_entries = Column(Text, default="[]")
    is_locked = Column(Boolean, default=False)

    project = relationship("ProjectRow", back_populates="lore_entries")

    def to_model(self) -> LoreEntry:
        return LoreEntry(
            id=UUID(self.id),
            title=self.title,
            content=self.content,
            category=self.category,
            tags=json.loads(self.tags),
            related_entries=[UUID(u) for u in json.loads(self.related_entries)],
            is_locked=self.is_locked,
        )

    @classmethod
    def from_model(cls, entry: LoreEntry, project_id: UUID) -> "LoreEntryRow":
        return cls(
            id=str(entry.id),
            project_id=str(project_id),
            title=entry.title,
            content=entry.content,
            category=entry.category,
            tags=json.dumps(entry.tags),
            related_entries=json.dumps([str(u) for u in entry.related_entries]),
            is_locked=entry.is_locked,
        )


class QuestRow(Base):
    __tablename__ = "quests"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    data_json = Column(Text, default="{}")

    def to_model(self) -> Quest:
        data = json.loads(self.data_json)
        return Quest(
            id=UUID(self.id),
            name=self.name,
            description=data.get("description", ""),
            objectives=[QuestObjective(**obj) for obj in data.get("objectives", [])],
            prerequisites=[QuestPrerequisite(**prep) for prep in data.get("prerequisites", [])],
            rewards=QuestReward(**data.get("rewards", {})),
            faction_id=UUID(data["faction_id"]) if data.get("faction_id") else None,
            is_main_quest=data.get("is_main_quest", False),
        )

    @classmethod
    def from_model(cls, quest: Quest, project_id: UUID) -> "QuestRow":
        data = {
            "description": quest.description,
            "objectives": [obj.model_dump(mode="json") for obj in quest.objectives],
            "prerequisites": [prep.model_dump(mode="json") for prep in quest.prerequisites],
            "rewards": quest.rewards.model_dump(mode="json"),
            "faction_id": str(quest.faction_id) if quest.faction_id else None,
            "is_main_quest": quest.is_main_quest,
        }
        return cls(
            id=str(quest.id),
            project_id=str(project_id),
            name=quest.name,
            data_json=json.dumps(data),
        )


class DialogueRow(Base):
    __tablename__ = "dialogues"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    exchange_id = Column(String, nullable=False)
    data_json = Column(Text, default="{}")

    def to_model(self) -> DialogueExchange:
        data = json.loads(self.data_json)
        return DialogueExchange(
            id=UUID(self.exchange_id),
            lines=[DialogueLine(**line) for line in data.get("lines", [])],
            context=data.get("context", ""),
            mood=data.get("mood", ""),
        )

    @classmethod
    def from_model(cls, exchange: DialogueExchange, project_id: UUID) -> "DialogueRow":
        data = {
            "lines": [line.model_dump(mode="json") for line in exchange.lines],
            "context": exchange.context,
            "mood": exchange.mood,
        }
        return cls(
            id=str(exchange.id),
            project_id=str(project_id),
            exchange_id=str(exchange.id),
            data_json=json.dumps(data),
        )


class DialogueTreeRow(Base):
    __tablename__ = "dialogue_trees"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    start_node_id = Column(String, default="")
    data_json = Column(Text, default="{}")

    def to_model(self) -> DialogueTree:
        data = json.loads(self.data_json)
        nodes = {
            k: DialogueNode(
                id=v["id"],
                type=DialogueNodeType(v["type"]),
                content=v.get("content", ""),
                choices=[DialogueChoice(**c) for c in v.get("choices", [])],
                conditions=[DialogueCondition(**c) for c in v.get("conditions", [])],
                variables_set=v.get("variables_set", {}),
                next_node_id=v.get("next_node_id", ""),
            )
            for k, v in data.get("nodes", {}).items()
        }
        edges = [DialogueEdge(**e) for e in data.get("edges", [])]
        variables = data.get("variables", {})

        from NarrativeForge.Engine.scripting.variables import InkVariableStore
        var_store = InkVariableStore()
        for name, value in variables.items():
            var_store.set(name, value)

        return DialogueTree(
            id=self.id,
            name=self.name,
            start_node_id=self.start_node_id,
            nodes=nodes,
            edges=edges,
            variables=var_store,
        )

    @classmethod
    def from_model(cls, tree: DialogueTree, project_id: UUID) -> "DialogueTreeRow":
        nodes_data = {}
        for k, node in tree.nodes.items():
            nodes_data[k] = {
                "id": node.id,
                "type": node.type.value,
                "content": node.content,
                "choices": [c.model_dump() for c in node.choices],
                "conditions": [c.model_dump() for c in node.conditions],
                "variables_set": node.variables_set,
                "next_node_id": node.next_node_id,
            }
        data = {
            "nodes": nodes_data,
            "edges": [e.model_dump() for e in tree.edges],
            "variables": tree.variables.to_dict(),
        }
        return cls(
            id=tree.id,
            project_id=str(project_id),
            name=tree.name,
            start_node_id=tree.start_node_id,
            data_json=json.dumps(data),
        )


class QuestGraphRow(Base):
    __tablename__ = "quest_graphs"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    start_node_id = Column(String, default="")
    data_json = Column(Text, default="{}")

    def to_model(self) -> QuestGraph:
        data = json.loads(self.data_json)
        nodes = {
            k: QuestNode(
                id=v["id"],
                type=QuestNodeType(v["type"]),
                name=v.get("name", ""),
                description=v.get("description", ""),
                objectives=v.get("objectives", []),
                rewards=v.get("rewards", {}),
                conditions=[QuestCondition(**c) for c in v.get("conditions", [])],
                next_node_ids=v.get("next_node_ids", []),
            )
            for k, v in data.get("nodes", {}).items()
        }
        edges = [QuestEdge(**e) for e in data.get("edges", [])]
        variables = data.get("variables", {})

        from NarrativeForge.Engine.scripting.variables import InkVariableStore
        var_store = InkVariableStore()
        for name, value in variables.items():
            var_store.set(name, value)

        from NarrativeForge.Engine.models.quest_graph import QuestStateTracker
        state = QuestStateTracker(data.get("state", {}))

        return QuestGraph(
            id=self.id,
            name=self.name,
            start_node_id=self.start_node_id,
            nodes=nodes,
            edges=edges,
            variables=var_store,
            state=state,
        )

    @classmethod
    def from_model(cls, graph: QuestGraph, project_id: UUID) -> "QuestGraphRow":
        nodes_data = {}
        for k, node in graph.nodes.items():
            nodes_data[k] = {
                "id": node.id,
                "type": node.type.value,
                "name": node.name,
                "description": node.description,
                "objectives": node.objectives,
                "rewards": node.rewards,
                "conditions": [c.model_dump() for c in node.conditions],
                "next_node_ids": node.next_node_ids,
            }
        data = {
            "nodes": nodes_data,
            "edges": [e.model_dump() for e in graph.edges],
            "variables": graph.variables.to_dict(),
            "state": graph.state._state,
        }
        return cls(
            id=graph.id,
            project_id=str(project_id),
            name=graph.name,
            start_node_id=graph.start_node_id,
            data_json=json.dumps(data),
        )


class Database:
    def __init__(self, db_url: str = "sqlite+aiosqlite:///:memory:"):
        self.db_url = db_url
        self.engine = create_async_engine(db_url)
        self._initialized = False

    async def init(self):
        if self._initialized:
            return
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._initialized = True

    async def close(self):
        await self.engine.dispose()

    async def create_project(self, project: Project) -> Project:
        await self.init()
        async with AsyncSession(self.engine) as session:
            row = ProjectRow.from_model(project)
            session.add(row)
            await session.commit()
            return project

    async def get_project(self, project_id: UUID) -> Project | None:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(ProjectRow).where(ProjectRow.id == str(project_id))
            )
            row = result.scalar_one_or_none()
            return row.to_model() if row else None

    async def list_projects(self) -> list[Project]:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(select(ProjectRow))
            return [row.to_model() for row in result.scalars().all()]

    async def delete_project(self, project_id: UUID) -> bool:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                sql_delete(ProjectRow).where(ProjectRow.id == str(project_id))
            )
            await session.commit()
            return result.rowcount > 0

    async def create_character(self, project_id: UUID, character: Character) -> Character:
        await self.init()
        async with AsyncSession(self.engine) as session:
            row = CharacterRow.from_model(character, project_id)
            session.add(row)
            await session.commit()
            return character

    async def get_character(self, character_id: UUID) -> Character | None:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(CharacterRow).where(CharacterRow.id == str(character_id))
            )
            row = result.scalar_one_or_none()
            return row.to_model() if row else None

    async def list_characters(self, project_id: UUID) -> list[Character]:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(CharacterRow).where(CharacterRow.project_id == str(project_id))
            )
            return [row.to_model() for row in result.scalars().all()]

    async def delete_character(self, character_id: UUID) -> bool:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                sql_delete(CharacterRow).where(CharacterRow.id == str(character_id))
            )
            await session.commit()
            return result.rowcount > 0

    async def create_location(self, project_id: UUID, location: Location) -> Location:
        await self.init()
        async with AsyncSession(self.engine) as session:
            row = LocationRow.from_model(location, project_id)
            session.add(row)
            await session.commit()
            return location

    async def get_location(self, location_id: UUID) -> Location | None:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(LocationRow).where(LocationRow.id == str(location_id))
            )
            row = result.scalar_one_or_none()
            return row.to_model() if row else None

    async def list_locations(self, project_id: UUID) -> list[Location]:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(LocationRow).where(LocationRow.project_id == str(project_id))
            )
            return [row.to_model() for row in result.scalars().all()]

    async def delete_location(self, location_id: UUID) -> bool:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                sql_delete(LocationRow).where(LocationRow.id == str(location_id))
            )
            await session.commit()
            return result.rowcount > 0

    async def create_faction(self, project_id: UUID, faction: Faction) -> Faction:
        await self.init()
        async with AsyncSession(self.engine) as session:
            row = FactionRow.from_model(faction, project_id)
            session.add(row)
            await session.commit()
            return faction

    async def get_faction(self, faction_id: UUID) -> Faction | None:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(FactionRow).where(FactionRow.id == str(faction_id))
            )
            row = result.scalar_one_or_none()
            return row.to_model() if row else None

    async def list_factions(self, project_id: UUID) -> list[Faction]:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(FactionRow).where(FactionRow.project_id == str(project_id))
            )
            return [row.to_model() for row in result.scalars().all()]

    async def delete_faction(self, faction_id: UUID) -> bool:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                sql_delete(FactionRow).where(FactionRow.id == str(faction_id))
            )
            await session.commit()
            return result.rowcount > 0

    async def create_timeline_event(self, project_id: UUID, event: TimelineEvent) -> TimelineEvent:
        await self.init()
        async with AsyncSession(self.engine) as session:
            row = TimelineEventRow.from_model(event, project_id)
            session.add(row)
            await session.commit()
            return event

    async def get_timeline_event(self, event_id: UUID) -> TimelineEvent | None:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(TimelineEventRow).where(TimelineEventRow.id == str(event_id))
            )
            row = result.scalar_one_or_none()
            return row.to_model() if row else None

    async def list_timeline_events(self, project_id: UUID) -> list[TimelineEvent]:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(TimelineEventRow).where(TimelineEventRow.project_id == str(project_id))
            )
            return [row.to_model() for row in result.scalars().all()]

    async def delete_timeline_event(self, event_id: UUID) -> bool:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                sql_delete(TimelineEventRow).where(TimelineEventRow.id == str(event_id))
            )
            await session.commit()
            return result.rowcount > 0

    async def create_lore_entry(self, project_id: UUID, entry: LoreEntry) -> LoreEntry:
        await self.init()
        async with AsyncSession(self.engine) as session:
            row = LoreEntryRow.from_model(entry, project_id)
            session.add(row)
            await session.commit()
            return entry

    async def get_lore_entry(self, entry_id: UUID) -> LoreEntry | None:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(LoreEntryRow).where(LoreEntryRow.id == str(entry_id))
            )
            row = result.scalar_one_or_none()
            return row.to_model() if row else None

    async def list_lore_entries(self, project_id: UUID) -> list[LoreEntry]:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(LoreEntryRow).where(LoreEntryRow.project_id == str(project_id))
            )
            return [row.to_model() for row in result.scalars().all()]

    async def delete_lore_entry(self, entry_id: UUID) -> bool:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                sql_delete(LoreEntryRow).where(LoreEntryRow.id == str(entry_id))
            )
            await session.commit()
            return result.rowcount > 0

    async def create_quest(self, project_id: UUID, quest: Quest) -> Quest:
        await self.init()
        async with AsyncSession(self.engine) as session:
            row = QuestRow.from_model(quest, project_id)
            session.add(row)
            await session.commit()
            return quest

    async def get_quest(self, project_id: UUID, quest_id: UUID) -> Quest | None:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(QuestRow).where(
                    QuestRow.id == str(quest_id),
                    QuestRow.project_id == str(project_id),
                )
            )
            row = result.scalar_one_or_none()
            return row.to_model() if row else None

    async def list_quests(self, project_id: UUID) -> list[Quest]:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(QuestRow).where(QuestRow.project_id == str(project_id))
            )
            return [row.to_model() for row in result.scalars().all()]

    async def create_dialogue(self, project_id: UUID, exchange: DialogueExchange) -> DialogueExchange:
        await self.init()
        async with AsyncSession(self.engine) as session:
            row = DialogueRow.from_model(exchange, project_id)
            session.add(row)
            await session.commit()
            return exchange

    async def list_dialogues(self, project_id: UUID) -> list[DialogueExchange]:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(DialogueRow).where(DialogueRow.project_id == str(project_id))
            )
            return [row.to_model() for row in result.scalars().all()]

    async def create_dialogue_tree(self, project_id: UUID, tree: DialogueTree) -> DialogueTree:
        await self.init()
        async with AsyncSession(self.engine) as session:
            row = DialogueTreeRow.from_model(tree, project_id)
            session.add(row)
            await session.commit()
            return tree

    async def get_dialogue_tree(self, tree_id: str) -> DialogueTree | None:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(DialogueTreeRow).where(DialogueTreeRow.id == tree_id)
            )
            row = result.scalar_one_or_none()
            return row.to_model() if row else None

    async def list_dialogue_trees(self, project_id: UUID) -> list[DialogueTree]:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(DialogueTreeRow).where(DialogueTreeRow.project_id == str(project_id))
            )
            return [row.to_model() for row in result.scalars().all()]

    async def delete_dialogue_tree(self, tree_id: str) -> bool:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                sql_delete(DialogueTreeRow).where(DialogueTreeRow.id == tree_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def create_quest_graph(self, project_id: UUID, graph: QuestGraph) -> QuestGraph:
        await self.init()
        async with AsyncSession(self.engine) as session:
            row = QuestGraphRow.from_model(graph, project_id)
            session.add(row)
            await session.commit()
            return graph

    async def get_quest_graph(self, graph_id: str) -> QuestGraph | None:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(QuestGraphRow).where(QuestGraphRow.id == graph_id)
            )
            row = result.scalar_one_or_none()
            return row.to_model() if row else None

    async def list_quest_graphs(self, project_id: UUID) -> list[QuestGraph]:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(QuestGraphRow).where(QuestGraphRow.project_id == str(project_id))
            )
            return [row.to_model() for row in result.scalars().all()]

    async def delete_quest_graph(self, graph_id: str) -> bool:
        await self.init()
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                sql_delete(QuestGraphRow).where(QuestGraphRow.id == graph_id)
            )
            await session.commit()
            return result.rowcount > 0
