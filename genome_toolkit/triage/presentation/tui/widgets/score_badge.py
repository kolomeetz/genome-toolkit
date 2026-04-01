"""Score badge widget showing score number with bucket-colored background."""

from __future__ import annotations

from textual.reactive import reactive
from textual.widget import Widget
from textual.app import ComposeResult
from rich.text import Text


BUCKET_COLORS = {
    "DO_NOW": "#E53E3E",
    "THIS_WEEK": "#DD6B20",
    "BACKLOG": "#718096",
    "CONSIDER_DROPPING": "#A0AEC0",
    "SUGGESTION": "#3182CE",
}

BUCKET_LABELS = {
    "DO_NOW": "DO NOW",
    "THIS_WEEK": "THIS WEEK",
    "BACKLOG": "BACKLOG",
    "CONSIDER_DROPPING": "DROP?",
    "SUGGESTION": "SUGGESTED",
}


class ScoreBadge(Widget):
    """Compact score indicator with bucket-colored background."""

    DEFAULT_CSS = """
    ScoreBadge {
        width: auto;
        height: 1;
        min-width: 6;
        padding: 0 1;
    }
    """

    score: reactive[float] = reactive(0.0)
    bucket: reactive[str] = reactive("BACKLOG")

    def __init__(
        self,
        score: float = 0.0,
        bucket: str = "BACKLOG",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.score = score
        self.bucket = bucket

    def render(self) -> Text:
        color = BUCKET_COLORS.get(self.bucket, "#718096")
        score_text = f" {self.score:.0f} "
        text = Text(score_text)
        text.stylize(f"bold reverse {color}")
        return text
