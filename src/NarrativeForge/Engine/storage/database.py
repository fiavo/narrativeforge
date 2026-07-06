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
    GameGenre,
    PersonalityProfile,
    Project,
    Quest,
    QuestObjective,
    QuestPrerequisite,
    QuestReward,
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
