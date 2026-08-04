"""SQLite database access.

Small helpers around the standard library sqlite3 module.
One file, three tables:
  documents - uploaded files.
  chunks    - text pieces and their embeddings.
  revisions - spaced repetition state per topic.
"""

import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any

from backend import config

_connection: sqlite3.Connection | None = None
_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding BLOB
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);

CREATE TABLE IF NOT EXISTS revisions (
    topic TEXT PRIMARY KEY,
    ease REAL NOT NULL,
    interval_days INTEGER NOT NULL,
    repetitions INTEGER NOT NULL,
    next_review TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Public alias so other modules do not touch the private helper.
now = _now


def connect() -> sqlite3.Connection:
    """Open the database connection (created once, reused after)."""
    global _connection
    with _lock:
        if _connection is None:
            config.ensure_dirs()
            _connection = sqlite3.connect(config.DB_PATH, check_same_thread=False)
            _connection.row_factory = sqlite3.Row
            _connection.executescript(SCHEMA)
            _connection.commit()
        return _connection


def query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Run a SELECT and return rows as dicts."""
    conn = connect()
    with _lock:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def execute(sql: str, params: tuple = ()) -> int:
    """Run an INSERT, UPDATE, or DELETE. Returns the last row id."""
    conn = connect()
    with _lock:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid or 0
