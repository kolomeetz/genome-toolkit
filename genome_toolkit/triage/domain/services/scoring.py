from __future__ import annotations

from datetime import date

from genome_toolkit.triage.domain.item import TriageItem
from genome_toolkit.triage.domain.score import Score, ScoreBreakdown, TriageBucket
from genome_toolkit.triage.domain.signals import LabSignal
from genome_toolkit.triage.domain.weights import ScoringWeights

_UNKNOWN_DEFAULT = 60


class ScoringService:
    def score(
        self,
        item: TriageItem,
        weights: ScoringWeights,
        lab_signals: list[LabSignal],
        defer_count: int,
    ) -> Score:
        priority_raw = float(item.priority.value)
        overdue_raw = self._overdue_raw(item.due)
        evidence_raw = float(item.evidence_tier.value) if item.evidence_tier else _UNKNOWN_DEFAULT
        lab_raw = self._lab_signal_raw(item, lab_signals)
        context_raw = float(item.context.value)
        severity_raw = float(item.severity.value) if item.severity else _UNKNOWN_DEFAULT
        stuck_raw = min(defer_count * 33, 100)

        breakdown = ScoreBreakdown(
            priority_score=priority_raw * weights.priority,
            overdue_score=overdue_raw * weights.overdue,
            evidence_score=evidence_raw * weights.evidence,
            lab_signal_score=lab_raw * weights.lab_signal,
            context_score=context_raw * weights.context,
            severity_score=severity_raw * weights.severity,
            stuck_score=stuck_raw * weights.stuck,
        )

        composite = (
            breakdown.priority_score
            + breakdown.overdue_score
            + breakdown.evidence_score
            + breakdown.lab_signal_score
            + breakdown.context_score
            + breakdown.severity_score
            + breakdown.stuck_score
        )
        composite = max(0.0, min(100.0, composite))

        bucket = self._classify(composite)

        return Score(value=composite, breakdown=breakdown, bucket=bucket)

    @staticmethod
    def _overdue_raw(due: date | None) -> float:
        if due is None:
            return 40.0
        delta = (date.today() - due).days  # positive = overdue
        if delta < -7:
            return 0.0
        if delta < 0:
            return 20.0
        if delta == 0:
            return 60.0
        if delta <= 7:
            return 75.0
        if delta <= 14:
            return 85.0
        if delta <= 30:
            return 95.0
        return 100.0

    @staticmethod
    def _lab_signal_raw(item: TriageItem, lab_signals: list[LabSignal]) -> float:
        if not lab_signals or not item.linked_genes:
            return 0.0
        item_genes = set(item.linked_genes)
        max_z = 0.0
        for sig in lab_signals:
            if item_genes.intersection(sig.linked_genes):
                max_z = max(max_z, sig.z_score)
        if max_z == 0.0:
            return 0.0
        return min(max_z * 25, 100.0)

    @staticmethod
    def _classify(score: float) -> TriageBucket:
        if score >= 70:
            return TriageBucket.DO_NOW
        if score >= 50:
            return TriageBucket.THIS_WEEK
        if score >= 30:
            return TriageBucket.BACKLOG
        return TriageBucket.CONSIDER_DROPPING
