import pytest
from httpx import ASGITransport, AsyncClient

from NarrativeForge.Engine.main import app
from NarrativeForge.Engine.storage.database import Database
from NarrativeForge.Engine.api import init_projects


@pytest.fixture(autouse=True)
async def setup_db():
    test_db = Database("sqlite+aiosqlite:///:memory:")
    await test_db.init()
    init_projects(test_db)
    yield
    await test_db.close()


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _create_project(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/projects", json={"name": "Test", "genre": "RPG"}
    )
    return resp.json()["id"]


async def test_story_bible_full_assembly(client: AsyncClient):
    pid = await _create_project(client)

    await client.post(f"/api/projects/{pid}/characters", json={"name": "Hero"})
    await client.post(f"/api/projects/{pid}/locations", json={"name": "Castle"})
    await client.post(f"/api/projects/{pid}/factions", json={"name": "Guild"})
    await client.post(f"/api/projects/{pid}/timeline", json={"title": "War"})
    await client.post(
        f"/api/projects/{pid}/lore",
        json={"title": "Ancient Lore", "category": "history"},
    )

    resp = await client.get(f"/api/projects/{pid}/story-bible")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == pid
    assert len(data["characters"]) == 1
    assert data["characters"][0]["name"] == "Hero"
    assert len(data["locations"]) == 1
    assert data["locations"][0]["name"] == "Castle"
    assert len(data["factions"]) == 1
    assert data["factions"][0]["name"] == "Guild"
    assert len(data["timeline"]) == 1
    assert data["timeline"][0]["title"] == "War"
    assert len(data["lore_entries"]) == 1
    assert data["lore_entries"][0]["title"] == "Ancient Lore"


async def test_crud_character(client: AsyncClient):
    pid = await _create_project(client)

    create_resp = await client.post(
        f"/api/projects/{pid}/characters",
        json={"name": "Aria", "role": "Protagonist", "backstory": "Orphan"},
    )
    assert create_resp.status_code == 201
    char_id = create_resp.json()["id"]
    assert create_resp.json()["name"] == "Aria"
    assert create_resp.json()["role"] == "Protagonist"

    get_resp = await client.get(f"/api/projects/{pid}/characters/{char_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["backstory"] == "Orphan"

    list_resp = await client.get(f"/api/projects/{pid}/characters")
    assert len(list_resp.json()) == 1

    del_resp = await client.delete(f"/api/projects/{pid}/characters/{char_id}")
    assert del_resp.status_code == 204

    gone = await client.get(f"/api/projects/{pid}/characters/{char_id}")
    assert gone.status_code == 404


async def test_crud_location_and_faction(client: AsyncClient):
    pid = await _create_project(client)

    loc_resp = await client.post(
        f"/api/projects/{pid}/locations",
        json={"name": "Dark Forest", "type": "wilderness", "significance": "Quest hub"},
    )
    assert loc_resp.status_code == 201
    loc_id = loc_resp.json()["id"]
    assert loc_resp.json()["type"] == "wilderness"

    fac_resp = await client.post(
        f"/api/projects/{pid}/factions",
        json={"name": "Rangers", "description": "Forest protectors", "goals": ["patrol"]},
    )
    assert fac_resp.status_code == 201
    fac_id = fac_resp.json()["id"]

    assert (await client.get(f"/api/projects/{pid}/locations/{loc_id}")).status_code == 200
    assert (await client.get(f"/api/projects/{pid}/factions/{fac_id}")).status_code == 200

    assert (await client.delete(f"/api/projects/{pid}/locations/{loc_id}")).status_code == 204
    assert (await client.delete(f"/api/projects/{pid}/factions/{fac_id}")).status_code == 204


async def test_crud_timeline_and_lore(client: AsyncClient):
    pid = await _create_project(client)

    tl_resp = await client.post(
        f"/api/projects/{pid}/timeline",
        json={"title": "The Great War", "timestamp": "Year 100", "order": 1},
    )
    assert tl_resp.status_code == 201
    tl_id = tl_resp.json()["id"]
    assert tl_resp.json()["timestamp"] == "Year 100"

    lore_resp = await client.post(
        f"/api/projects/{pid}/lore",
        json={"title": "Magic System", "content": "Mana flows everywhere", "category": "magic"},
    )
    assert lore_resp.status_code == 201
    lore_id = lore_resp.json()["id"]

    assert (await client.get(f"/api/projects/{pid}/timeline/{tl_id}")).status_code == 200
    assert (await client.get(f"/api/projects/{pid}/lore/{lore_id}")).status_code == 200

    assert (await client.delete(f"/api/projects/{pid}/timeline/{tl_id}")).status_code == 204
    assert (await client.delete(f"/api/projects/{pid}/lore/{lore_id}")).status_code == 204


async def test_story_bible_not_found_project(client: AsyncClient):
    resp = await client.get("/api/projects/00000000-0000-0000-0000-000000000000/story-bible")
    assert resp.status_code == 404
