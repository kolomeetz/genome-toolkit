"""Tests for prepare_for_imputation.py — VCF export with sample duplication."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from prepare_for_imputation import genotype_to_vcf_fields, write_vcf


class TestGenotypeToVcfFields:
    def test_heterozygous(self):
        assert genotype_to_vcf_fields("AG") == ("A", "G", "0/1")

    def test_homozygous(self):
        assert genotype_to_vcf_fields("AA") == ("A", ".", "0/0")

    def test_haploid(self):
        assert genotype_to_vcf_fields("A") == ("A", ".", "0")

    def test_invalid_length(self):
        assert genotype_to_vcf_fields("AGT") is None


class TestWriteVcf:
    def test_default_20_sample_columns(self, tmp_path):
        variants = [("1", 100, "rs123", "AG")]
        out = str(tmp_path / "test.vcf")
        written, skipped = write_vcf(variants, out)

        assert written == 1
        lines = Path(out).read_text().strip().split("\n")
        header_line = [l for l in lines if l.startswith("#CHROM")][0]
        cols = header_line.split("\t")
        # 9 fixed columns + 20 sample columns
        assert len(cols) == 29
        assert cols[9] == "SAMPLE_01"
        assert cols[28] == "SAMPLE_20"

        # Data line should have GT duplicated 20 times
        data_line = [l for l in lines if not l.startswith("#")][0]
        data_cols = data_line.split("\t")
        assert len(data_cols) == 29
        gt_values = data_cols[9:]
        assert all(gt == "0/1" for gt in gt_values)

    def test_custom_sample_count(self, tmp_path):
        variants = [("1", 100, "rs456", "CC")]
        out = str(tmp_path / "test.vcf")
        written, _ = write_vcf(variants, out, num_samples=5)

        lines = Path(out).read_text().strip().split("\n")
        header_line = [l for l in lines if l.startswith("#CHROM")][0]
        cols = header_line.split("\t")
        assert len(cols) == 14  # 9 fixed + 5 samples

    def test_sorting(self, tmp_path):
        variants = [
            ("2", 500, "rs2", "AG"),
            ("1", 200, "rs1b", "CC"),
            ("1", 100, "rs1a", "TT"),
        ]
        out = str(tmp_path / "test.vcf")
        write_vcf(variants, out, num_samples=1)

        lines = Path(out).read_text().strip().split("\n")
        data = [l for l in lines if not l.startswith("#")]
        assert data[0].startswith("1\t100")
        assert data[1].startswith("1\t200")
        assert data[2].startswith("2\t500")
