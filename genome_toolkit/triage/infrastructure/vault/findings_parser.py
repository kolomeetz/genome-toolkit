"""FindingsRepository implementation: parse Meta/Findings Index.md."""
from __future__ import annotations

import re
from pathlib import Path

from genome_toolkit.triage.domain.item import EvidenceTier
from genome_toolkit.triage.domain.ports.repositories import FindingsRepository
from genome_toolkit.triage.domain.signals import Finding

_EVIDENCE_MAP = {
    "E1": EvidenceTier.E1,
    "E2": EvidenceTier.E2,
    "E3": EvidenceTier.E3,
    "E4": EvidenceTier.E4,
    "E5": EvidenceTier.E5,
}

# Strip wikilinks for display: [[X]] -> X, [[X|Y]] -> Y
_WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]*?))?\]\]")


def _strip_wikilinks(text: str) -> str:
    def _repl(m: re.Match[str]) -> str:
        return m.group(2) if m.group(2) else m.group(1)
    return _WIKILINK_RE.sub(_repl, text)


class VaultFindingsRepository(FindingsRepository):
    def __init__(self, vault_path: Path) -> None:
        self._vault_path = vault_path

    def get_unincorporated(self) -> list[Finding]:
        findings_file = self._vault_path / "Meta" / "Findings Index.md"
        if not findings_file.exists():
            return []

        text = findings_file.read_text(encoding="utf-8")
        return self._parse_table(text)

    def _parse_table(self, text: str) -> list[Finding]:
        lines = text.splitlines()
        findings: list[Finding] = []

        # Find the table header
        header_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith("|") and "Finding" in line:
                header_idx = i
                break

        if header_idx is None:
            return []

        # Parse header to find column indices
        header = lines[header_idx]
        cols = [c.strip() for c in header.split("|")]
        # cols will have empty strings at start/end from leading/trailing |

        # Skip separator line
        data_start = header_idx + 2

        for line in lines[data_start:]:
            line = line.strip()
            if not line.startswith("|"):
                break

            cells = [c.strip() for c in line.split("|")]
            # cells[0] is empty (before first |), cells[-1] is empty (after last |)
            if len(cells) < 5:
                continue

            finding_text = cells[1].strip()
            source_note = cells[2].strip()
            evidence_str = cells[3].strip()
            incorporated = cells[4].strip()

            # Only return unincorporated findings
            incorporated_clean = _strip_wikilinks(incorporated).strip().lower()
            if "not yet" not in incorporated_clean:
                continue

            # Parse evidence tier
            evidence_tier = _EVIDENCE_MAP.get(evidence_str, EvidenceTier.E5)

            findings.append(Finding(
                text=finding_text,
                source_note=source_note,
                evidence_tier=evidence_tier,
                actionable=True,
                incorporated_into=None,
            ))

        return findings
