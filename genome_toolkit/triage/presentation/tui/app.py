"""Main Textual App for the Triage TUI dashboard."""

from __future__ import annotations

import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane

from genome_toolkit.triage.presentation.tui.screens.urgency import UrgencyScreen
from genome_toolkit.triage.presentation.tui.screens.context import ContextScreen
from genome_toolkit.triage.presentation.tui.screens.suggestions import SuggestionsScreen
from genome_toolkit.triage.presentation.tui.screens.history import HistoryScreen
from genome_toolkit.triage.presentation.tui.widgets.batch_bar import BatchBar
from genome_toolkit.triage.presentation.tui.widgets.item_card import ItemCard
from genome_toolkit.triage.presentation.tui.stub_data import ScoredItemStub

log = logging.getLogger(__name__)


class TriageApp(App):
    """Genome Triage TUI dashboard with 4 tabs."""

    TITLE = "Genome Triage"
    CSS_PATH = "triage.tcss"

    BINDINGS = [
        ("q", "quit_app", "Quit"),
        ("s", "save_svg", "Save SVG"),
        ("slash", "search", "Search"),
    ]

    def __init__(self, vault_path: Path | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._vault_path = vault_path
        self._items: list[ScoredItemStub] | None = None
        self._suggestions: list[ScoredItemStub] | None = None
        self._report = None
        self._pending_actions: list[tuple] = []

        if vault_path is not None:
            self._load_real_data()

    def _load_real_data(self) -> None:
        """Build repos, run triage session, convert to stubs."""
        try:
            from genome_toolkit.triage.infrastructure.vault.task_parser import VaultTaskRepository
            from genome_toolkit.triage.infrastructure.vault.findings_parser import VaultFindingsRepository
            from genome_toolkit.triage.infrastructure.scripts.lab_adapter import VaultLabSignalRepository
            from genome_toolkit.triage.infrastructure.persistence.session_store import MarkdownSessionRepository
            from genome_toolkit.triage.application.triage_use_case import RunTriageSession
            from genome_toolkit.triage.presentation.tui.data_bridge import (
                scored_item_to_stub,
                suggestion_to_stub,
            )

            task_repo = VaultTaskRepository(self._vault_path)
            findings_repo = VaultFindingsRepository(self._vault_path)
            lab_repo = VaultLabSignalRepository(self._vault_path)
            session_repo = MarkdownSessionRepository(self._vault_path)

            use_case = RunTriageSession(
                task_repo=task_repo,
                findings_repo=findings_repo,
                lab_signal_repo=lab_repo,
                session_repo=session_repo,
            )
            report = use_case.execute()
            self._report = report

            self._items = [scored_item_to_stub(si) for si in report.scored_items]
            self._suggestions = [suggestion_to_stub(s) for s in report.suggestions]

            log.info(
                "Loaded %d items and %d suggestions from vault",
                len(self._items),
                len(self._suggestions),
            )
        except Exception:
            log.exception("Failed to load vault data, falling back to stubs")
            self._items = None
            self._suggestions = None

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Urgency", id="urgency"):
                yield UrgencyScreen(items=self._items)
            with TabPane("Context", id="context"):
                yield ContextScreen(items=self._items)
            with TabPane("Suggestions", id="suggestions"):
                yield SuggestionsScreen(suggestions=self._suggestions)
            with TabPane("History", id="history"):
                yield HistoryScreen(vault_path=self._vault_path)
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
