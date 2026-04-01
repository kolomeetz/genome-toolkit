from __future__ import annotations

from collections import Counter
from datetime import datetime

from genome_toolkit.triage.domain.item import Context, TriageItem
from genome_toolkit.triage.domain.ports.repositories import (
    FindingsRepository,
    LabSignalRepository,
    SessionRepository,
    TaskRepository,
)
from genome_toolkit.triage.domain.score import TriageBucket
from genome_toolkit.triage.domain.services.scoring import ScoringService
from genome_toolkit.triage.domain.services.suggestion import SuggestionGenerator
from genome_toolkit.triage.domain.weights import ScoringWeights

from .report import ScoredItem, TriageReport


class RunTriageSession:
    """Orchestrates a full triage scoring + suggestion run."""

    def __init__(
        self,
        task_repo: TaskRepository,
        findings_repo: FindingsRepository,
        lab_signal_repo: LabSignalRepository,
        session_repo: SessionRepository,
        weights: ScoringWeights | None = None,
    ) -> None:
        self._task_repo = task_repo
        self._findings_repo = findings_repo
        self._lab_signal_repo = lab_signal_repo
        self._session_repo = session_repo
        self._weights = weights or ScoringWeights()
        self._scoring = ScoringService()
        self._suggestion_gen = SuggestionGenerator()

    def execute(
        self,
        context_filter: Context | None = None,
        bucket_filter: TriageBucket | None = None,
    ) -> TriageReport:
        # 1. Gather data
        items = self._task_repo.get_all_open()
        lab_signals = self._lab_signal_repo.get_active_signals()
        findings = self._findings_repo.get_unincorporated()

        # 2. Score each item
        scored: list[ScoredItem] = []
        for item in items:
            defer_count = self._session_repo.get_defer_count(item.item_id)
            score = self._scoring.score(item, self._weights, lab_signals, defer_count)
            scored.append(ScoredItem(item=item, score=score))

        # 3. Generate suggestions
        suggestions = self._suggestion_gen.generate(
            findings=findings,
            stale_topics=[],
            lab_signals=lab_signals,
            existing_items=items,
        )

        # 4. Sort by score descending
        scored.sort(key=lambda si: si.score.value, reverse=True)

        # 5. Apply filters
        if context_filter is not None:
            scored = [si for si in scored if si.item.context == context_filter]

        if bucket_filter is not None:
            scored = [si for si in scored if si.score.bucket == bucket_filter]

        # 6. Compute bucket counts (from filtered set)
        bucket_counter: Counter[TriageBucket] = Counter()
        for si in scored:
            bucket_counter[si.score.bucket] += 1

        return TriageReport(
            scored_items=scored,
            suggestions=suggestions,
            total_items=len(scored),
            bucket_counts=dict(bucket_counter),
            timestamp=datetime.now(),
        )
