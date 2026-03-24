#!/usr/bin/env python3
"""
Atomic question claim manager for parallel BL campaigns.

Workers call this before starting each question to prevent duplicate work
when multiple Claude processes run against the same questions.md.

Usage:
  python claim.py claim   <project_path> <question_id> <worker_id>  -> CLAIMED | TAKEN
  python claim.py release <project_path> <question_id>               -> OK
  python claim.py complete <project_path> <question_id> <verdict>    -> OK
  python claim.py status  <project_path>                             -> table
  python claim.py pending <project_path>                             -> list of unclaimed IDs
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def _claims_path(project_path: str) -> Path:
    return Path(project_path) / "claims.json"


def _lock_path(project_path: str) -> Path:
    return Path(project_path) / "claims.lock"


def _acquire_lock(project_path: str, retries: int = 30) -> bool:
    lock = _lock_path(project_path)
    for _ in range(retries):
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return True
        except FileExistsError:
            time.sleep(0.1)
    return False


def _release_lock(project_path: str) -> None:
    lock = _lock_path(project_path)
    try:
        lock.unlink()
    except FileNotFoundError:
        pass


def _load(project_path: str) -> dict:
    p = _claims_path(project_path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(project_path: str, claims: dict) -> None:
    p = _claims_path(project_path)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(claims, indent=2), encoding="utf-8")
    tmp.replace(p)


def cmd_claim(project_path: str, question_id: str, worker_id: str) -> str:
    """Try to claim a question. Returns CLAIMED or TAKEN."""
    if not _acquire_lock(project_path):
        return "LOCK_FAILED"
    try:
        claims = _load(project_path)
        if question_id in claims and claims[question_id]["status"] in (
            "IN_PROGRESS",
            "DONE",
        ):
            return "TAKEN"
        claims[question_id] = {
            "worker": worker_id,
            "claimed_at": datetime.now(timezone.utc).isoformat(),
            "status": "IN_PROGRESS",
        }
        _save(project_path, claims)
        return "CLAIMED"
    finally:
        _release_lock(project_path)


def cmd_release(project_path: str, question_id: str) -> str:
    """Release a stuck claim (for crashed workers)."""
    if not _acquire_lock(project_path):
        return "LOCK_FAILED"
    try:
        claims = _load(project_path)
        if question_id in claims:
            del claims[question_id]
            _save(project_path, claims)
        return "OK"
    finally:
        _release_lock(project_path)


def cmd_complete(project_path: str, question_id: str, verdict: str) -> str:
    """Mark a question done with its verdict."""
    if not _acquire_lock(project_path):
        return "LOCK_FAILED"
    try:
        claims = _load(project_path)
        if question_id not in claims:
            claims[question_id] = {"worker": "unknown"}
        claims[question_id].update(
            {
                "status": "DONE",
                "verdict": verdict,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        _save(project_path, claims)
        return "OK"
    finally:
        _release_lock(project_path)


def cmd_status(project_path: str) -> None:
    """Print claims table."""
    claims = _load(project_path)
    if not claims:
        print("No active claims.")
        return
    print(
        f"{'Question':<12} {'Worker':<15} {'Status':<12} {'Verdict':<12} {'Claimed At'}"
    )
    print("-" * 72)
    for qid, info in sorted(claims.items()):
        print(
            f"{qid:<12} {info.get('worker', '?'):<15} {info.get('status', '?'):<12} "
            f"{info.get('verdict', '—'):<12} {info.get('claimed_at', '')[:19]}"
        )


def cmd_pending(project_path: str) -> None:
    """Print unclaimed PENDING question IDs from questions.md."""
    claims = _load(project_path)
    claimed_ids = {
        qid for qid, v in claims.items() if v.get("status") in ("IN_PROGRESS", "DONE")
    }

    questions_path = Path(project_path) / "questions.md"
    if not questions_path.exists():
        print("ERROR: questions.md not found", file=sys.stderr)
        sys.exit(1)

    pending = []
    for line in questions_path.read_text(encoding="utf-8").splitlines():
        # Match table rows: | ID | PENDING | ...
        if "| PENDING |" in line or "| pending |" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                qid = parts[1].strip()
                if qid and qid not in claimed_ids:
                    pending.append(qid)

    for qid in pending:
        print(qid)


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    cmd, project_path = args[0], args[1]
    rest = args[2:]

    dispatch = {
        "claim": lambda: print(cmd_claim(project_path, rest[0], rest[1])),
        "release": lambda: print(cmd_release(project_path, rest[0])),
        "complete": lambda: print(
            cmd_complete(project_path, rest[0], rest[1] if rest[1:] else "DONE")
        ),
        "status": lambda: cmd_status(project_path),
        "pending": lambda: cmd_pending(project_path),
    }

    fn = dispatch.get(cmd)
    if fn is None:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
    fn()


if __name__ == "__main__":
    main()
