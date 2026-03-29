"""Tests for the onboarding scoring engine."""
import json
import pytest
from pathlib import Path

from lib.db import get_connection, init_db


REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = REPO_ROOT / "scripts" / "data" / "migrations"
GENE_MAP = REPO_ROOT / "scripts" / "data" / "gene_rsid_map.json"


def _setup_db_with_snps(tmp_path, snps: list[tuple]) -> Path:
    """Helper: create DB with migrations, seed genes, insert specific SNPs."""
    from scripts.seed_genes import seed_genes
    db_path = tmp_path / "test.db"
    seed_genes(db_path)

    conn = get_connection(db_path)
    for rsid, chrom, pos, genotype in snps:
        conn.execute(
            "INSERT INTO snps (rsid, profile_id, chromosome, position, genotype, is_rsid, source) VALUES (?, 'default', ?, ?, ?, 1, 'genotyped')",
            (rsid, chrom, pos, genotype),
        )
    conn.commit()
    conn.close()
    return db_path


class TestResolveGoals:
    def test_single_goal(self):
        from scripts.onboard import resolve_goals
        from lib.config import GOAL_MAP

        merged = resolve_goals(["medication_safety"], GOAL_MAP)
        assert "Drug Metabolism" in merged["target_systems"]
        assert "CYP2D6" in merged["seed_genes"]
        assert "Wallet Card" in merged["first_reports"]

    def test_multiple_goals_merge(self):
        from scripts.onboard import resolve_goals
        from lib.config import GOAL_MAP

        merged = resolve_goals(["medication_safety", "mental_health"], GOAL_MAP)
        assert "CYP2D6" in merged["seed_genes"]
        assert "COMT" in merged["seed_genes"]
        # Should deduplicate
        assert len(merged["seed_genes"]) == len(set(merged["seed_genes"]))

    def test_comprehensive_gets_all_systems(self):
        from scripts.onboard import resolve_goals
        from lib.config import GOAL_MAP

        merged = resolve_goals(["comprehensive"], GOAL_MAP)
        assert len(merged["target_systems"]) > 5


class TestScoreGene:
    def test_pgx_gene_with_medication_scores_highest(self):
        from scripts.onboard import score_gene
        from lib.config import GOAL_MAP

        sg = score_gene(
            "CYP2D6",
            available={"CYP2D6": {"count": 3, "source": "genotyped"}},
            seed_genes=["CYP2D6"],
            goal_ids=["medication_safety"],
            goal_map=GOAL_MAP,
            medications=["sertraline"],
        )
        assert sg.score > 15  # goal_match + medication_match + data_quality

    def test_gene_without_data_scores_lower(self):
        from scripts.onboard import score_gene
        from lib.config import GOAL_MAP

        with_data = score_gene("COMT", available={"COMT": {"count": 1, "source": "genotyped"}},
                               seed_genes=["COMT"], goal_ids=["mental_health"], goal_map=GOAL_MAP)
        without_data = score_gene("COMT", available={},
                                  seed_genes=["COMT"], goal_ids=["mental_health"], goal_map=GOAL_MAP)
        assert with_data.score > without_data.score

    def test_multi_goal_gene_gets_bonus(self):
        from scripts.onboard import score_gene
        from lib.config import GOAL_MAP

        # COMT is in both mental_health and addiction_recovery
        single = score_gene("COMT", available={}, seed_genes=["COMT"],
                           goal_ids=["mental_health"], goal_map=GOAL_MAP)
        multi = score_gene("COMT", available={}, seed_genes=["COMT"],
                          goal_ids=["mental_health", "addiction_recovery"], goal_map=GOAL_MAP)
        assert multi.score > single.score


class TestGenerateOnboardingPlan:
    def test_plan_respects_max_genes(self, tmp_path):
        from scripts.onboard import generate_onboarding_plan
        from lib.config import GOAL_MAP, SCORING_WEIGHTS

        db_path = _setup_db_with_snps(tmp_path, [("rs4680", "22", 19951271, "AG")])

        plan = generate_onboarding_plan(
            ["comprehensive"], db_path,
            limits={"max_genes": 12, "min_genes": 8},
        )
        assert len(plan.ranked_genes) <= 12

    def test_plan_includes_target_systems(self, tmp_path):
        from scripts.onboard import generate_onboarding_plan

        db_path = _setup_db_with_snps(tmp_path, [])
        plan = generate_onboarding_plan(["medication_safety"], db_path)
        assert "Drug Metabolism" in plan.target_systems

    def test_plan_includes_reports(self, tmp_path):
        from scripts.onboard import generate_onboarding_plan

        db_path = _setup_db_with_snps(tmp_path, [])
        plan = generate_onboarding_plan(["medication_safety"], db_path)
        assert "Wallet Card" in plan.first_reports

    def test_genotyped_genes_rank_higher(self, tmp_path):
        from scripts.onboard import generate_onboarding_plan

        # Insert COMT rs4680 as genotyped
        db_path = _setup_db_with_snps(tmp_path, [("rs4680", "22", 19951271, "AG")])

        plan = generate_onboarding_plan(["mental_health"], db_path)
        symbols = [g.symbol for g in plan.ranked_genes]
        comt_idx = symbols.index("COMT") if "COMT" in symbols else 999
        # COMT should be near the top since it has genotyped data
        assert comt_idx < 5

    def test_medication_boost(self, tmp_path):
        from scripts.onboard import generate_onboarding_plan

        db_path = _setup_db_with_snps(tmp_path, [
            ("rs3892097", "22", 42524947, "GA"),  # CYP2D6
        ])

        plan_no_meds = generate_onboarding_plan(["medication_safety"], db_path)
        plan_with_meds = generate_onboarding_plan(["medication_safety"], db_path, medications=["sertraline"])

        # Find CYP2D6 scores
        score_no_meds = next((g.score for g in plan_no_meds.ranked_genes if g.symbol == "CYP2D6"), 0)
        score_with_meds = next((g.score for g in plan_with_meds.ranked_genes if g.symbol == "CYP2D6"), 0)
        assert score_with_meds > score_no_meds
