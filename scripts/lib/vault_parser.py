"""Unified Obsidian vault parser for the Genome Toolkit.

Replaces the 3 different parsing approaches found across existing scripts.
Based on python-frontmatter with extensions for wikilinks, Dataview fields,
and Obsidian-specific date formats.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterator

import frontmatter

# --- Regex patterns ---

# Wikilinks: [[target]], [[target|alias]], [[target#heading]], ![[embed]]
WIKILINK_RE = re.compile(
    r"(!?)\[\[([^\]|#]+?)(?:#([^\]|]*?))?(?:\|([^\]]*?))?\]\]"
)

# Dataview inline fields: [key:: value]
DATAVIEW_INLINE_RE = re.compile(
    r"\[([a-zA-Z_][\w]*?)::\s*(.+?)\]"
)

# Wikilinks inside YAML values
YAML_WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")

# Inline tags (not in code blocks)
TAG_RE = re.compile(r"(?<!\w)#([a-zA-Z][\w/-]*)")

# Date patterns for normalization
DATE_PATTERNS = [
    # '2026-03-25' or 2026-03-25
    re.compile(r"^'?(\d{4}-\d{2}-\d{2})'?$"),
    # '[[20260325]]' or [[20260325]]
    re.compile(r"^'?\[\[(\d{8})\]\]'?$"),
    # '[[2026-03-25]]'
    re.compile(r"^'?\[\[(\d{4}-\d{2}-\d{2})\]\]'?$"),
    # bare YYYYMMDD
    re.compile(r"^(\d{8})$"),
]


@dataclass
class ObsidianLink:
    """A parsed wikilink from an Obsidian note."""
    raw: str
    target: str
    alias: str | None = None
    heading: str | None = None
    is_embed: bool = False


@dataclass
class VaultNote:
    """A parsed Obsidian vault note with structured metadata."""
    path: Path
    name: str
    frontmatter: dict[str, Any]
    body: str
    sections: dict[str, str]
    wikilinks: list[ObsidianLink]
    embeds: list[str]
    dataview_fields: dict[str, list[str]]
    tags: list[str]
    frontmatter_valid: bool = True
    warnings: list[str] = field(default_factory=list)


# --- Per-process cache ---
_cache: dict[tuple[str, float, int], VaultNote] = {}


def _cache_key(path: Path) -> tuple[str, float, int]:
    """Cache key based on path, mtime, and size."""
    stat = path.stat()
    return (str(path), stat.st_mtime_ns, stat.st_size)


def parse_note(filepath: Path, use_cache: bool = True) -> VaultNote:
    """Parse a single Obsidian note into structured data."""
    filepath = filepath.resolve()

    if use_cache:
        key = _cache_key(filepath)
        if key in _cache:
            return _cache[key]

    warnings = []
    fm_valid = True

    # Parse frontmatter
    try:
        post = frontmatter.load(str(filepath))
        meta = dict(post.metadata) if post.metadata else {}
        body = post.content
    except Exception as e:
        warnings.append(f"Frontmatter parse error: {e}")
        fm_valid = False
        text = filepath.read_text(encoding="utf-8")
        meta = {}
        body = text

    # Extract wikilinks and embeds from body
    wikilinks = []
    embeds = []
    for m in WIKILINK_RE.finditer(body):
        is_embed = m.group(1) == "!"
        target = m.group(2).strip()
        heading = (m.group(3) or "").strip() or None
        alias = (m.group(4) or "").strip() or None
        raw = m.group(0)

        if is_embed:
            embeds.append(target)
        else:
            wikilinks.append(ObsidianLink(
                raw=raw,
                target=target,
                heading=heading,
                alias=alias,
                is_embed=False,
            ))

    # Extract Dataview inline fields
    dv_fields: dict[str, list[str]] = {}
    for m in DATAVIEW_INLINE_RE.finditer(body):
        key = m.group(1).strip()
        value = m.group(2).strip()
        dv_fields.setdefault(key, []).append(value)

    # Extract inline tags
    inline_tags = list(set(TAG_RE.findall(body)))

    # Combine with frontmatter tags
    fm_tags = meta.get("tags", [])
    if isinstance(fm_tags, str):
        fm_tags = [fm_tags]
    all_tags = list(set(inline_tags + (fm_tags or [])))

    # Extract sections by ## headings
    sections = {}
    parts = re.split(r"^## (.+)$", body, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        content = parts[i + 1] if i + 1 < len(parts) else ""
        sections[heading] = content.strip()

    note = VaultNote(
        path=filepath,
        name=filepath.stem,
        frontmatter=meta,
        body=body,
        sections=sections,
        wikilinks=wikilinks,
        embeds=embeds,
        dataview_fields=dv_fields,
        tags=all_tags,
        frontmatter_valid=fm_valid,
        warnings=warnings,
    )

    if use_cache:
        _cache[_cache_key(filepath)] = note

    return note


def iter_vault_notes(
    vault_root: Path,
    exclude_dirs: set[str] | None = None,
    note_type: str | None = None,
) -> Iterator[VaultNote]:
    """Iterate over all notes in the vault, optionally filtering by type."""
    if exclude_dirs is None:
        exclude_dirs = {"Templates", "data", ".obsidian", ".trash", ".claude", "Guides"}

    for md in sorted(vault_root.rglob("*.md")):
        rel = md.relative_to(vault_root)
        if any(part in exclude_dirs for part in rel.parts):
            continue
        note = parse_note(md)
        if note_type and note.frontmatter.get("type") != note_type:
            continue
        yield note


def get_link_list(note: VaultNote, field_name: str) -> list[ObsidianLink]:
    """Extract wikilinks from a frontmatter field value.

    Handles: ["[[Target]]", "[[Target|Alias]]", "[[Target#Heading]]"]
    Returns list of ObsidianLink with target, alias, heading.
    """
    raw = note.frontmatter.get(field_name, [])
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []

    links = []
    for item in raw:
        item_str = str(item)
        for m in WIKILINK_RE.finditer(item_str):
            links.append(ObsidianLink(
                raw=m.group(0),
                target=m.group(2).strip(),
                heading=(m.group(3) or "").strip() or None,
                alias=(m.group(4) or "").strip() or None,
            ))
    return links


def clean_yaml_wikilinks(value: Any) -> Any:
    """Strip [[]] from YAML values recursively."""
    if isinstance(value, str):
        return YAML_WIKILINK_RE.sub(r"\1", value)
    if isinstance(value, list):
        return [clean_yaml_wikilinks(v) for v in value]
    if isinstance(value, dict):
        return {k: clean_yaml_wikilinks(v) for k, v in value.items()}
    return value


def parse_date(raw: Any) -> date | None:
    """Normalize Obsidian date values to Python date objects.

    Handles: '2026-03-25', '[[20260325]]', '[[2026-03-25]]', 20260325
    """
    if isinstance(raw, date):
        return raw
    if raw is None:
        return None

    raw_str = str(raw).strip()

    for pattern in DATE_PATTERNS:
        m = pattern.match(raw_str)
        if m:
            val = m.group(1)
            if "-" in val:
                parts = val.split("-")
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
            else:
                return date(int(val[:4]), int(val[4:6]), int(val[6:8]))

    return None


def clear_cache() -> None:
    """Clear the per-process note cache."""
    _cache.clear()
