"""Tests for gene table seeding."""
import json
import pytest
from pathlib import Path

from lib.db import get_connection, init_db


REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = REPO_ROOT / "scripts" / "data" / "migrations"
GENE_MAP = REPO_ROOT / "scripts" / "data" / "gene_rsid_map.json"


class TestGeneRsidMap:
    """Validate gene_rsid_map.json structure."""

    @pytest.fixture
    def gene_map(self):
        with open(GENE_MAP) as f:
            return json.load(f)

    def test_has_genes(self, gene_map):
        assert "genes" in gene_map
        assert len(gene_map["genes"]) >= 50

    def test_each_gene_has_required_fields(self, gene_map):
        for symbol, info in gene_map["genes"].items():
            assert "full_name" in info, f"{symbol} missing full_name"
            assert "chromosome" in info, f"{symbol} missing chromosome"
            assert "rsids" in info, f"{symbol} missing rsids"
            assert isinstance(info["rsids"], list), f"{symbol} rsids not a list"
            assert len(info["rsids"]) >= 1, f"{symbol} has no rsids"

    def test_all_rsids_start_with_rs(self, gene_map):
        for symbol, info in gene_map["genes"].items():
            for rsid in info["rsids"]:
                assert rsid.startswith("rs"), f"{symbol}: {rsid} doesn't start with 'rs'"

    def test_key_pgx_genes_present(self, gene_map):
        pgx = ["CYP2D6", "CYP2C19", "CYP2C9", "CYP1A2", "DPYD", "TPMT"]
        for gene in pgx:
            assert gene in gene_map["genes"], f"PGx gene {gene} missing"

    def test_key_nutrition_genes_present(self, gene_map):
        nutrition = ["FADS1", "FADS2", "FTO", "MTHFR", "VDR", "LCT", "PNPLA3"]
        for gene in nutrition:
            assert gene in gene_map["genes"], f"Nutrition gene {gene} missing"

    def test_key_neuro_genes_present(self, gene_map):
        neuro = ["COMT", "DRD2", "BDNF", "SLC6A4", "OPRM1", "FKBP5"]
        for gene in neuro:
            assert gene in gene_map["genes"], f"Neuro gene {gene} missing"


class TestSeedGenes:
    """Test seeding genes into SQLite."""

    def test_seed_populates_table(self, tmp_path):
        from scripts.seed_genes import seed_genes

        db_path = tmp_path / "test.db"
        count = seed_genes(db_path)

        assert count >= 50
        conn = get_connection(db_path)
        row = conn.execute("SELECT COUNT(*) FROM genes").fetchone()[0]
        assert row == count
        conn.close()

    def test_seed_stores_rsids_as_json(self, tmp_path):
        from scripts.seed_genes import seed_genes

        db_path = tmp_path / "test.db"
        seed_genes(db_path)

        conn = get_connection(db_path)
        row = conn.execute("SELECT rsids FROM genes WHERE gene_symbol='COMT'").fetchone()
        rsids = json.loads(row[0])
        assert isinstance(rsids, list)
        assert "rs4680" in rsids
        conn.close()

    def test_seed_idempotent(self, tmp_path):
        from scripts.seed_genes import seed_genes

        db_path = tmp_path / "test.db"
        count1 = seed_genes(db_path)
        count2 = seed_genes(db_path)

        assert count1 == count2
        conn = get_connection(db_path)
        row = conn.execute("SELECT COUNT(*) FROM genes").fetchone()[0]
        assert row == count1  # no duplicates
        conn.close()

    def test_gene_lookup_with_snps(self, tmp_path):
        """Simulate the workflow: seed genes, import SNPs, lookup by gene."""
        from scripts.seed_genes import seed_genes

        db_path = tmp_path / "test.db"
        seed_genes(db_path)

        conn = get_connection(db_path)
        # Insert a fake SNP matching COMT rs4680
        conn.execute(
            "INSERT INTO snps (rsid, profile_id, chromosome, position, genotype, is_rsid, source) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("rs4680", "default", "22", 19951271, "AG", True, "genotyped"),
        )
        conn.commit()

        # Lookup: "What's my COMT genotype?"
        row = conn.execute("""
            SELECT s.rsid, s.genotype, s.source
            FROM snps s
            JOIN genes g ON s.rsid IN (SELECT value FROM json_each(g.rsids))
            WHERE g.gene_symbol = 'COMT' AND s.profile_id = 'default'
        """).fetchone()

        assert row is not None
        assert row["rsid"] == "rs4680"
        assert row["genotype"] == "AG"
        conn.close()
