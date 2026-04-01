from __future__ import annotations

from pathlib import Path

from genome_toolkit.triage.domain.item import EvidenceTier
from genome_toolkit.triage.domain.signals import Finding
from genome_toolkit.triage.infrastructure.vault.findings_parser import (
    VaultFindingsRepository,
)


FIXTURE_VAULT = Path(__file__).resolve().parents[2] / "fixtures" / "vault"


def test_parses_unincorporated_findings_only() -> None:
    repo = VaultFindingsRepository(FIXTURE_VAULT)
    findings = repo.get_unincorporated()

    assert len(findings) == 2
    assert all(isinstance(f, Finding) for f in findings)
    texts = [f.text for f in findings]
    assert any("IL1B" in t for t in texts)
    assert any("NAT2" in t for t in texts)


def test_preserves_metadata_fields() -> None:
    repo = VaultFindingsRepository(FIXTURE_VAULT)
    findings = repo.get_unincorporated()
    finding = next(f for f in findings if "IL1B" in f.text)

    assert "NotebookLM" in finding.source_note
    assert finding.evidence_tier == EvidenceTier.E3
    assert finding.actionable is True
    assert finding.incorporated_into is None


def test_skips_incorporated_findings() -> None:
    repo = VaultFindingsRepository(FIXTURE_VAULT)
    findings = repo.get_unincorporated()
    texts = [f.text for f in findings]
    assert not any("CYP2D6 *4/*10 reduced activity" in t for t in texts)
    assert not any("FADS1/FADS2 LD" in t for t in texts)
