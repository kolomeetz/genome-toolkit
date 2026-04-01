from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from genome_toolkit.triage.domain.item import (
    Context,
    EvidenceTier,
    ItemId,
    Priority,
    SourceLocation,
    TriageItem,
)
from genome_toolkit.triage.domain.signals import Direction, Finding, LabSignal, StaleTopic
from genome_toolkit.triage.domain.suggestion import Suggestion, SuggestionSource
from genome_toolkit.triage.domain.services.suggestion import SuggestionGenerator


def _make_item(text: str = "Do something", genes: list[str] | None = None) -> TriageItem:
    return TriageItem(
        item_id=ItemId.from_content("Note", text),
        source=SourceLocation(file_path=Path("a.md"), line_number=1),
        text=text,
        priority=Priority.MEDIUM,
        context=Context.RESEARCH,
        due=None,
        completed=False,
        evidence_tier=None,
        severity=None,
        linked_genes=genes or [],
        linked_systems=[],
        blocked_by=[],
        clinically_validated=False,
    )


class TestSuggestionGenerator:
    def setup_method(self):
        self.gen = SuggestionGenerator()

    def test_unincorporated_finding_generates_suggestion(self):
        finding = Finding(
            text="NAT2 slow acetylator affects caffeine metabolism",
            source_note="Research/caffeine.md",
            evidence_tier=EvidenceTier.E2,
            actionable=True,
            incorporated_into=None,
        )
        results = self.gen.generate([finding], [], [], [])
        assert len(results) == 1
        assert results[0].source_type == SuggestionSource.UNINCORPORATED_FINDING

    def test_incorporated_finding_ignored(self):
        finding = Finding(
            text="something",
            source_note="a.md",
            evidence_tier=EvidenceTier.E3,
            actionable=True,
            incorporated_into="Genes/NAT2.md",
        )
        results = self.gen.generate([finding], [], [], [])
        assert len(results) == 0

    def test_non_actionable_finding_ignored(self):
        finding = Finding(
            text="background info",
            source_note="a.md",
            evidence_tier=EvidenceTier.E4,
            actionable=False,
            incorporated_into=None,
        )
        results = self.gen.generate([finding], [], [], [])
        assert len(results) == 0

    def test_stale_topic_generates_suggestion(self):
        stale = StaleTopic(
            topic="FKBP5 cortisol",
            last_researched=date(2025, 6, 1),
            recheck_interval_months=6,
            months_overdue=4.0,
            linked_genes=["FKBP5"],
        )
        results = self.gen.generate([], [stale], [], [])
        assert len(results) == 1
        assert results[0].source_type == SuggestionSource.STALE_RESEARCH

    def test_lab_threshold_generates_suggestion(self):
        sig = LabSignal(
            biomarker="CRP",
            value=8.0,
            threshold=5.0,
            direction=Direction.ABOVE,
            z_score=2.5,
            linked_genes=["IL6"],
            confidence=0.9,
        )
        results = self.gen.generate([], [], [sig], [])
        assert len(results) == 1
        assert results[0].source_type == SuggestionSource.LAB_THRESHOLD

    def test_dedup_marks_possible_duplicate(self):
        finding = Finding(
            text="Request CRP blood test from prescriber soon",
            source_note="a.md",
            evidence_tier=EvidenceTier.E2,
            actionable=True,
            incorporated_into=None,
        )
        existing = _make_item(text="Request CRP blood test from prescriber")
        results = self.gen.generate([finding], [], [], [existing])
        assert len(results) == 1
        assert results[0].possible_duplicate_of is not None

    def test_dedup_does_not_suppress(self):
        """Conservative dedup: marks as possible duplicate, never suppresses."""
        finding = Finding(
            text="Request CRP blood test from prescriber soon",
            source_note="a.md",
            evidence_tier=EvidenceTier.E2,
            actionable=True,
            incorporated_into=None,
        )
        existing = _make_item(text="Request CRP blood test from prescriber")
        results = self.gen.generate([finding], [], [], [existing])
        assert len(results) == 1  # still present, not suppressed

    def test_no_false_duplicate_for_dissimilar(self):
        finding = Finding(
            text="Update BDNF gene note with new pathway data",
            source_note="a.md",
            evidence_tier=EvidenceTier.E3,
            actionable=True,
            incorporated_into=None,
        )
        existing = _make_item(text="Request CRP blood test from prescriber")
        results = self.gen.generate([finding], [], [], [existing])
        assert len(results) == 1
        assert results[0].possible_duplicate_of is None
