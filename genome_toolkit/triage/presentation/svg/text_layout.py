"""Text layout utilities for SVG rendering.

Provides text wrapping, tspan generation, font metric estimation,
and truncation helpers for producing readable SVG text elements.
"""

import re
import textwrap

# Markdown patterns
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)")
_WIKILINK_ALIAS_RE = re.compile(r"\[\[([^|\]]+)\|([^\]]+)\]\]")
_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def wrap_text(text: str, max_chars: int) -> list[str]:
    """Wrap text into lines of at most *max_chars* characters.

    Uses :func:`textwrap.wrap` with long-word breaking disabled so that
    single words exceeding *max_chars* are preserved intact.

    Returns a list with at least one element (empty string for empty input).
    """
    if not text:
        return [""]
    lines = textwrap.wrap(text, width=max_chars, break_long_words=False, break_on_hyphens=False)
    return lines if lines else [text]


def text_to_tspans(
    text: str,
    x: float,
    y: float,
    max_chars: int,
    line_height: float,
) -> str:
    """Generate SVG ``<tspan>`` elements for *text*.

    The first ``<tspan>`` is positioned at (*x*, *y*).  Subsequent lines
    use ``dy`` offsets of *line_height*.
    """
    lines = wrap_text(text, max_chars)
    parts: list[str] = []
    for i, line in enumerate(lines):
        if i == 0:
            parts.append(f'<tspan x="{x}" y="{y}">{_escape(line)}</tspan>')
        else:
            parts.append(f'<tspan x="{x}" dy="{line_height}">{_escape(line)}</tspan>')
    return "".join(parts)


def estimate_text_width(text: str, font_size: float) -> float:
    """Conservative monospace width estimate.

    Uses the convention ``ch ~= 0.6 * em`` where ``em == font_size``.
    """
    return len(text) * 0.6 * font_size


def truncate_with_ellipsis(text: str, max_chars: int) -> str:
    """Truncate *text* to at most *max_chars*, appending ``...`` if needed."""
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return "..."[:max_chars]
    return text[: max_chars - 3] + "..."


def strip_markdown(text: str) -> str:
    """Remove markdown syntax, returning display text for length calculations."""
    text = _WIKILINK_ALIAS_RE.sub(r"\2", text)
    text = _WIKILINK_RE.sub(r"\1", text)
    text = _BOLD_RE.sub(r"\1", text)
    text = _ITALIC_RE.sub(r"\1", text)
    text = _INLINE_CODE_RE.sub(r"\1", text)
    return text


def markdown_to_svg_tspans(text: str) -> str:
    """Convert inline markdown to SVG tspan elements.

    - **bold** -> <tspan font-weight="bold">bold</tspan>
    - *italic* -> <tspan font-style="italic">italic</tspan>
    - [[Link]] -> <tspan fill="#3182CE">Link</tspan>
    - [[Link|Alias]] -> <tspan fill="#3182CE">Alias</tspan>
    - `code` -> <tspan fill="#718096">code</tspan>
    """
    # Order matters: wikilinks before bold (both use special chars)
    text = _escape(text)
    # Wikilinks with alias (already escaped, brackets are literal text)
    text = re.sub(
        r"\[\[([^|\]]+)\|([^\]]+)\]\]",
        r'<tspan fill="#3182CE">\2</tspan>',
        text,
    )
    # Wikilinks without alias
    text = re.sub(
        r"\[\[([^\]]+)\]\]",
        r'<tspan fill="#3182CE">\1</tspan>',
        text,
    )
    # Bold
    text = re.sub(
        r"\*\*(.+?)\*\*",
        r'<tspan font-weight="bold">\1</tspan>',
        text,
    )
    # Italic
    text = re.sub(
        r"(?<!\*)\*([^*]+?)\*(?!\*)",
        r'<tspan font-style="italic">\1</tspan>',
        text,
    )
    # Inline code
    text = re.sub(
        r"`([^`]+)`",
        r'<tspan fill="#718096">\1</tspan>',
        text,
    )
    return text


def _escape(text: str) -> str:
    """Minimal XML escaping for SVG text content."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
