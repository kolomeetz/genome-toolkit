"""Genotek (Генотек) raw data parser.

Genotek is a Russian DTC genetic testing company. Their raw data export
uses the same 4-column TSV format as 23andMe: rsid, chromosome, position, genotype.
Header comments prefixed with # contain "Genotek" or "genotek.ru".
Assembly: GRCh37/hg19. Typical SNP count: 600K-700K (Illumina GSA arrays).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from .base import GenomeProvider, ProviderMetadata, QcStats, SnpRecord
from .twentythree import TwentyThreeAndMe


class Genotek(GenomeProvider):
    """Parser for Genotek raw data files.

    Reuses 23andMe's parsing logic since the TSV format is identical.
    Detection differentiates by looking for "genotek" in file header.
    """

    @classmethod
    def detect(cls, filepath: Path, header_lines: list[str]) -> float:
        """Detect Genotek format from header lines."""
        has_genotek_comment = False
        has_correct_header = False

        for line in header_lines:
            lower = line.lower()
            if "genotek" in lower:
                has_genotek_comment = True
            if not line.startswith("#") and "\t" in line:
                parts = line.split("\t")
                if len(parts) == 4:
                    if parts[0].startswith("rs") or parts[0].startswith("i"):
                        has_correct_header = True

        if has_genotek_comment and has_correct_header:
            return 0.96  # slightly higher than 23andMe to win when both match
        if has_genotek_comment:
            return 0.75
        return 0.0

    def metadata(self, filepath: Path, header_lines: list[str]) -> ProviderMetadata:
        """Extract Genotek metadata."""
        return ProviderMetadata(
            provider="genotek",
            provider_version="unknown",
            assembly="GRCh37",
            file_path=str(filepath),
        )

    def parse(self, filepath: Path) -> tuple[Iterator[SnpRecord], QcStats]:
        """Parse Genotek raw data file (same format as 23andMe)."""
        # Delegate to 23andMe's parser — identical TSV format
        parser = TwentyThreeAndMe()
        return parser.parse(filepath)
