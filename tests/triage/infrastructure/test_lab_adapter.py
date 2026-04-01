from __future__ import annotations

from pathlib import Path

import pytest

from genome_toolkit.triage.domain.signals import Direction, LabSignal
from genome_toolkit.triage.infrastructure.scripts.lab_adapter import (
    VaultLabSignalRepository,
)


FIXTURE_VAULT = Path(__file__).resolve().parents[2] / "fixtures" / "vault"


@pytest.fixture
def lab_repo() -> VaultLabSignalRepository:
    return VaultLabSignalRepository(FIXTURE_VAULT)


def test_returns_lab_signal_instances(lab_repo: VaultLabSignalRepository) -> None:
    signals = lab_repo.get_active_signals()
    assert all(isinstance(s, LabSignal) for s in signals)


def test_crp_above_threshold(lab_repo: VaultLabSignalRepository) -> None:
    signals = lab_repo.get_active_signals()
    crp_signals = [s for s in signals if s.biomarker == "CRP"]
    assert len(crp_signals) == 1
    crp = crp_signals[0]
    assert crp.value == 1.8
    assert crp.threshold == 1.0
    assert crp.direction == Direction.ABOVE
    assert crp.z_score == pytest.approx(0.8)  # (1.8 - 1.0) / 1.0


def test_transferrin_saturation_signal(lab_repo: VaultLabSignalRepository) -> None:
    signals = lab_repo.get_active_signals()
    ts = [s for s in signals if s.biomarker == "Transferrin Saturation"]
    assert len(ts) == 1
    assert ts[0].direction == Direction.ABOVE
    assert ts[0].threshold == 45.0
    assert ts[0].value == 48.0
    assert "HFE" in ts[0].linked_genes


def test_alt_below_threshold_no_signal(lab_repo: VaultLabSignalRepository) -> None:
    signals = lab_repo.get_active_signals()
    alt = [s for s in signals if s.biomarker == "ALT"]
    # ALT=45 is below threshold of 80 -> no signal
    assert len(alt) == 0


def test_ferritin_below_threshold_no_signal(lab_repo: VaultLabSignalRepository) -> None:
    signals = lab_repo.get_active_signals()
    ferritin = [s for s in signals if s.biomarker == "Ferritin"]
    # Ferritin=285 is below threshold of 300 -> no signal
    assert len(ferritin) == 0


def test_crp_linked_genes(lab_repo: VaultLabSignalRepository) -> None:
    signals = lab_repo.get_active_signals()
    crp = next(s for s in signals if s.biomarker == "CRP")
    assert "IL1B" in crp.linked_genes


def test_z_score_calculation(lab_repo: VaultLabSignalRepository) -> None:
    signals = lab_repo.get_active_signals()
    ts = next(s for s in signals if s.biomarker == "Transferrin Saturation")
    expected_z = (48.0 - 45.0) / 45.0
    assert ts.z_score == pytest.approx(expected_z, rel=1e-3)


def test_confidence_is_between_0_and_1(lab_repo: VaultLabSignalRepository) -> None:
    signals = lab_repo.get_active_signals()
    for s in signals:
        assert 0.0 <= s.confidence <= 1.0
