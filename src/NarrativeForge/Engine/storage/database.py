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
    GameGenre,
    PersonalityProfile,
    Project,
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
