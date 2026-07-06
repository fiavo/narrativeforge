from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from NarrativeForge.Engine.main import app
from NarrativeForge.Engine.storage.database import Database
from NarrativeForge.Engine.pipeline.orchestrator import PipelineOrchestrator
from NarrativeForge.Engine.api import init_projects, init_generation, init_dialogues, init_quests


@pytest.fixture(autouse=True)
async def setup_db():
    test_db = Database("sqlite+aiosqlite:///:memory:")
    await test_db.init()
    init_projects(test_db)
    init_dialogues(test_db)
    init_quests(test_db)

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


async def test_create_dialogue_tree(client: AsyncClient):
    create_resp = await client.post(
        "/api/projects", json={"name": "Dialogue Test", "genre": "RPG"}
    )
    project_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/projects/{project_id}/dialogues",
        json={
            "name": "Intro Dialogue",
            "start_node_id": "node1",
            "nodes": {
                "node1": {
                    "id": "node1",
                    "type": "text",
                    "content": "Hello, traveler!",
                }
            },
            "edges": [],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Intro Dialogue"
    assert data["start_node_id"] == "node1"
    assert "node1" in data["nodes"]
    assert data["nodes"]["node1"]["content"] == "Hello, traveler!"


async def test_list_dialogue_trees(client: AsyncClient):
    create_resp = await client.post(
        "/api/projects", json={"name": "List Test", "genre": "Fantasy"}
    )
    project_id = create_resp.json()["id"]

    await client.post(
        f"/api/projects/{project_id}/dialogues",
        json={"name": "Tree A", "start_node_id": "n1", "nodes": {}, "edges": []},
    )
    await client.post(
        f"/api/projects/{project_id}/dialogues",
        json={"name": "Tree B", "start_node_id": "n2", "nodes": {}, "edges": []},
    )

    resp = await client.get(f"/api/projects/{project_id}/dialogues")
    assert resp.status_code == 200
    trees = resp.json()
    assert len(trees) == 2
    names = {t["name"] for t in trees}
    assert names == {"Tree A", "Tree B"}


async def test_parse_ink_dialogue(client: AsyncClient):
    ink_script = """=== start ===
Welcome, adventurer!
+ [Hello!] -> greet
+ [Goodbye] -> farewell

=== greet ===
Nice to meet you!
-> END

=== farewell ===
Farewell!
-> END"""

    resp = await client.post(
        "/api/dialogues/parse",
        json={"script": ink_script, "name": "Parsed Dialogue"},
    )
    assert resp.status_code == 200
    data = resp.json()
    tree = data["tree"]
    assert tree["name"] == "Parsed Dialogue"
    assert tree["start_node_id"] != ""
    assert len(tree["nodes"]) > 0
    assert len(tree["edges"]) > 0


async def test_create_quest_graph(client: AsyncClient):
    create_resp = await client.post(
        "/api/projects", json={"name": "Quest Test", "genre": "RPG"}
    )
    project_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/projects/{project_id}/quests",
        json={
            "name": "Main Quest",
            "start_node_id": "start1",
            "nodes": {
                "start1": {
                    "id": "start1",
                    "type": "start",
                    "name": "Begin Journey",
                    "description": "Start your adventure",
                }
            },
            "edges": [],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Main Quest"
    assert data["start_node_id"] == "start1"
    assert "start1" in data["nodes"]
    assert data["nodes"]["start1"]["description"] == "Start your adventure"
