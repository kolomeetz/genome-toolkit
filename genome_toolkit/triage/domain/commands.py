from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from genome_toolkit.triage.domain.item import Context, ItemId, Priority

_ALLOWED_DEFER_DAYS = frozenset({7, 14, 30})


@dataclass(frozen=True)
class DeferCommand:
    item_id: ItemId
    days: int
    note: str | None = None

    def __post_init__(self) -> None:
        if self.days not in _ALLOWED_DEFER_DAYS:
            raise ValueError(
                f"days must be in {{{', '.join(str(d) for d in sorted(_ALLOWED_DEFER_DAYS))}}}, got {self.days}"
            )


@dataclass(frozen=True)
class ApproveCommand:
    item_id: ItemId
    note: str | None = None


@dataclass(frozen=True)
class DropCommand:
    item_id: ItemId
    note: str

    def __post_init__(self) -> None:
        if not self.note.strip():
            raise ValueError("note is required and must be non-empty")


@dataclass(frozen=True)
class ChangePriorityCommand:
    item_id: ItemId
    new_priority: Priority
    note: str | None = None


@dataclass(frozen=True)
class CreateCommand:
    file_path: Path
    text: str
    priority: Priority
    context: Context
    due: date | None = None
