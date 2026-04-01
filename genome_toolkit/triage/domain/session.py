from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum

from genome_toolkit.triage.domain.item import Context, ItemId, Priority


class Action(Enum):
    APPROVE = "APPROVE"
    DEFER = "DEFER"
    DROP = "DROP"
    CHANGE_PRIORITY = "CHANGE_PRIORITY"
    CREATE = "CREATE"


@dataclass(frozen=True)
class TriageStateSnapshot:
    priority: Priority | None
    due: date | None
    context: Context | None
    completed: bool


@dataclass(frozen=True)
class TriageDecision:
    item_id: ItemId
    action: Action
    previous: TriageStateSnapshot
    new: TriageStateSnapshot
    note: str | None


@dataclass
class TriageSession:
    session_id: str
    timestamp: datetime
    decisions: list[TriageDecision] = field(default_factory=list)

    def add_decision(self, decision: TriageDecision) -> None:
        # Check for conflicting actions on same item_id
        for existing in self.decisions:
            if existing.item_id == decision.item_id:
                raise ValueError(
                    f"conflicting actions on item {decision.item_id.value}: "
                    f"already has {existing.action.value}, cannot add {decision.action.value}"
                )
        self.decisions.append(decision)
