from uuid import uuid4

import pytest

from NarrativeForge.Engine.models import GameGenre, Project, StoryBible
from NarrativeForge.Engine.versioning import DiffEngine, DiffResult, DiffType, VersionManager


@pytest.fixture
def sample_project():
    return Project(name="Test Game", genre=GameGenre.RPG)


@pytest.fixture
def sample_bible(sample_project):
    return StoryBible(project_id=sample_project.id)


@pytest.fixture
def manager(tmp_path):
    return VersionManager(tmp_path / "versions")


class TestDiffEngine:
    def test_no_changes(self):
        engine = DiffEngine()
        snap = {"a": 1, "b": "hello"}
        result = engine.compute_diff(snap, snap)
        assert not result.has_changes
        assert len(result.differences) == 0

    def test_added_keys(self):
        engine = DiffEngine()
        old = {"a": 1}
        new = {"a": 1, "b": 2}
        result = engine.compute_diff(old, new)
        assert len(result.added) == 1
        assert result.added[0].path == "b"
        assert result.added[0].new_value == 2

    def test_removed_keys(self):
        engine = DiffEngine()
        old = {"a": 1, "b": 2}
        new = {"a": 1}
        result = engine.compute_diff(old, new)
        assert len(result.removed) == 1
        assert result.removed[0].path == "b"
        assert result.removed[0].old_value == 2

    def test_modified_keys(self):
        engine = DiffEngine()
        old = {"a": 1}
        new = {"a": 2}
        result = engine.compute_diff(old, new)
        assert len(result.modified) == 1
        assert result.modified[0].path == "a"
        assert result.modified[0].old_value == 1
        assert result.modified[0].new_value == 2


class TestVersionManager:
    def test_create_and_list(self, manager, sample_project, sample_bible):
        v = manager.create_snapshot(sample_project, sample_bible, description="First")
        assert v.version_number == 1
        assert v.description == "First"

        versions = manager.list_versions(sample_project.id)
        assert len(versions) == 1
        assert versions[0].id == v.id

    def test_list_versions_newest_first(self, manager, sample_project, sample_bible):
        v1 = manager.create_snapshot(sample_project, sample_bible, description="v1")
        v2 = manager.create_snapshot(sample_project, sample_bible, description="v2")
        versions = manager.list_versions(sample_project.id)
        assert len(versions) == 2
        assert versions[0].version_number > versions[1].version_number

    def test_get_version(self, manager, sample_project, sample_bible):
        v = manager.create_snapshot(sample_project, sample_bible)
        retrieved = manager.get_version(sample_project.id, v.id)
        assert retrieved is not None
        assert retrieved.id == v.id

    def test_get_version_not_found(self, manager, sample_project):
        result = manager.get_version(sample_project.id, uuid4())
        assert result is None

    def test_compare_versions(self, manager, sample_project, sample_bible):
        v1 = manager.create_snapshot(sample_project, sample_bible, description="v1")
        modified_project = sample_project.model_copy(deep=True)
        modified_project.name = "Modified Game"
        v2 = manager.create_snapshot(modified_project, sample_bible, description="v2")
        diff = manager.compare_versions(sample_project.id, v1.id, v2.id)
        assert isinstance(diff, DiffResult)
        assert diff.has_changes

    def test_restore_version(self, manager, sample_project, sample_bible):
        v = manager.create_snapshot(sample_project, sample_bible)
        restored = manager.restore_version(sample_project.id, v.id)
        assert restored is not None
        project, bible = restored
        assert project.name == sample_project.name
        assert project.genre == sample_project.genre
        assert bible.project_id == sample_bible.project_id

    def test_delete_version(self, manager, sample_project, sample_bible):
        v = manager.create_snapshot(sample_project, sample_bible)
        result = manager.delete_version(sample_project.id, v.id)
        assert result is True
        assert manager.get_version(sample_project.id, v.id) is None

    def test_delete_nonexistent_version(self, manager, sample_project):
        result = manager.delete_version(sample_project.id, uuid4())
        assert result is False

    def test_version_number_increments(self, manager, sample_project, sample_bible):
        v1 = manager.create_snapshot(sample_project, sample_bible)
        v2 = manager.create_snapshot(sample_project, sample_bible)
        assert v2.version_number == v1.version_number + 1

    def test_snapshot_preserves_data(self, manager, sample_project, sample_bible):
        v = manager.create_snapshot(sample_project, sample_bible)
        retrieved = manager.get_version(sample_project.id, v.id)
        assert retrieved.snapshot["project"]["name"] == sample_project.name
        assert retrieved.snapshot["project"]["genre"] == sample_project.genre.value
