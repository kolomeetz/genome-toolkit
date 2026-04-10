"""Smoke tests for skill-referenced files.

Verifies that every file path referenced in a SKILL.md actually exists on disk,
and that every file inside a skill's references/ directory is non-empty.
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# Regex to find backtick-quoted paths that look like repo-relative file paths.
# Matches tokens like `config/foo.yaml`, `scripts/lib/bar.py`,
# `skills/genome-onboard/references/baz.yaml`, etc.
# Excludes shell variables ($FOO), bare directory aliases without extension
# (scripts/analytics/), date placeholders (Daily/YYYY-MM-DD.md),
# and paths that start with Reports/ or Templates/ (vault paths, not repo paths).
_BACKTICK_PATH_RE = re.compile(r'`([a-zA-Z][^\s`]+)`')

# Prefixes that indicate a repo-relative path we should verify
_REPO_PREFIXES = (
    "config/",
    "scripts/",
    "skills/",
)

# Patterns to skip — these are vault paths, placeholders, or non-file tokens
_SKIP_PATTERNS = (
    "$",           # shell variable
    "YYYY",        # date placeholder
    "/genome-",    # slash-command references
)


def _skill_dirs():
    """Return all skill sub-directories."""
    return sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())


def _skill_manifest(skill_dir: Path) -> Path | None:
    """Return the SKILL.md path if it exists."""
    candidate = skill_dir / "SKILL.md"
    return candidate if candidate.exists() else None


def _extract_repo_paths(skill_md: Path) -> list[tuple[str, Path]]:
    """
    Parse a SKILL.md and return (raw_ref, resolved_path) for every
    backtick token that looks like a repo-relative file reference.
    """
    text = skill_md.read_text(encoding="utf-8")
    results = []
    for token in _BACKTICK_PATH_RE.findall(text):
        # Skip obvious non-path tokens
        if any(pat in token for pat in _SKIP_PATTERNS):
            continue
        if not any(token.startswith(prefix) for prefix in _REPO_PREFIXES):
            continue
        # Skip bare directory references (end with /)
        if token.endswith("/"):
            continue
        resolved = REPO_ROOT / token
        results.append((token, resolved))
    return results


# ---------------------------------------------------------------------------
# Test 1: every skills/ directory has a SKILL.md
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("skill_dir", _skill_dirs(), ids=lambda p: p.name)
def test_skill_has_manifest(skill_dir):
    manifest = skill_dir / "SKILL.md"
    assert manifest.exists(), f"Missing SKILL.md in {skill_dir.name}/"


# ---------------------------------------------------------------------------
# Test 2: every file referenced in SKILL.md exists on disk
# ---------------------------------------------------------------------------

def _referenced_file_cases():
    cases = []
    for skill_dir in _skill_dirs():
        manifest = _skill_manifest(skill_dir)
        if manifest is None:
            continue
        for raw_ref, resolved in _extract_repo_paths(manifest):
            cases.append(
                pytest.param(
                    raw_ref,
                    resolved,
                    id=f"{skill_dir.name}::{raw_ref}",
                )
            )
    return cases


@pytest.mark.parametrize("raw_ref,resolved", _referenced_file_cases())
def test_referenced_file_exists(raw_ref, resolved):
    assert resolved.exists(), (
        f"SKILL.md references `{raw_ref}` but {resolved} does not exist"
    )


# ---------------------------------------------------------------------------
# Test 3: every file in a skill's references/ directory is non-empty
# ---------------------------------------------------------------------------

def _references_file_cases():
    cases = []
    for skill_dir in _skill_dirs():
        refs_dir = skill_dir / "references"
        if not refs_dir.is_dir():
            continue
        for f in sorted(refs_dir.iterdir()):
            if f.is_file():
                cases.append(
                    pytest.param(f, id=f"{skill_dir.name}/references/{f.name}")
                )
    return cases


@pytest.mark.parametrize("ref_file", _references_file_cases())
def test_references_file_nonempty(ref_file):
    assert ref_file.stat().st_size > 0, (
        f"references file is empty: {ref_file.relative_to(REPO_ROOT)}"
    )
