from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

import pytest

from genome_toolkit.triage.domain.item import (
    Context,
    EvidenceTier,
    ItemId,
    Priority,
    Severity,
    SourceLocation,
    TriageItem,
)


class TestItemId:
    def test_from_content_hash(self):
        item_id = ItemId.from_content("MyNote", "Request CRP blood test")
        expected = hashlib.sha256("MyNote|Request CRP blood test".encode()).hexdigest()
        assert item_id.value == expected

    def test_from_block_id(self):
        item_id = ItemId.from_block_id("abc123")
        assert item_id.value == "abc123"

    def test_equality(self):
        a = ItemId.from_content("Note", "task")
        b = ItemId.from_content("Note", "task")
        assert a == b

    def test_inequality(self):
        a = ItemId.from_content("Note", "task1")
        b = ItemId.from_content("Note", "task2")
        assert a != b

    def test_frozen(self):
        item_id = ItemId.from_content("Note", "task")
        with pytest.raises(AttributeError):
            item_id.value = "changed"  # type: ignore[misc]


class TestSourceLocation:
    def test_creation(self):
        loc = SourceLocation(file_path=Path("Reports/Summary.md"), line_number=42)
        assert loc.file_path == Path("Reports/Summary.md")
        assert loc.line_number == 42

    def test_frozen(self):
        loc = SourceLocation(file_path=Path("a.md"), line_number=1)
        with pytest.raises(AttributeError):
            loc.line_number = 5  # type: ignore[misc]


class TestPriority:
    def test_values(self):
        assert Priority.CRITICAL.value == 100
        assert Priority.HIGH.value == 75
        assert Priority.MEDIUM.value == 50
        assert Priority.LOW.value == 25


class TestContext:
    def test_values(self):
        assert Context.PRESCRIBER.value == 100
        assert Context.TESTING.value == 80
        assert Context.MONITORING.value == 60
        assert Context.RESEARCH.value == 40
        assert Context.VAULT_MAINTENANCE.value == 20


class TestEvidenceTier:
    def test_values(self):
        assert EvidenceTier.E1.value == 100
        assert EvidenceTier.E2.value == 80
        assert EvidenceTier.E3.value == 60
        assert EvidenceTier.E4.value == 40
        assert EvidenceTier.E5.value == 20


class TestSeverity:
    def test_values(self):
        assert Severity.LIFE_THREATENING.value == 100
        assert Severity.SIGNIFICANT.value == 75
        assert Severity.MODERATE.value == 50
        assert Severity.LIFESTYLE.value == 25
        assert Severity.UNKNOWN.value == 60


class TestTriageItem:
    def _make_item(self, **overrides) -> TriageItem:
        defaults = dict(
            item_id=ItemId.from_content("Note", "task"),
            source=SourceLocation(file_path=Path("a.md"), line_number=1),
            text="Do something",
            priority=Priority.MEDIUM,
            context=Context.RESEARCH,
            due=None,
            completed=False,
            evidence_tier=None,
            severity=None,
            linked_genes=[],
            linked_systems=[],
            blocked_by=[],
            clinically_validated=False,
        )
        defaults.update(overrides)
        return TriageItem(**defaults)

    def test_creation(self):
        item = self._make_item()
        assert item.text == "Do something"
        assert item.completed is False

    def test_defer_returns_command(self):
        item = self._make_item()
        cmd = item.defer(7)
        assert cmd.item_id == item.item_id
        assert cmd.days == 7

    def test_defer_invalid_days(self):
        item = self._make_item()
        with pytest.raises(ValueError, match="days must be"):
            item.defer(10)

    def test_approve_returns_command(self):
        item = self._make_item()
        cmd = item.approve()
        assert cmd.item_id == item.item_id

    def test_drop_returns_command(self):
        item = self._make_item()
        cmd = item.drop("not relevant")
        assert cmd.item_id == item.item_id
        assert cmd.note == "not relevant"

    def test_change_priority_returns_command(self):
        item = self._make_item()
        cmd = item.change_priority(Priority.HIGH)
        assert cmd.new_priority == Priority.HIGH
