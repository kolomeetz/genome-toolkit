from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Iterator


TASK_LINE_RE = re.compile(r"^\s*-\s*\[(?P<state>[ xX])\]\s*(?P<body>.+)$")
DATAVIEW_RE = re.compile(r"\[([a-zA-Z_][\w-]*)::\s*(.*?)\]")
BLOCK_ID_RE = re.compile(r"\^([\w-]+)")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#([^\]|]*))?(?:\|([^\]]+))?\]\]")


@dataclass
class ParsedTaskLine:
    line_number: int
    completed: bool
    clean_text: str
    fields: dict[str, str]
    block_id: str | None
    raw_body: str


DATE_PATTERNS = (
    re.compile(r"^'?((?:19|20)\d{2}-\d{2}-\d{2})'?$"),
    re.compile(r"^'?\[\[(\d{8})\]\]'?$"),
    re.compile(r"^(\d{8})$"),
)


def iter_task_lines(lines: list[str]) -> Iterator[ParsedTaskLine]:
    for line_number, raw in enumerate(lines, start=1):
        match = TASK_LINE_RE.match(raw)
        if not match:
            continue
        completed = match.group("state").lower() == "x"
        body = match.group("body").strip()
        fields: dict[str, str] = {}
        for key, value in DATAVIEW_RE.findall(body):
            fields[key.lower()] = value.strip()
        block_match = BLOCK_ID_RE.search(body)
        block_id = block_match.group(1) if block_match else None
        clean_text = normalize_task_text(body)
        yield ParsedTaskLine(
            line_number=line_number,
            completed=completed,
            clean_text=clean_text,
            fields=fields,
            block_id=block_id,
            raw_body=body,
        )


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split()).strip()


def extract_wikilinks(text: str) -> list[str]:
    links: list[str] = []
    for target, _, _alias in WIKILINK_RE.findall(text):
        value = target.strip()
        if value:
            links.append(value)
    return links


def parse_date_value(raw_value: str | None) -> date | None:
    if not raw_value:
        return None
    value = raw_value.strip().strip("'")
    for pattern in DATE_PATTERNS:
        match = pattern.match(value)
        if not match:
            continue
        digits = match.group(1)
        if len(digits) == 8 and digits.isdigit() and "-" not in digits:
            return date(int(digits[0:4]), int(digits[4:6]), int(digits[6:8]))
        return date.fromisoformat(digits)
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def strip_dataview_fields(text: str) -> str:
    return DATAVIEW_RE.sub("", text)


def remove_block_ids(text: str) -> str:
    return BLOCK_ID_RE.sub("", text)


def normalize_task_text(text: str) -> str:
    cleaned = strip_dataview_fields(text)
    cleaned = remove_block_ids(cleaned)
    cleaned = cleaned.strip()
    cleaned = cleaned.rstrip("—").rstrip("-").strip()
    return _collapse_whitespace(cleaned)


def replace_inline_field(line: str, key: str, value: str) -> tuple[str, bool]:
    pattern = re.compile(rf"\[{re.escape(key)}::\s*([^\]]*?)\]", re.IGNORECASE)
    replacement = f"[{key}:: {value}]"
    new_line, count = pattern.subn(replacement, line)
    return (new_line if count else line, bool(count))


def extract_inline_field(line: str, key: str) -> str | None:
    pattern = re.compile(rf"\[{re.escape(key)}::\s*([^\]]*?)\]", re.IGNORECASE)
    match = pattern.search(line)
    if match:
        return match.group(1).strip()
    return None


def strip_block_ids(text: str) -> str:
    return BLOCK_ID_RE.sub("", text)


__all__ = [
    "ParsedTaskLine",
    "iter_task_lines",
    "extract_wikilinks",
    "parse_date_value",
    "normalize_task_text",
    "replace_inline_field",
    "extract_inline_field",
    "strip_dataview_fields",
    "remove_block_ids",
]
