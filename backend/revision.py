"""Spaced repetition (SM-2).

The classic SuperMemo SM-2 algorithm. Each topic has an ease factor, an
interval in days, and a repetition count. When the student reviews a topic and
grades their recall from 0 to 5, the schedule is updated:

  - quality 3 or higher means success: interval grows (1 day, 6 days, then
    interval times ease).
  - quality below 3 means failure: repetitions reset, interval goes back to 1.
"""

from datetime import date, timedelta

from backend import db

MIN_EASE = 1.3
INITIAL_EASE = 2.5


def _today_iso() -> str:
    return date.today().isoformat()


def _due_iso(interval_days: int) -> str:
    return (date.today() + timedelta(days=interval_days)).isoformat()


def get_revisions() -> list[dict]:
    """Return all topics, with due ones first."""
    rows = db.query(
        "SELECT topic, ease, interval_days, repetitions, next_review "
        "FROM revisions ORDER BY next_review ASC"
    )
    return rows


def get_due_revisions() -> list[dict]:
    """Return only topics due today or earlier."""
    rows = db.query(
        "SELECT topic, ease, interval_days, repetitions, next_review "
        "FROM revisions WHERE next_review <= ? ORDER BY next_review ASC",
        (_today_iso(),),
    )
    return rows


def schedule(topic: str) -> dict:
    """Create a new revision card for a topic (due tomorrow)."""
    db.execute(
        "INSERT INTO revisions (topic, ease, interval_days, repetitions, next_review, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (topic, INITIAL_EASE, 1, 0, _due_iso(1), db.now()),
    )
    return {
        "topic": topic,
        "ease": INITIAL_EASE,
        "interval_days": 1,
        "repetitions": 0,
        "next_review": _due_iso(1),
    }


def grade(topic: str, quality: int) -> dict:
    """Apply an SM-2 quality grade (0-5) to a topic's card."""
    if not 0 <= quality <= 5:
        raise ValueError("quality must be between 0 and 5")

    row = db.query("SELECT * FROM revisions WHERE topic = ?", (topic,))
    if not row:
        # A topic without a card gets one, seeded as if failed once.
        base = schedule(topic)
        repetitions, ease, interval_days = 0, base["ease"], 0
    else:
        r = row[0]
        repetitions, ease, interval_days = (
            r["repetitions"],
            r["ease"],
            r["interval_days"],
        )

    if quality >= 3:
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 6
        else:
            interval_days = round(interval_days * ease)
        repetitions += 1
        ease = max(MIN_EASE, ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    else:
        repetitions = 0
        interval_days = 1
        ease = max(MIN_EASE, ease)

    next_review = _due_iso(interval_days)
    db.execute(
        "INSERT INTO revisions (topic, ease, interval_days, repetitions, next_review, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(topic) DO UPDATE SET ease=excluded.ease, "
        "interval_days=excluded.interval_days, repetitions=excluded.repetitions, "
        "next_review=excluded.next_review",
        (topic, ease, interval_days, repetitions, next_review, db.now()),
    )

    return {
        "topic": topic,
        "ease": round(ease, 2),
        "interval_days": interval_days,
        "repetitions": repetitions,
        "next_review": next_review,
    }
