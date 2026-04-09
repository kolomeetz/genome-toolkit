#!/usr/bin/env python3
"""Check for newer PGC GWAS dataset configs on HuggingFace.

Queries the HuggingFace parquet API for each trait in the TRAITS registry
and compares available configs against the currently configured default.
Detects configs with a newer year suffix than what we're using.

Usage:
    python scripts/check_gwas_updates.py
    python scripts/check_gwas_updates.py --notify
    python scripts/check_gwas_updates.py --json

Exit codes:
    0  All traits are up to date.
    1  Updates available for one or more traits.
    2  Error during execution.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

import requests

# Import the authoritative trait registry from the ingest script.
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from ingest_pgc_gwas import TRAITS


def _extract_year(config_name: str) -> int | None:
    """Extract a 4-digit year from a config name like 'mdd2025' or 'anx2026'."""
    m = re.search(r"(\d{4})", config_name)
    if m:
        return int(m.group(1))
    return None


def _fetch_configs(dataset: str, session: requests.Session) -> list[str]:
    """Fetch available configs for a dataset from the HF parquet API.

    Returns a list of config names (e.g. ['mdd2023', 'mdd2025']).
    Handles rate limits with exponential backoff.
    """
    url = f"https://huggingface.co/api/datasets/{dataset}/parquet"
    for attempt in range(5):
        try:
            resp = session.get(url, timeout=30)
        except requests.RequestException as e:
            print(f"  Warning: request failed for {dataset}: {e}", file=sys.stderr)
            return []

        if resp.status_code == 429:
            wait = min(2 ** attempt * 10, 120)
            print(f"  Rate limited, waiting {wait}s (attempt {attempt + 1}/5)...",
                  file=sys.stderr)
            time.sleep(wait)
            continue

        if resp.status_code == 404:
            print(f"  Warning: dataset {dataset} not found (404)", file=sys.stderr)
            return []

        if not resp.ok:
            print(f"  Warning: HTTP {resp.status_code} for {dataset}", file=sys.stderr)
            return []

        # The parquet API returns a dict keyed by config name, each containing
        # split -> [shard URLs]. We only need the top-level keys.
        data = resp.json()
        if isinstance(data, dict):
            return list(data.keys())
        return []

    print(f"  Warning: gave up after rate limits for {dataset}", file=sys.stderr)
    return []


def _find_newer_configs(
    current_config: str, available_configs: list[str]
) -> list[str]:
    """Return configs that have a year newer than the current one."""
    current_year = _extract_year(current_config)
    if current_year is None:
        return []

    newer = []
    for cfg in available_configs:
        if cfg == current_config:
            continue
        year = _extract_year(cfg)
        if year is not None and year > current_year:
            newer.append(cfg)

    # Sort by year descending so the newest is first.
    newer.sort(key=lambda c: _extract_year(c) or 0, reverse=True)
    return newer


def _send_notification(title: str, message: str) -> None:
    """Send a macOS notification via osascript."""
    script = (
        f'display notification "{message}" '
        f'with title "{title}"'
    )
    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=10,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Warning: could not send macOS notification", file=sys.stderr)


def check_updates() -> dict[str, dict]:
    """Check all traits for available updates.

    Returns a dict keyed by trait name, each containing:
        - dataset: HF dataset ID
        - current_config: what we're using
        - available_configs: all configs on HF
        - newer_configs: configs with a newer year
    """
    session = requests.Session()
    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        session.headers["Authorization"] = f"Bearer {hf_token}"

    results: dict[str, dict] = {}
    for trait, meta in TRAITS.items():
        dataset = meta["dataset"]
        current = meta["default_config"]

        available = _fetch_configs(dataset, session)
        newer = _find_newer_configs(current, available)

        results[trait] = {
            "dataset": dataset,
            "display_name": meta["display_name"],
            "current_config": current,
            "available_configs": sorted(available),
            "newer_configs": newer,
        }

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check for newer PGC GWAS dataset configs on HuggingFace.",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Send a macOS notification if updates are found.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON for machine consumption.",
    )
    args = parser.parse_args()

    results = check_updates()

    traits_with_updates = {
        trait: info
        for trait, info in results.items()
        if info["newer_configs"]
    }

    if args.json_output:
        output = {
            "up_to_date": len(traits_with_updates) == 0,
            "traits": results,
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print(f"Checked {len(results)} traits against HuggingFace.\n")

        for trait, info in results.items():
            newer = info["newer_configs"]
            current = info["current_config"]
            available = info["available_configs"]

            if newer:
                print(f"  {trait} ({info['display_name']})")
                print(f"    Current:   {current}")
                print(f"    Newer:     {', '.join(newer)}")
                print(f"    All:       {', '.join(available)}")
                print()
            else:
                print(f"  {trait}: up to date ({current})")

        if traits_with_updates:
            count = len(traits_with_updates)
            print(f"\n{count} trait(s) have newer configs available.")
        else:
            print("\nAll traits are up to date.")

    # macOS notification
    if args.notify and traits_with_updates:
        names = ", ".join(traits_with_updates.keys())
        _send_notification(
            "GWAS Updates Available",
            f"Newer configs for: {names}",
        )

    sys.exit(1 if traits_with_updates else 0)


if __name__ == "__main__":
    main()
