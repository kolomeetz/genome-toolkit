"""LabSignalRepository implementation: parse Biomarkers/ YAML frontmatter."""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import frontmatter

from genome_toolkit.triage.domain.ports.repositories import LabSignalRepository
from genome_toolkit.triage.domain.signals import Direction, LabSignal


class _ThresholdRule(NamedTuple):
    threshold: float
    direction: Direction
    linked_genes: list[str]
    confidence: float


# Clinical thresholds for generating signals.
# Multiple thresholds per biomarker are supported (higher threshold = higher z_score).
_THRESHOLD_RULES: dict[str, list[_ThresholdRule]] = {
    "CRP": [
        _ThresholdRule(1.0, Direction.ABOVE, ["IL1B", "IL6"], 0.8),
    ],
    "ALT": [
        _ThresholdRule(80.0, Direction.ABOVE, ["PNPLA3"], 0.7),
    ],
    "Ferritin": [
        _ThresholdRule(300.0, Direction.ABOVE, ["HFE"], 0.8),
    ],
    "Transferrin Saturation": [
        _ThresholdRule(45.0, Direction.ABOVE, ["HFE"], 0.9),
    ],
}


class VaultLabSignalRepository(LabSignalRepository):
    def __init__(self, vault_path: Path) -> None:
        self._vault_path = vault_path

    def get_active_signals(self) -> list[LabSignal]:
        biomarker_dir = self._vault_path / "Biomarkers"
        if not biomarker_dir.exists():
            return []

        signals: list[LabSignal] = []

        # Process all biomarker files, sorted by name (most recent last)
        for md_file in sorted(biomarker_dir.glob("*.md")):
            try:
                post = frontmatter.load(str(md_file))
                meta = dict(post.metadata) if post.metadata else {}
            except Exception:
                continue

            markers = meta.get("markers", [])
            if not isinstance(markers, list):
                continue

            for marker in markers:
                if not isinstance(marker, dict):
                    continue
                name = marker.get("name", "")
                value = marker.get("value")
                if value is None:
                    continue

                try:
                    value = float(value)
                except (ValueError, TypeError):
                    continue

                rules = _THRESHOLD_RULES.get(name, [])
                for rule in rules:
                    if rule.direction == Direction.ABOVE and value > rule.threshold:
                        z_score = (value - rule.threshold) / rule.threshold
                        signals.append(LabSignal(
                            biomarker=name,
                            value=value,
                            threshold=rule.threshold,
                            direction=rule.direction,
                            z_score=z_score,
                            linked_genes=list(rule.linked_genes),
                            confidence=rule.confidence,
                        ))
                    elif rule.direction == Direction.BELOW and value < rule.threshold:
                        z_score = (rule.threshold - value) / rule.threshold
                        signals.append(LabSignal(
                            biomarker=name,
                            value=value,
                            threshold=rule.threshold,
                            direction=rule.direction,
                            z_score=z_score,
                            linked_genes=list(rule.linked_genes),
                            confidence=rule.confidence,
                        ))

        return signals
