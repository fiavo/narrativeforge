import json
from typing import AsyncIterator
import pytest
from httpx import ASGITransport, AsyncClient

from NarrativeForge.Engine.main import app
from NarrativeForge.Engine.storage.database import Database
from NarrativeForge.Engine.api import init_projects, init_generation, init_dialogues, init_quests
from NarrativeForge.Engine.ai_providers.base import AIProvider, CompletionOptions, Message
from NarrativeForge.Engine.pipeline.orchestrator import PipelineOrchestrator
from NarrativeForge.Engine.plugins.plugin_manager import PluginManager
from NarrativeForge.Engine.plugins.plugin_info import PluginInfo, PluginType
from NarrativeForge.Engine.plugins.plugin_config import PluginConfig

AGENT_RESPONSES = {
    "WorldAgent": json.dumps({
        "locations": [
            {
                "name": "Silverhold",
                "type": "city",
                "description": "A gleaming city of white stone.",
                "significance": "Capital of the realm.",
            }
        ],
        "factions": [
            {
                "name": "The Council of Stars",
                "description": "A secretive governing body.",
                "goals": ["Maintain peace"],
                "allies": ["Silverhold"],
                "enemies": [],
            }
        ],
        "lore_entries": [
            {
                "title": "The Founding",
                "category": "culture",
                "content": "Silverhold was built by the first kings.",
                "tags": ["history"],
            }
        ],
    }),
    "TimelineAgent": json.dumps({
        "title": "The Great Awakening",
        "timestamp": "Year 1000",
        "description": "Magic returned to the world.",
        "participants": ["The Archmage", "The Council of Stars"],
        "location": "Silverhold",
        "consequences": ["New era of exploration"],
    }),
    "CriticAgent": json.dumps({
        "overall_score": 0.88,
        "scores": {
            "coherence": 0.9,
            "character_depth": 0.85,
            "pacing": 0.88,
            "dialogue_quality": 0.85,
            "creativity": 0.9,
            "emotional_impact": 0.87,
        },
        "summary": "Strong narrative overall.",
        "strengths": ["Good pacing", "Creative world-building"],
        "weaknesses": ["Minor dialogue issues"],
    }),
    "RewriteAgent": json.dumps({
        "rewritten_text": "The warrior's blade gleamed in the torchlight.",
        "mode": "polish",
        "changes_summary": "Enhanced description.",
    }),
}


class FakeProvider(AIProvider):
    def __init__(self, responses: dict[str, str] | None = None):
        self._responses = responses or {}
        self.call_count = 0

    async def complete(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> str:
        self.call_count += 1
        for msg in messages:
            content = msg.content if hasattr(msg, "content") else ""
            if "world-builder" in content:
                return AGENT_RESPONSES["WorldAgent"]
            if "chronologist" in content:
                return AGENT_RESPONSES["TimelineAgent"]
            if "quality critic" in content:
                return AGENT_RESPONSES["CriticAgent"]
            if "text rewriter" in content:
                return AGENT_RESPONSES["RewriteAgent"]
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
    init_dialogues(test_db)
    init_quests(test_db)
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


INK_DIALOGUE_SCRIPT = """\
=== greet ===
Hello there, adventurer.
+ [Hello] -> farewell
+ [Goodbye] -> farewell
=== farewell ===
Farewell, traveler.
-> END
"""

INK_QUEST_SCRIPT = """\
=== start_quest ===
Find the ancient artifact hidden in the caves.
-> objective_1
=== objective_1 ===
Navigate through the dark caves.
+ [Reward] -> quest_reward
=== quest_reward ===
You receive the artifact.
-> END
"""


async def test_dialogue_tree_workflow(client: AsyncClient):
    payload = {
        "name": "Dialogue E2E Test",
        "genre": "RPG",
        "tone": "mysterious",
        "themes": ["dialogue", "ink"],
    }
    resp = await client.post("/api/projects", json=payload)
    assert resp.status_code == 201
    project = resp.json()
    project_id = project["id"]

    tree_payload = {
        "name": "Manual Tree",
        "start_node_id": "n1",
        "nodes": {
            "n1": {
                "id": "n1",
                "type": "text",
                "content": "Welcome!",
                "choices": [],
                "conditions": [],
                "variables_set": {},
                "next_node_id": "",
            }
        },
        "edges": [],
    }
    resp = await client.post(f"/api/projects/{project_id}/dialogues", json=tree_payload)
    assert resp.status_code == 201
    tree = resp.json()
    assert tree["name"] == "Manual Tree"
    assert tree["start_node_id"] == "n1"
    assert "n1" in tree["nodes"]

    resp = await client.get(f"/api/projects/{project_id}/dialogues")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    parse_payload = {"script": INK_DIALOGUE_SCRIPT, "name": "Ink Dialogue"}
    resp = await client.post("/api/dialogues/parse", json=parse_payload)
    assert resp.status_code == 200
    parsed = resp.json()
    ink_tree = parsed["tree"]
    assert ink_tree["name"] == "Ink Dialogue"
    assert len(ink_tree["nodes"]) > 0
    assert ink_tree["start_node_id"] != ""
    assert ink_tree["start_node_id"] in ink_tree["nodes"]

    has_choices = any(
        node.get("choices") for node in ink_tree["nodes"].values()
    )
    assert has_choices

    resp = await client.get(f"/api/dialogues/{tree['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == tree["id"]

    resp = await client.delete(f"/api/dialogues/{tree['id']}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/dialogues/{tree['id']}")
    assert resp.status_code == 404

    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204


async def test_quest_graph_workflow(client: AsyncClient):
    payload = {
        "name": "Quest E2E Test",
        "genre": "Fantasy",
        "tone": "epic",
        "themes": ["quest", "ink"],
    }
    resp = await client.post("/api/projects", json=payload)
    assert resp.status_code == 201
    project = resp.json()
    project_id = project["id"]

    graph_payload = {
        "name": "Manual Graph",
        "start_node_id": "q1",
        "nodes": {
            "q1": {
                "id": "q1",
                "type": "start",
                "name": "begin",
                "description": "Start the quest",
                "objectives": [],
                "rewards": {},
                "conditions": [],
                "next_node_ids": [],
            }
        },
        "edges": [],
    }
    resp = await client.post(f"/api/projects/{project_id}/quests", json=graph_payload)
    assert resp.status_code == 201
    graph = resp.json()
    assert graph["name"] == "Manual Graph"
    assert graph["start_node_id"] == "q1"
    assert "q1" in graph["nodes"]

    resp = await client.get(f"/api/projects/{project_id}/quests")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    parse_payload = {"script": INK_QUEST_SCRIPT, "name": "Ink Quest"}
    resp = await client.post("/api/quests/parse", json=parse_payload)
    assert resp.status_code == 200
    parsed = resp.json()
    ink_graph = parsed["graph"]
    assert ink_graph["name"] == "Ink Quest"
    assert len(ink_graph["nodes"]) > 0
    assert ink_graph["start_node_id"] != ""
    assert ink_graph["start_node_id"] in ink_graph["nodes"]

    assert len(ink_graph["edges"]) > 0

    node_types = [n["type"] for n in ink_graph["nodes"].values()]
    assert "start" in node_types

    resp = await client.get(f"/api/quests/{graph['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == graph["id"]

    resp = await client.delete(f"/api/quests/{graph['id']}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/quests/{graph['id']}")
    assert resp.status_code == 404

    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204


async def test_world_generation_flow(client: AsyncClient):
    project_id = await _create_project(client)

    resp = await client.post(
        "/api/agents/WorldAgent",
        json={"project_id": project_id, "request": "Generate a fantasy world"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_name"] == "WorldAgent"
    assert isinstance(data["content"], dict)
    assert "locations" in data["content"]
    assert "factions" in data["content"]
    assert "lore_entries" in data["content"]
    assert len(data["content"]["locations"]) > 0
    assert "metadata" in data
    assert "location_count" in data["metadata"]
    assert "faction_count" in data["metadata"]
    assert "lore_entry_count" in data["metadata"]

    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204


async def test_timeline_generation_flow(client: AsyncClient):
    project_id = await _create_project(client)

    resp = await client.post(
        "/api/agents/TimelineAgent",
        json={"project_id": project_id, "request": "Create a timeline event"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_name"] == "TimelineAgent"
    assert isinstance(data["content"], dict)
    assert "title" in data["content"]
    assert "description" in data["content"]
    assert "metadata" in data
    assert "has_title" in data["metadata"]
    assert "has_description" in data["metadata"]

    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204


async def test_critic_flow(client: AsyncClient):
    project_id = await _create_project(client)

    resp = await client.post(
        "/api/agents/CriticAgent",
        json={"project_id": project_id, "request": "Evaluate this story"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_name"] == "CriticAgent"
    assert isinstance(data["content"], dict)
    assert "overall_score" in data["content"]
    assert "scores" in data["content"]
    assert "summary" in data["content"]
    assert "metadata" in data
    assert "overall_score" in data["metadata"]
    assert "criterion_count" in data["metadata"]

    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204


async def test_rewrite_flow(client: AsyncClient):
    project_id = await _create_project(client)

    resp = await client.post(
        "/api/agents/RewriteAgent",
        json={"project_id": project_id, "request": "Polish this: The hero walked."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_name"] == "RewriteAgent"
    assert isinstance(data["content"], dict)
    assert "rewritten_text" in data["content"]
    assert "mode" in data["content"]
    assert "metadata" in data
    assert "mode" in data["metadata"]
    assert "temperature" in data["metadata"]

    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204


async def test_export_ink_format(client: AsyncClient):
    resp = await client.post(
        "/api/projects",
        json={
            "name": "Ink Export Test",
            "genre": "RPG",
            "tone": "epic",
            "themes": ["dialogue", "ink"],
        },
    )
    assert resp.status_code == 201
    project = resp.json()
    project_id = project["id"]

    parse_payload = {"script": INK_DIALOGUE_SCRIPT, "name": "Exported Dialogue"}
    resp = await client.post("/api/dialogues/parse", json=parse_payload)
    assert resp.status_code == 200
    ink_tree = resp.json()["tree"]

    export_payload = {
        "format": "json",
        "content": ink_tree,
        "filename": "ink_dialogue",
    }
    resp = await client.post("/api/export", json=export_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "ink_dialogue.json"
    assert data["format"] == "json"
    assert "name" in data["content"]
    assert "Exported Dialogue" in data["content"]
    assert "nodes" in data["content"]

    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204


async def test_export_json_format(client: AsyncClient):
    resp = await client.post(
        "/api/projects",
        json={
            "name": "JSON Export Test",
            "genre": "Fantasy",
            "tone": "dark",
            "themes": ["export", "json"],
        },
    )
    assert resp.status_code == 201
    project = resp.json()
    project_id = project["id"]

    resp = await client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    project_data = resp.json()

    export_payload = {
        "format": "json",
        "content": project_data,
        "filename": "project_export",
    }
    resp = await client.post("/api/export", json=export_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "project_export.json"
    assert data["format"] == "json"
    parsed = json.loads(data["content"])
    assert parsed["name"] == "JSON Export Test"
    assert parsed["genre"] == "Fantasy"

    resp = await client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 204


async def test_export_formats_list(client: AsyncClient):
    resp = await client.get("/api/export/formats")
    assert resp.status_code == 200
    data = resp.json()
    assert "formats" in data
    formats = data["formats"]
    assert "json" in formats
    assert "markdown" in formats
    assert "text" in formats
    assert "yaml" in formats
    assert len(formats) == 4


async def test_plugin_discovery_api(client: AsyncClient):
    resp = await client.get("/api/plugins")
    assert resp.status_code == 200
    plugins = resp.json()
    assert isinstance(plugins, list)

    assert len(plugins) >= 1
    names = [p["name"] for p in plugins]
    assert "example-agent" in names
    example = next(p for p in plugins if p["name"] == "example-agent")
    assert example["version"] == "1.0.0"
    assert example["type"] == "agent"
    assert example["enabled"] is True
    assert isinstance(example["description"], str)
    assert isinstance(example["author"], str)


async def test_plugin_manager_end_to_end():
    config = PluginConfig(config_path=None)
    config._config_path = None
    config._disabled = set()
    manager = PluginManager(config=config)

    discovered = manager.discover()
    assert isinstance(discovered, list)
    assert len(discovered) >= 1

    ep_agent = next(p for p in discovered if p.name == "example-agent")
    assert ep_agent.version == "1.0.0"
    assert ep_agent.plugin_type == PluginType.AGENT

    custom = PluginInfo(
        name="test-custom",
        version="2.0.0",
        description="A custom test plugin",
        author="Test Author",
        plugin_type=PluginType.PROVIDER,
        entry_point="collections:OrderedDict",
    )
    manager.register(custom)
    plugins = manager.get_plugins()
    assert "test-custom" in plugins
    assert plugins["test-custom"].version == "2.0.0"

    instance = manager.load("test-custom")
    assert instance is not None
    assert plugins["test-custom"].instance is instance

    instance2 = manager.load("test-custom")
    assert instance2 is instance

    disabled = PluginInfo(
        name="disabled-plugin",
        enabled=False,
        entry_point="collections:OrderedDict",
    )
    manager.register(disabled)
    config.set_enabled("disabled-plugin", False)
    with pytest.raises(ValueError, match="disabled"):
        manager.load("disabled-plugin")

    all_plugins = manager.get_plugins()
    assert "disabled-plugin" not in all_plugins


async def test_story_bible_character_workflow(client: AsyncClient):
    resp = await client.post(
        "/api/projects",
        json={"name": "Story Test", "genre": "RPG"},
    )
    assert resp.status_code == 201
    pid = resp.json()["id"]

    resp = await client.post(
        f"/api/projects/{pid}/characters",
        json={"name": "Hero", "role": "Protagonist", "backstory": "A legendary warrior"},
    )
    assert resp.status_code == 201
    char = resp.json()
    assert char["name"] == "Hero"
    cid = char["id"]

    resp = await client.get(f"/api/projects/{pid}/characters/{cid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Hero"
    assert resp.json()["backstory"] == "A legendary warrior"

    resp = await client.get(f"/api/projects/{pid}/characters")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.delete(f"/api/projects/{pid}/characters/{cid}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/projects/{pid}/characters/{cid}")
    assert resp.status_code == 404

    resp = await client.delete(f"/api/projects/{pid}")
    assert resp.status_code == 204


async def test_story_bible_location_workflow(client: AsyncClient):
    resp = await client.post(
        "/api/projects",
        json={"name": "Location Test", "genre": "RPG"},
    )
    assert resp.status_code == 201
    pid = resp.json()["id"]

    resp = await client.post(
        f"/api/projects/{pid}/locations",
        json={
            "name": "Dark Forest",
            "type": "wilderness",
            "description": "A mysterious forest",
            "significance": "Quest hub",
        },
    )
    assert resp.status_code == 201
    loc = resp.json()
    assert loc["name"] == "Dark Forest"
    assert loc["type"] == "wilderness"
    lid = loc["id"]

    resp = await client.get(f"/api/projects/{pid}/locations/{lid}")
    assert resp.status_code == 200
    assert resp.json()["description"] == "A mysterious forest"

    resp = await client.get(f"/api/projects/{pid}/locations")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get(f"/api/projects/{pid}/story-bible")
    assert resp.status_code == 200
    bible = resp.json()
    assert len(bible["locations"]) == 1
    assert bible["locations"][0]["name"] == "Dark Forest"

    resp = await client.delete(f"/api/projects/{pid}")
    assert resp.status_code == 204


async def test_story_bible_faction_workflow(client: AsyncClient):
    resp = await client.post(
        "/api/projects",
        json={"name": "Faction Test", "genre": "RPG"},
    )
    assert resp.status_code == 201
    pid = resp.json()["id"]

    resp = await client.post(
        f"/api/projects/{pid}/factions",
        json={
            "name": "Dark Order",
            "description": "An evil organization",
            "goals": ["conquest", "power"],
        },
    )
    assert resp.status_code == 201
    fac = resp.json()
    assert fac["name"] == "Dark Order"
    assert fac["goals"] == ["conquest", "power"]
    fid = fac["id"]

    resp = await client.get(f"/api/projects/{pid}/factions/{fid}")
    assert resp.status_code == 200
    assert resp.json()["description"] == "An evil organization"

    resp = await client.get(f"/api/projects/{pid}/factions")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get(f"/api/projects/{pid}/story-bible")
    assert resp.status_code == 200
    bible = resp.json()
    assert len(bible["factions"]) == 1
    assert bible["factions"][0]["name"] == "Dark Order"

    resp = await client.delete(f"/api/projects/{pid}")
    assert resp.status_code == 204
