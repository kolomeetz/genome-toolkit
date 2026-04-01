from __future__ import annotations

import shutil
from pathlib import Path

import pytest


FIXTURE_VAULT = Path(__file__).resolve().parents[2] / "fixtures" / "vault"


@pytest.fixture
def vault_copy(tmp_path):
    dst = tmp_path / "vault"
    shutil.copytree(FIXTURE_VAULT, dst)
    return dst
