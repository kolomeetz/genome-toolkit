#!/usr/bin/env python3
"""Preflight checks for genome-toolkit onboarding.

Validates that the Obsidian vault and database are ready before
running the onboarding engine. Each check returns a structured
result with status, message, and fix instructions.

Usage:
    python3 scripts/check_prerequisites.py --vault ~/Brains/genome
    python3 scripts/check_prerequisites.py --vault ~/Brains/genome --db data/genome.db
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

# Required directories that vault-template ships
EXPECTED_VAULT_DIRS = ["Genes", "Guides", "Reports", "Templates"]

# The one plugin that absolutely must be present
CRITICAL_PLUGIN = "dataview"

# Nice-to-have plugins
OPTIONAL_PLUGINS = ["templater-obsidian"]


def _check(
    name: str,
    status: str,
    message: str,
    fix: str = "",
) -> dict:
    return {"name": name, "status": status, "message": message, "fix": fix}


def check_community_plugins_enabled(vault_path: Path) -> dict:
    """Check that .obsidian/community-plugins.json exists and is non-empty."""
    cp_path = vault_path / ".obsidian" / "community-plugins.json"
    if not cp_path.exists():
        return _check(
            "community_plugins_enabled",
            "missing",
            "community-plugins.json not found — community plugins are not enabled",
            "Open Obsidian → Settings → Community plugins → enable 'Turn on community plugins', "
            "then install at least the Dataview plugin.",
        )
    try:
        data = json.loads(cp_path.read_text())
    except (json.JSONDecodeError, ValueError):
        return _check(
            "community_plugins_enabled",
            "missing",
            "community-plugins.json is corrupt or not valid JSON",
            "Delete the file and re-enable community plugins in Obsidian settings.",
        )
    if not isinstance(data, list) or len(data) == 0:
        return _check(
            "community_plugins_enabled",
            "missing",
            "community-plugins.json is empty — no plugins registered",
            "Install the Dataview plugin via Obsidian → Settings → Community plugins → Browse.",
        )
    return _check(
        "community_plugins_enabled",
        "ok",
        f"{len(data)} community plugin(s) registered",
    )


def check_dataview_installed(vault_path: Path) -> dict:
    """Check that the Dataview plugin files are present."""
    main_js = vault_path / ".obsidian" / "plugins" / "dataview" / "main.js"
    if not main_js.exists():
        return _check(
            "dataview_installed",
            "missing",
            "Dataview plugin not installed — MoC pages and dashboards will be empty",
            "Install Dataview: Obsidian → Settings → Community plugins → Browse → search 'Dataview' → Install → Enable.",
        )
    return _check(
        "dataview_installed",
        "ok",
        "Dataview plugin is installed",
    )


def check_templater_installed(vault_path: Path) -> dict:
    """Check that the Templater plugin is installed (optional)."""
    main_js = vault_path / ".obsidian" / "plugins" / "templater-obsidian" / "main.js"
    if not main_js.exists():
        return _check(
            "templater_installed",
            "warning",
            "Templater plugin not installed — template expansion will not work automatically",
            "Install Templater: Obsidian → Settings → Community plugins → Browse → search 'Templater' → Install → Enable.",
        )
    return _check(
        "templater_installed",
        "ok",
        "Templater plugin is installed",
    )


def check_database(db_path: Path) -> dict:
    """Check that genome.db exists and has variant data."""
    if not db_path.exists():
        return _check(
            "database",
            "missing",
            f"Database not found at {db_path}",
            "Run genome-import first: python3 scripts/import_genotypes.py --input <your-file>",
        )
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM snps")
        count = cursor.fetchone()[0]
        conn.close()
    except sqlite3.OperationalError:
        return _check(
            "database",
            "missing",
            f"Database at {db_path} has no 'snps' table — it may not be initialized",
            "Run genome-import to populate the database.",
        )
    if count == 0:
        return _check(
            "database",
            "missing",
            "Database exists but contains no variants",
            "Run genome-import to load your genotype data.",
        )
    return _check(
        "database",
        "ok",
        f"Database has {count:,} variants",
    )


def check_vault_initialized(vault_path: Path) -> dict:
    """Check that vault has the expected directories from vault-template."""
    missing = [d for d in EXPECTED_VAULT_DIRS if not (vault_path / d).is_dir()]
    if missing:
        return _check(
            "vault_initialized",
            "missing",
            f"Vault is missing expected directories: {', '.join(missing)}",
            "Initialize the vault from the template: cp -r vault-template/* <your-vault>/",
        )
    return _check(
        "vault_initialized",
        "ok",
        "Vault has all expected directories",
    )


def check_prerequisites(
    vault_path: str | Path,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Run all preflight checks and return a list of results.

    Each result is a dict with keys: name, status, message, fix.
    Status is one of: "ok", "missing", "warning".
    """
    vault = Path(vault_path).expanduser().resolve()
    results: list[dict] = []

    results.append(check_vault_initialized(vault))
    results.append(check_community_plugins_enabled(vault))
    results.append(check_dataview_installed(vault))
    results.append(check_templater_installed(vault))

    if db_path is not None:
        results.append(check_database(Path(db_path).expanduser().resolve()))

    return results


def has_critical_failures(results: list[dict]) -> bool:
    """Return True if any check has status 'missing'."""
    return any(r["status"] == "missing" for r in results)


def print_results(results: list[dict]) -> None:
    """Pretty-print check results to stdout."""
    icons = {"ok": "[OK]", "missing": "[FAIL]", "warning": "[WARN]"}
    print("\n--- Preflight Checks ---\n")
    for r in results:
        icon = icons.get(r["status"], "[??]")
        print(f"  {icon}  {r['name']}: {r['message']}")
        if r["status"] in ("missing", "warning") and r["fix"]:
            print(f"         Fix: {r['fix']}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Check prerequisites for genome onboarding")
    parser.add_argument("--vault", type=Path, required=True, help="Path to Obsidian vault")
    parser.add_argument("--db", type=Path, default=None, help="Path to genome.db (optional)")
    args = parser.parse_args()

    results = check_prerequisites(args.vault, args.db)
    print_results(results)

    if has_critical_failures(results):
        print("Onboarding cannot proceed — fix the issues above first.")
        sys.exit(1)
    else:
        print("All critical checks passed. Ready for onboarding.")


if __name__ == "__main__":
    main()
