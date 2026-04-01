"""Virtualized item list using Textual's ListView."""

from __future__ import annotations

from textual.widgets import ListView, ListItem
from textual.app import ComposeResult

from genome_toolkit.triage.presentation.tui.stub_data import ScoredItemStub
from genome_toolkit.triage.presentation.tui.widgets.item_card import ItemCard


class ItemListView(ListView):
    """Virtualized scrollable list of ItemCard widgets."""

    DEFAULT_CSS = """
    ItemListView {
        width: 1fr;
        height: 1fr;
    }
    """

    def __init__(self, items: list[ScoredItemStub], **kwargs) -> None:
        super().__init__(**kwargs)
        self._items = items

    def compose(self) -> ComposeResult:
        for item in self._items:
            list_item = ListItem(ItemCard(item))
            yield list_item

    def get_cards(self) -> list[ItemCard]:
        """Get all ItemCard widgets in this list."""
        return list(self.query(ItemCard))
