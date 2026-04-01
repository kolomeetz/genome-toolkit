from __future__ import annotations

from datetime import date
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
from genome_toolkit.triage.domain.signals import Direction, LabSignal
from genome_toolkit.triage.domain.weights import ScoringWeights


@pytest.fixture
def default_weights() -> ScoringWeights:
    return ScoringWeights()


@pytest.fixture
def sample_item_id() -> ItemId:
    return ItemId.from_content("TestNote", "sample task")


@pytest.fixture
def sample_source() -> SourceLocation:
    return SourceLocation(file_path=Path("Reports/Summary.md"), line_number=42)


@pytest.fixture
def sample_item(sample_item_id: ItemId, sample_source: SourceLocation) -> TriageItem:
    return TriageItem(
        item_id=sample_item_id,
        source=sample_source,
        text="Request CRP blood test",
        priority=Priority.HIGH,
        context=Context.PRESCRIBER,
        due=date(2026, 4, 15),
        completed=False,
        evidence_tier=EvidenceTier.E1,
        severity=Severity.SIGNIFICANT,
        linked_genes=["IL6", "IL1B"],
        linked_systems=["Immune System"],
        blocked_by=[],
        clinically_validated=False,
    )


@pytest.fixture
def sample_lab_signal() -> LabSignal:
    return LabSignal(
        biomarker="CRP",
        value=8.5,
        threshold=5.0,
        direction=Direction.ABOVE,
        z_score=2.1,
        linked_genes=["IL6", "IL1B"],
        confidence=0.9,
    )
