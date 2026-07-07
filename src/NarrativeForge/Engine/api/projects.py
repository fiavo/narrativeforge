from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from NarrativeForge.Engine.models import (
    Character,
    CharacterArc,
    CharacterRole,
    Faction,
    GameGenre,
    LoreEntry,
    Location,
    PersonalityProfile,
    Project,
    StoryBible,
    TimelineEvent,
)
from NarrativeForge.Engine.storage.database import Database

router = APIRouter(prefix="/api/projects", tags=["projects"])

_db: Database | None = None


def init(db: Database):
    global _db
    _db = db


async def _require_project(project_id: UUID) -> Project:
    project = await _db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


class ProjectCreate(BaseModel):
    name: str
    genre: GameGenre
    sub_genres: list[GameGenre] = Field(default_factory=list)
    target_audience: str = ""
    tone: str = ""
    themes: list[str] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    genre: GameGenre
    sub_genres: list[GameGenre]
    target_audience: str
    tone: str
    themes: list[str]
    story_bible_id: UUID | None
    settings: dict
    created_at: str
    updated_at: str


def _to_response(p: Project) -> ProjectResponse:
    return ProjectResponse(
        id=p.id,
        name=p.name,
        genre=p.genre,
        sub_genres=p.sub_genres,
        target_audience=p.target_audience,
        tone=p.tone,
        themes=p.themes,
        story_bible_id=p.story_bible_id,
        settings=p.settings,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


class CharacterCreate(BaseModel):
    name: str
    alias: str = ""
    role: CharacterRole = CharacterRole.Supporting
    personality: PersonalityProfile = Field(default_factory=PersonalityProfile)
    backstory: str = ""
    motivation: str = ""
    goals: list[str] = Field(default_factory=list)
    fears: list[str] = Field(default_factory=list)
    dialogue_style: str = ""
    appearance: str = ""


class CharacterResponse(BaseModel):
    id: UUID
    name: str
    alias: str
    role: CharacterRole
    personality: PersonalityProfile
    backstory: str
    motivation: str
    goals: list[str]
    fears: list[str]
    dialogue_style: str
    appearance: str
    is_alive: bool


def _character_to_response(c: Character) -> CharacterResponse:
    return CharacterResponse(
        id=c.id,
        name=c.name,
        alias=c.alias,
        role=c.role,
        personality=c.personality,
        backstory=c.backstory,
        motivation=c.motivation,
        goals=c.goals,
        fears=c.fears,
        dialogue_style=c.dialogue_style,
        appearance=c.appearance,
        is_alive=c.is_alive,
    )


class LocationCreate(BaseModel):
    name: str
    type: str = ""
    description: str = ""
    significance: str = ""


class LocationResponse(BaseModel):
    id: UUID
    name: str
    type: str
    description: str
    significance: str


def _location_to_response(loc: Location) -> LocationResponse:
    return LocationResponse(
        id=loc.id,
        name=loc.name,
        type=loc.type,
        description=loc.description,
        significance=loc.significance,
    )


class FactionCreate(BaseModel):
    name: str
    description: str = ""
    goals: list[str] = Field(default_factory=list)


class FactionResponse(BaseModel):
    id: UUID
    name: str
    description: str
    goals: list[str]


def _faction_to_response(f: Faction) -> FactionResponse:
    return FactionResponse(
        id=f.id,
        name=f.name,
        description=f.description,
        goals=f.goals,
    )


class TimelineEventCreate(BaseModel):
    title: str
    description: str = ""
    timestamp: str = ""
    order: int = 0
    consequences: list[str] = Field(default_factory=list)


class TimelineEventResponse(BaseModel):
    id: UUID
    title: str
    description: str
    timestamp: str
    order: int
    consequences: list[str]


def _timeline_to_response(e: TimelineEvent) -> TimelineEventResponse:
    return TimelineEventResponse(
        id=e.id,
        title=e.title,
        description=e.description,
        timestamp=e.timestamp,
        order=e.order,
        consequences=e.consequences,
    )


class LoreEntryCreate(BaseModel):
    title: str
    content: str = ""
    category: str = ""
    tags: list[str] = Field(default_factory=list)


class LoreEntryResponse(BaseModel):
    id: UUID
    title: str
    content: str
    category: str
    tags: list[str]


def _lore_to_response(entry: LoreEntry) -> LoreEntryResponse:
    return LoreEntryResponse(
        id=entry.id,
        title=entry.title,
        content=entry.content,
        category=entry.category,
        tags=entry.tags,
    )


class StoryBibleResponse(BaseModel):
    project_id: UUID
    characters: list[CharacterResponse]
    locations: list[LocationResponse]
    factions: list[FactionResponse]
    timeline: list[TimelineEventResponse]
    lore_entries: list[LoreEntryResponse]


async def _assemble_story_bible(project_id: UUID) -> StoryBibleResponse:
    characters = await _db.list_characters(project_id)
    locations = await _db.list_locations(project_id)
    factions = await _db.list_factions(project_id)
    timeline = await _db.list_timeline_events(project_id)
    lore_entries = await _db.list_lore_entries(project_id)
    return StoryBibleResponse(
        project_id=project_id,
        characters=[_character_to_response(c) for c in characters],
        locations=[_location_to_response(l) for l in locations],
        factions=[_faction_to_response(f) for f in factions],
        timeline=[_timeline_to_response(e) for e in timeline],
        lore_entries=[_lore_to_response(le) for le in lore_entries],
    )


# ── Project CRUD ──────────────────────────────────────────────


@router.get("", response_model=list[ProjectResponse])
async def list_projects():
    projects = await _db.list_projects()
    return [_to_response(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID):
    project = await _require_project(project_id)
    return _to_response(project)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreate):
    project = Project(
        name=body.name,
        genre=body.genre,
        sub_genres=body.sub_genres,
        target_audience=body.target_audience,
        tone=body.tone,
        themes=body.themes,
        settings=body.settings,
    )
    created = await _db.create_project(project)
    return _to_response(created)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: UUID):
    deleted = await _db.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")


# ── Story Bible (full composite view) ─────────────────────────


@router.get("/{project_id}/story-bible", response_model=StoryBibleResponse)
async def get_story_bible(project_id: UUID):
    await _require_project(project_id)
    return await _assemble_story_bible(project_id)


# ── Characters CRUD ───────────────────────────────────────────


@router.get("/{project_id}/characters", response_model=list[CharacterResponse])
async def list_characters(project_id: UUID):
    await _require_project(project_id)
    characters = await _db.list_characters(project_id)
    return [_character_to_response(c) for c in characters]


@router.get("/{project_id}/characters/{character_id}", response_model=CharacterResponse)
async def get_character(project_id: UUID, character_id: UUID):
    await _require_project(project_id)
    character = await _db.get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return _character_to_response(character)


@router.post(
    "/{project_id}/characters", response_model=CharacterResponse, status_code=201
)
async def create_character(project_id: UUID, body: CharacterCreate):
    await _require_project(project_id)
    character = Character(
        name=body.name,
        alias=body.alias,
        role=body.role,
        personality=body.personality,
        backstory=body.backstory,
        motivation=body.motivation,
        goals=body.goals,
        fears=body.fears,
        dialogue_style=body.dialogue_style,
        appearance=body.appearance,
    )
    created = await _db.create_character(project_id, character)
    return _character_to_response(created)


@router.delete(
    "/{project_id}/characters/{character_id}", status_code=204
)
async def delete_character(project_id: UUID, character_id: UUID):
    await _require_project(project_id)
    deleted = await _db.delete_character(character_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Character not found")


# ── Locations CRUD ────────────────────────────────────────────


@router.get("/{project_id}/locations", response_model=list[LocationResponse])
async def list_locations(project_id: UUID):
    await _require_project(project_id)
    locations = await _db.list_locations(project_id)
    return [_location_to_response(l) for l in locations]


@router.get("/{project_id}/locations/{location_id}", response_model=LocationResponse)
async def get_location(project_id: UUID, location_id: UUID):
    await _require_project(project_id)
    location = await _db.get_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return _location_to_response(location)


@router.post(
    "/{project_id}/locations", response_model=LocationResponse, status_code=201
)
async def create_location(project_id: UUID, body: LocationCreate):
    await _require_project(project_id)
    location = Location(
        name=body.name,
        type=body.type,
        description=body.description,
        significance=body.significance,
    )
    created = await _db.create_location(project_id, location)
    return _location_to_response(created)


@router.delete(
    "/{project_id}/locations/{location_id}", status_code=204
)
async def delete_location(project_id: UUID, location_id: UUID):
    await _require_project(project_id)
    deleted = await _db.delete_location(location_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Location not found")


# ── Factions CRUD ─────────────────────────────────────────────


@router.get("/{project_id}/factions", response_model=list[FactionResponse])
async def list_factions(project_id: UUID):
    await _require_project(project_id)
    factions = await _db.list_factions(project_id)
    return [_faction_to_response(f) for f in factions]


@router.get("/{project_id}/factions/{faction_id}", response_model=FactionResponse)
async def get_faction(project_id: UUID, faction_id: UUID):
    await _require_project(project_id)
    faction = await _db.get_faction(faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    return _faction_to_response(faction)


@router.post(
    "/{project_id}/factions", response_model=FactionResponse, status_code=201
)
async def create_faction(project_id: UUID, body: FactionCreate):
    await _require_project(project_id)
    faction = Faction(
        name=body.name,
        description=body.description,
        goals=body.goals,
    )
    created = await _db.create_faction(project_id, faction)
    return _faction_to_response(created)


@router.delete(
    "/{project_id}/factions/{faction_id}", status_code=204
)
async def delete_faction(project_id: UUID, faction_id: UUID):
    await _require_project(project_id)
    deleted = await _db.delete_faction(faction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Faction not found")


# ── Timeline Events CRUD ──────────────────────────────────────


@router.get("/{project_id}/timeline", response_model=list[TimelineEventResponse])
async def list_timeline(project_id: UUID):
    await _require_project(project_id)
    events = await _db.list_timeline_events(project_id)
    return [_timeline_to_response(e) for e in events]


@router.get(
    "/{project_id}/timeline/{event_id}", response_model=TimelineEventResponse
)
async def get_timeline_event(project_id: UUID, event_id: UUID):
    await _require_project(project_id)
    event = await _db.get_timeline_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Timeline event not found")
    return _timeline_to_response(event)


@router.post(
    "/{project_id}/timeline", response_model=TimelineEventResponse, status_code=201
)
async def create_timeline_event(project_id: UUID, body: TimelineEventCreate):
    await _require_project(project_id)
    event = TimelineEvent(
        title=body.title,
        description=body.description,
        timestamp=body.timestamp,
        order=body.order,
        consequences=body.consequences,
    )
    created = await _db.create_timeline_event(project_id, event)
    return _timeline_to_response(created)


@router.delete(
    "/{project_id}/timeline/{event_id}", status_code=204
)
async def delete_timeline_event(project_id: UUID, event_id: UUID):
    await _require_project(project_id)
    deleted = await _db.delete_timeline_event(event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Timeline event not found")


# ── Lore Entries CRUD ─────────────────────────────────────────


@router.get("/{project_id}/lore", response_model=list[LoreEntryResponse])
async def list_lore(project_id: UUID):
    await _require_project(project_id)
    entries = await _db.list_lore_entries(project_id)
    return [_lore_to_response(e) for e in entries]


@router.get("/{project_id}/lore/{entry_id}", response_model=LoreEntryResponse)
async def get_lore_entry(project_id: UUID, entry_id: UUID):
    await _require_project(project_id)
    entry = await _db.get_lore_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Lore entry not found")
    return _lore_to_response(entry)


@router.post(
    "/{project_id}/lore", response_model=LoreEntryResponse, status_code=201
)
async def create_lore_entry(project_id: UUID, body: LoreEntryCreate):
    await _require_project(project_id)
    entry = LoreEntry(
        title=body.title,
        content=body.content,
        category=body.category,
        tags=body.tags,
    )
    created = await _db.create_lore_entry(project_id, entry)
    return _lore_to_response(created)


@router.delete(
    "/{project_id}/lore/{entry_id}", status_code=204
)
async def delete_lore_entry(project_id: UUID, entry_id: UUID):
    await _require_project(project_id)
    deleted = await _db.delete_lore_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Lore entry not found")
