from __future__ import annotations

from difflib import SequenceMatcher

from genome_toolkit.triage.domain.item import Context, Priority, TriageItem
from genome_toolkit.triage.domain.signals import Finding, LabSignal, StaleTopic
from genome_toolkit.triage.domain.suggestion import Suggestion, SuggestionSource

_DEDUP_THRESHOLD = 0.85


class SuggestionGenerator:
    def generate(
        self,
        findings: list[Finding],
        stale_topics: list[StaleTopic],
        lab_signals: list[LabSignal],
        existing_items: list[TriageItem],
    ) -> list[Suggestion]:
        suggestions: list[Suggestion] = []

        for f in findings:
            if f.incorporated_into is not None or not f.actionable:
                continue
            dup = self._find_duplicate(f.text, existing_items)
            suggestions.append(
                Suggestion(
                    text=f"Incorporate finding: {f.text}",
                    source_type=SuggestionSource.UNINCORPORATED_FINDING,
                    source_reference=f.source_note,
                    recommended_priority=self._priority_from_tier(f.evidence_tier),
                    recommended_context=Context.VAULT_MAINTENANCE,
                    rationale=f"Unincorporated actionable finding from {f.source_note}",
                    possible_duplicate_of=dup,
                )
            )

        for st in stale_topics:
            dup = self._find_duplicate(st.topic, existing_items)
            suggestions.append(
                Suggestion(
                    text=f"Research update needed: {st.topic}",
                    source_type=SuggestionSource.STALE_RESEARCH,
                    source_reference=st.topic,
                    recommended_priority=Priority.MEDIUM,
                    recommended_context=Context.RESEARCH,
                    rationale=f"{st.months_overdue:.0f} months overdue for review",
                    possible_duplicate_of=dup,
                )
            )

        for sig in lab_signals:
            dup = self._find_duplicate(sig.biomarker, existing_items)
            suggestions.append(
                Suggestion(
                    text=f"Lab signal: {sig.biomarker} {sig.direction.value} threshold (z={sig.z_score:.1f})",
                    source_type=SuggestionSource.LAB_THRESHOLD,
                    source_reference=sig.biomarker,
                    recommended_priority=Priority.HIGH if sig.z_score >= 2.0 else Priority.MEDIUM,
                    recommended_context=Context.PRESCRIBER if sig.z_score >= 2.0 else Context.MONITORING,
                    rationale=f"{sig.biomarker}={sig.value} vs threshold {sig.threshold}",
                    possible_duplicate_of=dup,
                )
            )

        return suggestions

    @staticmethod
    def _find_duplicate(text: str, existing: list[TriageItem]) -> str | None:
        for item in existing:
            ratio = SequenceMatcher(None, text.lower(), item.text.lower()).ratio()
            if ratio >= _DEDUP_THRESHOLD:
                return item.text
        return None

    @staticmethod
    def _priority_from_tier(tier) -> Priority:
        from genome_toolkit.triage.domain.item import EvidenceTier

        if tier in (EvidenceTier.E1, EvidenceTier.E2):
            return Priority.HIGH
        if tier == EvidenceTier.E3:
            return Priority.MEDIUM
        return Priority.LOW
