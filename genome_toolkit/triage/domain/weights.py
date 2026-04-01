from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringWeights:
    priority: float = 0.25
    overdue: float = 0.20
    evidence: float = 0.15
    lab_signal: float = 0.15
    context: float = 0.10
    severity: float = 0.10
    stuck: float = 0.05

    def __post_init__(self) -> None:
        total = (
            self.priority + self.overdue + self.evidence + self.lab_signal
            + self.context + self.severity + self.stuck
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                f"Weights must sum to 1.0, got {total:.4f}"
            )
