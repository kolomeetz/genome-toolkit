"""Portable configuration for the Genome Toolkit.

Resolution order for vault root:
  1. GENOME_VAULT_ROOT environment variable
  2. config/default.yaml (if running from toolkit repo)
  3. Current working directory
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def _find_config_dir() -> Path:
    """Locate the config/ directory relative to this file or CWD."""
    # Try relative to this script (scripts/lib/config.py -> ../../config/)
    script_config = Path(__file__).resolve().parent.parent.parent / "config"
    if script_config.is_dir():
        return script_config
    # Try CWD
    cwd_config = Path.cwd() / "config"
    if cwd_config.is_dir():
        return cwd_config
    return script_config  # fallback, may not exist


def _load_yaml(path: Path) -> dict:
    """Load a YAML file, returning empty dict if not found."""
    if path.is_file():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


# --- Load configuration ---

CONFIG_DIR = _find_config_dir()
_defaults = _load_yaml(CONFIG_DIR / "default.yaml")

# --- Paths ---

VAULT_ROOT = Path(os.environ.get("GENOME_VAULT_ROOT", "")).expanduser() if os.environ.get("GENOME_VAULT_ROOT") else Path.cwd()
DATA_DIR = VAULT_ROOT / "data"
DB_PATH = Path(os.environ.get("GENOME_DB_PATH", "")).expanduser() if os.environ.get("GENOME_DB_PATH") else DATA_DIR / "genome.db"
RAW_DIR = DATA_DIR / "raw"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_DIR = DATA_DIR / "output"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "data" / "migrations"

# Vault note directories (relative names from config, resolved against VAULT_ROOT)
_vault_dirs = _defaults.get("vault_dirs", {})
GENES_DIR = VAULT_ROOT / _vault_dirs.get("genes", "Genes")
SYSTEMS_DIR = VAULT_ROOT / _vault_dirs.get("systems", "Systems")
PHENOTYPES_DIR = VAULT_ROOT / _vault_dirs.get("phenotypes", "Phenotypes")
PROTOCOLS_DIR = VAULT_ROOT / _vault_dirs.get("protocols", "Protocols")
REPORTS_DIR = VAULT_ROOT / _vault_dirs.get("reports", "Reports")
RESEARCH_DIR = VAULT_ROOT / _vault_dirs.get("research", "Research")
META_DIR = VAULT_ROOT / _vault_dirs.get("meta", "Meta")
BIOMARKERS_DIR = VAULT_ROOT / _vault_dirs.get("biomarkers", "Biomarkers")
TEMPLATES_DIR = VAULT_ROOT / _vault_dirs.get("templates", "Templates")
GUIDES_DIR = VAULT_ROOT / _vault_dirs.get("guides", "Guides")

# --- API rate limits ---

RATE_LIMITS: dict[str, float] = _defaults.get("rate_limits", {
    "snpedia": 1.0,
    "clinvar_eutils": 0.11,
    "pharmgkb": 1.0,
    "gwas_catalog": 0.5,
    "myvariant": 0.1,
})

# --- Cache TTL ---

CACHE_TTL: dict[str, int] = _defaults.get("cache_ttl", {
    "snpedia": 180,
    "clinvar": 90,
    "pharmgkb": 180,
    "gwas_catalog": 90,
    "dbsnp": 365,
    "myvariant": 90,
})

# --- Imputation defaults ---

IMPUTATION: dict[str, Any] = _defaults.get("imputation", {})
MIN_R2: float = IMPUTATION.get("min_r2", 0.3)
QUALITY_TIERS: dict[str, float] = _defaults.get("quality_tiers", {
    "high": 0.9,
    "good": 0.8,
    "moderate": 0.5,
    "low": 0.3,
})

# --- Evidence tiers ---

_evidence = _load_yaml(CONFIG_DIR / "evidence_tiers.yaml")
EVIDENCE_TIERS: dict[str, dict] = _evidence.get("tiers", {})

# --- Goal map ---

_goals = _load_yaml(CONFIG_DIR / "goal_map.yaml")
GOAL_MAP: dict[str, dict] = _goals.get("goals", {})
SCORING_WEIGHTS: dict[str, int] = _goals.get("scoring", {})
GENERATION_LIMITS: dict[str, int] = _goals.get("limits", {})
