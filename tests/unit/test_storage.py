from uuid import uuid4

import pytest

from NarrativeForge.Engine.models import (
    Character,
    CharacterRole,
    DialogueExchange,
    DialogueLine,
    DialogueTree,
    DialogueNode,
    DialogueNodeType,
    DialogueEdge,
    DialogueChoice,
    GameGenre,
    Project,
    Quest,
    QuestObjective,
    QuestReward,
    QuestGraph,
    QuestNode,
    QuestNodeType,
    QuestEdge,
    StoryBible,
)
from NarrativeForge.Engine.storage.database import Database
from NarrativeForge.Engine.storage.json_store import JsonStore


@pytest.fixture
def sample_project():
    return Project(name="Test Game", genre=GameGenre.RPG)


@pytest.fixture
def sample_character():
    return Character(name="Hero", role=CharacterRole.Protagonist)


@pytest.fixture
def sample_story_bible(sample_project):
    return StoryBible(project_id=sample_project.id)


class TestDatabase:
    @pytest.fixture
    def db(self):
        return Database("sqlite+aiosqlite:///:memory:")

    @pytest.fixture
    def project(self):
        return Project(name="Test Game", genre=GameGenre.RPG)

    @pytest.fixture
    def character(self):
        return Character(name="Hero", role=CharacterRole.Protagonist)

    async def test_create_and_get_project(self, db, project):
        await db.create_project(project)
        retrieved = await db.get_project(project.id)
        assert retrieved is not None
        assert retrieved.name == "Test Game"
        assert retrieved.genre == GameGenre.RPG

    async def test_list_projects_empty(self, db):
        projects = await db.list_projects()
        assert projects == []

    async def test_list_projects_multiple(self, db):
        p1 = Project(name="Game 1", genre=GameGenre.RPG)
        p2 = Project(name="Game 2", genre=GameGenre.Fantasy)
        await db.create_project(p1)
        await db.create_project(p2)
        projects = await db.list_projects()
        assert len(projects) == 2
        names = {p.name for p in projects}
        assert names == {"Game 1", "Game 2"}

    async def test_delete_project(self, db, project):
        await db.create_project(project)
        result = await db.delete_project(project.id)
        assert result is True
        retrieved = await db.get_project(project.id)
        assert retrieved is None

    async def test_delete_nonexistent_project(self, db):
        result = await db.delete_project(uuid4())
        assert result is False

    async def test_get_nonexistent_project(self, db):
        retrieved = await db.get_project(uuid4())
        assert retrieved is None

    async def test_create_and_get_character(self, db, project, character):
        await db.create_project(project)
        await db.create_character(project.id, character)
        retrieved = await db.get_character(character.id)
        assert retrieved is not None
        assert retrieved.name == "Hero"
        assert retrieved.role == CharacterRole.Protagonist

    async def test_list_characters(self, db, project):
        await db.create_project(project)
        c1 = Character(name="Hero", role=CharacterRole.Protagonist)
        c2 = Character(name="Villain", role=CharacterRole.Antagonist)
        await db.create_character(project.id, c1)
        await db.create_character(project.id, c2)
        chars = await db.list_characters(project.id)
        assert len(chars) == 2
        names = {c.name for c in chars}
        assert names == {"Hero", "Villain"}

    async def test_delete_character(self, db, project, character):
        await db.create_project(project)
        await db.create_character(project.id, character)
        result = await db.delete_character(character.id)
        assert result is True
        retrieved = await db.get_character(character.id)
        assert retrieved is None

    async def test_character_personality_preserved(self, db, project):
        await db.create_project(project)
        char = Character(
            name="Complex Hero",
            role=CharacterRole.Protagonist,
            personality={
                "traits": ["brave", "loyal"],
                "values": ["justice"],
                "fears": ["failure"],
                "desires": ["freedom"],
            },
            arc={
                "start_state": "naive",
                "end_state": "wise",
                "turning_points": ["betrayal"],
            },
        )
        await db.create_character(project.id, char)
        retrieved = await db.get_character(char.id)
        assert retrieved.personality.traits == ["brave", "loyal"]
        assert retrieved.arc.start_state == "naive"

    async def test_project_fields_roundtrip(self, db):
        project = Project(
            name="Complex Game",
            genre=GameGenre.Cyberpunk,
            sub_genres=[GameGenre.SciFi, GameGenre.Noir],
            target_audience="Adults",
            tone="Dark",
            themes=["identity", "technology"],
            settings={"difficulty": "hard"},
        )
        await db.create_project(project)
        retrieved = await db.get_project(project.id)
        assert retrieved.sub_genres == [GameGenre.SciFi, GameGenre.Noir]
        assert retrieved.target_audience == "Adults"
        assert retrieved.themes == ["identity", "technology"]
        assert retrieved.settings == {"difficulty": "hard"}

    async def test_create_and_get_quest(self, db, project):
        await db.create_project(project)
        quest = Quest(
            name="Find the Sword",
            description="Locate the legendary sword in the cave.",
            objectives=[QuestObjective(description="Enter the cave", type="explore")],
            rewards=QuestReward(xp=100, gold=50),
            is_main_quest=True,
        )
        await db.create_quest(project.id, quest)
        retrieved = await db.get_quest(project.id, quest.id)
        assert retrieved is not None
        assert retrieved.name == "Find the Sword"
        assert retrieved.description == "Locate the legendary sword in the cave."
        assert len(retrieved.objectives) == 1
        assert retrieved.objectives[0].description == "Enter the cave"
        assert retrieved.rewards.xp == 100
        assert retrieved.is_main_quest is True

    async def test_list_quests(self, db, project):
        await db.create_project(project)
        q1 = Quest(name="Quest 1")
        q2 = Quest(name="Quest 2")
        await db.create_quest(project.id, q1)
        await db.create_quest(project.id, q2)
        quests = await db.list_quests(project.id)
        assert len(quests) == 2
        names = {q.name for q in quests}
        assert names == {"Quest 1", "Quest 2"}

    async def test_create_and_get_dialogue(self, db, project):
        await db.create_project(project)
        from uuid import uuid4
        char_id = uuid4()
        exchange = DialogueExchange(
            lines=[
                DialogueLine(character_id=char_id, character_name="Hero", text="Hello!"),
                DialogueLine(character_id=char_id, character_name="Villain", text="Goodbye!"),
            ],
            context="First meeting",
            mood="tense",
        )
        await db.create_dialogue(project.id, exchange)
        dialogues = await db.list_dialogues(project.id)
        assert len(dialogues) == 1
        retrieved = dialogues[0]
        assert retrieved.context == "First meeting"
        assert retrieved.mood == "tense"
        assert len(retrieved.lines) == 2
        assert retrieved.lines[0].text == "Hello!"
        assert retrieved.lines[1].text == "Goodbye!"

    async def test_list_dialogues(self, db, project):
        await db.create_project(project)
        from uuid import uuid4
        char_id = uuid4()
        d1 = DialogueExchange(lines=[DialogueLine(character_id=char_id, character_name="A", text="Hi")])
        d2 = DialogueExchange(lines=[DialogueLine(character_id=char_id, character_name="B", text="Hey")])
        await db.create_dialogue(project.id, d1)
        await db.create_dialogue(project.id, d2)
        dialogues = await db.list_dialogues(project.id)
        assert len(dialogues) == 2

    async def test_create_and_get_dialogue_tree(self, db, project):
        await db.create_project(project)
        tree = DialogueTree(
            name="Intro Dialogue",
            start_node_id="node1",
            nodes={
                "node1": DialogueNode(
                    id="node1",
                    type=DialogueNodeType.TEXT,
                    content="Welcome!",
                    next_node_id="node2",
                ),
                "node2": DialogueNode(
                    id="node2",
                    type=DialogueNodeType.CHOICE,
                    choices=[
                        {"text": "Yes", "next_node_id": "node3"},
                        {"text": "No", "next_node_id": "node4"},
                    ],
                ),
            },
            edges=[
                {"source_id": "node1", "target_id": "node2"},
                {"source_id": "node2", "target_id": "node3"},
            ],
        )
        await db.create_dialogue_tree(project.id, tree)
        retrieved = await db.get_dialogue_tree(tree.id)
        assert retrieved is not None
        assert retrieved.name == "Intro Dialogue"
        assert retrieved.start_node_id == "node1"
        assert len(retrieved.nodes) == 2
        assert retrieved.nodes["node1"].content == "Welcome!"
        assert retrieved.nodes["node1"].type == DialogueNodeType.TEXT
        assert len(retrieved.edges) == 2
        assert retrieved.edges[0].source_id == "node1"

    async def test_list_dialogue_trees(self, db, project):
        await db.create_project(project)
        t1 = DialogueTree(name="Tree 1", start_node_id="n1", nodes={"n1": DialogueNode(id="n1", type=DialogueNodeType.TEXT, content="Hi")})
        t2 = DialogueTree(name="Tree 2", start_node_id="n1", nodes={"n1": DialogueNode(id="n1", type=DialogueNodeType.TEXT, content="Hey")})
        await db.create_dialogue_tree(project.id, t1)
        await db.create_dialogue_tree(project.id, t2)
        trees = await db.list_dialogue_trees(project.id)
        assert len(trees) == 2
        names = {t.name for t in trees}
        assert names == {"Tree 1", "Tree 2"}

    async def test_delete_dialogue_tree(self, db, project):
        await db.create_project(project)
        tree = DialogueTree(name="ToDelete", start_node_id="n1", nodes={"n1": DialogueNode(id="n1", type=DialogueNodeType.TEXT, content="Hi")})
        await db.create_dialogue_tree(project.id, tree)
        result = await db.delete_dialogue_tree(tree.id)
        assert result is True
        retrieved = await db.get_dialogue_tree(tree.id)
        assert retrieved is None

    async def test_create_and_get_quest_graph(self, db, project):
        await db.create_project(project)
        graph = QuestGraph(
            name="Main Quest Graph",
            start_node_id="start",
            nodes={
                "start": QuestNode(id="start", type=QuestNodeType.START, name="Start"),
                "obj1": QuestNode(id="obj1", type=QuestNodeType.OBJECTIVE, name="Find Item", description="Locate the artifact"),
                "end": QuestNode(id="end", type=QuestNodeType.END, name="Complete"),
            },
            edges=[
                {"source_id": "start", "target_id": "obj1"},
                {"source_id": "obj1", "target_id": "end"},
            ],
        )
        await db.create_quest_graph(project.id, graph)
        retrieved = await db.get_quest_graph(graph.id)
        assert retrieved is not None
        assert retrieved.name == "Main Quest Graph"
        assert retrieved.start_node_id == "start"
        assert len(retrieved.nodes) == 3
        assert retrieved.nodes["obj1"].name == "Find Item"
        assert retrieved.nodes["obj1"].type == QuestNodeType.OBJECTIVE
        assert len(retrieved.edges) == 2
        assert retrieved.edges[0].source_id == "start"

    async def test_list_quest_graphs(self, db, project):
        await db.create_project(project)
        g1 = QuestGraph(name="Graph 1", start_node_id="n1", nodes={"n1": QuestNode(id="n1", type=QuestNodeType.START)})
        g2 = QuestGraph(name="Graph 2", start_node_id="n1", nodes={"n1": QuestNode(id="n1", type=QuestNodeType.START)})
        await db.create_quest_graph(project.id, g1)
        await db.create_quest_graph(project.id, g2)
        graphs = await db.list_quest_graphs(project.id)
        assert len(graphs) == 2
        names = {g.name for g in graphs}
        assert names == {"Graph 1", "Graph 2"}

    async def test_delete_quest_graph(self, db, project):
        await db.create_project(project)
        graph = QuestGraph(name="ToDelete", start_node_id="n1", nodes={"n1": QuestNode(id="n1", type=QuestNodeType.START)})
        await db.create_quest_graph(project.id, graph)
        result = await db.delete_quest_graph(graph.id)
        assert result is True
        retrieved = await db.get_quest_graph(graph.id)
        assert retrieved is None


class TestJsonStore:
    @pytest.fixture
    def store(self, tmp_path):
        return JsonStore(tmp_path)

    @pytest.fixture
    def project(self):
        return Project(name="Test Game", genre=GameGenre.RPG)

    @pytest.fixture
    def story_bible(self, project):
        return StoryBible(project_id=project.id)

    def test_save_and_load_project(self, store, project, story_bible):
        path = store.save_project(project, story_bible)
        assert path.exists()
        assert path.suffix == ".nforge"

        loaded_project, loaded_bible = store.load_project(path)
        assert loaded_project.name == project.name
        assert loaded_project.genre == project.genre
        assert loaded_bible.project_id == project.id

    def test_list_projects_empty(self, store):
        projects = store.list_projects()
        assert projects == []

    def test_list_projects(self, store):
        p1 = Project(name="Game 1", genre=GameGenre.RPG)
        p2 = Project(name="Game 2", genre=GameGenre.Fantasy)
        sb1 = StoryBible(project_id=p1.id)
        sb2 = StoryBible(project_id=p2.id)
        store.save_project(p1, sb1)
        store.save_project(p2, sb2)
        projects = store.list_projects()
        assert len(projects) == 2

    def test_delete_project(self, store, project, story_bible):
        store.save_project(project, story_bible)
        result = store.delete_project(project.id)
        assert result is True
        assert store.list_projects() == []

    def test_delete_nonexistent_project(self, store):
        result = store.delete_project(uuid4())
        assert result is False

    def test_nforge_file_is_json(self, store, project, story_bible):
        path = store.save_project(project, story_bible)
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "project" in data
        assert "story_bible" in data
        assert data["project"]["name"] == "Test Game"

    def test_story_bible_preserved(self, store, project):
        from NarrativeForge.Engine.models import Character, Location, TimelineEvent
        c = Character(name="Hero")
        loc = Location(name="Castle")
        event = TimelineEvent(title="War", order=1)
        bible = StoryBible(
            project_id=project.id,
            characters={c.id: c},
            locations={loc.id: loc},
            timeline=[event],
        )
        path = store.save_project(project, bible)
        loaded_project, loaded_bible = store.load_project(path)
        assert len(loaded_bible.characters) == 1
        assert len(loaded_bible.locations) == 1
        assert len(loaded_bible.timeline) == 1
