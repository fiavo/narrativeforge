from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from NarrativeForge.Engine.main import app
from NarrativeForge.Engine.storage.database import Database
from NarrativeForge.Engine.pipeline.orchestrator import PipelineOrchestrator
from NarrativeForge.Engine.api import init_projects, init_generation


@pytest.fixture(autouse=True)
async def setup_db():
    test_db = Database("sqlite+aiosqlite:///:memory:")
    await test_db.init()
    init_projects(test_db)

    mock_provider = AsyncMock()
    mock_provider.complete.return_value = '{"result": "mocked"}'
    mock_orchestrator = PipelineOrchestrator(mock_provider)
    init_generation(test_db, mock_orchestrator)
    yield
    await test_db.close()


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_create_project(client: AsyncClient):
    payload = {
        "name": "Test Game",
        "genre": "RPG",
        "tone": "dark",
    }
    resp = await client.post("/api/projects", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Game"
    assert data["genre"] == "RPG"
    assert "id" in data


async def test_list_projects_empty(client: AsyncClient):
    resp = await client.get("/api/projects")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_projects_after_create(client: AsyncClient):
    await client.post("/api/projects", json={"name": "A", "genre": "Horror"})
    resp = await client.get("/api/projects")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_get_project(client: AsyncClient):
    create_resp = await client.post("/api/projects", json={"name": "B", "genre": "SciFi"})
    project_id = create_resp.json()["id"]
    resp = await client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "B"


async def test_get_project_not_found(client: AsyncClient):
    resp = await client.get("/api/projects/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_delete_project(client: AsyncClient):
    create_resp = await client.post("/api/projects", json={"name": "C", "genre": "Fantasy"})
    project_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204
    get_resp = await client.get(f"/api/projects/{project_id}")
    assert get_resp.status_code == 404


async def test_delete_project_not_found(client: AsyncClient):
    resp = await client.delete("/api/projects/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_generate_project_not_found(client: AsyncClient):
    resp = await client.post(
        "/api/generate",
        json={"project_id": "00000000-0000-0000-0000-000000000000", "request": "test"},
    )
    assert resp.status_code == 404


async def test_direct_agent_invocation(client: AsyncClient):
    create_resp = await client.post(
        "/api/projects", json={"name": "Agent Test", "genre": "Fantasy"}
    )
    project_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/agents/StoryAgent",
        json={"project_id": project_id, "request": "Generate story beats"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_name"] == "StoryAgent"
    assert "content" in data
    assert "metadata" in data
    assert data["metadata"]["genre"] == "Fantasy"


async def test_direct_agent_invalid_name(client: AsyncClient):
    create_resp = await client.post(
        "/api/projects", json={"name": "Agent Test", "genre": "Fantasy"}
    )
    project_id = create_resp.json()["id"]

    resp = await client.post(
        "/api/agents/InvalidAgent",
        json={"project_id": project_id, "request": "test"},
    )
    assert resp.status_code == 400
    assert "Unknown agent" in resp.json()["detail"]
