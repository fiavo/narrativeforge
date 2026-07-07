from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DiffType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class DiffEntry(BaseModel):
    path: str
    diff_type: DiffType
    old_value: Any = None
    new_value: Any = None


class DiffResult(BaseModel):
    differences: list[DiffEntry] = Field(default_factory=list)

    @property
    def added(self) -> list[DiffEntry]:
        return [d for d in self.differences if d.diff_type == DiffType.ADDED]

    @property
    def removed(self) -> list[DiffEntry]:
        return [d for d in self.differences if d.diff_type == DiffType.REMOVED]

    @property
    def modified(self) -> list[DiffEntry]:
        return [d for d in self.differences if d.diff_type == DiffType.MODIFIED]

    @property
    def has_changes(self) -> bool:
        return len(self.differences) > 0


class DiffEngine:
    def compute_diff(self, old_snapshot: dict, new_snapshot: dict) -> DiffResult:
        diffs: list[DiffEntry] = []
        all_keys = set(old_snapshot.keys()) | set(new_snapshot.keys())

        for key in sorted(all_keys):
            if key not in old_snapshot:
                diffs.append(DiffEntry(
                    path=key,
                    diff_type=DiffType.ADDED,
                    new_value=new_snapshot[key],
                ))
            elif key not in new_snapshot:
                diffs.append(DiffEntry(
                    path=key,
                    diff_type=DiffType.REMOVED,
                    old_value=old_snapshot[key],
                ))
            elif old_snapshot[key] != new_snapshot[key]:
                diffs.append(DiffEntry(
                    path=key,
                    diff_type=DiffType.MODIFIED,
                    old_value=old_snapshot[key],
                    new_value=new_snapshot[key],
                ))

        return DiffResult(differences=diffs)
