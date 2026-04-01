from __future__ import annotations

from datetime import date
from enum import Enum

import pytest

from genome_toolkit.triage.domain.signals import (
    Direction,
    Finding,
    LabSignal,
    StaleTopic,
)
from genome_toolkit.triage.domain.item import EvidenceTier


class TestDirection:
    def test_values(self):
        assert Direction.ABOVE.name == "ABOVE"
        assert Direction.BELOW.name == "BELOW"


class TestLabSignal:
    def test_creation(self):
        sig = LabSignal(
            biomarker="CRP",
            value=8.5,
            threshold=5.0,
            direction=Direction.ABOVE,
            z_score=2.1,
            linked_genes=["IL6", "IL1B"],
            confidence=0.9,
        )
        assert sig.biomarker == "CRP"
        assert sig.z_score == 2.1

    def test_frozen(self):
        sig = LabSignal(
            biomarker="CRP",
            value=8.5,
            threshold=5.0,
            direction=Direction.ABOVE,
            z_score=2.1,
            linked_genes=[],
            confidence=0.9,
        )
        with pytest.raises(AttributeError):
            sig.value = 10.0  # type: ignore[misc]


class TestFinding:
    def test_unincorporated(self):
        f = Finding(
            text="NAT2 slow acetylator affects caffeine",
            source_note="Research/caffeine.md",
            evidence_tier=EvidenceTier.E2,
            actionable=True,
            incorporated_into=None,
        )
        assert f.incorporated_into is None
        assert f.actionable is True

    def test_incorporated(self):
        f = Finding(
            text="something",
            source_note="a.md",
            evidence_tier=EvidenceTier.E4,
            actionable=False,
            incorporated_into="Genes/NAT2.md",
        )
        assert f.incorporated_into == "Genes/NAT2.md"


class TestStaleTopic:
    def test_creation(self):
        st = StaleTopic(
            topic="FKBP5 cortisol interventions",
            last_researched=date(2025, 10, 1),
            recheck_interval_months=6,
            months_overdue=3.0,
            linked_genes=["FKBP5"],
        )
        assert st.months_overdue == 3.0

    def test_frozen(self):
        st = StaleTopic(
            topic="t",
            last_researched=date(2025, 1, 1),
            recheck_interval_months=6,
            months_overdue=1.0,
            linked_genes=[],
        )
        with pytest.raises(AttributeError):
            st.topic = "changed"  # type: ignore[misc]
