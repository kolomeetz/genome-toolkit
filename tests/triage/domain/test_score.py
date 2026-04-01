from __future__ import annotations

import pytest

from genome_toolkit.triage.domain.score import Score, ScoreBreakdown, TriageBucket


class TestTriageBucket:
    def test_values(self):
        assert TriageBucket.DO_NOW.name == "DO_NOW"
        assert TriageBucket.THIS_WEEK.name == "THIS_WEEK"
        assert TriageBucket.BACKLOG.name == "BACKLOG"
        assert TriageBucket.CONSIDER_DROPPING.name == "CONSIDER_DROPPING"


class TestScoreBreakdown:
    def test_creation(self):
        bd = ScoreBreakdown(
            priority_score=25.0,
            overdue_score=15.0,
            evidence_score=12.0,
            lab_signal_score=7.5,
            context_score=6.0,
            severity_score=5.0,
            stuck_score=1.65,
        )
        assert bd.priority_score == 25.0

    def test_frozen(self):
        bd = ScoreBreakdown(
            priority_score=0,
            overdue_score=0,
            evidence_score=0,
            lab_signal_score=0,
            context_score=0,
            severity_score=0,
            stuck_score=0,
        )
        with pytest.raises(AttributeError):
            bd.priority_score = 10  # type: ignore[misc]


class TestScore:
    def test_creation(self):
        bd = ScoreBreakdown(25, 15, 12, 7.5, 6, 5, 1.65)
        s = Score(value=72.15, breakdown=bd, bucket=TriageBucket.DO_NOW)
        assert s.value == 72.15
        assert s.bucket == TriageBucket.DO_NOW

    def test_frozen(self):
        bd = ScoreBreakdown(0, 0, 0, 0, 0, 0, 0)
        s = Score(value=0, breakdown=bd, bucket=TriageBucket.CONSIDER_DROPPING)
        with pytest.raises(AttributeError):
            s.value = 50  # type: ignore[misc]
