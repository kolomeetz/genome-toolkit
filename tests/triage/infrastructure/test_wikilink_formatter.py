from __future__ import annotations

from genome_toolkit.triage.infrastructure.vault.wikilink_formatter import (
    format_wikilinks,
    strip_wikilinks,
)


def test_strip_simple_wikilink() -> None:
    assert strip_wikilinks("See [[CYP2D6]] for details") == "See CYP2D6 for details"


def test_strip_aliased_wikilink() -> None:
    assert strip_wikilinks("See [[CYP2D6|the gene]]") == "See the gene"


def test_strip_multiple_wikilinks() -> None:
    result = strip_wikilinks("[[IL1B]] and [[CYP2D6]] interact")
    assert result == "IL1B and CYP2D6 interact"


def test_strip_no_wikilinks() -> None:
    text = "No links here"
    assert strip_wikilinks(text) == text


def test_strip_heading_wikilink() -> None:
    assert strip_wikilinks("See [[CYP2D6#Action Items]]") == "See CYP2D6 > Action Items"


def test_format_wikilinks_simple() -> None:
    result = format_wikilinks("See [[CYP2D6]]")
    assert "CYP2D6" in result
    assert "[[" not in result


def test_format_wikilinks_aliased() -> None:
    result = format_wikilinks("See [[CYP2D6|the gene]]")
    assert "the gene" in result
    assert "[[" not in result


def test_format_empty_string() -> None:
    assert strip_wikilinks("") == ""
    assert format_wikilinks("") == ""
