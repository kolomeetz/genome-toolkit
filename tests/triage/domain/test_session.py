from __future__ import annotations

from datetime import date, datetime

import pytest

from genome_toolkit.triage.domain.item import Context, ItemId, Priority
from genome_toolkit.triage.domain.session import (
    Action,
    TriageDecision,
    TriageSession,
    TriageStateSnapshot,
)


class TestAction:
    def test_all_members(self):
        assert set(Action) == {
            Action.APPROVE,
            Action.DEFER,
            Action.DROP,
            Action.CHANGE_PRIORITY,
            Action.CREATE,
        }


class TestTriageStateSnapshot:
    def test_creation(self):
        snap = TriageStateSnapshot(
            priority=Priority.HIGH,
            due=date(2026, 4, 15),
            context=Context.PRESCRIBER,
            completed=False,
        )
        assert snap.priority == Priority.HIGH
        assert snap.completed is False

    def test_nullable_fields(self):
        snap = TriageStateSnapshot(
            priority=None, due=None, context=None, completed=False
        )
        assert snap.priority is None

    def test_frozen(self):
        snap = TriageStateSnapshot(
            priority=Priority.LOW, due=None, context=None, completed=False
        )
        with pytest.raises(AttributeError):
            snap.completed = True  # type: ignore[misc]


class TestTriageDecision:
    def test_creation(self):
        iid = ItemId.from_content("N", "t")
        prev = TriageStateSnapshot(Priority.MEDIUM, None, Context.RESEARCH, False)
        new = TriageStateSnapshot(Priority.MEDIUM, date(2026, 4, 8), Context.RESEARCH, False)
        dec = TriageDecision(
            item_id=iid, action=Action.DEFER, previous=prev, new=new, note="waiting"
        )
        assert dec.action == Action.DEFER
        assert dec.note == "waiting"


class TestTriageSession:
    def _make_session(self) -> TriageSession:
        return TriageSession(
            session_id="20260401-1430",
            timestamp=datetime(2026, 4, 1, 14, 30),
            decisions=[],
        )

    def _make_decision(self, stem: str, action: Action) -> TriageDecision:
        iid = ItemId.from_content(stem, "task")
        snap = TriageStateSnapshot(Priority.MEDIUM, None, Context.RESEARCH, False)
        return TriageDecision(item_id=iid, action=action, previous=snap, new=snap, note=None)

    def test_add_decision(self):
        session = self._make_session()
        dec = self._make_decision("A", Action.APPROVE)
        session.add_decision(dec)
        assert len(session.decisions) == 1

    def test_cannot_approve_and_drop_same_item(self):
        session = self._make_session()
        approve = self._make_decision("A", Action.APPROVE)
        drop = TriageDecision(
            item_id=approve.item_id,
            action=Action.DROP,
            previous=approve.previous,
            new=approve.new,
            note="reason",
        )
        session.add_decision(approve)
        with pytest.raises(ValueError, match="conflicting"):
            session.add_decision(drop)

    def test_cannot_drop_then_approve_same_item(self):
        session = self._make_session()
        iid = ItemId.from_content("X", "task")
        snap = TriageStateSnapshot(Priority.MEDIUM, None, Context.RESEARCH, False)
        drop = TriageDecision(item_id=iid, action=Action.DROP, previous=snap, new=snap, note="reason")
        approve = TriageDecision(item_id=iid, action=Action.APPROVE, previous=snap, new=snap, note=None)
        session.add_decision(drop)
        with pytest.raises(ValueError, match="conflicting"):
            session.add_decision(approve)

    def test_different_items_ok(self):
        session = self._make_session()
        session.add_decision(self._make_decision("A", Action.APPROVE))
        session.add_decision(self._make_decision("B", Action.DROP))
        assert len(session.decisions) == 2

    def test_duplicate_action_same_item_rejected(self):
        session = self._make_session()
        dec1 = self._make_decision("A", Action.DEFER)
        dec2 = self._make_decision("A", Action.CHANGE_PRIORITY)
        session.add_decision(dec1)
        with pytest.raises(ValueError, match="conflicting"):
            session.add_decision(dec2)
