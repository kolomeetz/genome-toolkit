"""Main Textual App for the Triage TUI dashboard."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane

from genome_toolkit.triage.presentation.tui.screens.urgency import UrgencyScreen
from genome_toolkit.triage.presentation.tui.screens.context import ContextScreen
from genome_toolkit.triage.presentation.tui.screens.suggestions import SuggestionsScreen
from genome_toolkit.triage.presentation.tui.screens.history import HistoryScreen
from genome_toolkit.triage.presentation.tui.widgets.batch_bar import BatchBar
from genome_toolkit.triage.presentation.tui.widgets.item_card import ItemCard


class TriageApp(App):
    """Genome Triage TUI dashboard with 4 tabs."""

    TITLE = "Genome Triage"
    CSS_PATH = "triage.tcss"

    BINDINGS = [
        ("q", "quit_app", "Quit"),
        ("s", "save_svg", "Save SVG"),
        ("slash", "search", "Search"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Urgency", id="urgency"):
                yield UrgencyScreen()
            with TabPane("Context", id="context"):
                yield ContextScreen()
            with TabPane("Suggestions", id="suggestions"):
                yield SuggestionsScreen()
            with TabPane("History", id="history"):
                yield HistoryScreen()
        yield BatchBar()
        yield Footer()

    def on_item_card_action_performed(self, event: ItemCard.ActionPerformed) -> None:
        """Handle actions from item cards and update the batch bar."""
        batch_bar = self.query_one(BatchBar)
        batch_bar.increment()

    def on_batch_bar_apply_requested(self, event: BatchBar.ApplyRequested) -> None:
        """Apply all pending changes."""
        batch_bar = self.query_one(BatchBar)
        # In the future, this will call the application layer
        self.notify(f"Applied {batch_bar.pending_count} changes")
        batch_bar.reset()

    def on_batch_bar_discard_requested(self, event: BatchBar.DiscardRequested) -> None:
        """Discard all pending changes."""
        batch_bar = self.query_one(BatchBar)
        self.notify("Discarded all pending changes")
        batch_bar.reset()

    def action_quit_app(self) -> None:
        """Quit the app, prompting if there are pending changes."""
        batch_bar = self.query_one(BatchBar)
        if batch_bar.pending_count > 0:
            self.notify(
                f"{batch_bar.pending_count} pending changes will be lost",
                severity="warning",
            )
        self.exit()

    def action_save_svg(self) -> None:
        """Save an SVG snapshot of the current view."""
        path = Path("triage-snapshot.svg")
        self.save_screenshot(str(path))
        self.notify(f"Saved SVG to {path}")

    def action_search(self) -> None:
        """Open search (placeholder for future implementation)."""
        self.notify("Search not yet implemented")


def main() -> None:
    """Entry point for the TUI."""
    app = TriageApp()
    app.run()


if __name__ == "__main__":
    main()
