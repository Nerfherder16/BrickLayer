"""
bl/agent_db.py — Agent performance database.

Tracks per-agent verdict history, success rates, and repair history.
JSON-backed, stored at {project_dir}/agent_db.json.

Score model:
  success verdicts  → 1.0 credit each
  partial verdicts  → 0.5 credit each
  failure verdicts  → 0.0 credit each
  score = (success + partial * 0.5) / total_runs  (range 0.0 – 1.0)

Overseer intervention triggers when score < UNDERPERFORMER_THRESHOLD
AND the agent has run at least MIN_RUNS_FOR_REVIEW times.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Verdict classification
# ---------------------------------------------------------------------------

# Full credit — agent produced actionable, correct output
_SUCCESS_VERDICTS = frozenset(
    {
        "HEALTHY",
        "FIXED",
        "COMPLIANT",
        "CALIBRATED",
        "IMPROVEMENT",
        "OK",
        "PROMISING",
        "DIAGNOSIS_COMPLETE",
        "NOT_APPLICABLE",
        "DONE",
    }
)

# Half credit — partial or conditional success
_PARTIAL_VERDICTS = frozenset(
    {
        "WARNING",
        "PARTIAL",
        "WEAK",
        "DEGRADED",
        "DEGRADED_TRENDING",
        "FIX_FAILED",
        "PENDING_EXTERNAL",
        "BLOCKED",
        "SUBJECTIVE",
        "IMMINENT",
        "PROBABLE",
        "POSSIBLE",
        "UNLIKELY",
    }
)

# Zero credit — agent failed, stalled, or produced noise
_FAILURE_VERDICTS = frozenset(
    {
        "FAILURE",
        "INCONCLUSIVE",
        "NON_COMPLIANT",
        "ALERT",
        "UNKNOWN",
        "UNCALIBRATED",
        "NOT_MEASURABLE",
        "REGRESSION",
    }
)

# Minimum runs before an agent is eligible for overseer review
MIN_RUNS_FOR_REVIEW = 3

# Score threshold below which overseer intervention triggers
UNDERPERFORMER_THRESHOLD = 0.40


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------


def _db_path(project_root: Path) -> Path:
    return project_root / "agent_db.json"


def _load(project_root: Path) -> dict:
    path = _db_path(project_root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save(project_root: Path, db: dict) -> None:
    _db_path(project_root).write_text(
        json.dumps(db, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Score calculation
# ---------------------------------------------------------------------------


def _compute_score(record: dict) -> float:
    """Compute score 0.0–1.0 from a record's verdict distribution."""
    total = record.get("runs", 0)
    if total == 0:
        return 1.0  # no data — assume healthy
    verdicts = record.get("verdicts", {})
    success = sum(verdicts.get(v, 0) for v in _SUCCESS_VERDICTS)
    partial = sum(verdicts.get(v, 0) for v in _PARTIAL_VERDICTS)
    return (success + partial * 0.5) / total


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def record_run(project_root: Path, agent_name: str, verdict: str) -> float:
    """
    Record one verdict for an agent.

    Creates the agent entry if it doesn't exist yet.
    Returns the agent's updated score.
    """
    db = _load(project_root)
    now = datetime.now(timezone.utc).isoformat()

    if agent_name not in db:
        db[agent_name] = {
            "runs": 0,
            "verdicts": {},
            "score": 1.0,
            "last_run": now,
            "created": now,
            "repair_count": 0,
            "last_repair": None,
        }

    rec = db[agent_name]
    rec["runs"] += 1
    rec["verdicts"][verdict] = rec["verdicts"].get(verdict, 0) + 1
    rec["last_run"] = now
    rec["score"] = round(_compute_score(rec), 4)

    _save(project_root, db)
    return rec["score"]


def get_score(project_root: Path, agent_name: str) -> float:
    """Return current score for an agent (1.0 if not yet tracked)."""
    db = _load(project_root)
    if agent_name not in db:
        return 1.0
    return round(_compute_score(db[agent_name]), 4)


def record_repair(project_root: Path, agent_name: str) -> None:
    """Mark that the overseer has repaired this agent (increments repair_count)."""
    db = _load(project_root)
    if agent_name not in db:
        return
    db[agent_name]["repair_count"] = db[agent_name].get("repair_count", 0) + 1
    db[agent_name]["last_repair"] = datetime.now(timezone.utc).isoformat()
    _save(project_root, db)


def get_underperformers(
    project_root: Path,
    threshold: float = UNDERPERFORMER_THRESHOLD,
    min_runs: int = MIN_RUNS_FOR_REVIEW,
) -> list[dict]:
    """
    Return agents eligible for overseer review, sorted by score ascending.

    An agent is eligible when:
    - runs >= min_runs (enough data to judge)
    - score < threshold
    """
    db = _load(project_root)
    result = []
    for name, rec in db.items():
        if rec.get("runs", 0) >= min_runs:
            score = _compute_score(rec)
            if score < threshold:
                result.append(
                    {
                        "name": name,
                        "score": round(score, 4),
                        "runs": rec["runs"],
                        "verdicts": rec["verdicts"],
                        "repair_count": rec.get("repair_count", 0),
                        "last_run": rec.get("last_run", ""),
                    }
                )
    return sorted(result, key=lambda x: x["score"])


def get_summary(project_root: Path) -> list[dict]:
    """
    Return all tracked agents sorted by score ascending.

    Used by overseer and reporting tools.
    """
    db = _load(project_root)
    rows = []
    for name, rec in db.items():
        rows.append(
            {
                "name": name,
                "runs": rec.get("runs", 0),
                "score": round(_compute_score(rec), 4),
                "verdicts": rec.get("verdicts", {}),
                "last_run": rec.get("last_run", ""),
                "repair_count": rec.get("repair_count", 0),
                "last_repair": rec.get("last_repair"),
            }
        )
    rows.sort(key=lambda x: x["score"])
    return rows
