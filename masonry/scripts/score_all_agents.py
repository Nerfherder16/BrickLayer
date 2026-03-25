"""Unified agent scorer — aggregates all signal types for DSPy training.

Calls score_findings, score_code_agents, score_ops_agents, score_routing,
merges into scored_all.jsonl, and updates last_score in agent_registry.yml.

Usage:
    python masonry/scripts/score_all_agents.py [--base-dir DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# agent_db.json run history
# ---------------------------------------------------------------------------

_MAX_RUNS = 50


def write_agent_db_record(
    agent_name: str,
    record: dict[str, Any],
    db_path: Path,
) -> None:
    """Append a run entry to agent_db.json for the given agent.

    Loads the existing agent record (if any), appends a new entry to the
    ``runs`` array, trims to the most recent ``_MAX_RUNS`` entries, then
    writes the full record back preserving all existing top-level fields.

    Args:
        agent_name: Key to use in the agent_db.json dict.
        record: The current scoring record with at minimum ``score`` and
            ``overall`` keys.
        db_path: Absolute path to agent_db.json (created if absent).
    """
    # Load existing db
    existing_db: dict[str, Any] = {}
    if db_path.exists():
        try:
            existing_db = json.loads(db_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing_db = {}

    # Start from existing agent record or the new record
    agent_rec: dict[str, Any] = dict(existing_db.get(agent_name, record))
    # Always update top-level fields from the new record
    for key, value in record.items():
        agent_rec[key] = value

    # Build new run entry
    run_entry: dict[str, Any] = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "verdict": record.get("overall", "UNKNOWN"),
        "score": record.get("score"),
        "duration_ms": None,
        "quality_score": None,
    }

    # Append and trim
    runs: list[dict[str, Any]] = list(agent_rec.get("runs", []))
    runs.append(run_entry)
    if len(runs) > _MAX_RUNS:
        runs = runs[-_MAX_RUNS:]
    agent_rec["runs"] = runs

    existing_db[agent_name] = agent_rec

    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text(
        json.dumps(existing_db, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

# ---------------------------------------------------------------------------
# Lazy imports for each scorer — warn and skip if unavailable
# ---------------------------------------------------------------------------


def _import_scorer(module_name: str) -> Any:
    """Import a scorer module by name, returning None on failure."""
    import importlib
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        print(f"WARNING: Could not import {module_name}: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# YAML line-level editor for agent_registry.yml
# ---------------------------------------------------------------------------


def _update_registry_last_scores(
    registry_path: Path,
    agent_scores: dict[str, float],
) -> int:
    """Update last_score fields in agent_registry.yml for each agent.

    Uses simple line-by-line editing to avoid YAML parsing dependencies.
    Returns number of agents updated.
    """
    if not registry_path.exists() or not agent_scores:
        return 0

    try:
        lines = registry_path.read_text(encoding="utf-8").splitlines(keepends=True)
    except OSError:
        return 0

    updated = 0
    current_agent: str | None = None
    name_pattern = re.compile(r"^- name:\s+(.+)$")
    last_score_pattern = re.compile(r"^(\s+)last_score:\s*.*$")
    # Track which agents still need a last_score inserted
    needs_insert: set[str] = set(agent_scores.keys())
    in_agent_block = False
    new_lines: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip("\n")

        # Detect agent block start
        name_match = name_pattern.match(stripped)
        if name_match:
            current_agent = name_match.group(1).strip()
            in_agent_block = True
            new_lines.append(line)
            i += 1
            continue

        # If we're in an agent block, look for last_score line
        if in_agent_block and current_agent and current_agent in agent_scores:
            ls_match = last_score_pattern.match(stripped)
            if ls_match:
                indent = ls_match.group(1)
                score = agent_scores[current_agent]
                new_lines.append(f"{indent}last_score: {score:.1f}\n")
                needs_insert.discard(current_agent)
                updated += 1
                i += 1
                continue

            # If we hit a new top-level list item (next agent), inject last_score before it
            if stripped.startswith("- name:") and current_agent in needs_insert:
                # Find the indentation level from surrounding lines
                new_lines.append(f"  last_score: {agent_scores[current_agent]:.1f}\n")
                needs_insert.discard(current_agent)
                updated += 1
                in_agent_block = False
                current_agent = None
                # Don't increment — re-process this line as a new agent block
                continue

        new_lines.append(line)
        i += 1

    # Handle last agent in file that may still need last_score
    if current_agent and current_agent in needs_insert:
        new_lines.append(f"  last_score: {agent_scores[current_agent]:.1f}\n")
        needs_insert.discard(current_agent)
        updated += 1

    try:
        registry_path.write_text("".join(new_lines), encoding="utf-8")
    except OSError as exc:
        print(f"WARNING: Could not write agent_registry.yml: {exc}", file=sys.stderr)
        return 0

    return updated


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


def _dedup_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate records by (question_id, agent) or (source+session_id+agent).

    Last entry wins on collision (later scorers are authoritative).
    """
    seen: dict[str, dict[str, Any]] = {}
    for rec in records:
        qid = rec.get("question_id", "")
        agent = rec.get("agent", "")
        session = rec.get("session_id", "")
        source = rec.get("source", "")
        branch = rec.get("branch", "")
        # commit_hash used as discriminator for ops records (F15.1)
        commit_hash = rec.get("commit_hash", "")

        if qid:
            key = f"qid:{qid}:{agent}"
        elif session:
            key = f"session:{session}:{agent}"
        else:
            key = f"src:{source}:{commit_hash or branch}:{agent}:{rec.get('score', 0)}"

        seen[key] = rec

    return list(seen.values())


# ---------------------------------------------------------------------------
# JSONL loading
# ---------------------------------------------------------------------------


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load a JSONL file, returning an empty list if absent or malformed."""
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


# ---------------------------------------------------------------------------
# Summary table printing
# ---------------------------------------------------------------------------


def _print_summary_table(
    scorer_summaries: list[dict[str, Any]],
    agent_record_counts: dict[str, int],
) -> None:
    """Print a summary table to stdout."""
    print("\n--- Score All Agents Summary ---")
    print(f"{'Scorer':<30} {'Records':>8} {'Agents':>10} {'Agents w/10+':>14}")
    print("-" * 66)

    for s in scorer_summaries:
        name = s.get("scorer", "unknown")
        records = s.get("records", 0)
        agents = s.get("agents_covered", [])
        agents_10plus = s.get("agents_10plus", 0)
        agents_str = str(len(agents)) if isinstance(agents, list) else str(agents)
        print(f"{name:<30} {records:>8} {agents_str:>10} {agents_10plus:>14}")

    print("-" * 66)
    total = sum(s.get("records", 0) for s in scorer_summaries)
    agents_with_10 = sum(1 for a, c in agent_record_counts.items() if c >= 10)
    print(f"{'TOTAL':<30} {total:>8} {len(agent_record_counts):>10} {agents_with_10:>14}")
    print()


# ---------------------------------------------------------------------------
# Main run function
# ---------------------------------------------------------------------------


def run(
    base_dir: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Aggregate all scorer outputs into scored_all.jsonl and update registry.

    Returns summary dict.
    """
    # Self-research mode: CWD is masonry/ dir
    _self_research_td = base_dir / "training_data"
    _normal_td = base_dir / "masonry" / "training_data"
    td_dir = _self_research_td if _self_research_td.exists() else _normal_td
    td_dir.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = td_dir / "scored_all.jsonl"

    findings_path = td_dir / "scored_findings.jsonl"
    code_path = td_dir / "scored_code_agents.jsonl"
    ops_path = td_dir / "scored_ops_agents.jsonl"
    routing_path = td_dir / "scored_routing.jsonl"
    synthetic_path = td_dir / "scored_synthetic.jsonl"

    scorer_summaries: list[dict[str, Any]] = []

    # 1. Run score_findings
    try:
        sys.path.insert(0, str(base_dir))
        from masonry.scripts import score_findings  # type: ignore[import]
        sf_summary = score_findings.run(base_dir, findings_path)
        scorer_summaries.append({
            "scorer": "score_findings",
            "records": sf_summary.get("training_ready", 0),
            "agents_covered": sf_summary.get("agents_covered", list(sf_summary.get("agents_with_10_plus", {}).keys())),
            "agents_10plus": len(sf_summary.get("agents_with_10_plus", {})),
        })
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: score_findings failed: {exc}", file=sys.stderr)
        scorer_summaries.append({"scorer": "score_findings", "records": 0, "agents_covered": [], "agents_10plus": 0})

    # 2. Run score_code_agents
    try:
        from masonry.scripts import score_code_agents  # type: ignore[import]
        sc_summary = score_code_agents.run(base_dir, code_path)
        scorer_summaries.append({
            "scorer": "score_code_agents",
            "records": sc_summary.get("training_ready", 0),
            "agents_covered": sc_summary.get("agents_covered", []),
            "agents_10plus": 0,  # code agents rarely hit 10+ in a single project
        })
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: score_code_agents failed: {exc}", file=sys.stderr)
        scorer_summaries.append({"scorer": "score_code_agents", "records": 0, "agents_covered": [], "agents_10plus": 0})

    # 3. Run score_ops_agents
    try:
        from masonry.scripts import score_ops_agents  # type: ignore[import]
        so_summary = score_ops_agents.run(base_dir, ops_path)
        scorer_summaries.append({
            "scorer": "score_ops_agents",
            "records": so_summary.get("total_records", 0),
            "agents_covered": so_summary.get("agents_covered", []),
            "agents_10plus": 0,
        })
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: score_ops_agents failed: {exc}", file=sys.stderr)
        scorer_summaries.append({"scorer": "score_ops_agents", "records": 0, "agents_covered": [], "agents_10plus": 0})

    # 4. Run score_routing
    try:
        from masonry.scripts import score_routing  # type: ignore[import]
        sr_summary = score_routing.run(base_dir, routing_path)
        routing_records = _load_jsonl(routing_path)
        routing_agents = sorted({
            rec["dispatched_agent"]
            for rec in routing_records
            if rec.get("dispatched_agent")
        })
        scorer_summaries.append({
            "scorer": "score_routing",
            "records": sr_summary.get("training_ready", 0),
            "agents_covered": routing_agents,
            "agents_10plus": 0,
        })
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: score_routing failed: {exc}", file=sys.stderr)
        scorer_summaries.append({"scorer": "score_routing", "records": 0, "agents_covered": [], "agents_10plus": 0})

    # 5. Load synthetic negatives (stable, not regenerated) and add to summary
    synthetic_records = _load_jsonl(synthetic_path)
    synthetic_agents = sorted({rec.get("agent", "") for rec in synthetic_records if rec.get("agent")})
    scorer_summaries.append({
        "scorer": "scored_synthetic",
        "records": len(synthetic_records),
        "agents_covered": synthetic_agents,
        "agents_10plus": 0,
    })

    # 6. Merge all JSONL files (including stable synthetic negatives)
    all_records: list[dict[str, Any]] = []
    for path in (findings_path, code_path, ops_path, routing_path, synthetic_path):
        all_records.extend(_load_jsonl(path))

    merged = _dedup_records(all_records)

    # 7. Write merged output
    with output_path.open("w", encoding="utf-8") as fh:
        for rec in merged:
            fh.write(json.dumps(rec) + "\n")

    # 8. Compute per-agent averages
    agent_scores: dict[str, list[float]] = defaultdict(list)
    for rec in merged:
        agent = rec.get("agent", "")
        score = rec.get("score")
        if agent and score is not None:
            agent_scores[agent].append(float(score))

    agent_averages: dict[str, float] = {
        agent: sum(scores) / len(scores)
        for agent, scores in agent_scores.items()
        if scores
    }

    agent_record_counts: dict[str, int] = {
        agent: len(scores) for agent, scores in agent_scores.items()
    }

    # 9. Update agent_registry.yml
    registry_path = base_dir / "masonry" / "agent_registry.yml"
    updated_agents = _update_registry_last_scores(registry_path, agent_averages)

    # 10. Append eval run to agent_db.json time-series
    db_path = base_dir / "agent_db.json"
    for agent_name, avg_score in agent_averages.items():
        if avg_score >= 0.7:
            overall = "HEALTHY"
        elif avg_score >= 0.4:
            overall = "WARNING"
        else:
            overall = "FAILURE"
        write_agent_db_record(
            agent_name,
            {"score": round(avg_score, 4), "overall": overall},
            db_path,
        )

    _print_summary_table(scorer_summaries, agent_record_counts)

    return {
        "total_records": len(merged),
        "unique_agents": len(agent_averages),
        "agents_with_10_plus": sum(1 for c in agent_record_counts.values() if c >= 10),
        "registry_agents_updated": updated_agents,
        "output_path": str(output_path),
        "scorer_summaries": scorer_summaries,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate all agent scores for DSPy training."
    )
    parser.add_argument("--base-dir", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for scored_all.jsonl (default: masonry/training_data/scored_all.jsonl)",
    )
    args = parser.parse_args()

    summary = run(base_dir=args.base_dir, output_path=args.output)
    print(f"Total merged records : {summary['total_records']}")
    print(f"Unique agents        : {summary['unique_agents']}")
    print(f"Agents with 10+      : {summary['agents_with_10_plus']}")
    print(f"Registry updated     : {summary['registry_agents_updated']} agents")
    print(f"Written to           : {summary['output_path']}")


if __name__ == "__main__":
    _main()
