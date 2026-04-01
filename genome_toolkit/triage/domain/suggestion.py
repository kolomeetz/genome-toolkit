from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from genome_toolkit.triage.domain.item import Context, Priority


class SuggestionSource(Enum):
    UNINCORPORATED_FINDING = "UNINCORPORATED_FINDING"
    STALE_RESEARCH = "STALE_RESEARCH"
    LAB_THRESHOLD = "LAB_THRESHOLD"
    STUCK_ITEM = "STUCK_ITEM"


@dataclass(frozen=True)
class Suggestion:
    text: str
    source_type: SuggestionSource
    source_reference: str
    recommended_priority: Priority
    recommended_context: Context
    rationale: str
    possible_duplicate_of: str | None = None
