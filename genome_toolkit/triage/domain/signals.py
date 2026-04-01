from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from genome_toolkit.triage.domain.item import EvidenceTier


class Direction(Enum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"


@dataclass(frozen=True)
class LabSignal:
    biomarker: str
    value: float
    threshold: float
    direction: Direction
    z_score: float
    linked_genes: list[str]
    confidence: float


@dataclass(frozen=True)
class Finding:
    text: str
    source_note: str
    evidence_tier: EvidenceTier
    actionable: bool
    incorporated_into: str | None


@dataclass(frozen=True)
class StaleTopic:
    topic: str
    last_researched: date
    recheck_interval_months: int
    months_overdue: float
    linked_genes: list[str]
