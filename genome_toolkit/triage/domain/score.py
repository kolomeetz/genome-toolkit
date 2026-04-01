from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TriageBucket(Enum):
    DO_NOW = "DO_NOW"
    THIS_WEEK = "THIS_WEEK"
    BACKLOG = "BACKLOG"
    CONSIDER_DROPPING = "CONSIDER_DROPPING"


@dataclass(frozen=True)
class ScoreBreakdown:
    priority_score: float
    overdue_score: float
    evidence_score: float
    lab_signal_score: float
    context_score: float
    severity_score: float
    stuck_score: float


@dataclass(frozen=True)
class Score:
    value: float
    breakdown: ScoreBreakdown
    bucket: TriageBucket
