"""Tests for preflight prerequisite checks."""
import json
import sqlite3
import pytest
from pathlib import Path

from scripts.check_prerequisites import (
    check_community_plugins_enabled,
    check_dataview_installed,
    check_templater_installed,
    check_database,
    check_vault_initialized,
    check_prerequisites,
    has_critical_failures,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vault(tmp_path):
    """Create a minimal valid vault structure."""
    for d in ["Genes", "Guides", "Reports", "Templates"]:
        (tmp_path / d).mkdir()
    obsidian = tmp_path / ".obsidian"
    obsidian.mkdir()
    (obsidian / "community-plugins.json").write_text(json.dumps(["dataview"]))
    plugins = obsidian / "plugins"
    plugins.mkdir()
    (plugins / "dataview").mkdir()
    (plugins / "dataview" / "main.js").write_text("// dataview")
    return tmp_path


@pytest.fixture
def db(tmp_path):
    """Create a minimal genome.db with one variant."""
    db_path = tmp_path / "genome.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE snps (rsid TEXT, profile_id TEXT, chromosome TEXT, "
        "position INTEGER, genotype TEXT, is_rsid INTEGER, source TEXT)"
    )
    conn.execute(
        "INSERT INTO snps VALUES ('rs4680', 'default', '22', 19951271, 'AG', 1, 'genotyped')"
    )
    conn.commit()
    conn.close()
    return db_path


# ---------------------------------------------------------------------------
# check_community_plugins_enabled
# ---------------------------------------------------------------------------

class TestCommunityPlugins:
    def test_ok_when_plugins_registered(self, vault):
        result = check_community_plugins_enabled(vault)
        assert result["status"] == "ok"

    def test_missing_when_file_absent(self, tmp_path):
        (tmp_path / ".obsidian").mkdir()
        result = check_community_plugins_enabled(tmp_path)
        assert result["status"] == "missing"
        assert "fix" in result and result["fix"]

    def test_missing_when_empty_array(self, tmp_path):
        obsidian = tmp_path / ".obsidian"
        obsidian.mkdir()
        (obsidian / "community-plugins.json").write_text("[]")
        result = check_community_plugins_enabled(tmp_path)
        assert result["status"] == "missing"

    def test_missing_when_invalid_json(self, tmp_path):
        obsidian = tmp_path / ".obsidian"
        obsidian.mkdir()
        (obsidian / "community-plugins.json").write_text("{bad json")
        result = check_community_plugins_enabled(tmp_path)
        assert result["status"] == "missing"


# ---------------------------------------------------------------------------
# check_dataview_installed
# ---------------------------------------------------------------------------

class TestDataview:
    def test_ok_when_installed(self, vault):
        result = check_dataview_installed(vault)
        assert result["status"] == "ok"

    def test_missing_when_no_plugin_dir(self, tmp_path):
        result = check_dataview_installed(tmp_path)
        assert result["status"] == "missing"
        assert "Dataview" in result["fix"]


# ---------------------------------------------------------------------------
# check_templater_installed
# ---------------------------------------------------------------------------

class TestTemplater:
    def test_warning_when_absent(self, tmp_path):
        result = check_templater_installed(tmp_path)
        assert result["status"] == "warning"

    def test_ok_when_installed(self, tmp_path):
        plugin_dir = tmp_path / ".obsidian" / "plugins" / "templater-obsidian"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "main.js").write_text("// templater")
        result = check_templater_installed(tmp_path)
        assert result["status"] == "ok"


# ---------------------------------------------------------------------------
# check_database
# ---------------------------------------------------------------------------

class TestDatabase:
    def test_ok_with_data(self, db):
        result = check_database(db)
        assert result["status"] == "ok"
        assert "1" in result["message"]  # "1 variants"

    def test_missing_when_no_file(self, tmp_path):
        result = check_database(tmp_path / "nope.db")
        assert result["status"] == "missing"

    def test_missing_when_no_snps_table(self, tmp_path):
        db_path = tmp_path / "empty.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE other (id INTEGER)")
        conn.close()
        result = check_database(db_path)
        assert result["status"] == "missing"
        assert "snps" in result["message"]

    def test_missing_when_zero_rows(self, tmp_path):
        db_path = tmp_path / "zero.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE snps (rsid TEXT, profile_id TEXT, chromosome TEXT, "
            "position INTEGER, genotype TEXT, is_rsid INTEGER, source TEXT)"
        )
        conn.commit()
        conn.close()
        result = check_database(db_path)
        assert result["status"] == "missing"
        assert "no variants" in result["message"]


# ---------------------------------------------------------------------------
# check_vault_initialized
# ---------------------------------------------------------------------------

class TestVaultInitialized:
    def test_ok_with_all_dirs(self, vault):
        result = check_vault_initialized(vault)
        assert result["status"] == "ok"

    def test_missing_when_dirs_absent(self, tmp_path):
        result = check_vault_initialized(tmp_path)
        assert result["status"] == "missing"
        assert "Genes" in result["message"]

    def test_partial_dirs(self, tmp_path):
        (tmp_path / "Genes").mkdir()
        (tmp_path / "Guides").mkdir()
        # Missing Reports and Templates
        result = check_vault_initialized(tmp_path)
        assert result["status"] == "missing"
        assert "Reports" in result["message"]


# ---------------------------------------------------------------------------
# check_prerequisites (integration)
# ---------------------------------------------------------------------------

class TestCheckPrerequisites:
    def test_all_pass_on_valid_vault(self, vault, db):
        results = check_prerequisites(vault, db)
        assert all(r["status"] in ("ok", "warning") for r in results)
        assert not has_critical_failures(results)

    def test_skips_db_when_not_provided(self, vault):
        results = check_prerequisites(vault)
        names = [r["name"] for r in results]
        assert "database" not in names

    def test_includes_db_when_provided(self, vault, db):
        results = check_prerequisites(vault, db)
        names = [r["name"] for r in results]
        assert "database" in names

    def test_detects_failures_on_empty_dir(self, tmp_path):
        results = check_prerequisites(tmp_path)
        assert has_critical_failures(results)

    def test_accepts_string_path(self, vault):
        results = check_prerequisites(str(vault))
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# has_critical_failures
# ---------------------------------------------------------------------------

class TestHasCriticalFailures:
    def test_false_when_all_ok(self):
        assert not has_critical_failures([
            {"name": "a", "status": "ok", "message": "", "fix": ""},
            {"name": "b", "status": "warning", "message": "", "fix": ""},
        ])

    def test_true_when_missing(self):
        assert has_critical_failures([
            {"name": "a", "status": "ok", "message": "", "fix": ""},
            {"name": "b", "status": "missing", "message": "", "fix": ""},
        ])
