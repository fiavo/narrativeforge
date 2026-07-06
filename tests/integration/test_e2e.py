import json
from typing import AsyncIterator
import pytest
from httpx import ASGITransport, AsyncClient

from NarrativeForge.Engine.main import app
from NarrativeForge.Engine.storage.database import Database
from NarrativeForge.Engine.api import init_projects, init_generation
from NarrativeForge.Engine.ai_providers.base import AIProvider, CompletionOptions, Message
from NarrativeForge.Engine.pipeline.orchestrator import PipelineOrchestrator


class FakeProvider(AIProvider):
    def __init__(self, responses: dict[str, str] | None = None):
        self._responses = responses or {}
        self.call_count = 0

    async def complete(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> str:
        self.call_count += 1
        if self.call_count == 1:
            return self._responses.get(
                "director",
                json.dumps(
                    {
                        "request_type": "generate",
                        "sub_tasks": [
                            {"agent": "story", "instruction": "Write scene"},
                            {"agent": "consistency", "instruction": "Check consistency"},
                        ],
                        "summary": "Generate story content",
                    }
                ),
            )
        if self.call_count == 2:
            return self._responses.get(
                "story",
                json.dumps(
                    [
                        {"title": "The Opening", "description": "A dark forest at twilight"}
                    ]
                ),
            )
        return self._responses.get(
            "checker",
            json.dumps(
                {
                    "score": 0.95,
                    "issues": [],
                    "summary": "Content is consistent",
                }
            ),
        )

    async def stream(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> AsyncIterator[str]:
        result = await self.complete(messages, options)
        for word in result.split():
            yield word + " "


@pytest.fixture(autouse=True)
async def setup_db():
    test_db = Database("sqlite+aiosqlite:///:memory:")
    await test_db.init()
    provider = FakeProvider()
    orchestrator = PipelineOrchestrator(provider)
    init_projects(test_db)
    init_generation(test_db, orchestrator)
    yield
    await test_db.close()


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_full_workflow(client: AsyncClient):
    # 1. Health check
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # 2. Verify no projects initially
    resp = await client.get("/api/projects")
    assert resp.status_code == 200
    assert resp.json() == []

    # 3. Create project
    payload = {
        "name": "E2E Test Game",
        "genre": "RPG",
        "tone": "epic",
        "themes": ["adventure", "mystery"],
    }
    resp = await client.post("/api/projects", json=payload)
    assert resp.status_code == 201
    project = resp.json()
    project_id = project["id"]
    assert project["name"] == "E2E Test Game"
    assert project["genre"] == "RPG"
    assert project_id is not None

    # 4. Verify project exists via GET
    resp = await client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "E2E Test Game"

    # 5. List projects
    resp = await client.get("/api/projects")
    assert resp.status_code == 200
    projects = resp.json()
    assert len(projects) == 1
    assert projects[0]["id"] == project_id

    # 6. Generate content
    resp = await client.post(
        "/api/generate",
        json={"project_id": project_id, "request": "Write an opening scene"},
    )
    assert resp.status_code == 200
    gen = resp.json()
    assert gen["content"] is not None
    assert len(gen["stages"]) == 3
    assert "Director" in gen["stages"]
    assert "Story" in gen["stages"]
    assert "Consistency" in gen["stages"]

    # 7. Delete project
    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204

    # 8. Confirm deletion
    resp = await client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 404

    # 9. Confirm list is empty
    resp = await client.get("/api/projects")
    assert resp.status_code == 200
    assert resp.json() == []


async def _create_project(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/projects",
        json={
            "name": "Agent Test Game",
            "genre": "RPG",
            "tone": "mysterious",
            "themes": ["magic", "intrigue"],
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_dialogue_generation_flow(client: AsyncClient):
    project_id = await _create_project(client)

    resp = await client.post(
        "/api/agents/DialogueAgent",
        json={"project_id": project_id, "request": "Write a confrontation between two rivals"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_name"] == "DialogueAgent"
    assert data["content"] is not None
    assert "metadata" in data
    assert "dialogue_type" in data["metadata"]
    assert "exchange_count" in data["metadata"]

    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204


async def test_quest_generation_flow(client: AsyncClient):
    project_id = await _create_project(client)

    resp = await client.post(
        "/api/agents/QuestAgent",
        json={"project_id": project_id, "request": "Create a main quest to defeat the dragon"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_name"] == "QuestAgent"
    assert data["content"] is not None
    assert "metadata" in data
    assert "genre" in data["metadata"]
    assert "has_objectives" in data["metadata"]
    assert "has_rewards" in data["metadata"]
    assert "is_main_quest" in data["metadata"]

    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204


async def test_lore_generation_flow(client: AsyncClient):
    project_id = await _create_project(client)

    resp = await client.post(
        "/api/agents/LoreAgent",
        json={"project_id": project_id, "request": "Describe the ancient history of the kingdom"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_name"] == "LoreAgent"
    assert data["content"] is not None
    assert "metadata" in data
    assert "category" in data["metadata"]
    assert "has_title" in data["metadata"]
    assert "has_content" in data["metadata"]
    assert "genre" in data["metadata"]

    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204
