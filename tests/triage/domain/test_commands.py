from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from genome_toolkit.triage.domain.commands import (
    ApproveCommand,
    ChangePriorityCommand,
    CreateCommand,
    DeferCommand,
    DropCommand,
)
from genome_toolkit.triage.domain.item import Context, ItemId, Priority


class TestDeferCommand:
    def test_valid_days(self):
        iid = ItemId.from_content("N", "t")
        for d in (7, 14, 30):
            cmd = DeferCommand(item_id=iid, days=d)
            assert cmd.days == d

    def test_invalid_days_rejected(self):
        iid = ItemId.from_content("N", "t")
        with pytest.raises(ValueError, match="days must be"):
            DeferCommand(item_id=iid, days=10)

    def test_frozen(self):
        cmd = DeferCommand(item_id=ItemId.from_content("N", "t"), days=7)
        with pytest.raises(AttributeError):
            cmd.days = 14  # type: ignore[misc]

    def test_optional_note(self):
        iid = ItemId.from_content("N", "t")
        cmd = DeferCommand(item_id=iid, days=7, note="waiting")
        assert cmd.note == "waiting"


class TestDropCommand:
    def test_requires_note(self):
        iid = ItemId.from_content("N", "t")
        with pytest.raises(ValueError, match="note.*required"):
            DropCommand(item_id=iid, note="")

    def test_valid(self):
        iid = ItemId.from_content("N", "t")
        cmd = DropCommand(item_id=iid, note="not actionable")
        assert cmd.note == "not actionable"


class TestApproveCommand:
    def test_creation(self):
        iid = ItemId.from_content("N", "t")
        cmd = ApproveCommand(item_id=iid)
        assert cmd.item_id == iid
        assert cmd.note is None


class TestChangePriorityCommand:
    def test_creation(self):
        iid = ItemId.from_content("N", "t")
        cmd = ChangePriorityCommand(item_id=iid, new_priority=Priority.HIGH)
        assert cmd.new_priority == Priority.HIGH


class TestCreateCommand:
    def test_creation(self):
        cmd = CreateCommand(
            file_path=Path("Systems/HPA Axis.md"),
            text="Add cortisol protocol",
            priority=Priority.MEDIUM,
            context=Context.RESEARCH,
        )
        assert cmd.due is None

    def test_with_due(self):
        cmd = CreateCommand(
            file_path=Path("a.md"),
            text="t",
            priority=Priority.LOW,
            context=Context.VAULT_MAINTENANCE,
            due=date(2026, 5, 1),
        )
        assert cmd.due == date(2026, 5, 1)
