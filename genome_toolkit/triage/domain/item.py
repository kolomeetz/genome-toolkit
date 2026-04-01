from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from enum import IntEnum
from pathlib import Path


class Priority(IntEnum):
    CRITICAL = 100
    HIGH = 75
    MEDIUM = 50
    LOW = 25


class Context(IntEnum):
    PRESCRIBER = 100
    TESTING = 80
    MONITORING = 60
    RESEARCH = 40
    VAULT_MAINTENANCE = 20


class EvidenceTier(IntEnum):
    E1 = 100
    E2 = 80
    E3 = 60
    E4 = 40
    E5 = 20


class Severity(IntEnum):
    LIFE_THREATENING = 100
    SIGNIFICANT = 75
    MODERATE = 50
    LIFESTYLE = 25
    UNKNOWN = 60


@dataclass(frozen=True)
class ItemId:
    value: str

    @classmethod
    def from_content(cls, file_stem: str, task_text: str) -> ItemId:
        raw = f"{file_stem}|{task_text}"
        return cls(value=hashlib.sha256(raw.encode()).hexdigest())

    @classmethod
    def from_block_id(cls, block_id: str) -> ItemId:
        return cls(value=block_id)


@dataclass(frozen=True)
class SourceLocation:
    file_path: Path
    line_number: int


@dataclass
class TriageItem:
    item_id: ItemId
    source: SourceLocation
    text: str
    priority: Priority
    context: Context
    due: date | None
    completed: bool
    evidence_tier: EvidenceTier | None
    severity: Severity | None
    linked_genes: list[str] = field(default_factory=list)
    linked_systems: list[str] = field(default_factory=list)
    blocked_by: list[ItemId] = field(default_factory=list)
    clinically_validated: bool = False

    def defer(self, days: int) -> DeferCommand:
        from genome_toolkit.triage.domain.commands import DeferCommand

        if days not in {7, 14, 30}:
            raise ValueError(f"days must be in {{7, 14, 30}}, got {days}")
        return DeferCommand(item_id=self.item_id, days=days)

    def approve(self) -> ApproveCommand:
        from genome_toolkit.triage.domain.commands import ApproveCommand

        return ApproveCommand(item_id=self.item_id)

    def drop(self, note: str) -> DropCommand:
        from genome_toolkit.triage.domain.commands import DropCommand

        return DropCommand(item_id=self.item_id, note=note)

    def change_priority(self, new: Priority) -> ChangePriorityCommand:
        from genome_toolkit.triage.domain.commands import ChangePriorityCommand

        return ChangePriorityCommand(item_id=self.item_id, new_priority=new)
