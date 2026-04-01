"""SVG renderer for triage reports.

Computes all layout coordinates in Python and delegates structure
to Jinja2 SVG templates.  No browser or JS dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .text_layout import (
    truncate_with_ellipsis,
    wrap_text,
    text_to_tspans,
    strip_markdown,
    markdown_to_svg_tspans,
)

# ---------------------------------------------------------------------------
# Stub domain types (local, until domain layer is wired)
# ---------------------------------------------------------------------------


@dataclass
class ScoredItem:
    text: str
    score: float
    bucket: str  # "DO_NOW", "THIS_WEEK", "BACKLOG", "CONSIDER_DROPPING"
    priority: str
    context: str
    due: str | None
    evidence_tier: str | None
    breakdown: dict[str, float]  # factor_name -> score


@dataclass
class Suggestion:
    text: str
    source_type: str
    rationale: str
    recommended_priority: str


@dataclass
class TriageReport:
    items: list[ScoredItem]
    suggestions: list[Suggestion]
    total_items: int
    bucket_counts: dict[str, int]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BUCKET_COLORS: dict[str, str] = {
    "DO_NOW": "#E53E3E",
    "THIS_WEEK": "#DD6B20",
    "BACKLOG": "#718096",
    "CONSIDER_DROPPING": "#A0AEC0",
}

BUCKET_LABELS: dict[str, str] = {
    "DO_NOW": "Do Now",
    "THIS_WEEK": "This Week",
    "BACKLOG": "Backlog",
    "CONSIDER_DROPPING": "Consider Dropping",
}

MAX_CONTENT_WIDTH = 800
ITEM_CHARS_PER_LINE = 36  # chars per line for multiline wrapping
ITEM_MAX_LINES = 3  # max lines for item text
ITEM_TRUNCATE_CARD = 60
BAR_MAX_WIDTH = 200
TEXT_ZONE_WIDTH = 280  # fixed zone for item text, bar starts after
LINE_HEIGHT = 15  # px between text lines


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


class SvgRenderer:
    """Renders triage reports as SVG strings."""

    def __init__(self) -> None:
        templates_dir = Path(__file__).parent / "templates"
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=False,
        )

    # -- public API ---------------------------------------------------------

    def render_overview(self, report: TriageReport) -> str:
        """Horizontal bar chart of items colored by bucket, grouped by context."""
        groups = self._layout_overview(report)
        height = self._overview_height(groups)
        tpl = self._env.get_template("overview.svg.j2")
        return tpl.render(
            width=MAX_CONTENT_WIDTH,
            height=height,
            groups=groups,
        )

    def render_score_card(self, item: ScoredItem) -> str:
        """Individual item card with score breakdown bars."""
        bars, card_height = self._layout_score_card(item)
        bucket_color = BUCKET_COLORS.get(item.bucket, "#718096")
        tpl = self._env.get_template("score_card.svg.j2")
        return tpl.render(
            width=MAX_CONTENT_WIDTH,
            height=card_height,
            bucket=BUCKET_LABELS.get(item.bucket, item.bucket),
            bucket_color=bucket_color,
            score=int(item.score),
            title_tspans=truncate_with_ellipsis(item.text, ITEM_TRUNCATE_CARD),
            meta_y=90,
            priority=item.priority,
            context=item.context,
            due=item.due,
            evidence_tier=item.evidence_tier,
            bars=bars,
        )

    def render_dashboard(self, report: TriageReport) -> str:
        """Combined: bucket distribution + top 10 + suggestions count."""
        buckets, top_items, height = self._layout_dashboard(report)
        tpl = self._env.get_template("dashboard.svg.j2")
        return tpl.render(
            width=MAX_CONTENT_WIDTH,
            height=height,
            buckets=buckets,
            suggestions_x=600,
            suggestions_count=len(report.suggestions),
            top_items=top_items,
        )

    def render_visit_report(self, report: TriageReport) -> str:
        """Doctor visit: prescriber items, E1-E2 evidence only."""
        visit_items = [
            it for it in report.items
            if it.context == "prescriber"
            and it.evidence_tier in ("E1", "E2")
        ]
        laid_out, height = self._layout_visit(visit_items)
        tpl = self._env.get_template("visit_report.svg.j2")
        return tpl.render(
            width=MAX_CONTENT_WIDTH,
            height=height,
            items=laid_out,
        )

    # -- layout helpers -----------------------------------------------------

    @staticmethod
    def _layout_overview(report: TriageReport) -> list[dict]:
        """Group items by context and compute bar positions.

        Text wraps to up to ITEM_MAX_LINES lines. Bar is vertically
        centred against the text block. Row height adapts to line count.
        """
        from itertools import groupby

        sorted_items = sorted(report.items, key=lambda it: it.context)
        groups: list[dict] = []
        y_cursor = 56  # after title
        text_x = 30
        bar_x = text_x + TEXT_ZONE_WIDTH
        score_max_x = MAX_CONTENT_WIDTH - 40

        for ctx, ctx_items in groupby(sorted_items, key=lambda it: it.context):
            items_list = sorted(list(ctx_items), key=lambda it: -it.score)
            group: dict = {
                "context": ctx,
                "label_y": y_cursor,
                "bars": [],
            }
            y_cursor += 8
            available_bar_width = score_max_x - bar_x - 30

            for it in items_list:
                color = BUCKET_COLORS.get(it.bucket, "#718096")
                bar_width = max(4, it.score / 100 * available_bar_width)

                # Strip markdown for accurate char counting, wrap on display text
                display_text = strip_markdown(it.text)
                lines_display = wrap_text(display_text, ITEM_CHARS_PER_LINE)
                # Also wrap raw text at same positions for markdown rendering
                lines_raw = wrap_text(it.text, ITEM_CHARS_PER_LINE + 6)  # extra room for ** and [[]]

                # Align: use display lines count but render from raw
                # Simple approach: wrap raw, cap, render with markdown
                if len(lines_raw) > ITEM_MAX_LINES:
                    lines_raw = lines_raw[:ITEM_MAX_LINES]
                    lines_raw[-1] = truncate_with_ellipsis(lines_raw[-1], ITEM_CHARS_PER_LINE + 6)

                num_lines = len(lines_raw)
                text_block_height = num_lines * LINE_HEIGHT
                bar_height = 16

                # Generate tspan elements with markdown rendered as SVG
                tspan_parts = []
                for li, ln in enumerate(lines_raw):
                    svg_content = markdown_to_svg_tspans(ln)
                    if li == 0:
                        tspan_parts.append(f'<tspan x="{text_x}" y="{y_cursor + 12}">{svg_content}</tspan>')
                    else:
                        tspan_parts.append(f'<tspan x="{text_x}" dy="{LINE_HEIGHT}">{svg_content}</tspan>')
                tspans = "".join(tspan_parts)

                # Bar vertically centred on text block
                bar_y = y_cursor + (text_block_height - bar_height) / 2

                group["bars"].append({
                    "tspans": tspans,
                    "num_lines": num_lines,
                    "score": int(it.score),
                    "color": color,
                    "text_x": text_x,
                    "bar_x": bar_x,
                    "bar_y": bar_y,
                    "score_x": bar_x + bar_width + 8,
                    "score_y": bar_y + bar_height - 3,
                    "y": y_cursor,
                    "bar_width": bar_width,
                    "bar_height": bar_height,
                })
                # Row height: text block + padding
                y_cursor += max(text_block_height, bar_height) + 10
            y_cursor += 12
            groups.append(group)
        return groups

    @staticmethod
    def _overview_height(groups: list[dict]) -> int:
        if not groups:
            return 80
        last = groups[-1]
        if last["bars"]:
            return int(last["bars"][-1]["y"] + 40)
        return int(last["label_y"] + 40)

    @staticmethod
    def _layout_score_card(item: ScoredItem) -> tuple[list[dict], int]:
        """Compute bar positions for score card breakdown."""
        bar_x = 120
        bg_width = BAR_MAX_WIDTH
        bars: list[dict] = []
        y = 120
        for label, value in item.breakdown.items():
            fill_width = max(0, min(value / 25 * BAR_MAX_WIDTH, BAR_MAX_WIDTH))
            bars.append({
                "label": label,
                "y": y,
                "bar_x": bar_x,
                "bg_width": bg_width,
                "fill_width": fill_width,
                "value_label": f"{value:.1f}",
            })
            y += 22
        card_height = y + 20
        return bars, card_height

    @staticmethod
    def _layout_dashboard(report: TriageReport) -> tuple[list[dict], list[dict], int]:
        """Compute bucket bars and top-item list for dashboard."""
        bucket_order = ["DO_NOW", "THIS_WEEK", "BACKLOG", "CONSIDER_DROPPING"]
        total = max(report.total_items, 1)
        buckets: list[dict] = []
        x = 20
        for bk in bucket_order:
            count = report.bucket_counts.get(bk, 0)
            bar_width = max(4, count / total * 500)
            buckets.append({
                "label": BUCKET_LABELS.get(bk, bk),
                "count": count,
                "color": BUCKET_COLORS.get(bk, "#718096"),
                "x": x,
                "bar_width": bar_width,
            })
            x += bar_width + 8

        top_items: list[dict] = []
        sorted_items = sorted(report.items, key=lambda it: -it.score)[:10]
        y = 190
        for it in sorted_items:
            color = BUCKET_COLORS.get(it.bucket, "#718096")
            top_items.append({
                "text": truncate_with_ellipsis(it.text, ITEM_TRUNCATE_CARD),
                "score": int(it.score),
                "color": color,
                "y": y,
            })
            y += 26

        height = y + 20
        return buckets, top_items, height

    @staticmethod
    def _layout_visit(items: list[ScoredItem]) -> tuple[list[dict], int]:
        """Compute card positions for visit report."""
        if not items:
            return [], 100

        sorted_items = sorted(items, key=lambda it: -it.score)
        laid_out: list[dict] = []
        y = 70
        card_height = 52
        for it in sorted_items:
            color = BUCKET_COLORS.get(it.bucket, "#718096")
            laid_out.append({
                "text": truncate_with_ellipsis(it.text, ITEM_TRUNCATE_CARD),
                "score": int(it.score),
                "color": color,
                "priority": it.priority,
                "evidence_tier": it.evidence_tier,
                "due": it.due,
                "y": y,
                "card_height": card_height,
            })
            y += card_height + 8
        height = y + 20
        return laid_out, height
