#!/usr/bin/env python3
"""Goal-driven onboarding engine for genome-toolkit.

Reads health goals, queries genotype data, scores genes by priority,
and returns a ranked list for initial vault note generation.

Usage:
    python3 onboard.py --goals medication_safety mental_health --db genome.db
    python3 onboard.py --goals comprehensive --medications sertraline
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import DB_PATH, GOAL_MAP, SCORING_WEIGHTS, GENERATION_LIMITS, MIGRATIONS_DIR
from lib.db import get_connection, init_db


@dataclass
class ScoredGene:
    """A gene scored for onboarding priority."""
    symbol: str
    score: float
    reasons: list[str] = field(default_factory=list)
    has_genotype: bool = False
    variant_count: int = 0
    source: str = "unknown"  # genotyped or imputed


@dataclass
class OnboardingPlan:
    """The output of the onboarding engine."""
    goals: list[str]
    target_systems: list[str]
    ranked_genes: list[ScoredGene]
    first_reports: list[str]
    first_tests: list[str]
    first_protocols: list[str]
    total_available_variants: int = 0


def resolve_goals(goal_ids: list[str], goal_map: dict) -> dict:
    """Merge multiple goals into a unified target set."""
    merged = {
        "target_systems": [],
        "seed_genes": [],
        "first_reports": [],
        "first_tests": [],
        "first_protocols": [],
    }

    for gid in goal_ids:
        goal = goal_map.get(gid)
        if not goal:
            continue

        systems = goal.get("target_systems", [])
        if systems == "all":
            # Comprehensive: collect all systems from all goals
            for g in goal_map.values():
                s = g.get("target_systems", [])
                if isinstance(s, list):
                    merged["target_systems"].extend(s)
        elif isinstance(systems, list):
            merged["target_systems"].extend(systems)

        genes = goal.get("seed_genes", [])
        if genes == "top_scored":
            pass  # handled by scoring
        elif isinstance(genes, list):
            merged["seed_genes"].extend(genes)

        for key in ["first_reports", "first_tests", "first_protocols"]:
            merged[key].extend(goal.get(key, []))

    # Deduplicate while preserving order
    for key in merged:
        merged[key] = list(dict.fromkeys(merged[key]))

    return merged


def query_available_genotypes(db_path: Path, gene_map_path: Path, profile_id: str = "default") -> dict[str, dict]:
    """Query which seed genes have genotyped data.

    Returns: {gene_symbol: {rsids_found: [...], source: 'genotyped'/'imputed', count: N}}
    """
    with open(gene_map_path) as f:
        gene_data = json.load(f)["genes"]

    conn = get_connection(db_path)
    results = {}

    for symbol, info in gene_data.items():
        rsids = info["rsids"]
        placeholders = ",".join(["?"] * len(rsids))
        rows = conn.execute(
            f"SELECT rsid, genotype, source, r2_quality FROM snps WHERE rsid IN ({placeholders}) AND profile_id = ?",
            (*rsids, profile_id),
        ).fetchall()

        if rows:
            results[symbol] = {
                "rsids_found": [r["rsid"] for r in rows],
                "genotypes": {r["rsid"]: r["genotype"] for r in rows},
                "source": "genotyped" if any(r["source"] == "genotyped" for r in rows) else "imputed",
                "count": len(rows),
            }

    conn.close()
    return results


def score_gene(
    symbol: str,
    available: dict[str, dict],
    seed_genes: list[str],
    goal_ids: list[str],
    goal_map: dict,
    medications: list[str] | None = None,
    weights: dict | None = None,
) -> ScoredGene:
    """Score a single gene for onboarding priority.

    Scoring formula:
      score = w_med * medication_match
            + w_goal * goal_match
            + w_severe * severe_finding
            + w_data * data_quality
    """
    if weights is None:
        weights = SCORING_WEIGHTS

    w_med = weights.get("medication_match", 8)
    w_goal = weights.get("goal_match", 6)
    w_severe = weights.get("severe_finding", 5)
    w_data = weights.get("evidence_weight", 2)

    score = 0.0
    reasons = []
    has_genotype = symbol in available
    variant_count = available.get(symbol, {}).get("count", 0)
    source = available.get(symbol, {}).get("source", "unknown")

    # Goal match: is this gene in the seed list?
    if symbol in seed_genes:
        score += w_goal
        reasons.append("matches selected goal")

    # Data quality: do we have genotype data?
    if has_genotype:
        if source == "genotyped":
            score += w_data * 3  # highest confidence
            reasons.append("genotyped data available")
        else:
            score += w_data * 1  # imputed
            reasons.append("imputed data available")

    # Medication match: is this a CYP gene and user takes drugs metabolized by it?
    pgx_genes = {"CYP2D6", "CYP2C19", "CYP2C9", "CYP1A2", "CYP3A4", "CYP2B6", "DPYD", "TPMT", "NAT2", "SLCO1B1"}
    if symbol in pgx_genes and medications:
        score += w_med
        reasons.append(f"PGx gene (current medications: {', '.join(medications[:3])})")
    elif symbol in pgx_genes:
        score += w_med * 0.5  # PGx gene but no specific medication match
        reasons.append("PGx gene (no specific medication provided)")

    # Bonus for being in multiple goals' seed lists
    goal_count = sum(
        1 for gid in goal_ids
        if isinstance(goal_map.get(gid, {}).get("seed_genes"), list)
        and symbol in goal_map[gid]["seed_genes"]
    )
    if goal_count > 1:
        score += w_goal * 0.5 * (goal_count - 1)
        reasons.append(f"relevant to {goal_count} selected goals")

    return ScoredGene(
        symbol=symbol,
        score=score,
        reasons=reasons,
        has_genotype=has_genotype,
        variant_count=variant_count,
        source=source,
    )


def generate_onboarding_plan(
    goal_ids: list[str],
    db_path: Path,
    profile_id: str = "default",
    medications: list[str] | None = None,
    goal_map: dict | None = None,
    weights: dict | None = None,
    limits: dict | None = None,
) -> OnboardingPlan:
    """Generate a complete onboarding plan from goals and genotype data."""
    if goal_map is None:
        goal_map = GOAL_MAP
    if weights is None:
        weights = SCORING_WEIGHTS
    if limits is None:
        limits = GENERATION_LIMITS

    gene_map_path = Path(__file__).parent / "data" / "gene_rsid_map.json"

    # Resolve goals
    merged = resolve_goals(goal_ids, goal_map)

    # Query available genotypes
    available = query_available_genotypes(db_path, gene_map_path, profile_id)

    # Collect all candidate genes
    candidates = set(merged["seed_genes"])
    if "comprehensive" in goal_ids:
        with open(gene_map_path) as f:
            all_genes = json.load(f)["genes"].keys()
        candidates = set(all_genes)

    # Score each candidate
    scored = []
    for symbol in candidates:
        sg = score_gene(symbol, available, merged["seed_genes"], goal_ids, goal_map, medications, weights)
        scored.append(sg)

    # Sort by score descending, then alphabetically for ties
    scored.sort(key=lambda g: (-g.score, g.symbol))

    # Cap at limits
    max_genes = limits.get("max_genes", 12)
    min_genes = limits.get("min_genes", 8)
    ranked = scored[:max_genes]

    # Ensure minimum if we have enough candidates
    if len(ranked) < min_genes and len(scored) > len(ranked):
        ranked = scored[:min_genes]

    return OnboardingPlan(
        goals=goal_ids,
        target_systems=merged["target_systems"],
        ranked_genes=ranked,
        first_reports=merged["first_reports"],
        first_tests=merged["first_tests"],
        first_protocols=merged.get("first_protocols", []),
        total_available_variants=sum(v["count"] for v in available.values()),
    )


def main():
    parser = argparse.ArgumentParser(description="Generate onboarding plan from health goals")
    parser.add_argument("--goals", nargs="+", required=True, help="Health goal IDs from goal_map.yaml")
    parser.add_argument("--medications", nargs="*", default=None, help="Current medications")
    parser.add_argument("--profile", default="default", help="Profile ID")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Database path")
    args = parser.parse_args()

    plan = generate_onboarding_plan(args.goals, args.db, args.profile, args.medications)

    print(f"\n{'='*60}")
    print(f"Onboarding Plan: {', '.join(args.goals)}")
    print(f"{'='*60}")
    print(f"\nTarget Systems: {', '.join(plan.target_systems)}")
    print(f"Available Variants: {plan.total_available_variants}")
    print(f"\nGenes to Create ({len(plan.ranked_genes)}):")
    for i, g in enumerate(plan.ranked_genes, 1):
        data_flag = "+" if g.has_genotype else "-"
        print(f"  {i:2d}. [{data_flag}] {g.symbol:12s} score={g.score:.1f}  {'; '.join(g.reasons)}")
    print(f"\nFirst Reports: {', '.join(plan.first_reports)}")
    print(f"First Tests: {', '.join(plan.first_tests)}")
    print(f"First Protocols: {', '.join(plan.first_protocols)}")


if __name__ == "__main__":
    main()
