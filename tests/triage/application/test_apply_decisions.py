from __future__ import annotations

from datetime import date, timedelta

import pytest

from genome_toolkit.triage.domain.commands import (
    ApproveCommand,
    ChangePriorityCommand,
    CreateCommand,
    DeferCommand,
    DropCommand,
)
from genome_toolkit.triage.domain.item import Context, Priority, TriageItem
from genome_toolkit.triage.domain.session import Action
from genome_toolkit.triage.application.apply_decisions import ApplyDecisions

from .conftest import InMemorySessionRepository, InMemoryTaskRepository


class TestApplyDecisions:
    """Tests for the ApplyDecisions use case."""

    def test_creates_valid_session_with_approve(
        self, high_priority_prescriber_item: TriageItem
    ) -> None:
        task_repo = InMemoryTaskRepository([high_priority_prescriber_item])
        session_repo = InMemorySessionRepository()
        use_case = ApplyDecisions(task_repo=task_repo, session_repo=session_repo)

        cmd = ApproveCommand(item_id=high_priority_prescriber_item.item_id)
        session = use_case.execute([(high_priority_prescriber_item, cmd)])

        assert len(session.decisions) == 1
        assert session.decisions[0].action == Action.APPROVE
        assert session.decisions[0].new.completed is True
        assert len(task_repo.applied_commands) == 1

    def test_creates_valid_session_with_defer(
        self, high_priority_prescriber_item: TriageItem
    ) -> None:
        task_repo = InMemoryTaskRepository([high_priority_prescriber_item])
        session_repo = InMemorySessionRepository()
        use_case = ApplyDecisions(task_repo=task_repo, session_repo=session_repo)

        cmd = DeferCommand(item_id=high_priority_prescriber_item.item_id, days=7)
        session = use_case.execute([(high_priority_prescriber_item, cmd)])

        assert len(session.decisions) == 1
        assert session.decisions[0].action == Action.DEFER
        expected_due = (high_priority_prescriber_item.due or date.today()) + timedelta(days=7)
        assert session.decisions[0].new.due == expected_due

    def test_creates_valid_session_with_drop(
        self, high_priority_prescriber_item: TriageItem
    ) -> None:
        task_repo = InMemoryTaskRepository([high_priority_prescriber_item])
        session_repo = InMemorySessionRepository()
        use_case = ApplyDecisions(task_repo=task_repo, session_repo=session_repo)

        cmd = DropCommand(
            item_id=high_priority_prescriber_item.item_id,
            note="Not actionable at this time",
        )
        session = use_case.execute([(high_priority_prescriber_item, cmd)])

        assert len(session.decisions) == 1
        assert session.decisions[0].action == Action.DROP
        assert session.decisions[0].new.completed is True
        assert session.decisions[0].note == "Not actionable at this time"

    def test_creates_valid_session_with_change_priority(
        self, high_priority_prescriber_item: TriageItem
    ) -> None:
        task_repo = InMemoryTaskRepository([high_priority_prescriber_item])
        session_repo = InMemorySessionRepository()
        use_case = ApplyDecisions(task_repo=task_repo, session_repo=session_repo)

        cmd = ChangePriorityCommand(
            item_id=high_priority_prescriber_item.item_id,
            new_priority=Priority.LOW,
        )
        session = use_case.execute([(high_priority_prescriber_item, cmd)])

        assert len(session.decisions) == 1
        assert session.decisions[0].action == Action.CHANGE_PRIORITY
        assert session.decisions[0].new.priority == Priority.LOW

    def test_creates_valid_session_with_create(
        self, high_priority_prescriber_item: TriageItem
    ) -> None:
        from pathlib import Path

        task_repo = InMemoryTaskRepository([high_priority_prescriber_item])
        session_repo = InMemorySessionRepository()
        use_case = ApplyDecisions(task_repo=task_repo, session_repo=session_repo)

        cmd = CreateCommand(
            file_path=Path("Reports/Summary.md"),
            text="New action item from findings",
            priority=Priority.HIGH,
            context=Context.VAULT_MAINTENANCE,
        )
        session = use_case.execute([(high_priority_prescriber_item, cmd)])

        assert len(session.decisions) == 1
        assert session.decisions[0].action == Action.CREATE
        assert len(task_repo.created_items) == 1

    def test_rejects_conflicting_actions_approve_and_drop(
        self, high_priority_prescriber_item: TriageItem
    ) -> None:
        task_repo = InMemoryTaskRepository([high_priority_prescriber_item])
        session_repo = InMemorySessionRepository()
        use_case = ApplyDecisions(task_repo=task_repo, session_repo=session_repo)

        approve_cmd = ApproveCommand(item_id=high_priority_prescriber_item.item_id)
        drop_cmd = DropCommand(
            item_id=high_priority_prescriber_item.item_id,
            note="conflicting",
        )

        with pytest.raises(ValueError, match="conflicting actions"):
            use_case.execute([
                (high_priority_prescriber_item, approve_cmd),
                (high_priority_prescriber_item, drop_cmd),
            ])

    def test_multiple_items_different_actions(
        self,
        high_priority_prescriber_item: TriageItem,
        low_priority_research_item: TriageItem,
    ) -> None:
        task_repo = InMemoryTaskRepository(
            [high_priority_prescriber_item, low_priority_research_item]
        )
        session_repo = InMemorySessionRepository()
        use_case = ApplyDecisions(task_repo=task_repo, session_repo=session_repo)

        decisions = [
            (
                high_priority_prescriber_item,
                ApproveCommand(item_id=high_priority_prescriber_item.item_id),
            ),
            (
                low_priority_research_item,
                DropCommand(
                    item_id=low_priority_research_item.item_id,
                    note="not relevant",
                ),
            ),
        ]
        session = use_case.execute(decisions)

        assert len(session.decisions) == 2
        assert len(task_repo.applied_commands) == 2

    def test_session_saved_to_repo(
        self, high_priority_prescriber_item: TriageItem
    ) -> None:
        task_repo = InMemoryTaskRepository([high_priority_prescriber_item])
        session_repo = InMemorySessionRepository()
        use_case = ApplyDecisions(task_repo=task_repo, session_repo=session_repo)

        cmd = ApproveCommand(item_id=high_priority_prescriber_item.item_id)
        use_case.execute([(high_priority_prescriber_item, cmd)])

        recent = session_repo.get_recent()
        assert len(recent) == 1

    def test_previous_snapshot_captures_original_state(
        self, high_priority_prescriber_item: TriageItem
    ) -> None:
        task_repo = InMemoryTaskRepository([high_priority_prescriber_item])
        session_repo = InMemorySessionRepository()
        use_case = ApplyDecisions(task_repo=task_repo, session_repo=session_repo)

        cmd = ChangePriorityCommand(
            item_id=high_priority_prescriber_item.item_id,
            new_priority=Priority.LOW,
        )
        session = use_case.execute([(high_priority_prescriber_item, cmd)])

        decision = session.decisions[0]
        assert decision.previous.priority == Priority.CRITICAL
        assert decision.new.priority == Priority.LOW
