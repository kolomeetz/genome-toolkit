from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from genome_toolkit.triage.domain.item import TriageItem
from genome_toolkit.triage.domain.score import Score, TriageBucket
from genome_toolkit.triage.domain.suggestion import Suggestion


@dataclass
class ScoredItem:
    item: TriageItem
    score: Score


@dataclass
class TriageReport:
    scored_items: list[ScoredItem]
    suggestions: list[Suggestion]
    total_items: int
    bucket_counts: dict[TriageBucket, int]
    timestamp: datetime
