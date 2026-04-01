"""Wikilink formatting utilities for display."""
from __future__ import annotations

import re

# Matches [[target]], [[target|alias]], [[target#heading]], [[target#heading|alias]]
_WIKILINK_RE = re.compile(
    r"\[\[([^\]|#]+?)(?:#([^\]|]*?))?(?:\|([^\]]*?))?\]\]"
)


def strip_wikilinks(text: str) -> str:
    """Remove [[ ]] syntax, keeping display text.

    - ``[[Target]]`` -> ``Target``
    - ``[[Target|Alias]]`` -> ``Alias``
    - ``[[Target#Heading]]`` -> ``Target > Heading``
    """
    def _replace(m: re.Match[str]) -> str:
        target = m.group(1).strip()
        heading = (m.group(2) or "").strip()
        alias = (m.group(3) or "").strip()
        if alias:
            return alias
        if heading:
            return f"{target} > {heading}"
        return target

    return _WIKILINK_RE.sub(_replace, text)


def format_wikilinks(text: str) -> str:
    """Convert wikilinks to styled plain text for display.

    Currently identical to strip_wikilinks but kept as a separate
    function so the presentation layer can swap in rich markup later.
    """
    return strip_wikilinks(text)
