"""Tests for the Textual TUI triage dashboard."""

from __future__ import annotations

import pytest
from datetime import date

from genome_toolkit.triage.presentation.tui.app import TriageApp
from genome_toolkit.triage.presentation.tui.widgets.item_card import ItemCard
from genome_toolkit.triage.presentation.tui.widgets.score_badge import ScoreBadge
from genome_toolkit.triage.presentation.tui.widgets.batch_bar import BatchBar
from genome_toolkit.triage.presentation.tui.stub_data import make_sample_items, ScoredItemStub


@pytest.fixture
def sample_stub() -> ScoredItemStub:
    return ScoredItemStub(
        text="Request CRP blood test from prescriber",
        score=82.0,
        bucket="DO_NOW",
        priority="critical",
        context="prescriber",
        due=date(2026, 4, 15),
        evidence_tier="E1",
        severity="significant",
        linked_genes=["IL6", "IL1B"],
        lab_signal="CRP > threshold",
        breakdown={
            "priority": 25.0,
            "overdue": 15.0,
            "evidence": 15.0,
            "lab_signal": 12.0,
            "context": 10.0,
            "severity": 7.5,
            "stuck": 0.0,
        },
        clinically_validated=False,
        blocked_by=[],
    )


class TestTriageAppMount:
    """Test that the app mounts correctly with all tabs."""

    @pytest.mark.asyncio
    async def test_app_has_four_tabs(self):
        app = TriageApp()
        async with app.run_test() as pilot:
            tabs = app.query("TabPane")
            assert len(tabs) == 4

    @pytest.mark.asyncio
    async def test_tab_ids(self):
        app = TriageApp()
        async with app.run_test() as pilot:
            tab_ids = {tab.id for tab in app.query("TabPane")}
            assert tab_ids == {"urgency", "context", "suggestions", "history"}

    @pytest.mark.asyncio
    async def test_has_header_and_footer(self):
        app = TriageApp()
        async with app.run_test() as pilot:
            headers = app.query("Header")
            footers = app.query("Footer")
            assert len(headers) == 1
            assert len(footers) == 1


class TestTabSwitching:
    """Test that tab switching works."""

    @pytest.mark.asyncio
    async def test_switch_to_context_tab(self):
        app = TriageApp()
        async with app.run_test() as pilot:
            tabbed = app.query_one("TabbedContent")
            tabbed.active = "context"
            await pilot.pause()
            assert tabbed.active == "context"

    @pytest.mark.asyncio
    async def test_switch_to_suggestions_tab(self):
        app = TriageApp()
        async with app.run_test() as pilot:
            tabbed = app.query_one("TabbedContent")
            tabbed.active = "suggestions"
            await pilot.pause()
            assert tabbed.active == "suggestions"


class TestItemCard:
    """Test item card widget rendering."""

    @pytest.mark.asyncio
    async def test_card_renders_score(self, sample_stub):
        app = TriageApp()
        async with app.run_test() as pilot:
            # The urgency screen has items with scores
            cards = app.query("ItemCard")
            assert len(cards) > 0
            first_card = cards[0]
            # Card should contain score badge
            badges = first_card.query("ScoreBadge")
            assert len(badges) == 1

    @pytest.mark.asyncio
    async def test_card_renders_text(self, sample_stub):
        app = TriageApp()
        async with app.run_test() as pilot:
            cards = app.query("ItemCard")
            assert len(cards) > 0
            # The card text should be in the rendered content
            first_card = cards[0]
            assert first_card.item.text != ""

    @pytest.mark.asyncio
    async def test_card_starts_collapsed(self, sample_stub):
        app = TriageApp()
        async with app.run_test() as pilot:
            cards = app.query("ItemCard")
            assert len(cards) > 0
            assert cards[0].expanded is False


class TestExpandCollapse:
    """Test expand/collapse via Enter key."""

    @pytest.mark.asyncio
    async def test_enter_expands_card(self):
        app = TriageApp()
        async with app.run_test() as pilot:
            cards = app.query("ItemCard")
            assert len(cards) > 0
            first_card = cards[0]
            first_card.focus()
            await pilot.pause()
            assert first_card.expanded is False
            await pilot.press("enter")
            assert first_card.expanded is True

    @pytest.mark.asyncio
    async def test_enter_again_collapses(self):
        app = TriageApp()
        async with app.run_test() as pilot:
            cards = app.query("ItemCard")
            first_card = cards[0]
            first_card.focus()
            await pilot.pause()
            await pilot.press("enter")
            assert first_card.expanded is True
            await pilot.press("enter")
            assert first_card.expanded is False


class TestPriorityCycle:
    """Test that 'p' key cycles priority."""

    @pytest.mark.asyncio
    async def test_p_cycles_priority(self):
        app = TriageApp()
        async with app.run_test() as pilot:
            cards = app.query("ItemCard")
            first_card = cards[0]
            first_card.focus()
            await pilot.pause()
            original_priority = first_card.item.priority
            await pilot.press("p")
            assert first_card.item.priority != original_priority


class TestBatchBar:
    """Test batch bar pending count."""

    @pytest.mark.asyncio
    async def test_batch_bar_starts_at_zero(self):
        app = TriageApp()
        async with app.run_test() as pilot:
            batch_bars = app.query("BatchBar")
            assert len(batch_bars) == 1
            assert batch_bars[0].pending_count == 0

    @pytest.mark.asyncio
    async def test_batch_bar_increments_on_action(self):
        app = TriageApp()
        async with app.run_test() as pilot:
            cards = app.query("ItemCard")
            first_card = cards[0]
            first_card.focus()
            await pilot.pause()
            # Cycle priority to create a pending change
            await pilot.press("p")
            batch_bars = app.query("BatchBar")
            assert batch_bars[0].pending_count == 1
