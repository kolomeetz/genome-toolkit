"""History screen: past triage sessions with decision tables."""

from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static, DataTable
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Vertical
from rich.text import Text

from genome_toolkit.triage.presentation.tui.stub_data import (
    make_sample_history,
    TriageSessionStub,
)


ACTION_STYLES = {
    "approve": "green",
    "defer": "yellow",
    "drop": "red",
    "create": "blue",
}


class SessionPanel(Widget):
    """Renders a single triage session with its decisions."""

    DEFAULT_CSS = """
    SessionPanel {
        width: 1fr;
        height: auto;
        margin: 0 0 2 0;
        padding: 1 2;
        border: solid $secondary;
        background: $surface;
    }

    SessionPanel .session-header {
        width: 1fr;
        height: 2;
        text-style: bold;
        padding: 0 0 1 0;
    }

    SessionPanel .session-summary {
        width: 1fr;
        height: auto;
        margin: 1 0 0 0;
        color: $text-muted;
    }

    SessionPanel DataTable {
        width: 1fr;
        height: auto;
    }
    """

    def __init__(self, session: TriageSessionStub, **kwargs) -> None:
        super().__init__(**kwargs)
        self.session = session

    def compose(self) -> ComposeResult:
        with Vertical():
            header_text = Text(f"Session: {self.session.timestamp}", style="bold")
            yield Static(header_text, classes="session-header")

            table = DataTable()
            table.add_columns("Action", "Item", "Score", "From", "To", "Note")
            for d in self.session.decisions:
                action_style = ACTION_STYLES.get(d["action"], "white")
                table.add_row(
                    Text(d["action"], style=action_style),
                    d["item"],
                    d["score"],
                    d["from"],
                    d["to"],
                    d.get("note", ""),
                )
            yield table

            yield Static(
                Text(self.session.summary, style="dim italic"),
                classes="session-summary",
            )


class HistoryScreen(Widget):
    """Shows past triage sessions with decision tables."""

    DEFAULT_CSS = """
    HistoryScreen {
        width: 1fr;
        height: 1fr;
    }

    HistoryScreen .history-header {
        width: 1fr;
        height: 3;
        padding: 1 2;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        sessions = make_sample_history()
        with VerticalScroll():
            header_text = Text(
                f"Triage History ({len(sessions)} sessions)",
                style="bold",
            )
            yield Static(header_text, classes="history-header")
            for session in sessions:
                yield SessionPanel(session)
