from uuid import uuid4
from NarrativeForge.Engine.models.dialogue import DialogueLine, DialogueExchange, DialogueResult
from NarrativeForge.Engine.models.quest import (
    QuestObjective,
    QuestPrerequisite,
    QuestReward,
    Quest,
)
from NarrativeForge.Engine.models.lore import LoreEntry


class TestDialogueLine:
    def test_dialogue_line_creation(self):
        char_id = uuid4()
        line = DialogueLine(
            character_id=char_id, character_name="Hero", text="Hello there!"
        )
        assert line.character_id == char_id
        assert line.character_name == "Hero"
        assert line.text == "Hello there!"
        assert line.emotion == ""
        assert line.action == ""
        assert line.pause_after == 0.0

    def test_dialogue_line_with_emotion_and_action(self):
        char_id = uuid4()
        line = DialogueLine(
            character_id=char_id,
            character_name="Villain",
            text="You dare?",
            emotion="anger",
            action="slams fist on table",
            pause_after=1.5,
        )
        assert line.emotion == "anger"
        assert line.action == "slams fist on table"
        assert line.pause_after == 1.5


class TestDialogueExchange:
    def test_dialogue_exchange_creation(self):
        exchange = DialogueExchange()
        assert exchange.id is not None
        assert exchange.lines == []
        assert exchange.context == ""
        assert exchange.mood == ""

    def test_dialogue_exchange_with_lines(self):
        char_id = uuid4()
        line1 = DialogueLine(character_id=char_id, character_name="A", text="Hi")
        line2 = DialogueLine(character_id=char_id, character_name="B", text="Hello")
        exchange = DialogueExchange(
            lines=[line1, line2], context="First meeting", mood="tense"
        )
        assert len(exchange.lines) == 2
        assert exchange.context == "First meeting"
        assert exchange.mood == "tense"


class TestDialogueResult:
    def test_dialogue_result_creation(self):
        result = DialogueResult()
        assert result.exchanges == []
        assert result.format == "text"
        assert result.formatted_text == ""

    def test_dialogue_result_with_exchanges(self):
        exchange = DialogueExchange(context="Scene 1")
        result = DialogueResult(
            exchanges=[exchange],
            format="script",
            formatted_text="A: Hello\nB: Hi",
        )
        assert len(result.exchanges) == 1
        assert result.format == "script"
        assert "A: Hello" in result.formatted_text


class TestQuestObjective:
    def test_quest_objective_creation(self):
        obj = QuestObjective(description="Defeat the dragon")
        assert obj.description == "Defeat the dragon"
        assert obj.id is not None
        assert obj.target == ""
        assert obj.quantity == 1
        assert obj.is_required is True

    def test_quest_objective_defaults(self):
        obj = QuestObjective(description="Explore the cave")
        assert obj.type.value == "talk"


class TestQuestPrerequisite:
    def test_quest_prerequisite_creation(self):
        quest_id = uuid4()
        prereq = QuestPrerequisite(quest_id=quest_id, relationship="ally")
        assert prereq.quest_id == quest_id
        assert prereq.relationship == "ally"


class TestQuestReward:
    def test_quest_reward_creation(self):
        reward = QuestReward(xp=100, gold=50, items=["sword", "shield"], reputation=10)
        assert reward.xp == 100
        assert reward.gold == 50
        assert len(reward.items) == 2
        assert reward.reputation == 10

    def test_quest_reward_defaults(self):
        reward = QuestReward()
        assert reward.xp == 0
        assert reward.gold == 0
        assert reward.items == []
        assert reward.reputation == 0


class TestQuest:
    def test_quest_creation(self):
        quest = Quest(name="Main Quest")
        assert quest.name == "Main Quest"
        assert quest.id is not None
        assert quest.description == ""
        assert quest.is_main_quest is False

    def test_quest_with_all_fields(self):
        faction_id = uuid4()
        obj = QuestObjective(description="Collect herbs", quantity=5)
        prereq = QuestPrerequisite(quest_id=uuid4())
        reward = QuestReward(xp=200, gold=100)
        quest = Quest(
            name="Herb Gathering",
            description="Gather rare herbs for the healer",
            objectives=[obj],
            prerequisites=[prereq],
            rewards=reward,
            faction_id=faction_id,
            is_main_quest=True,
        )
        assert len(quest.objectives) == 1
        assert len(quest.prerequisites) == 1
        assert quest.faction_id == faction_id
        assert quest.is_main_quest is True
        assert quest.rewards.xp == 200


class TestLoreEntryNew:
    def test_lore_entry_with_tags_and_related(self):
        related_id = uuid4()
        entry = LoreEntry(
            title="Ancient Magic",
            content="Mysterious forces",
            category="Magic",
            tags=["magic", "ancient", "powerful"],
            related_entries=[related_id],
        )
        assert entry.title == "Ancient Magic"
        assert "magic" in entry.tags
        assert len(entry.related_entries) == 1
        assert entry.related_entries[0] == related_id

    def test_lore_entry_defaults(self):
        entry = LoreEntry(title="Test Entry")
        assert entry.tags == []
        assert entry.related_entries == []
        assert entry.is_locked is False
