from __future__ import annotations

import pytest

from genome_toolkit.triage.domain.score import TriageBucket
from genome_toolkit.triage.domain.services.bucket import BucketClassifier


class TestBucketClassifier:
    def setup_method(self):
        self.classifier = BucketClassifier()

    def test_do_now(self):
        assert self.classifier.classify(70) == TriageBucket.DO_NOW
        assert self.classifier.classify(100) == TriageBucket.DO_NOW
        assert self.classifier.classify(85) == TriageBucket.DO_NOW

    def test_this_week(self):
        assert self.classifier.classify(50) == TriageBucket.THIS_WEEK
        assert self.classifier.classify(69.9) == TriageBucket.THIS_WEEK

    def test_backlog(self):
        assert self.classifier.classify(30) == TriageBucket.BACKLOG
        assert self.classifier.classify(49.9) == TriageBucket.BACKLOG

    def test_consider_dropping(self):
        assert self.classifier.classify(0) == TriageBucket.CONSIDER_DROPPING
        assert self.classifier.classify(29.9) == TriageBucket.CONSIDER_DROPPING
