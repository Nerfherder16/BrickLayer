"""
bl/history.py — SQLite verdict history ledger and regression detector.

Stores every verdict produced by a campaign run. Detects regressions
(HEALTHY → FAILURE/WARNING) across runs so degradations don't go unnoticed.

Schema
------
verdict_history
    id            INTEGER PRIMARY KEY AUTOINCREMENT
    question_id   TEXT NOT NULL
    verdict       TEXT NOT NULL        -- FAILURE|WARNING|HEALTHY|INCONCLUSIVE
    failure_type  TEXT                 -- from classify_failure_type()
    confidence    TEXT                 -- high|medium|low|uncertain
    summary       TEXT
    run_id        TEXT                 -- arbitrary label; defaults to ISO timestamp
    timestamp     TEXT NOT NULL        -- ISO-8601 UTC

Index: (question_id, timestamp) for fast per-question queries.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from bl.config import cfg

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS verdict_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id  TEXT NOT NULL,
    verdict      TEXT NOT NULL,
    failure_type TEXT,
    confidence   TEXT,
    summary      TEXT,
    run_id       TEXT,
    timestamp    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_qid_time
    ON verdict_history(question_id, timestamp);
"""


def _db_path() -> Path:
    return cfg.history_db


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------


def record_verdict(
    question_id: str,
    verdict: str,
    summary: str = "",
    failure_type: str | None = None,
    confidence: str | None = None,
    run_id: str | None = None,
) -> None:
    """Append a verdict row to the history ledger."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rid = run_id or ts
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO verdict_history
                (question_id, verdict, failure_type, confidence, summary, run_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (question_id, verdict, failure_type, confidence, summary[:500], rid, ts),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def get_history(question_id: str, limit: int = 20) -> list[dict]:
    """Return the N most recent verdict records for a question (newest first)."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT question_id, verdict, failure_type, confidence, summary, run_id, timestamp
            FROM verdict_history
            WHERE question_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (question_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_latest() -> list[dict]:
    """Return the most recent verdict row per question_id."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT question_id, verdict, failure_type, confidence, summary, run_id, timestamp
            FROM verdict_history
            WHERE id IN (
                SELECT MAX(id) FROM verdict_history GROUP BY question_id
            )
            ORDER BY question_id
            """
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Regression detection
# ---------------------------------------------------------------------------

# A regression is a verdict transition in this set:
_REGRESSIONS: set[tuple[str, str]] = {
    ("HEALTHY", "FAILURE"),
    ("HEALTHY", "WARNING"),
    ("WARNING", "FAILURE"),
}


def detect_regression(question_id: str, new_verdict: str) -> dict | None:
    """
    Check whether new_verdict is a regression relative to the previous run.

    Returns a regression dict if regressed, None otherwise:
        {question_id, previous_verdict, new_verdict, previous_timestamp}
    """
    history = get_history(question_id, limit=2)
    if len(history) < 2:
        return None  # not enough history to compare

    # history[0] is the row we just wrote; history[1] is the prior run
    previous = history[1]
    prev_verdict = previous["verdict"]

    if (prev_verdict, new_verdict) in _REGRESSIONS:
        return {
            "question_id": question_id,
            "previous_verdict": prev_verdict,
            "new_verdict": new_verdict,
            "previous_timestamp": previous["timestamp"],
        }
    return None


def get_regressions() -> list[dict]:
    """
    Scan the full history and return all question_ids where the most recent
    verdict is worse than the run before it.
    """
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT question_id, verdict, timestamp
            FROM verdict_history
            ORDER BY question_id, id DESC
            """
        ).fetchall()

    # Group into per-qid lists (already sorted newest-first within each group)
    by_qid: dict[str, list] = {}
    for row in rows:
        qid = row["question_id"]
        by_qid.setdefault(qid, []).append(row)

    regressions = []
    for qid, records in by_qid.items():
        if len(records) < 2:
            continue
        current, previous = records[0], records[1]
        if (previous["verdict"], current["verdict"]) in _REGRESSIONS:
            regressions.append(
                {
                    "question_id": qid,
                    "previous_verdict": previous["verdict"],
                    "new_verdict": current["verdict"],
                    "previous_timestamp": previous["timestamp"],
                    "current_timestamp": current["timestamp"],
                }
            )
    return regressions


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def regression_report() -> str:
    """Return a human-readable regression summary, or empty string if none."""
    regressions = get_regressions()
    if not regressions:
        return ""

    lines = [f"REGRESSIONS DETECTED ({len(regressions)}):"]
    for r in regressions:
        lines.append(
            f"  {r['question_id']}: {r['previous_verdict']} -> {r['new_verdict']}"
            f"  (was: {r['previous_timestamp']})"
        )
    return "\n".join(lines)
