"""Triage system configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TriageConfig:
    vault_path: Path | None = None

    # Scoring weights
    priority_weight: float = 0.25
    overdue_weight: float = 0.20
    evidence_weight: float = 0.15
    lab_signal_weight: float = 0.15
    context_weight: float = 0.10
    severity_weight: float = 0.10
    stuck_weight: float = 0.05

    # Bucket thresholds
    do_now_threshold: int = 70
    this_week_threshold: int = 50
    backlog_threshold: int = 30

    @classmethod
    def from_env(cls) -> TriageConfig:
        """Load config from environment variables."""
        vault_path_str = os.environ.get("GENOME_VAULT_PATH")
        vault_path = Path(vault_path_str) if vault_path_str else None
        return cls(vault_path=vault_path)

    @classmethod
    def from_toml(cls, path: Path) -> TriageConfig:
        """Load config from a TOML file, falling back to defaults for missing keys."""
        if not path.exists():
            return cls()

        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[no-redef]
            except ImportError:
                return cls()

        with open(path, "rb") as f:
            data = tomllib.load(f)

        triage = data.get("triage", {})
        kwargs: dict[str, Any] = {}

        if "vault_path" in triage:
            kwargs["vault_path"] = Path(triage["vault_path"])

        for key in (
            "priority_weight", "overdue_weight", "evidence_weight",
            "lab_signal_weight", "context_weight", "severity_weight",
            "stuck_weight",
        ):
            if key in triage:
                kwargs[key] = float(triage[key])

        for key in ("do_now_threshold", "this_week_threshold", "backlog_threshold"):
            if key in triage:
                kwargs[key] = int(triage[key])

        return cls(**kwargs)
