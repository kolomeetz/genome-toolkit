#!/usr/bin/env python3
"""Seed the genes table from gene_rsid_map.json.

Populates gene_symbol, full_name, chromosome, and rsids for all curated genes.
Safe to run multiple times — uses INSERT OR REPLACE.

Usage:
    python3 seed_genes.py [--db path/to/genome.db]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import DB_PATH, MIGRATIONS_DIR
from lib.db import get_connection, init_db


def seed_genes(db_path: Path) -> int:
    """Seed genes table from gene_rsid_map.json. Returns count of genes seeded."""
    map_path = Path(__file__).parent / "data" / "gene_rsid_map.json"
    if not map_path.exists():
        print(f"Error: Gene map not found at {map_path}")
        sys.exit(1)

    with open(map_path) as f:
        data = json.load(f)

    conn = get_connection(db_path)
    init_db(db_path, MIGRATIONS_DIR)

    count = 0
    for symbol, info in data["genes"].items():
        conn.execute(
            "INSERT OR REPLACE INTO genes (gene_symbol, full_name, chromosome, rsids) VALUES (?, ?, ?, ?)",
            (symbol, info["full_name"], info["chromosome"], json.dumps(info["rsids"])),
        )
        count += 1

    conn.commit()
    conn.close()
    return count


def main():
    parser = argparse.ArgumentParser(description="Seed genes table from gene_rsid_map.json")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Database path")
    args = parser.parse_args()

    count = seed_genes(args.db)
    print(f"Seeded {count} genes into {args.db}")


if __name__ == "__main__":
    main()
