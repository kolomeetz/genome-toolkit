from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from genome_toolkit.triage.domain.item import (
    Context,
    EvidenceTier,
    ItemId,
    Priority,
    Severity,
    SourceLocation,
    TriageItem,
)
from genome_toolkit.triage.domain.score import TriageBucket
from genome_toolkit.triage.domain.signals import Direction, LabSignal
from genome_toolkit.triage.domain.weights import ScoringWeights
from genome_toolkit.triage.domain.services.scoring import ScoringService


def _make_item(**overrides) -> TriageItem:
    defaults = dict(
        item_id=ItemId.from_content("Note", "task"),
        source=SourceLocation(file_path=Path("a.md"), line_number=1),
        text="Do something",
        priority=Priority.MEDIUM,
        context=Context.RESEARCH,
        due=None,
        completed=False,
        evidence_tier=None,
        severity=None,
        linked_genes=[],
        linked_systems=[],
        blocked_by=[],
        clinically_validated=False,
    )
    defaults.update(overrides)
    return TriageItem(**defaults)


def _make_lab_signal(biomarker: str = "CRP", z_score: float = 2.0, genes: list[str] | None = None) -> LabSignal:
    return LabSignal(
        biomarker=biomarker,
        value=8.0,
        threshold=5.0,
        direction=Direction.ABOVE,
        z_score=z_score,
        linked_genes=genes or [],
        confidence=0.9,
    )


class TestScoringService:
    def setup_method(self):
        self.service = ScoringService()
        self.weights = ScoringWeights()

    def test_priority_score(self):
        item = _make_item(priority=Priority.CRITICAL)
        score = self.service.score(item, self.weights, [], 0)
        # priority=100 * 0.25 = 25
        assert score.breakdown.priority_score == 25.0

    def test_priority_low(self):
        item = _make_item(priority=Priority.LOW)
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.priority_score == pytest.approx(25 * 0.25)

    def test_overdue_no_due(self):
        item = _make_item(due=None)
        score = self.service.score(item, self.weights, [], 0)
        # no due = 40 * 0.20 = 8
        assert score.breakdown.overdue_score == pytest.approx(40 * 0.20)

    def test_overdue_future_more_than_7d(self):
        item = _make_item(due=date.today() + timedelta(days=10))
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.overdue_score == pytest.approx(0 * 0.20)

    def test_overdue_future_1_to_7d(self):
        item = _make_item(due=date.today() + timedelta(days=3))
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.overdue_score == pytest.approx(20 * 0.20)

    def test_overdue_due_today(self):
        item = _make_item(due=date.today())
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.overdue_score == pytest.approx(60 * 0.20)

    def test_overdue_1_to_7d_overdue(self):
        item = _make_item(due=date.today() - timedelta(days=3))
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.overdue_score == pytest.approx(75 * 0.20)

    def test_overdue_8_to_14d(self):
        item = _make_item(due=date.today() - timedelta(days=10))
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.overdue_score == pytest.approx(85 * 0.20)

    def test_overdue_15_to_30d(self):
        item = _make_item(due=date.today() - timedelta(days=20))
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.overdue_score == pytest.approx(95 * 0.20)

    def test_overdue_more_than_30d(self):
        item = _make_item(due=date.today() - timedelta(days=45))
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.overdue_score == pytest.approx(100 * 0.20)

    def test_evidence_known(self):
        item = _make_item(evidence_tier=EvidenceTier.E1)
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.evidence_score == pytest.approx(100 * 0.15)

    def test_evidence_unknown(self):
        item = _make_item(evidence_tier=None)
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.evidence_score == pytest.approx(60 * 0.15)

    def test_lab_signal_no_signals(self):
        item = _make_item(linked_genes=["IL6"])
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.lab_signal_score == 0.0

    def test_lab_signal_linked(self):
        item = _make_item(linked_genes=["IL6"])
        sig = _make_lab_signal(z_score=3.0, genes=["IL6"])
        score = self.service.score(item, self.weights, [sig], 0)
        # min(3.0 * 25, 100) = 75; 75 * 0.15 = 11.25
        assert score.breakdown.lab_signal_score == pytest.approx(75 * 0.15)

    def test_lab_signal_capped_at_100(self):
        item = _make_item(linked_genes=["IL6"])
        sig = _make_lab_signal(z_score=5.0, genes=["IL6"])
        score = self.service.score(item, self.weights, [sig], 0)
        # min(5.0 * 25, 100) = 100; 100 * 0.15 = 15
        assert score.breakdown.lab_signal_score == pytest.approx(100 * 0.15)

    def test_lab_signal_unlinked_ignored(self):
        item = _make_item(linked_genes=["COMT"])
        sig = _make_lab_signal(z_score=3.0, genes=["IL6"])
        score = self.service.score(item, self.weights, [sig], 0)
        assert score.breakdown.lab_signal_score == 0.0

    def test_context_score(self):
        item = _make_item(context=Context.PRESCRIBER)
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.context_score == pytest.approx(100 * 0.10)

    def test_severity_known(self):
        item = _make_item(severity=Severity.LIFE_THREATENING)
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.severity_score == pytest.approx(100 * 0.10)

    def test_severity_unknown(self):
        item = _make_item(severity=None)
        score = self.service.score(item, self.weights, [], 0)
        assert score.breakdown.severity_score == pytest.approx(60 * 0.10)

    def test_stuck_score(self):
        item = _make_item()
        score = self.service.score(item, self.weights, [], 2)
        # min(2 * 33, 100) = 66; 66 * 0.05 = 3.3
        assert score.breakdown.stuck_score == pytest.approx(66 * 0.05)

    def test_stuck_capped(self):
        item = _make_item()
        score = self.service.score(item, self.weights, [], 5)
        # min(5 * 33, 100) = 100; 100 * 0.05 = 5
        assert score.breakdown.stuck_score == pytest.approx(100 * 0.05)

    def test_composite_score_is_sum_of_breakdown(self):
        item = _make_item(
            priority=Priority.CRITICAL,
            context=Context.PRESCRIBER,
            evidence_tier=EvidenceTier.E1,
            severity=Severity.SIGNIFICANT,
            due=date.today(),
        )
        score = self.service.score(item, self.weights, [], 0)
        expected = (
            score.breakdown.priority_score
            + score.breakdown.overdue_score
            + score.breakdown.evidence_score
            + score.breakdown.lab_signal_score
            + score.breakdown.context_score
            + score.breakdown.severity_score
            + score.breakdown.stuck_score
        )
        assert score.value == pytest.approx(expected)

    def test_bucket_assignment_do_now(self):
        item = _make_item(
            priority=Priority.CRITICAL,
            context=Context.PRESCRIBER,
            evidence_tier=EvidenceTier.E1,
            severity=Severity.LIFE_THREATENING,
            due=date.today() - timedelta(days=5),
        )
        score = self.service.score(item, self.weights, [], 0)
        assert score.bucket == TriageBucket.DO_NOW

    def test_score_clamped_0_to_100(self):
        item = _make_item(priority=Priority.LOW)
        score = self.service.score(item, self.weights, [], 0)
        assert 0 <= score.value <= 100
