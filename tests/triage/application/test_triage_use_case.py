from __future__ import annotations

from datetime import date

from genome_toolkit.triage.domain.item import (
    Context,
    EvidenceTier,
    Priority,
    Severity,
    TriageItem,
)
from genome_toolkit.triage.domain.score import TriageBucket
from genome_toolkit.triage.domain.signals import Finding, LabSignal
from genome_toolkit.triage.application.report import TriageReport
from genome_toolkit.triage.application.triage_use_case import RunTriageSession

from .conftest import (
    InMemoryFindingsRepository,
    InMemoryLabSignalRepository,
    InMemorySessionRepository,
    InMemoryTaskRepository,
)


class TestRunTriageSession:
    """Tests for the RunTriageSession use case."""

    def test_returns_items_sorted_by_score_descending(
        self,
        high_priority_prescriber_item: TriageItem,
        low_priority_research_item: TriageItem,
        medium_vault_item: TriageItem,
    ) -> None:
        task_repo = InMemoryTaskRepository(
            [low_priority_research_item, high_priority_prescriber_item, medium_vault_item]
        )
        use_case = RunTriageSession(
            task_repo=task_repo,
            findings_repo=InMemoryFindingsRepository(),
            lab_signal_repo=InMemoryLabSignalRepository(),
            session_repo=InMemorySessionRepository(),
        )

        report = use_case.execute()

        scores = [si.score.value for si in report.scored_items]
        assert scores == sorted(scores, reverse=True), (
            f"Items should be sorted by score descending, got {scores}"
        )
        assert report.total_items == 3

    def test_context_filter_prescriber(
        self,
        high_priority_prescriber_item: TriageItem,
        low_priority_research_item: TriageItem,
        medium_vault_item: TriageItem,
    ) -> None:
        task_repo = InMemoryTaskRepository(
            [high_priority_prescriber_item, low_priority_research_item, medium_vault_item]
        )
        use_case = RunTriageSession(
            task_repo=task_repo,
            findings_repo=InMemoryFindingsRepository(),
            lab_signal_repo=InMemoryLabSignalRepository(),
            session_repo=InMemorySessionRepository(),
        )

        report = use_case.execute(context_filter=Context.PRESCRIBER)

        assert all(si.item.context == Context.PRESCRIBER for si in report.scored_items)
        assert report.total_items == 1

    def test_bucket_filter_do_now(
        self,
        high_priority_prescriber_item: TriageItem,
        low_priority_research_item: TriageItem,
        crp_lab_signal: LabSignal,
    ) -> None:
        task_repo = InMemoryTaskRepository(
            [high_priority_prescriber_item, low_priority_research_item]
        )
        use_case = RunTriageSession(
            task_repo=task_repo,
            findings_repo=InMemoryFindingsRepository(),
            lab_signal_repo=InMemoryLabSignalRepository([crp_lab_signal]),
            session_repo=InMemorySessionRepository(),
        )

        report = use_case.execute(bucket_filter=TriageBucket.DO_NOW)

        assert all(
            si.score.bucket == TriageBucket.DO_NOW for si in report.scored_items
        )

    def test_suggestions_include_unincorporated_findings(
        self,
        high_priority_prescriber_item: TriageItem,
        unincorporated_finding: Finding,
    ) -> None:
        task_repo = InMemoryTaskRepository([high_priority_prescriber_item])
        findings_repo = InMemoryFindingsRepository([unincorporated_finding])
        use_case = RunTriageSession(
            task_repo=task_repo,
            findings_repo=findings_repo,
            lab_signal_repo=InMemoryLabSignalRepository(),
            session_repo=InMemorySessionRepository(),
        )

        report = use_case.execute()

        assert len(report.suggestions) >= 1
        texts = [s.text for s in report.suggestions]
        assert any("NAT2" in t for t in texts)

    def test_bucket_counts_reflect_filtered_items(
        self,
        high_priority_prescriber_item: TriageItem,
        low_priority_research_item: TriageItem,
    ) -> None:
        task_repo = InMemoryTaskRepository(
            [high_priority_prescriber_item, low_priority_research_item]
        )
        use_case = RunTriageSession(
            task_repo=task_repo,
            findings_repo=InMemoryFindingsRepository(),
            lab_signal_repo=InMemoryLabSignalRepository(),
            session_repo=InMemorySessionRepository(),
        )

        report = use_case.execute()

        total_from_buckets = sum(report.bucket_counts.values())
        assert total_from_buckets == report.total_items

    def test_completed_items_excluded(self, make_item) -> None:
        open_item = make_item("Open task", priority=Priority.HIGH)
        done_item = make_item("Done task", priority=Priority.HIGH, completed=True)
        task_repo = InMemoryTaskRepository([open_item, done_item])
        use_case = RunTriageSession(
            task_repo=task_repo,
            findings_repo=InMemoryFindingsRepository(),
            lab_signal_repo=InMemoryLabSignalRepository(),
            session_repo=InMemorySessionRepository(),
        )

        report = use_case.execute()

        assert report.total_items == 1
        assert report.scored_items[0].item.text == "Open task"

    def test_defer_count_affects_score(
        self, high_priority_prescriber_item: TriageItem
    ) -> None:
        task_repo = InMemoryTaskRepository([high_priority_prescriber_item])
        session_repo = InMemorySessionRepository()
        session_repo.set_defer_count(high_priority_prescriber_item.item_id, 3)

        use_case_with_defers = RunTriageSession(
            task_repo=task_repo,
            findings_repo=InMemoryFindingsRepository(),
            lab_signal_repo=InMemoryLabSignalRepository(),
            session_repo=session_repo,
        )
        report_deferred = use_case_with_defers.execute()

        session_repo_zero = InMemorySessionRepository()
        use_case_no_defers = RunTriageSession(
            task_repo=task_repo,
            findings_repo=InMemoryFindingsRepository(),
            lab_signal_repo=InMemoryLabSignalRepository(),
            session_repo=session_repo_zero,
        )
        report_fresh = use_case_no_defers.execute()

        deferred_score = report_deferred.scored_items[0].score.value
        fresh_score = report_fresh.scored_items[0].score.value
        assert deferred_score > fresh_score, (
            f"Deferred item score ({deferred_score}) should be higher than fresh ({fresh_score})"
        )

    def test_lab_signals_boost_linked_items(
        self,
        high_priority_prescriber_item: TriageItem,
        crp_lab_signal: LabSignal,
    ) -> None:
        task_repo = InMemoryTaskRepository([high_priority_prescriber_item])

        use_case_with_lab = RunTriageSession(
            task_repo=task_repo,
            findings_repo=InMemoryFindingsRepository(),
            lab_signal_repo=InMemoryLabSignalRepository([crp_lab_signal]),
            session_repo=InMemorySessionRepository(),
        )
        report_with = use_case_with_lab.execute()

        use_case_no_lab = RunTriageSession(
            task_repo=task_repo,
            findings_repo=InMemoryFindingsRepository(),
            lab_signal_repo=InMemoryLabSignalRepository(),
            session_repo=InMemorySessionRepository(),
        )
        report_without = use_case_no_lab.execute()

        score_with = report_with.scored_items[0].score.value
        score_without = report_without.scored_items[0].score.value
        assert score_with > score_without

    def test_report_has_timestamp(self, make_item) -> None:
        task_repo = InMemoryTaskRepository([make_item("Some task")])
        use_case = RunTriageSession(
            task_repo=task_repo,
            findings_repo=InMemoryFindingsRepository(),
            lab_signal_repo=InMemoryLabSignalRepository(),
            session_repo=InMemorySessionRepository(),
        )

        report = use_case.execute()

        assert report.timestamp is not None

    def test_empty_items_returns_empty_report(self) -> None:
        use_case = RunTriageSession(
            task_repo=InMemoryTaskRepository(),
            findings_repo=InMemoryFindingsRepository(),
            lab_signal_repo=InMemoryLabSignalRepository(),
            session_repo=InMemorySessionRepository(),
        )

        report = use_case.execute()

        assert report.total_items == 0
        assert report.scored_items == []
