"""Abstract base class for genome data providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class SnpRecord:
    """A single SNP call from any provider."""
    source_id: str         # rsid or positional ID from the file
    chromosome: str
    position: int
    genotype: str          # two-char genotype (e.g., "AG", "CC")
    is_rsid: bool = True   # False for internal IDs (23andMe "i" prefix)
    ref: str | None = None
    alt: str | None = None
    quality: float | None = None  # for imputed data, r² score


@dataclass
class ProviderMetadata:
    """Metadata about the detected provider and file."""
    provider: str          # e.g., "23andme", "ancestry"
    provider_version: str  # e.g., "v4", "v5", "unknown"
    assembly: str          # e.g., "GRCh37", "GRCh38"
    file_path: str
    estimated_snp_count: int | None = None


@dataclass
class QcStats:
    """Quality control statistics from parsing."""
    total_input: int = 0
    passed_qc: int = 0
    no_calls: int = 0
    non_rsid: int = 0
    indels: int = 0
    invalid_alleles: int = 0
    malformed_lines: int = 0
    skipped_chrom: int = 0
    multiallelic: int = 0
    details: dict = field(default_factory=dict)


class GenomeProvider(ABC):
    """Abstract base for all genome data providers."""

    @classmethod
    @abstractmethod
    def detect(cls, filepath: Path, header_lines: list[str]) -> float:
        """Return confidence (0.0-1.0) that this file matches this provider.

        Args:
            filepath: Path to the input file
            header_lines: First 20 lines of the file (for header inspection)
        """
        ...

    @abstractmethod
    def parse(self, filepath: Path) -> tuple[Iterator[SnpRecord], QcStats]:
        """Parse the file, yielding SnpRecord objects.

        Returns:
            Tuple of (iterator of records, QC statistics)
        """
        ...

    @abstractmethod
    def metadata(self, filepath: Path, header_lines: list[str]) -> ProviderMetadata:
        """Extract provider metadata from the file."""
        ...


def read_header_lines(filepath: Path, n: int = 20) -> list[str]:
    """Read the first N lines of a file for format detection."""
    import gzip

    lines = []
    opener = gzip.open if str(filepath).endswith(".gz") else open
    mode = "rt" if str(filepath).endswith(".gz") else "r"

    with opener(filepath, mode) as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            lines.append(line.rstrip("\n"))
    return lines


def detect_provider(filepath: Path) -> tuple[type[GenomeProvider], float]:
    """Auto-detect the provider for a genome file.

    Returns the best-matching provider class and its confidence score.
    Raises ValueError if no provider matches with confidence > 0.
    """
    from . import twentythree, ancestry, myheritage, vcf

    providers: list[type[GenomeProvider]] = [
        twentythree.TwentyThreeAndMe,
        ancestry.AncestryDNA,
        myheritage.MyHeritage,
        vcf.GenericVCF,
    ]

    header_lines = read_header_lines(filepath)
    best_provider = None
    best_confidence = 0.0

    for provider_cls in providers:
        confidence = provider_cls.detect(filepath, header_lines)
        if confidence > best_confidence:
            best_confidence = confidence
            best_provider = provider_cls

    if best_provider is None or best_confidence == 0:
        raise ValueError(
            f"Could not detect genome data format for {filepath}. "
            "Supported formats: 23andMe, AncestryDNA, MyHeritage, VCF."
        )

    return best_provider, best_confidence
