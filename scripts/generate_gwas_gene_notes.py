#!/usr/bin/env python3
"""Generate Obsidian gene notes from GWAS hit files.

Reads all GWAS hit files in config/gwas/, maps SNPs to genes using the
curated gene_rsid_map.json and the genes table in genome.db, groups by
gene, and generates Obsidian-flavored markdown notes for top genes.

Usage:
    python scripts/generate_gwas_gene_notes.py
    python scripts/generate_gwas_gene_notes.py --top 10 --dry-run
    python scripts/generate_gwas_gene_notes.py --update
    python scripts/generate_gwas_gene_notes.py --vault-root ~/Brains/genome
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GWAS_DIR = PROJECT_ROOT / "config" / "gwas"
GENE_MAP_PATH = PROJECT_ROOT / "scripts" / "data" / "gene_rsid_map.json"
DEFAULT_DB = PROJECT_ROOT / "data" / "genome.db"

# Display-name mapping for trait slugs (matches GWAS file names).
TRAIT_DISPLAY: dict[str, str] = {
    "anxiety": "Anxiety disorders",
    "depression": "Major depressive disorder",
    "bipolar": "Bipolar disorder",
    "adhd": "ADHD",
    "ptsd": "Post-traumatic stress disorder",
    "substance-use": "Substance use disorders",
}

# Wikilink-friendly trait labels for Obsidian cross-references.
TRAIT_WIKILINKS: dict[str, str] = {
    "anxiety": "Anxiety",
    "depression": "Depression",
    "bipolar": "Bipolar Disorder",
    "adhd": "ADHD",
    "ptsd": "PTSD",
    "substance-use": "Substance Use",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_gene_rsid_map() -> tuple[dict[str, dict], dict[str, str]]:
    """Load gene_rsid_map.json. Returns (gene_info_by_symbol, rsid_to_gene)."""
    if not GENE_MAP_PATH.exists():
        print(f"Warning: gene map not found at {GENE_MAP_PATH}", file=sys.stderr)
        return {}, {}

    with open(GENE_MAP_PATH) as f:
        data = json.load(f)

    gene_info: dict[str, dict] = {}
    rsid_to_gene: dict[str, str] = {}
    for symbol, info in data.get("genes", {}).items():
        gene_info[symbol] = info
        for rsid in info.get("rsids", []):
            rsid_to_gene[rsid] = symbol

    return gene_info, rsid_to_gene


def load_genes_from_db(db_path: Path) -> tuple[dict[str, dict], dict[str, str]]:
    """Load gene info from genome.db genes table and enrichments.
    Returns (gene_info_by_symbol, rsid_to_gene).
    """
    gene_info: dict[str, dict] = {}
    rsid_to_gene: dict[str, str] = {}

    if not db_path.exists():
        return gene_info, rsid_to_gene

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # From genes table
    try:
        for row in conn.execute("SELECT gene_symbol, full_name, chromosome, rsids FROM genes"):
            symbol = row["gene_symbol"]
            if not symbol:
                continue
            rsids = json.loads(row["rsids"]) if row["rsids"] else []
            gene_info[symbol] = {
                "full_name": row["full_name"] or "",
                "chromosome": row["chromosome"] or "",
                "rsids": rsids,
            }
            for rsid in rsids:
                rsid_to_gene[rsid] = symbol
    except sqlite3.OperationalError:
        pass

    # From myvariant enrichments
    try:
        for row in conn.execute(
            "SELECT rsid, json_extract(data, '$.gene_symbol') as gene_symbol "
            "FROM enrichments WHERE source = 'myvariant' AND gene_symbol IS NOT NULL"
        ):
            rsid = row["rsid"]
            symbol = row["gene_symbol"]
            if rsid and symbol:
                rsid_to_gene[rsid] = symbol
                if symbol not in gene_info:
                    gene_info[symbol] = {"full_name": "", "chromosome": "", "rsids": []}
                if rsid not in gene_info[symbol].get("rsids", []):
                    gene_info[symbol].setdefault("rsids", []).append(rsid)
    except sqlite3.OperationalError:
        pass

    conn.close()
    return gene_info, rsid_to_gene


def load_gwas_hits() -> list[tuple[str, dict, list[dict]]]:
    """Load all GWAS hit files. Returns list of (trait_slug, metadata, hits)."""
    results = []
    for path in sorted(GWAS_DIR.glob("*-hits.json")):
        trait_slug = path.stem.replace("-hits", "")
        with open(path) as f:
            data = json.load(f)
        results.append((trait_slug, data, data.get("hits", [])))
    return results


# ---------------------------------------------------------------------------
# Gene grouping and ranking
# ---------------------------------------------------------------------------

@dataclass
class GeneHit:
    """A single GWAS association for a gene."""
    trait: str
    rsid: str
    effect: float | None
    p_value: float | None
    effect_allele: str | None
    other_allele: str | None
    effect_scale: str


@dataclass
class GeneRecord:
    """Aggregated GWAS data for one gene."""
    symbol: str
    full_name: str
    chromosome: str
    hits: list[GeneHit]

    @property
    def traits(self) -> list[str]:
        return sorted(set(h.trait for h in self.hits))

    @property
    def is_pleiotropic(self) -> bool:
        return len(self.traits) > 1

    @property
    def n_hits(self) -> int:
        return len(self.hits)

    @property
    def best_p(self) -> float:
        pvals = [h.p_value for h in self.hits if h.p_value is not None]
        return min(pvals) if pvals else 1.0


def group_by_gene(
    gwas_data: list[tuple[str, dict, list[dict]]],
    rsid_to_gene: dict[str, str],
    gene_info: dict[str, dict],
) -> dict[str, GeneRecord]:
    """Group GWAS hits by gene symbol."""
    records: dict[str, GeneRecord] = {}

    for trait_slug, metadata, hits in gwas_data:
        effect_scale = metadata.get("effect_scale", "beta")
        for hit in hits:
            rsid = hit.get("rsid")
            if not rsid:
                continue
            gene = rsid_to_gene.get(rsid)
            if not gene:
                continue

            gh = GeneHit(
                trait=trait_slug,
                rsid=rsid,
                effect=hit.get("effect"),
                p_value=hit.get("p_value"),
                effect_allele=hit.get("effect_allele"),
                other_allele=hit.get("other_allele"),
                effect_scale=effect_scale,
            )

            if gene not in records:
                info = gene_info.get(gene, {})
                records[gene] = GeneRecord(
                    symbol=gene,
                    full_name=info.get("full_name", ""),
                    chromosome=info.get("chromosome", ""),
                    hits=[],
                )
            records[gene].hits.append(gh)

    return records


def rank_genes(records: dict[str, GeneRecord], top_n: int) -> list[GeneRecord]:
    """Rank genes by pleiotropy (number of distinct traits) then total hit count."""
    ranked = sorted(
        records.values(),
        key=lambda r: (len(r.traits), r.n_hits, -r.best_p),
        reverse=True,
    )
    return ranked[:top_n]


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def _effect_direction(effect: float | None) -> str:
    if effect is None:
        return "?"
    return "risk (+)" if effect > 0 else "protective (-)"


def _fmt_p(p: float | None) -> str:
    if p is None:
        return "N/A"
    return f"{p:.2e}"


def _fmt_effect(effect: float | None) -> str:
    if effect is None:
        return "N/A"
    return f"{effect:+.4f}"


def generate_note(gene: GeneRecord, today: str) -> str:
    """Generate Obsidian-flavored markdown for a gene note."""
    trait_links = ", ".join(
        f"[[{TRAIT_WIKILINKS.get(t, t)}]]" for t in gene.traits
    )

    # YAML frontmatter
    traits_yaml = "\n".join(f"  - {TRAIT_WIKILINKS.get(t, t)}" for t in gene.traits)
    lines = [
        "---",
        "type: gene",
        f"gene_symbol: {gene.symbol}",
        f'full_name: "{gene.full_name}"' if gene.full_name else f"full_name: {gene.symbol}",
        f'chromosome: "{gene.chromosome}"' if gene.chromosome else "",
        "source: PGC-GWAS",
        "evidence_tier: gwas-significant",
        "traits:",
        traits_yaml,
        f"created: {today}",
        "tags:",
        "  - gene",
        "  - gwas",
        "---",
        "",
        f"# {gene.symbol}",
    ]

    if gene.full_name:
        lines.append(f"**{gene.full_name}**")
    lines.append("")

    # Gene description placeholder
    lines.extend([
        "## Gene Function",
        "",
        f"> [!info] Placeholder",
        f"> Gene function description for {gene.symbol} -- to be filled in with curated content.",
        "",
    ])

    # GWAS Associations table
    lines.append("## GWAS Associations")
    lines.append("")
    lines.append("| Trait | rsID | Effect | p-value | Direction |")
    lines.append("|-------|------|--------|---------|-----------|")

    # Sort by p-value (best first)
    sorted_hits = sorted(gene.hits, key=lambda h: h.p_value or 1.0)
    for h in sorted_hits:
        trait_link = f"[[{TRAIT_WIKILINKS.get(h.trait, h.trait)}]]"
        direction = _effect_direction(h.effect)
        lines.append(
            f"| {trait_link} | {h.rsid} | {_fmt_effect(h.effect)} | {_fmt_p(h.p_value)} | {direction} |"
        )

    lines.append("")

    # Cross-trait summary for pleiotropic genes
    if gene.is_pleiotropic:
        lines.append("## Cross-Trait Summary")
        lines.append("")
        lines.append(
            f"{gene.symbol} shows genome-wide significant associations across "
            f"**{len(gene.traits)} psychiatric traits**: {trait_links}. "
            f"This pleiotropy suggests the gene may influence shared biological "
            f"pathways underlying multiple conditions."
        )
        lines.append("")

        # Per-trait breakdown
        trait_groups: dict[str, list[GeneHit]] = defaultdict(list)
        for h in sorted_hits:
            trait_groups[h.trait].append(h)

        for trait, hits in trait_groups.items():
            display = TRAIT_DISPLAY.get(trait, trait)
            best = min(hits, key=lambda h: h.p_value or 1.0)
            lines.append(
                f"- **{display}**: {len(hits)} hit(s), best p = {_fmt_p(best.p_value)}"
            )

        lines.append("")

    return "\n".join(lines)


def generate_gwas_section(gene: GeneRecord) -> str:
    """Generate just the GWAS Associations section for appending to existing notes."""
    lines = [
        "",
        "## GWAS Associations",
        "",
        "| Trait | rsID | Effect | p-value | Direction |",
        "|-------|------|--------|---------|-----------|",
    ]

    sorted_hits = sorted(gene.hits, key=lambda h: h.p_value or 1.0)
    for h in sorted_hits:
        trait_link = f"[[{TRAIT_WIKILINKS.get(h.trait, h.trait)}]]"
        direction = _effect_direction(h.effect)
        lines.append(
            f"| {trait_link} | {h.rsid} | {_fmt_effect(h.effect)} | {_fmt_p(h.p_value)} | {direction} |"
        )

    lines.append("")

    if gene.is_pleiotropic:
        trait_links = ", ".join(
            f"[[{TRAIT_WIKILINKS.get(t, t)}]]" for t in gene.traits
        )
        lines.append(
            f"> [!note] Cross-trait pleiotropy\n"
            f"> {gene.symbol} has GWAS-significant associations across "
            f"{len(gene.traits)} traits: {trait_links}."
        )
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# File writing
# ---------------------------------------------------------------------------

def write_notes(
    genes: list[GeneRecord],
    vault_root: Path,
    update: bool,
    dry_run: bool,
) -> dict[str, int]:
    """Write gene notes to vault. Returns counts of created/updated/skipped."""
    genes_dir = vault_root / "Genes"
    genes_dir.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    stats = {"created": 0, "updated": 0, "skipped": 0, "exists": 0}

    for gene in genes:
        note_path = genes_dir / f"{gene.symbol}.md"
        exists = note_path.exists()

        if exists and not update:
            if dry_run:
                print(f"  SKIP {gene.symbol} (exists: {note_path})")
            stats["exists"] += 1
            continue

        if exists and update:
            # Check if GWAS section already present
            content = note_path.read_text()
            if "## GWAS Associations" in content:
                if dry_run:
                    print(f"  SKIP {gene.symbol} (GWAS section already present)")
                stats["skipped"] += 1
                continue

            # Append GWAS section
            section = generate_gwas_section(gene)
            if dry_run:
                print(f"  UPDATE {gene.symbol} -- append GWAS section ({gene.n_hits} hits, {len(gene.traits)} traits)")
            else:
                with open(note_path, "a") as f:
                    f.write(section)
                print(f"  Updated {note_path.name}")
            stats["updated"] += 1
            continue

        # Create new note
        content = generate_note(gene, today)
        if dry_run:
            print(f"  CREATE {gene.symbol} ({gene.n_hits} hits, {len(gene.traits)} traits, best p={_fmt_p(gene.best_p)})")
        else:
            note_path.write_text(content)
            print(f"  Created {note_path.name}")
        stats["created"] += 1

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Obsidian gene notes from PGC GWAS hit files.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top genes to process (default: 20).",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing notes by appending GWAS section if not present.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created/updated without writing files.",
    )
    parser.add_argument(
        "--vault-root",
        type=Path,
        default=None,
        help="Obsidian vault root (default: $GENOME_VAULT_ROOT or ~/Brains/genome).",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"Path to genome.db (default: {DEFAULT_DB}).",
    )
    args = parser.parse_args()

    # Resolve vault root
    vault_root = args.vault_root
    if vault_root is None:
        env_root = os.environ.get("GENOME_VAULT_ROOT")
        if env_root:
            vault_root = Path(env_root).expanduser()
        else:
            vault_root = Path.home() / "Brains" / "genome"
    vault_root = vault_root.resolve()

    if not vault_root.is_dir():
        print(f"ERROR: vault root not found: {vault_root}", file=sys.stderr)
        sys.exit(1)

    print(f"Vault root: {vault_root}")
    print(f"GWAS dir:   {GWAS_DIR}")

    # Build rsid -> gene mapping from both sources
    gene_info_map, rsid_to_gene_map = load_gene_rsid_map()
    db_info, db_rsid_map = load_genes_from_db(args.db)

    # Merge: gene_rsid_map takes precedence, db supplements
    for symbol, info in db_info.items():
        if symbol not in gene_info_map:
            gene_info_map[symbol] = info
    for rsid, gene in db_rsid_map.items():
        if rsid not in rsid_to_gene_map:
            rsid_to_gene_map[rsid] = gene

    print(f"Gene mappings: {len(gene_info_map)} genes, {len(rsid_to_gene_map)} rsids")

    # Load GWAS hits
    gwas_data = load_gwas_hits()
    total_hits = sum(len(hits) for _, _, hits in gwas_data)
    print(f"GWAS files:  {len(gwas_data)} traits, {total_hits:,} total hits")

    # Group by gene
    records = group_by_gene(gwas_data, rsid_to_gene_map, gene_info_map)
    print(f"Genes with GWAS hits: {len(records)}")

    if not records:
        print("No genes matched any GWAS hits. Check gene_rsid_map.json coverage.")
        sys.exit(0)

    # Rank and select top genes
    top_genes = rank_genes(records, args.top)
    print(f"\nTop {len(top_genes)} genes (by pleiotropy, then hit count):")
    for i, g in enumerate(top_genes, 1):
        traits = ", ".join(g.traits)
        print(f"  {i:2d}. {g.symbol:<12s} {g.n_hits:3d} hits  {len(g.traits)} traits  best p={_fmt_p(g.best_p)}  [{traits}]")

    # Write notes
    print(f"\n{'DRY RUN -- ' if args.dry_run else ''}Writing notes to {vault_root / 'Genes'}:")
    stats = write_notes(top_genes, vault_root, args.update, args.dry_run)

    print(f"\nDone: {stats['created']} created, {stats['updated']} updated, "
          f"{stats['exists']} existing (skipped), {stats['skipped']} already had GWAS section")


if __name__ == "__main__":
    main()
