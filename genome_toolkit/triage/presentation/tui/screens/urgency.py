"""Urgency screen: all items sorted by score descending."""

from __future__ import annotations

from textual.widget import Widget
from textual.app import ComposeResult
from textual.containers import VerticalScroll

from genome_toolkit.triage.presentation.tui.stub_data import make_sample_items
from genome_toolkit.triage.presentation.tui.widgets.item_card import ItemCard


class UrgencyScreen(Widget):
    """Shows all items sorted by composite score, highest first."""

    DEFAULT_CSS = """
    UrgencyScreen {
        width: 1fr;
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        items = make_sample_items()
        items.sort(key=lambda i: i.score, reverse=True)
        with VerticalScroll():
            for item in items:
                yield ItemCard(item)
