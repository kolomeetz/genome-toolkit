from __future__ import annotations

import shutil
from datetime import date, datetime
from pathlib import Path

import pytest

from genome_toolkit.triage.domain.item import Context, ItemId, Priority
from genome_toolkit.triage.domain.session import (
    Action,
    TriageDecision,
    TriageSession,
    TriageStateSnapshot,
)
from genome_toolkit.triage.infrastructure.persistence.session_store import (
    MarkdownSessionRepository,
)


FIXTURE_VAULT = Path(__file__).resolve().parents[2] / "fixtures" / "vault"


@pytest.fixture
def session_repo(tmp_path: Path) -> MarkdownSessionRepository:
    dst = tmp_path / "vault"
    shutil.copytree(FIXTURE_VAULT, dst)
    return MarkdownSessionRepository(dst)


def _make_session(session_id: str = "test-session") -> TriageSession:
    session = TriageSession(
        session_id=session_id,
        timestamp=datetime(2026, 4, 1, 14, 30),
    )
    session.add_decision(TriageDecision(
        item_id=ItemId.from_block_id("task-crp-test"),
        action=Action.DEFER,
        previous=TriageStateSnapshot(
            priority=Priority.CRITICAL,
            due=date(2026, 4, 15),
            context=Context.TESTING,
            completed=False,
        ),
        new=TriageStateSnapshot(
            priority=Priority.CRITICAL,
            due=date(2026, 4, 22),
            context=Context.TESTING,
            completed=False,
        ),
        note="waiting for appointment",
    ))
    session.add_decision(TriageDecision(
        item_id=ItemId.from_block_id("task-nortriptyline"),
        action=Action.DROP,
        previous=TriageStateSnapshot(
            priority=Priority.HIGH,
            due=date(2026, 4, 30),
            context=Context.PRESCRIBER,
            completed=False,
        ),
        new=TriageStateSnapshot(
            priority=Priority.HIGH,
            due=date(2026, 4, 30),
            context=Context.PRESCRIBER,
            completed=True,
        ),
        note="not relevant now",
    ))
    return session


def test_save_session_creates_entry(session_repo: MarkdownSessionRepository) -> None:
    session = _make_session()
    session_repo.save_session(session)
    history_file = session_repo._vault_path / "Meta" / "Triage History.md"
    content = history_file.read_text(encoding="utf-8")
    assert "2026-04-01 14:30" in content
    assert "task-crp-test" in content
    assert "waiting for appointment" in content


def test_save_session_appends_to_existing(session_repo: MarkdownSessionRepository) -> None:
    s1 = _make_session("session-1")
    s2 = TriageSession(
        session_id="session-2",
        timestamp=datetime(2026, 4, 2, 10, 0),
    )
    s2.add_decision(TriageDecision(
        item_id=ItemId.from_block_id("task-iron-panel"),
        action=Action.APPROVE,
        previous=TriageStateSnapshot(
            priority=Priority.CRITICAL, due=date(2026, 4, 15),
            context=Context.TESTING, completed=False,
        ),
        new=TriageStateSnapshot(
            priority=Priority.CRITICAL, due=date(2026, 4, 15),
            context=Context.TESTING, completed=True,
        ),
        note=None,
    ))

    session_repo.save_session(s1)
    session_repo.save_session(s2)

    content = (session_repo._vault_path / "Meta" / "Triage History.md").read_text()
    assert "2026-04-01 14:30" in content
    assert "2026-04-02 10:00" in content


def test_get_recent_returns_sessions(session_repo: MarkdownSessionRepository) -> None:
    session_repo.save_session(_make_session())
    recent = session_repo.get_recent(limit=10)
    assert len(recent) >= 1
    assert isinstance(recent[0], TriageSession)


def test_get_defer_count(session_repo: MarkdownSessionRepository) -> None:
    # Save two sessions each deferring the same item
    for i in range(2):
        s = TriageSession(
            session_id=f"session-{i}",
            timestamp=datetime(2026, 4, 1 + i, 14, 30),
        )
        s.add_decision(TriageDecision(
            item_id=ItemId.from_block_id("task-crp-test"),
            action=Action.DEFER,
            previous=TriageStateSnapshot(
                priority=Priority.CRITICAL, due=date(2026, 4, 15),
                context=Context.TESTING, completed=False,
            ),
            new=TriageStateSnapshot(
                priority=Priority.CRITICAL, due=date(2026, 4, 22),
                context=Context.TESTING, completed=False,
            ),
            note="still waiting",
        ))
        session_repo.save_session(s)

    assert session_repo.get_defer_count(ItemId.from_block_id("task-crp-test")) == 2
    assert session_repo.get_defer_count(ItemId.from_block_id("nonexistent")) == 0


def test_get_recent_empty_history(session_repo: MarkdownSessionRepository) -> None:
    recent = session_repo.get_recent(limit=10)
    assert recent == []
