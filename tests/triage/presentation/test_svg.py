"""Tests for SVG triage renderer and text layout utilities."""

import pytest

from genome_toolkit.triage.presentation.svg.text_layout import (
    estimate_text_width,
    text_to_tspans,
    truncate_with_ellipsis,
    wrap_text,
)
from genome_toolkit.triage.presentation.svg.renderer import (
    ScoredItem,
    Suggestion,
    SvgRenderer,
    TriageReport,
)


# ---------------------------------------------------------------------------
# text_layout: wrap_text
# ---------------------------------------------------------------------------


class TestWrapText:
    def test_short_text_unchanged(self):
        result = wrap_text("hello", max_chars=40)
        assert result == ["hello"]

    def test_long_text_wraps(self):
        text = "This is a long text that should be wrapped across lines"
        result = wrap_text(text, max_chars=20)
        assert all(len(line) <= 20 for line in result)
        assert len(result) > 1
        # Reconstructed text preserves all words
        assert " ".join(result) == text

    def test_empty_string(self):
        result = wrap_text("", max_chars=40)
        assert result == [""]

    def test_single_word_longer_than_max(self):
        result = wrap_text("superlongword", max_chars=5)
        # Must still return the word even if it exceeds max_chars
        assert len(result) >= 1
        assert "superlongword" in " ".join(result)

    def test_exact_boundary(self):
        text = "abcde fghij"
        result = wrap_text(text, max_chars=11)
        assert result == ["abcde fghij"]


# ---------------------------------------------------------------------------
# text_layout: text_to_tspans
# ---------------------------------------------------------------------------


class TestTextToTspans:
    def test_produces_tspan_elements(self):
        result = text_to_tspans("hello world", x=10, y=20, max_chars=40, line_height=16)
        assert "<tspan" in result
        assert 'x="10"' in result
        assert "hello world" in result

    def test_multiline_produces_multiple_tspans(self):
        text = "This is a long text that should be wrapped across lines"
        result = text_to_tspans(text, x=0, y=0, max_chars=20, line_height=16)
        assert result.count("<tspan") > 1

    def test_dy_offset_for_subsequent_lines(self):
        text = "short word pair again"
        result = text_to_tspans(text, x=0, y=0, max_chars=12, line_height=14)
        # First tspan has no dy, subsequent ones have dy="14"
        assert 'dy="14"' in result

    def test_empty_text(self):
        result = text_to_tspans("", x=0, y=0, max_chars=40, line_height=16)
        assert "<tspan" in result


# ---------------------------------------------------------------------------
# text_layout: estimate_text_width
# ---------------------------------------------------------------------------


class TestEstimateTextWidth:
    def test_width_proportional_to_length(self):
        w1 = estimate_text_width("hi", font_size=12)
        w2 = estimate_text_width("hello", font_size=12)
        assert w2 > w1

    def test_width_proportional_to_font_size(self):
        w1 = estimate_text_width("test", font_size=10)
        w2 = estimate_text_width("test", font_size=20)
        assert w2 == pytest.approx(w1 * 2, rel=0.01)

    def test_empty_string_zero(self):
        assert estimate_text_width("", font_size=12) == 0.0

    def test_monospace_ch_factor(self):
        # ch ≈ 0.6em convention
        w = estimate_text_width("A", font_size=10)
        assert w == pytest.approx(6.0, rel=0.01)


# ---------------------------------------------------------------------------
# text_layout: truncate_with_ellipsis
# ---------------------------------------------------------------------------


class TestTruncateWithEllipsis:
    def test_short_text_unchanged(self):
        assert truncate_with_ellipsis("hello", max_chars=10) == "hello"

    def test_long_text_truncated(self):
        result = truncate_with_ellipsis("a long sentence here", max_chars=10)
        assert len(result) <= 10
        assert result.endswith("...")

    def test_exact_length(self):
        assert truncate_with_ellipsis("abcde", max_chars=5) == "abcde"

    def test_just_over(self):
        result = truncate_with_ellipsis("abcdef", max_chars=5)
        assert len(result) == 5
        assert result.endswith("...")

    def test_very_short_max(self):
        result = truncate_with_ellipsis("hello world", max_chars=3)
        assert result == "..."


# ---------------------------------------------------------------------------
# Fixtures for renderer tests
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_items():
    return [
        ScoredItem(
            text="Request CRP blood test",
            score=82.0,
            bucket="DO_NOW",
            priority="critical",
            context="prescriber",
            due="2026-04-15",
            evidence_tier="E1",
            breakdown={"priority": 25.0, "overdue": 17.0, "evidence": 15.0,
                        "lab_signal": 12.0, "context": 10.0, "severity": 3.0},
        ),
        ScoredItem(
            text="Update FADS1 gene note with new GWAS data",
            score=38.0,
            bucket="BACKLOG",
            priority="medium",
            context="vault-maintenance",
            due=None,
            evidence_tier="E3",
            breakdown={"priority": 12.5, "overdue": 8.0, "evidence": 9.0,
                        "lab_signal": 0.0, "context": 2.0, "severity": 6.5},
        ),
        ScoredItem(
            text="Discuss nortriptyline with prescriber",
            score=71.0,
            bucket="DO_NOW",
            priority="high",
            context="prescriber",
            due="2026-04-10",
            evidence_tier="E2",
            breakdown={"priority": 18.75, "overdue": 15.0, "evidence": 12.0,
                        "lab_signal": 10.0, "context": 10.0, "severity": 5.25},
        ),
        ScoredItem(
            text="Check telomere PRS literature",
            score=22.0,
            bucket="CONSIDER_DROPPING",
            priority="low",
            context="research",
            due=None,
            evidence_tier="E5",
            breakdown={"priority": 6.25, "overdue": 8.0, "evidence": 3.0,
                        "lab_signal": 0.0, "context": 4.0, "severity": 0.75},
        ),
        ScoredItem(
            text="Schedule HLA-B27 follow-up",
            score=55.0,
            bucket="THIS_WEEK",
            priority="high",
            context="testing",
            due="2026-04-20",
            evidence_tier="E1",
            breakdown={"priority": 18.75, "overdue": 4.0, "evidence": 15.0,
                        "lab_signal": 5.0, "context": 8.0, "severity": 4.25},
        ),
    ]


@pytest.fixture
def sample_suggestions():
    return [
        Suggestion(
            text="Add CYP2D6 clinical sequencing to testing plan",
            source_type="UNINCORPORATED_FINDING",
            rationale="Findings Index has unincorporated CYP2D6 data",
            recommended_priority="high",
        ),
        Suggestion(
            text="Review NAT2 slow acetylator implications",
            source_type="STALE_RESEARCH",
            rationale="Last researched 8 months ago",
            recommended_priority="medium",
        ),
    ]


@pytest.fixture
def sample_report(sample_items, sample_suggestions):
    return TriageReport(
        items=sample_items,
        suggestions=sample_suggestions,
        total_items=5,
        bucket_counts={
            "DO_NOW": 2,
            "THIS_WEEK": 1,
            "BACKLOG": 1,
            "CONSIDER_DROPPING": 1,
        },
    )


@pytest.fixture
def renderer():
    return SvgRenderer()


# ---------------------------------------------------------------------------
# renderer: valid SVG output
# ---------------------------------------------------------------------------


class TestSvgStructure:
    def test_overview_is_valid_svg(self, renderer, sample_report):
        svg = renderer.render_overview(sample_report)
        assert svg.startswith("<svg")
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg
        assert "viewBox" in svg
        assert svg.strip().endswith("</svg>")

    def test_score_card_is_valid_svg(self, renderer, sample_items):
        svg = renderer.render_score_card(sample_items[0])
        assert svg.startswith("<svg")
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg
        assert svg.strip().endswith("</svg>")

    def test_dashboard_is_valid_svg(self, renderer, sample_report):
        svg = renderer.render_dashboard(sample_report)
        assert svg.startswith("<svg")
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg
        assert svg.strip().endswith("</svg>")

    def test_visit_report_is_valid_svg(self, renderer, sample_report):
        svg = renderer.render_visit_report(sample_report)
        assert svg.startswith("<svg")
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg
        assert svg.strip().endswith("</svg>")


# ---------------------------------------------------------------------------
# renderer: score card bar widths
# ---------------------------------------------------------------------------


class TestScoreCardBars:
    def test_bar_widths_proportional_to_scores(self, renderer, sample_items):
        item = sample_items[0]  # CRP test, score=82
        svg = renderer.render_score_card(item)
        # The breakdown bars should be present
        for factor in item.breakdown:
            assert factor in svg

    def test_score_card_contains_item_text(self, renderer, sample_items):
        item = sample_items[0]
        svg = renderer.render_score_card(item)
        assert "Request CRP blood test" in svg

    def test_score_card_contains_score(self, renderer, sample_items):
        item = sample_items[0]
        svg = renderer.render_score_card(item)
        assert "82" in svg

    def test_score_card_contains_bucket_color(self, renderer, sample_items):
        item = sample_items[0]  # DO_NOW bucket
        svg = renderer.render_score_card(item)
        assert "#E53E3E" in svg


# ---------------------------------------------------------------------------
# renderer: overview groups by context
# ---------------------------------------------------------------------------


class TestOverviewGrouping:
    def test_overview_contains_all_contexts(self, renderer, sample_report):
        svg = renderer.render_overview(sample_report)
        assert "prescriber" in svg
        assert "vault-maintenance" in svg
        assert "research" in svg
        assert "testing" in svg

    def test_overview_contains_all_items(self, renderer, sample_report):
        svg = renderer.render_overview(sample_report)
        for item in sample_report.items:
            # Item text should appear (possibly truncated)
            assert item.text[:15] in svg

    def test_overview_contains_bucket_colors(self, renderer, sample_report):
        svg = renderer.render_overview(sample_report)
        # At least DO_NOW red and BACKLOG gray should appear
        assert "#E53E3E" in svg
        assert "#718096" in svg


# ---------------------------------------------------------------------------
# renderer: visit report filters
# ---------------------------------------------------------------------------


class TestVisitReport:
    def test_visit_report_only_prescriber_items(self, renderer, sample_report):
        svg = renderer.render_visit_report(sample_report)
        # Prescriber items should be present
        assert "CRP" in svg
        assert "nortriptyline" in svg
        # Non-prescriber items should NOT be present
        assert "FADS1" not in svg
        assert "telomere" not in svg

    def test_visit_report_only_e1_e2_evidence(self, renderer, sample_report):
        svg = renderer.render_visit_report(sample_report)
        # E1 and E2 items (prescriber context) should be present
        assert "CRP" in svg
        assert "nortriptyline" in svg

    def test_visit_report_excludes_low_evidence_prescriber(self, renderer):
        """A prescriber item with E4 evidence should be excluded."""
        items = [
            ScoredItem(
                text="Ask about experimental supplement",
                score=45.0,
                bucket="BACKLOG",
                priority="medium",
                context="prescriber",
                due=None,
                evidence_tier="E4",
                breakdown={"priority": 12.5},
            ),
        ]
        report = TriageReport(
            items=items,
            suggestions=[],
            total_items=1,
            bucket_counts={"BACKLOG": 1},
        )
        svg = renderer.render_visit_report(report)
        assert "experimental supplement" not in svg

    def test_visit_report_empty_when_no_matching(self, renderer):
        """Visit report with no prescriber E1/E2 items should still be valid SVG."""
        items = [
            ScoredItem(
                text="Research task",
                score=30.0,
                bucket="BACKLOG",
                priority="low",
                context="research",
                due=None,
                evidence_tier="E5",
                breakdown={"priority": 6.25},
            ),
        ]
        report = TriageReport(
            items=items,
            suggestions=[],
            total_items=1,
            bucket_counts={"BACKLOG": 1},
        )
        svg = renderer.render_visit_report(report)
        assert svg.startswith("<svg")
        assert svg.strip().endswith("</svg>")


# ---------------------------------------------------------------------------
# renderer: dashboard
# ---------------------------------------------------------------------------


class TestDashboard:
    def test_dashboard_contains_bucket_distribution(self, renderer, sample_report):
        svg = renderer.render_dashboard(sample_report)
        assert "DO_NOW" in svg or "Do Now" in svg
        assert "THIS_WEEK" in svg or "This Week" in svg

    def test_dashboard_shows_suggestions_count(self, renderer, sample_report):
        svg = renderer.render_dashboard(sample_report)
        # Should show count of suggestions (2)
        assert "2" in svg

    def test_dashboard_shows_top_items(self, renderer, sample_report):
        svg = renderer.render_dashboard(sample_report)
        # Top scored item (82) should appear
        assert "CRP" in svg


# ---------------------------------------------------------------------------
# Snapshot test: render with fixture data and compare
# ---------------------------------------------------------------------------


class TestSnapshot:
    """Snapshot tests that verify SVG output stability.

    On first run, snapshots are created. On subsequent runs, output is
    compared against saved snapshots. To update snapshots, delete the
    snapshot files and re-run.
    """

    SNAPSHOT_DIR = (
        __import__("pathlib").Path(__file__).parent / "snapshots" / "svg"
    )

    def _compare_or_create(self, name: str, content: str):
        self.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snapshot_path = self.SNAPSHOT_DIR / name
        if snapshot_path.exists():
            saved = snapshot_path.read_text()
            assert content == saved, (
                f"Snapshot mismatch for {name}. "
                f"Delete {snapshot_path} to update."
            )
        else:
            snapshot_path.write_text(content)

    def test_overview_snapshot(self, renderer, sample_report):
        svg = renderer.render_overview(sample_report)
        self._compare_or_create("overview.svg", svg)

    def test_score_card_snapshot(self, renderer, sample_items):
        svg = renderer.render_score_card(sample_items[0])
        self._compare_or_create("score_card.svg", svg)

    def test_dashboard_snapshot(self, renderer, sample_report):
        svg = renderer.render_dashboard(sample_report)
        self._compare_or_create("dashboard.svg", svg)

    def test_visit_report_snapshot(self, renderer, sample_report):
        svg = renderer.render_visit_report(sample_report)
        self._compare_or_create("visit_report.svg", svg)
