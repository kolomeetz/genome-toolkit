from __future__ import annotations

from genome_toolkit.triage.domain.score import TriageBucket


class BucketClassifier:
    def classify(self, score: float) -> TriageBucket:
        if score >= 70:
            return TriageBucket.DO_NOW
        if score >= 50:
            return TriageBucket.THIS_WEEK
        if score >= 30:
            return TriageBucket.BACKLOG
        return TriageBucket.CONSIDER_DROPPING
