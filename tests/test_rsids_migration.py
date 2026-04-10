"""Tests for migration 006: normalize genes.rsids to JSON arrays."""
import json
import sqlite3
import pytest

from lib.db import get_connection, apply_migrations, init_db


MIGRATIONS_DIR_NAME = "scripts/data/migrations"


def _insert_genes(conn, rows):
    """Insert test rows into genes table bypassing JSON encoding."""
    conn.executemany(
        "INSERT OR REPLACE INTO genes (gene_symbol, full_name, chromosome, rsids) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def _get_rsids(conn, gene_symbol):
    row = conn.execute(
        "SELECT rsids FROM genes WHERE gene_symbol = ?", (gene_symbol,)
    ).fetchone()
    return row[0] if row else None


class TestRsidsMigration:
    """Verify migration 006 converts all rsids variants to JSON arrays."""

    def test_null_rsids_unchanged(self, tmp_db, migrations_dir):
        """NULL rsids should remain NULL after migration."""
        # Apply migrations up through 005 by excluding 006, then insert, then apply 006
        # Simpler: apply all migrations, insert raw data via direct UPDATE, re-run just the logic
        init_db(tmp_db, migrations_dir)
        conn = get_connection(tmp_db)

        conn.execute(
            "INSERT OR REPLACE INTO genes (gene_symbol, rsids) VALUES ('NULL_GENE', NULL)"
        )
        conn.commit()

        # Apply the migration SQL directly
        sql = (migrations_dir / "006_normalize_genes_rsids.sql").read_text()
        conn.executescript(sql)

        assert _get_rsids(conn, "NULL_GENE") is None
        conn.close()

    def test_empty_rsids_unchanged(self, tmp_db, migrations_dir):
        """Empty-string rsids should remain unchanged (not converted to NULL or array)."""
        init_db(tmp_db, migrations_dir)
        conn = get_connection(tmp_db)

        conn.execute(
            "INSERT OR REPLACE INTO genes (gene_symbol, rsids) VALUES ('EMPTY_GENE', '')"
        )
        conn.commit()

        sql = (migrations_dir / "006_normalize_genes_rsids.sql").read_text()
        conn.executescript(sql)

        assert _get_rsids(conn, "EMPTY_GENE") == ""
        conn.close()

    def test_already_json_array_unchanged(self, tmp_db, migrations_dir):
        """Values already in JSON array format should not be double-encoded."""
        init_db(tmp_db, migrations_dir)
        conn = get_connection(tmp_db)

        original = '["rs1801133","rs1801131"]'
        conn.execute(
            "INSERT OR REPLACE INTO genes (gene_symbol, rsids) VALUES ('MTHFR', ?)",
            (original,),
        )
        conn.commit()

        sql = (migrations_dir / "006_normalize_genes_rsids.sql").read_text()
        conn.executescript(sql)

        result = _get_rsids(conn, "MTHFR")
        assert result == original
        conn.close()

    def test_single_rsid_wrapped(self, tmp_db, migrations_dir):
        """A single plain rsid text should be wrapped in a JSON array."""
        init_db(tmp_db, migrations_dir)
        conn = get_connection(tmp_db)

        conn.execute(
            "INSERT OR REPLACE INTO genes (gene_symbol, rsids) VALUES ('SINGLE_GENE', 'rs4680')"
        )
        conn.commit()

        sql = (migrations_dir / "006_normalize_genes_rsids.sql").read_text()
        conn.executescript(sql)

        result = _get_rsids(conn, "SINGLE_GENE")
        assert result is not None
        parsed = json.loads(result)
        assert parsed == ["rs4680"]
        conn.close()

    def test_comma_separated_converted(self, tmp_db, migrations_dir):
        """Comma-separated rsids should be converted to a JSON array."""
        init_db(tmp_db, migrations_dir)
        conn = get_connection(tmp_db)

        conn.execute(
            "INSERT OR REPLACE INTO genes (gene_symbol, rsids) VALUES ('MULTI_GENE', 'rs4680,rs6275,rs4818')"
        )
        conn.commit()

        sql = (migrations_dir / "006_normalize_genes_rsids.sql").read_text()
        conn.executescript(sql)

        result = _get_rsids(conn, "MULTI_GENE")
        assert result is not None
        parsed = json.loads(result)
        assert parsed == ["rs4680", "rs6275", "rs4818"]
        conn.close()

    def test_comma_separated_with_spaces(self, tmp_db, migrations_dir):
        """Comma-separated rsids with extra whitespace should be trimmed."""
        init_db(tmp_db, migrations_dir)
        conn = get_connection(tmp_db)

        conn.execute(
            "INSERT OR REPLACE INTO genes (gene_symbol, rsids) VALUES ('SPACE_GENE', ' rs123 , rs456 ')"
        )
        conn.commit()

        sql = (migrations_dir / "006_normalize_genes_rsids.sql").read_text()
        conn.executescript(sql)

        result = _get_rsids(conn, "SPACE_GENE")
        assert result is not None
        parsed = json.loads(result)
        assert parsed == ["rs123", "rs456"]
        conn.close()

    def test_json_each_query_works_after_migration(self, tmp_db, migrations_dir):
        """After migration, json_each(genes.rsids) should resolve SNPs correctly."""
        init_db(tmp_db, migrations_dir)
        conn = get_connection(tmp_db)

        # Insert a gene with comma-separated rsids (pre-migration format)
        conn.execute(
            "INSERT OR REPLACE INTO genes (gene_symbol, rsids) VALUES ('COMT', 'rs4680,rs4818')"
        )
        # Insert a matching SNP
        conn.execute(
            "INSERT INTO snps (rsid, profile_id, chromosome, position, genotype, is_rsid, source) "
            "VALUES ('rs4680', 'default', '22', 19951271, 'AG', 1, 'genotyped')"
        )
        conn.commit()

        # Apply migration
        sql = (migrations_dir / "006_normalize_genes_rsids.sql").read_text()
        conn.executescript(sql)

        # Query using json_each — should find the SNP
        row = conn.execute("""
            SELECT s.rsid, s.genotype
            FROM snps s
            JOIN genes g ON s.rsid IN (SELECT value FROM json_each(g.rsids))
            WHERE g.gene_symbol = 'COMT' AND s.profile_id = 'default'
        """).fetchone()

        assert row is not None, "json_each query returned no results after migration"
        assert row[0] == "rs4680"
        assert row[1] == "AG"
        conn.close()

    def test_migration_idempotent(self, tmp_db, migrations_dir):
        """Running the migration SQL twice should not corrupt data."""
        init_db(tmp_db, migrations_dir)
        conn = get_connection(tmp_db)

        conn.execute(
            "INSERT OR REPLACE INTO genes (gene_symbol, rsids) VALUES ('IDEMPOTENT_GENE', 'rs111,rs222')"
        )
        conn.commit()

        sql = (migrations_dir / "006_normalize_genes_rsids.sql").read_text()
        conn.executescript(sql)
        first = _get_rsids(conn, "IDEMPOTENT_GENE")

        conn.executescript(sql)
        second = _get_rsids(conn, "IDEMPOTENT_GENE")

        assert first == second
        parsed = json.loads(second)
        assert parsed == ["rs111", "rs222"]
        conn.close()
