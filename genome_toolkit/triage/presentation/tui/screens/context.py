"""Context screen: items grouped by context with section headers."""

from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from rich.text import Text

from genome_toolkit.triage.presentation.tui.stub_data import (
    make_sample_items,
    CONTEXT_ORDER,
    ScoredItemStub,
)
from genome_toolkit.triage.presentation.tui.widgets.item_card import ItemCard


CONTEXT_COLORS = {
    "prescriber": "#E53E3E",
    "testing": "#DD6B20",
    "monitoring": "#38A169",
    "research": "#3182CE",
    "vault-maintenance": "#718096",
}

CONTEXT_DISPLAY = {
    "prescriber": "Prescriber",
    "testing": "Testing",
    "monitoring": "Monitoring",
    "research": "Research",
    "vault-maintenance": "Vault Maintenance",
}


class ContextScreen(Widget):
    """Shows items grouped by context with section headers."""

    DEFAULT_CSS = """
    ContextScreen {
        width: 1fr;
        height: 1fr;
    }

    ContextScreen .context-header {
        width: 1fr;
        height: 3;
        padding: 1 2;
        text-style: bold;
        margin: 1 0 0 0;
    }
    """

    def compose(self) -> ComposeResult:
        items = make_sample_items()
        grouped: dict[str, list[ScoredItemStub]] = {}
        for item in items:
            grouped.setdefault(item.context, []).append(item)

        with VerticalScroll():
            for ctx in CONTEXT_ORDER:
                group = grouped.get(ctx, [])
                if not group:
                    continue
                group.sort(key=lambda i: i.score, reverse=True)
                display_name = CONTEXT_DISPLAY.get(ctx, ctx)
                color = CONTEXT_COLORS.get(ctx, "#718096")
                header_text = Text(
                    f"\u2501\u2501 {display_name} ({len(group)}) \u2501\u2501",
                    style=f"bold {color}",
                )
                yield Static(header_text, classes="context-header")
                for item in group:
                    yield ItemCard(item)
