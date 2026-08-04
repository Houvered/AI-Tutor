"""Tests for the SM-2 spaced repetition scheduler."""

from datetime import date, timedelta

from backend import config
from backend import db
from backend import revision


class TestRevision:
    def test_schedule_due_tomorrow(self, temp_db):
        card = revision.schedule("trees")
        assert card["interval_days"] == 1
        assert card["next_review"] == (date.today() + timedelta(days=1)).isoformat()

    def test_nothing_due_initially(self, temp_db):
        revision.schedule("trees")
        assert revision.get_due_revisions() == []

    def test_interval_progression(self, temp_db):
        revision.schedule("trees")
        assert revision.grade("trees", 4)["interval_days"] == 1
        assert revision.grade("trees", 4)["interval_days"] == 6
        third = revision.grade("trees", 5)
        # Third success uses old ease (2.5): interval = round(6 * 2.5) = 15.
        assert third["interval_days"] == 15

    def test_failure_resets(self, temp_db):
        revision.grade("trees", 5)
        revision.grade("trees", 5)
        failed = revision.grade("trees", 1)
        assert failed["repetitions"] == 0
        assert failed["interval_days"] == 1

    def test_invalid_quality_raises(self, temp_db):
        revision.schedule("trees")
        try:
            revision.grade("trees", 9)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

    def test_due_revisions_filter(self, temp_db):
        revision.grade("trees", 4)
        db.execute(
            "UPDATE revisions SET next_review = ? WHERE topic = ?",
            ((date.today() - timedelta(days=1)).isoformat(), "trees"),
        )
        topics = [r["topic"] for r in revision.get_due_revisions()]
        assert "trees" in topics