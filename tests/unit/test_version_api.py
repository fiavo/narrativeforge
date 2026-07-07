from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from NarrativeForge.Engine.main import app
from NarrativeForge.Engine.storage.database import Database
from NarrativeForge.Engine.pipeline.orchestrator import PipelineOrchestrator
from NarrativeForge.Engine.plugins.plugin_info import PluginInfo, PluginType
from NarrativeForge.Engine.api import (
    init_projects,
    init_generation,
    init_dialogues,
    init_quests,
    init_versions,
)
from NarrativeForge.Engine.versioning import VersionManager


@pytest.fixture(autouse=True)
async def setup_db(tmp_path):
    test_db = Database("sqlite+aiosqlite:///:memory:")
    await test_db.init()
    vm = VersionManager(tmp_path / "versions")
    init_projects(test_db)
    init_dialogues(test_db)
    init_quests(test_db)
    init_versions(test_db, vm)

    mock_provider = AsyncMock()
    mock_provider.complete.return_value = '{"result": "mocked"}'
    mock_orchestrator = PipelineOrchestrator(mock_provider)

    mock_plugin_manager = MagicMock()
    mock_plugin_manager.discover.return_value = [
        PluginInfo(
            name="test-plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            plugin_type=PluginType.AGENT,
            enabled=True,
        ),
    ]
    init_generation(test_db, mock_orchestrator, mock_plugin_manager)
    yield
    await test_db.close()


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_create_snapshot(client: AsyncClient):
    create_resp = await client.post(
        "/api/projects", json={"name": "Snap Test", "genre": "RPG"}
    )
    project_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/projects/{project_id}/versions",
        json={"description": "Initial snapshot", "author": "tester"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == "Initial snapshot"
    assert data["author"] == "tester"
    assert data["version_number"] == 1
    assert data["project_id"] == project_id


async def test_list_versions(client: AsyncClient):
    create_resp = await client.post(
        "/api/projects", json={"name": "List Test", "genre": "Fantasy"}
    )
    project_id = create_resp.json()["id"]

    await client.post(
        f"/api/projects/{project_id}/versions",
        json={"description": "v1", "author": "a"},
    )
    await client.post(
        f"/api/projects/{project_id}/versions",
        json={"description": "v2", "author": "b"},
    )

    resp = await client.get(f"/api/projects/{project_id}/versions")
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) == 2
    descriptions = {v["description"] for v in versions}
    assert descriptions == {"v1", "v2"}


async def test_delete_version(client: AsyncClient):
    create_resp = await client.post(
        "/api/projects", json={"name": "Del Test", "genre": "Horror"}
    )
    project_id = create_resp.json()["id"]

    snap_resp = await client.post(
        f"/api/projects/{project_id}/versions",
        json={"description": "To delete", "author": "tester"},
    )
    version_id = snap_resp.json()["id"]

    del_resp = await client.delete(f"/api/versions/{version_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/versions/{version_id}")
    assert get_resp.status_code == 404
