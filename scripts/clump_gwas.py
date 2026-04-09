#!/usr/bin/env python3
"""LD clumping for GWAS hit files — remove correlated SNPs by position.

Performs simple position-based LD clumping: within each chromosome, sort
hits by p_value, greedily select the top SNP (lead), and remove all other
SNPs within a window (default 500 kb).  This keeps only independent signals
and prevents inflated allele tallies in the app.

Usage:
    python scripts/clump_gwas.py                        # all traits, 500 kb
    python scripts/clump_gwas.py --trait anxiety         # single trait
    python scripts/clump_gwas.py --window 250            # 250 kb window
    python scripts/clump_gwas.py --dry-run               # preview only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# Resolve config dir relative to repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
GWAS_CONFIG_DIR = REPO_ROOT / "config" / "gwas"


def discover_traits(trait_filter: str | None = None) -> list[Path]:
    """Return paths to *-hits.json files, optionally filtered to one trait."""
    if not GWAS_CONFIG_DIR.exists():
        print("ERROR: GWAS config directory not found:", GWAS_CONFIG_DIR, file=sys.stderr)
        sys.exit(1)

    if trait_filter:
        path = GWAS_CONFIG_DIR / f"{trait_filter}-hits.json"
        if not path.exists():
            print(f"ERROR: no hits file for trait '{trait_filter}'", file=sys.stderr)
            sys.exit(2)
        return [path]

    paths = sorted(GWAS_CONFIG_DIR.glob("*-hits.json"))
    # Exclude already-clumped files
    paths = [p for p in paths if "-hits-clumped.json" not in p.name]
    if not paths:
        print("ERROR: no *-hits.json files found in", GWAS_CONFIG_DIR, file=sys.stderr)
        sys.exit(2)
    return paths


def clump_hits(hits: list[dict], window_kb: int) -> list[dict]:
    """Position-based LD clumping within each chromosome.

    Within each chromosome, sort by p_value (ascending), then greedily
    select the lead SNP and remove all SNPs within `window_kb` kb.
    """
    window_bp = window_kb * 1000

    # Group by chromosome
    by_chr: dict[int | str, list[dict]] = {}
    for hit in hits:
        chrom = hit.get("chr")
        if chrom is None:
            continue
        by_chr.setdefault(chrom, []).append(hit)

    kept: list[dict] = []

    for chrom in sorted(by_chr.keys(), key=lambda c: (isinstance(c, str), c)):
        chrom_hits = sorted(by_chr[chrom], key=lambda h: h.get("p_value") or 1.0)
        selected: list[dict] = []

        for hit in chrom_hits:
            pos = hit.get("pos")
            if pos is None:
                continue
            # Check whether this SNP falls within the window of any already-selected lead
            is_clumped = False
            for lead in selected:
                if abs(pos - lead["pos"]) <= window_bp:
                    is_clumped = True
                    break
            if not is_clumped:
                selected.append(hit)

        kept.extend(selected)

    # Re-sort by p_value ascending (strongest first), matching input convention
    kept.sort(key=lambda h: h.get("p_value") or 1.0)
    return kept


def process_trait(path: Path, window_kb: int, dry_run: bool) -> dict:
    """Clump one trait file. Returns a summary dict."""
    data = json.loads(path.read_text())
    trait = data.get("trait", path.stem.replace("-hits", ""))
    display_name = data.get("display_name", trait)
    hits = data.get("hits", [])
    n_before = len(hits)

    clumped = clump_hits(hits, window_kb)
    n_after = len(clumped)

    if not dry_run:
        output = dict(data)
        output["hits"] = clumped
        output["n_hits"] = n_after
        output["clumping_window_kb"] = window_kb
        output["n_hits_before_clump"] = n_before
        output["n_hits_after_clump"] = n_after

        out_path = path.parent / f"{trait}-hits-clumped.json"
        out_path.write_text(json.dumps(output, indent=2))

    return {
        "trait": trait,
        "display_name": display_name,
        "before": n_before,
        "after": n_after,
        "removed": n_before - n_after,
        "pct_kept": round(n_after / n_before * 100, 1) if n_before else 0,
    }


def print_summary(summaries: list[dict], window_kb: int, dry_run: bool) -> None:
    """Print a formatted summary table."""
    if dry_run:
        print("\n[DRY RUN] No files written.\n")
    else:
        print()

    # Column widths
    trait_w = max(len(s["display_name"]) for s in summaries) + 2
    header = (
        f"{'Trait':<{trait_w}} {'Before':>8} {'After':>8} {'Removed':>8} {'Kept %':>8}"
    )
    print(f"LD clumping summary (window = {window_kb} kb)")
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    total_before = 0
    total_after = 0
    for s in summaries:
        total_before += s["before"]
        total_after += s["after"]
        print(
            f"{s['display_name']:<{trait_w}} {s['before']:>8,} {s['after']:>8,} "
            f"{s['removed']:>8,} {s['pct_kept']:>7.1f}%"
        )

    print("-" * len(header))
    total_removed = total_before - total_after
    total_pct = round(total_after / total_before * 100, 1) if total_before else 0
    print(
        f"{'TOTAL':<{trait_w}} {total_before:>8,} {total_after:>8,} "
        f"{total_removed:>8,} {total_pct:>7.1f}%"
    )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LD clumping for GWAS hit files — keep only independent signals.",
    )
    parser.add_argument(
        "--trait",
        type=str,
        default=None,
        help="Trait to clump (e.g. 'anxiety'). Omit to process all traits.",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=500,
        help="Clumping window in kb (default: 500).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print summary without writing clumped files.",
    )
    args = parser.parse_args()

    paths = discover_traits(args.trait)
    summaries: list[dict] = []

    for path in paths:
        summary = process_trait(path, args.window, args.dry_run)
        summaries.append(summary)

    print_summary(summaries, args.window, args.dry_run)

    if not args.dry_run:
        for s in summaries:
            out = GWAS_CONFIG_DIR / f"{s['trait']}-hits-clumped.json"
            print(f"  Wrote {out}")


if __name__ == "__main__":
    main()
