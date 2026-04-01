from __future__ import annotations

import os
from pathlib import Path

import pytest

from genome_toolkit.triage.infrastructure.config import TriageConfig


def test_default_vault_path() -> None:
    config = TriageConfig()
    assert config.vault_path is None


def test_vault_path_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GENOME_VAULT_PATH", "/tmp/test-vault")
    config = TriageConfig.from_env()
    assert config.vault_path == Path("/tmp/test-vault")


def test_default_weights() -> None:
    config = TriageConfig()
    assert config.priority_weight == 0.25
    assert config.overdue_weight == 0.20
    assert config.evidence_weight == 0.15
    assert config.lab_signal_weight == 0.15
    assert config.context_weight == 0.10
    assert config.severity_weight == 0.10
    assert config.stuck_weight == 0.05


def test_default_bucket_thresholds() -> None:
    config = TriageConfig()
    assert config.do_now_threshold == 70
    assert config.this_week_threshold == 50
    assert config.backlog_threshold == 30


def test_from_env_without_vault_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GENOME_VAULT_PATH", raising=False)
    config = TriageConfig.from_env()
    assert config.vault_path is None


def test_from_toml(tmp_path: Path) -> None:
    toml_content = """\
[triage]
vault_path = "/tmp/toml-vault"
priority_weight = 0.30
do_now_threshold = 80
"""
    toml_file = tmp_path / "triage.toml"
    toml_file.write_text(toml_content)

    config = TriageConfig.from_toml(toml_file)
    assert config.vault_path == Path("/tmp/toml-vault")
    assert config.priority_weight == 0.30
    assert config.do_now_threshold == 80
    # Other weights stay default
    assert config.overdue_weight == 0.20


def test_from_toml_missing_file() -> None:
    config = TriageConfig.from_toml(Path("/nonexistent/triage.toml"))
    # Falls back to defaults
    assert config.vault_path is None
    assert config.priority_weight == 0.25
