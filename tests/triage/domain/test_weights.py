from __future__ import annotations

import pytest

from genome_toolkit.triage.domain.weights import ScoringWeights


class TestScoringWeights:
    def test_defaults_sum_to_one(self):
        w = ScoringWeights()
        total = (
            w.priority + w.overdue + w.evidence + w.lab_signal
            + w.context + w.severity + w.stuck
        )
        assert abs(total - 1.0) < 1e-9

    def test_default_values(self):
        w = ScoringWeights()
        assert w.priority == 0.25
        assert w.overdue == 0.20
        assert w.evidence == 0.15
        assert w.lab_signal == 0.15
        assert w.context == 0.10
        assert w.severity == 0.10
        assert w.stuck == 0.05

    def test_custom_weights_valid(self):
        w = ScoringWeights(
            priority=0.30, overdue=0.20, evidence=0.10,
            lab_signal=0.10, context=0.10, severity=0.10, stuck=0.10,
        )
        assert w.priority == 0.30

    def test_custom_weights_invalid_sum(self):
        with pytest.raises(ValueError, match="sum to 1.0"):
            ScoringWeights(
                priority=0.50, overdue=0.20, evidence=0.15,
                lab_signal=0.15, context=0.10, severity=0.10, stuck=0.05,
            )

    def test_frozen(self):
        w = ScoringWeights()
        with pytest.raises(AttributeError):
            w.priority = 0.5  # type: ignore[misc]
