"""Score mortar and trowel from masonry/routing_log.jsonl.

Routing log format (written by masonry-subagent-tracker.js):
  {"timestamp": "ISO", "event": "start", "agent": "...", "session_id": "abc", "parent_session": "xyz"}
  {"timestamp": "ISO", "event": "finding", "agent": "...", "session_id": "abc", "verdict": "FAILURE"}

Score logic:
- correct_agent_dispatched (70pts): agent name is in AGENT_CATEGORIES
- downstream_success (30pts): a finding was written (verdict != INCONCLUSIVE)
- Min 65 for training inclusion

Usage:
    python masonry/scripts/score_routing.py [--base-dir DIR] [--output PATH]
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Import rubrics — graceful degradation
# ---------------------------------------------------------------------------

try:
    from masonry.src.scoring.rubrics import AGENT_CATEGORIES, min_training_score
except ImportError:
    # Fallback: inline a minimal known-agents set
    AGENT_CATEGORIES: dict[str, str] = {  # type: ignore[assignment]
        "quantitative-analyst": "findings",
        "regulatory-researcher": "findings",
        "competitive-analyst": "findings",
        "research-analyst": "findings",
        "benchmark-engineer": "findings",
        "synthesizer-bl2": "findings",
        "health-monitor": "findings",
        "diagnose-analyst": "findings",
        "general-purpose": "findings",
        "developer": "code",
        "test-writer": "code",
        "fix-implementer": "code",
        "mortar": "routing",
        "trowel": "routing",
    }

    def min_training_score(agent_name: str) -> int:  # type: ignore[misc]
        return 65


_MIN_ROUTING_SCORE = 65
_MATCH_WINDOW_HOURS = 1

# Verdicts that count as "downstream success" (anything other than INCONCLUSIVE)
_INCONCLUSIVE_VERDICT = "INCONCLUSIVE"

# Normalize shortened legacy agent names to canonical full names
_AGENT_ALIASES: dict[str, str] = {
    "fix": "fix-implementer",
    "research": "research-analyst",
    "diagnose": "diagnose-analyst",
}


# ---------------------------------------------------------------------------
# Routing log loading
# ---------------------------------------------------------------------------


def _load_routing_log(log_path: Path) -> list[dict[str, Any]]:
    """Load routing_log.jsonl and return list of event dicts."""
    if not log_path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _parse_iso(ts: str) -> datetime | None:
    """Parse ISO timestamp, return None on failure."""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _score_session(
    start_event: dict[str, Any],
    finding_event: dict[str, Any] | None,
    normalized_agent: str | None = None,
) -> dict[str, Any]:
    """Score a single routing session."""
    agent = normalized_agent if normalized_agent is not None else _normalize_agent(
        start_event.get("agent", "unknown")
    )

    # correct_agent_dispatched (D24.2 fix — ground-truth-aware scoring):
    # - 70pts if target_agent exists in start_event AND matches dispatched agent (ground truth confirmed)
    # - 35pts partial credit if agent is known but no ground-truth label available
    # - 0pts if agent is unknown / not in registry
    target_agent = ""
    if isinstance(start_event.get("target_agent"), str):
        target_agent = start_event["target_agent"].strip()
    if agent and agent != "unknown" and agent in AGENT_CATEGORIES:
        if target_agent and target_agent == agent:
            correct_pts = 70  # ground-truth confirmed correct dispatch
        else:
            correct_pts = 35  # partial credit — no ground-truth label
    else:
        correct_pts = 0

    # downstream_success: a finding exists with a non-INCONCLUSIVE verdict
    if finding_event is not None:
        verdict = finding_event.get("verdict", "").upper()
        if verdict and verdict != _INCONCLUSIVE_VERDICT:
            downstream_pts = 30
        else:
            downstream_pts = 0
    else:
        downstream_pts = 0

    total = correct_pts + downstream_pts
    return {
        "score": total,
        "score_breakdown": {
            "correct_agent_dispatched": correct_pts,
            "downstream_success": downstream_pts,
        },
        "finding_verdict": finding_event.get("verdict") if finding_event else None,
    }


def _normalize_agent(agent: str) -> str:
    """Resolve legacy shortened agent names to canonical full names."""
    return _AGENT_ALIASES.get(agent, agent)


def _match_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Match start events to finding events by (session_id, agent) within the time window.

    Uses a compound (session_id, normalized_agent_name) key so that multiple agents
    sharing the same parent session do not overwrite each other.

    Returns list of training records for mortar/trowel.
    """
    # Index finding events by (session_id, normalized_agent) compound key.
    # Use defaultdict(list) so multiple findings per agent per session are kept;
    # we take the last one written (same behaviour as before but without cross-agent
    # collision).
    findings_by_key: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for ev in events:
        if ev.get("event") == "finding":
            sid = ev.get("session_id", "")
            agent_raw = ev.get("agent", "")
            agent_norm = _normalize_agent(agent_raw)
            if sid and agent_norm:
                findings_by_key[(sid, agent_norm)].append(ev)

    records: list[dict[str, Any]] = []

    for ev in events:
        if ev.get("event") != "start":
            continue

        session_id = ev.get("session_id", "")
        parent_session = ev.get("parent_session", "")
        agent_raw = ev.get("agent", "unknown")
        agent = _normalize_agent(agent_raw)
        timestamp = ev.get("timestamp", "")

        # The routing agent is the parent (mortar dispatched this start event)
        # We score mortar/trowel based on what they dispatched
        routing_agent = "mortar"  # default attribution
        if parent_session:
            # Check if the parent is a trowel session (heuristic: trowel sessions
            # dispatch campaign agents)
            pass

        # Find matching finding within time window using compound key.
        # Take the last finding written for this (session, agent) pair.
        candidate_findings = findings_by_key.get((session_id, agent), [])
        finding_event: dict[str, Any] | None = candidate_findings[-1] if candidate_findings else None
        if finding_event is not None:
            start_dt = _parse_iso(timestamp)
            finding_dt = _parse_iso(finding_event.get("timestamp", ""))
            if start_dt is not None and finding_dt is not None:
                diff = finding_dt - start_dt
                if diff > timedelta(hours=_MATCH_WINDOW_HOURS) or diff.total_seconds() < 0:
                    finding_event = None

        scored = _score_session(ev, finding_event, normalized_agent=agent)

        if scored["score"] >= min_training_score(routing_agent):
            records.append({
                "agent": routing_agent,
                "source": "routing_log",
                "session_id": session_id[:20] if session_id else "",
                "dispatched_agent": agent,
                "target_agent": ev.get("target_agent", ""),  # ground-truth label if present (D24.2)
                "score": scored["score"],
                "score_breakdown": scored["score_breakdown"],
                "input": {
                    "agent_dispatched": agent,
                    "parent_session": parent_session[:20] if parent_session else "",
                    "request_text": ev.get("request_text", ""),  # captured by tracker (F25.1)
                },
                "output": {
                    "finding_verdict": scored["finding_verdict"],
                },
            })

    return records


# ---------------------------------------------------------------------------
# Main run function
# ---------------------------------------------------------------------------


def run(
    base_dir: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Score routing agents from routing_log.jsonl.

    Returns summary: {events_scanned, sessions_matched, training_ready, output_path}
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log_path = base_dir / "masonry" / "routing_log.jsonl"
    events = _load_routing_log(log_path)

    if not events:
        # Graceful: write empty file and return zero summary
        output_path.write_text("", encoding="utf-8")
        return {
            "events_scanned": 0,
            "sessions_matched": 0,
            "training_ready": 0,
            "output_path": str(output_path),
        }

    records = _match_events(events)

    start_count = sum(1 for ev in events if ev.get("event") == "start")
    finding_count = sum(1 for ev in events if ev.get("event") == "finding")

    with output_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")

    return {
        "events_scanned": len(events),
        "sessions_matched": min(start_count, finding_count),
        "training_ready": len(records),
        "output_path": str(output_path),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _main() -> None:
    parser = argparse.ArgumentParser(description="Score routing agents from routing_log.jsonl.")
    parser.add_argument("--base-dir", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("masonry/training_data/scored_routing.jsonl"),
    )
    args = parser.parse_args()

    summary = run(base_dir=args.base_dir, output_path=args.output)
    print(f"Events scanned: {summary['events_scanned']}")
    print(f"Sessions matched: {summary['sessions_matched']}")
    print(f"Training records written: {summary['training_ready']}")
    print(f"Written to: {summary['output_path']}")


if __name__ == "__main__":
    _main()
