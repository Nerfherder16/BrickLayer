"""
bl/training_export.py — BrickLayer → Training System bridge.

Reads BrickLayer campaign artifacts and converts them into Trace records
that the training system (TraceStore) can consume for SFT / DPO / GRPO.

Data sources consumed:
  {project}/traces.jsonl       — per-question execution records (tracer.py)
  masonry/training_data/scored_all.jsonl — agent quality scores
  {project}/findings/{qid}.md  — verdict, confidence, needs_human

Output options (no hard dependency on training package required):
  1. JSONL file  — default, importable by TraceStore later
  2. SQLite directly — if BRICKLAYER_TRAINING_DB env var is set and the
                       training package is importable

Usage:
  # Export all campaigns → JSONL
  python bl/training_export.py --bl-root /path/to/BrickLayer

  # Export + write directly to training SQLite
  BRICKLAYER_TRAINING_DB=~/.bricklayer/training.db \\
      python bl/training_export.py --bl-root /path/to/BrickLayer

  # Export single project
  python bl/training_export.py --bl-root . --project projects/bl2

  # Called from score_all_agents.py (see patch instructions at bottom)
  from bl.training_export import BLTrainingExporter
  BLTrainingExporter(bl_root=BL_ROOT).export_all()
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from training_schema import (
    compute_trajectory_score,
    confidence_str_to_float,
    is_sft_eligible,
    verdict_to_binary_pass,
    verdict_to_critic_flag,
    verdict_to_partial_credit,
    NEEDS_HUMAN_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCORED_ALL_PATH = Path("masonry/training_data/scored_all.jsonl")
DEFAULT_OUTPUT_PATH = Path("training/export.jsonl")


# ---------------------------------------------------------------------------
# Minimal Trace schema — mirrors bricklayer/trace/models.py
# Written inline so this file has zero dependency on the training package.
# If the training package is installed, we use TraceStore directly.
# ---------------------------------------------------------------------------

def _make_trace(
    question_id: str,
    task_domain: str,
    task_description: str,
    agent_name: str,
    tracer_record: dict[str, Any],
    scored_entry: dict[str, Any] | None,
    verdict: str,
    confidence_raw: str | float | None,
    needs_human: bool,
    wave: int,
    mode: str,
) -> dict[str, Any]:
    """Build a Trace dict from BrickLayer source records."""

    eval_score = (scored_entry or {}).get("score")
    trajectory_score = compute_trajectory_score(eval_score, verdict, confidence_raw)
    confidence_float = confidence_str_to_float(confidence_raw)
    sft_eligible = is_sft_eligible(verdict, trajectory_score, needs_human)
    critic_flag = verdict_to_critic_flag(verdict)

    # GRPO group key — same agent + domain + wave are comparable runs
    grpo_key = f"{agent_name}:{task_domain}:{wave}"
    grpo_group_id = hashlib.md5(grpo_key.encode()).hexdigest()[:12]

    # Build the single TraceStep
    mode_part = tracer_record.get("tool_call", f"{mode}:{question_id}")
    step = {
        "step_index": 0,
        "action_type": "tool_call",
        "thought": tracer_record.get("thought", task_description),
        "action": {
            "type": "tool_call",
            "tool": mode_part.split(":")[0] if ":" in mode_part else mode,
            "args": {
                "question_id": question_id,
                "domain": task_domain,
            },
        },
        "observation": tracer_record.get("result_summary", ""),
        "tool_event": {
            "tool_name": mode_part,
            "args": {"question_id": question_id},
            "success": tracer_record.get("error_type") is None,
            "result": tracer_record.get("result_summary"),
            "error": tracer_record.get("error_type"),
            "latency_ms": tracer_record.get("latency_ms", 0.0),
            "timestamp": tracer_record.get("timestamp", datetime.now(timezone.utc).isoformat()),
        },
        # Critic scores from scored_all — step-level signal
        "critic_score": trajectory_score,
        "critic_flag": critic_flag,
        "critic_reason": f"verdict={verdict} confidence={confidence_float:.2f}",
        "elapsed_ms": tracer_record.get("latency_ms", 0.0),
        "timestamp": tracer_record.get("timestamp", datetime.now(timezone.utc).isoformat()),
    }

    # OutcomeSignal
    outcome = {
        "binary_pass": verdict_to_binary_pass(verdict),
        "partial_credit": verdict_to_partial_credit(verdict),
        "verifier_details": {
            "verdict": verdict,
            "confidence": confidence_float,
            "needs_human": needs_human,
            "eval_score_raw": eval_score,
        },
        "error": tracer_record.get("error_type"),
    }

    return {
        # Use question_id as deterministic ID — export is idempotent
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"bl:{question_id}")),
        "task_id": question_id,
        "task_domain": task_domain,
        "task_description": task_description,
        "agent_model": agent_name,
        "agent_temperature": 0.0,  # not tracked in BL
        "steps": [step],
        "final_answer": tracer_record.get("result_summary", ""),
        "outcome": outcome,
        "trajectory_score": trajectory_score,
        "sft_eligible": sft_eligible,
        "grpo_group_id": grpo_group_id,
        "grpo_reward": None,  # computed later by CriticPipeline.apply_grpo_rewards()
        "metadata": {
            "verdict": verdict,
            "severity": (scored_entry or {}).get("output", {}).get("severity", ""),
            "confidence": confidence_float,
            "needs_human": needs_human,
            "wave": wave,
            "mode": mode,
            "source": "bricklayer_campaign",
            "bl_agent": agent_name,
        },
        "created_at": tracer_record.get("timestamp", datetime.now(timezone.utc).isoformat()),
    }


# ---------------------------------------------------------------------------
# Finding parser — reads frontmatter from findings/{qid}.md
# ---------------------------------------------------------------------------

def _parse_finding(finding_path: Path) -> dict[str, Any]:
    """
    Parse key fields from a BrickLayer finding markdown file.

    Returns dict with: verdict, severity, confidence, needs_human,
    failure_type, mode, summary
    """
    result: dict[str, Any] = {
        "verdict": "INCONCLUSIVE",
        "severity": "Info",
        "confidence": 0.5,
        "needs_human": True,
        "failure_type": None,
        "mode": "simulate",
        "summary": "",
    }

    if not finding_path.exists():
        return result

    text = finding_path.read_text(encoding="utf-8", errors="replace")

    # Extract frontmatter fields using simple regex — no YAML parser needed
    patterns = {
        "verdict":      r"^\*\*Verdict\*\*:\s*(.+)$",
        "severity":     r"^\*\*Severity\*\*:\s*(.+)$",
        "confidence":   r"^\*\*Confidence\*\*:\s*(.+)$",
        "needs_human":  r"^\*\*Needs Human\*\*:\s*(.+)$",
        "failure_type": r"^\*\*Failure Type\*\*:\s*(.+)$",
        "mode":         r"^\*\*Mode\*\*:\s*(.+)$",
    }

    for key, pat in patterns.items():
        m = re.search(pat, text, re.MULTILINE)
        if m:
            result[key] = m.group(1).strip()

    # Normalise types
    verdict_raw = str(result["verdict"]).upper().strip()
    result["verdict"] = verdict_raw

    try:
        result["confidence"] = float(result["confidence"])
    except (ValueError, TypeError):
        result["confidence"] = confidence_str_to_float(result["confidence"])

    needs_human_raw = str(result["needs_human"]).lower().strip()
    result["needs_human"] = needs_human_raw in ("true", "1", "yes")

    # Extract Summary section (first line after "## Summary")
    summary_match = re.search(r"## Summary\s*\n(.+?)(?:\n##|\Z)", text, re.DOTALL)
    if summary_match:
        result["summary"] = summary_match.group(1).strip()[:200]

    return result


# ---------------------------------------------------------------------------
# scored_all.jsonl loader
# ---------------------------------------------------------------------------

def _load_scored_index(bl_root: Path) -> dict[str, dict[str, Any]]:
    """
    Load scored_all.jsonl and index by question_id.

    Only indexes live records (those with question_id).
    git_log records (no question_id) are skipped — they have no trace linkage.
    """
    path = bl_root / SCORED_ALL_PATH
    index: dict[str, dict[str, Any]] = {}

    if not path.exists():
        return index

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            qid = record.get("question_id")
            if not qid:
                continue  # git_log record — no question_id linkage

            # Keep the highest-scored record if question appears multiple times
            existing = index.get(qid)
            if existing is None or record.get("score", 0) > existing.get("score", 0):
                index[qid] = record

    return index


# ---------------------------------------------------------------------------
# Project discovery
# ---------------------------------------------------------------------------

def _find_campaign_dirs(bl_root: Path) -> list[Path]:
    """
    Find all directories that contain a traces.jsonl file.
    Searches bl_root directly and one level into projects/.
    """
    candidates: list[Path] = []

    # Root-level campaigns (recall/, masonry/, bricklayer-meta/, etc.)
    for traces_file in bl_root.glob("*/traces.jsonl"):
        candidates.append(traces_file.parent)

    # projects/ subdirectories
    projects_dir = bl_root / "projects"
    if projects_dir.exists():
        for traces_file in projects_dir.glob("*/traces.jsonl"):
            candidates.append(traces_file.parent)

    return candidates


# ---------------------------------------------------------------------------
# Core export logic
# ---------------------------------------------------------------------------

class BLTrainingExporter:
    """
    Converts BrickLayer campaign artifacts into training Trace records.

    Usage:
        exporter = BLTrainingExporter(bl_root="/path/to/BrickLayer")
        count = exporter.export_all()

    Output goes to:
        {bl_root}/training/export.jsonl      (always written)
        $BRICKLAYER_TRAINING_DB SQLite file  (if env var set + training pkg installed)
    """

    def __init__(
        self,
        bl_root: str | Path = ".",
        output_path: str | Path | None = None,
        db_path: str | Path | None = None,
        min_score: float = 0.0,  # export everything, let training system filter
    ) -> None:
        self.bl_root = Path(bl_root).resolve()
        self.output_path = Path(output_path) if output_path else self.bl_root / DEFAULT_OUTPUT_PATH
        self.db_path = Path(db_path) if db_path else _db_from_env()
        self.min_score = min_score
        self._scored_index: dict[str, dict] | None = None

    @property
    def scored_index(self) -> dict[str, dict]:
        if self._scored_index is None:
            self._scored_index = _load_scored_index(self.bl_root)
        return self._scored_index

    def export_project(self, project_dir: Path) -> list[dict]:
        """Export all traces from one campaign directory. Returns list of Trace dicts."""
        traces_path = project_dir / "traces.jsonl"
        if not traces_path.exists():
            return []

        findings_dir = project_dir / "findings"
        traces: list[dict] = []

        with open(traces_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue

                qid = rec.get("question_id")
                if not qid:
                    continue

                # Look up scored entry
                scored = self.scored_index.get(qid)

                # Parse finding for authoritative verdict + confidence
                finding = _parse_finding(findings_dir / f"{qid}.md")

                # Resolve verdict: prefer finding (authoritative) over tracer
                verdict = finding.get("verdict") or rec.get("verdict", "INCONCLUSIVE")
                confidence_raw = finding.get("confidence") or rec.get("confidence")
                needs_human = finding.get("needs_human", True)
                mode = finding.get("mode") or rec.get("tool_call", "").split(":")[0] or "simulate"
                domain = rec.get("domain", "unknown")

                # Wave: from scored entry or default 1
                wave = (scored or {}).get("wave", 1)
                if wave is None:
                    wave = 1

                # Agent name: scored_all is the authoritative source
                agent_name = (scored or {}).get("agent", "unknown")
                if agent_name == "unknown":
                    # Fall back to tracer tool_call pattern "mode:qid"
                    tool_call = rec.get("tool_call", "")
                    if ":" in tool_call:
                        agent_name = tool_call.split(":")[0]

                # Task description: finding summary or tracer thought
                task_description = finding.get("summary") or rec.get("thought", qid)

                trace = _make_trace(
                    question_id=qid,
                    task_domain=domain,
                    task_description=task_description,
                    agent_name=agent_name,
                    tracer_record=rec,
                    scored_entry=scored,
                    verdict=verdict,
                    confidence_raw=confidence_raw,
                    needs_human=needs_human,
                    wave=wave,
                    mode=mode,
                )

                if trace["trajectory_score"] is not None and trace["trajectory_score"] >= self.min_score:
                    traces.append(trace)

        return traces

    def export_all(self, project_dir: Path | None = None) -> int:
        """
        Export all campaigns (or one specific project).
        Returns total trace count written.
        """
        if project_dir:
            dirs = [Path(project_dir)]
        else:
            dirs = _find_campaign_dirs(self.bl_root)

        if not dirs:
            print("[training_export] No campaign directories found (no traces.jsonl files)")
            return 0

        all_traces: list[dict] = []
        for d in dirs:
            project_traces = self.export_project(d)
            all_traces.extend(project_traces)
            if project_traces:
                print(f"[training_export] {d.name}: {len(project_traces)} traces")

        if not all_traces:
            print("[training_export] No traces exported")
            return 0

        # Deduplicate by trace id (question_id is deterministic)
        seen: set[str] = set()
        unique_traces = []
        for t in all_traces:
            if t["id"] not in seen:
                seen.add(t["id"])
                unique_traces.append(t)

        # Write JSONL output
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            for trace in unique_traces:
                f.write(json.dumps(trace) + "\n")

        print(f"[training_export] {len(unique_traces)} traces → {self.output_path}")

        # Optionally write directly to training SQLite
        if self.db_path:
            count = _write_to_sqlite(unique_traces, self.db_path)
            print(f"[training_export] {count} traces → SQLite {self.db_path}")

        # Print summary stats
        _print_stats(unique_traces)

        return len(unique_traces)


# ---------------------------------------------------------------------------
# SQLite writer — mirrors TraceStore schema, no training package import needed
# ---------------------------------------------------------------------------

def _write_to_sqlite(traces: list[dict], db_path: Path | str) -> int:
    """
    Write traces directly to the training system SQLite schema.
    Mirrors TraceStore._init_db() schema — no import of the training package needed.
    Uses INSERT OR REPLACE so export is idempotent.
    """
    import sqlite3

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id               TEXT PRIMARY KEY,
                task_id          TEXT NOT NULL,
                task_domain      TEXT NOT NULL,
                agent_model      TEXT NOT NULL,
                trajectory_score REAL,
                sft_eligible     INTEGER DEFAULT 0,
                grpo_group_id    TEXT,
                grpo_reward      REAL,
                outcome_pass     INTEGER,
                outcome_partial  REAL,
                created_at       TEXT NOT NULL,
                data             TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_id   ON traces(task_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_domain    ON traces(task_domain)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sft       ON traces(sft_eligible)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_grpo      ON traces(grpo_group_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_score     ON traces(trajectory_score)")
        conn.commit()

        count = 0
        for trace in traces:
            outcome = trace.get("outcome") or {}
            conn.execute(
                "INSERT OR REPLACE INTO traces VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    trace["id"],
                    trace["task_id"],
                    trace["task_domain"],
                    trace["agent_model"],
                    trace.get("trajectory_score"),
                    int(trace.get("sft_eligible", False)),
                    trace.get("grpo_group_id"),
                    trace.get("grpo_reward"),
                    int(outcome.get("binary_pass", False)),
                    outcome.get("partial_credit", 0.0),
                    str(trace.get("created_at", "")),
                    json.dumps(trace),
                ),
            )
            count += 1
        conn.commit()

    return count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _db_from_env() -> Path | None:
    val = os.environ.get("BRICKLAYER_TRAINING_DB")
    return Path(val) if val else None


def _print_stats(traces: list[dict]) -> None:
    total = len(traces)
    sft = sum(1 for t in traces if t.get("sft_eligible"))
    passed = sum(1 for t in traces if (t.get("outcome") or {}).get("binary_pass"))
    scores = [t["trajectory_score"] for t in traces if t.get("trajectory_score") is not None]
    avg = sum(scores) / len(scores) if scores else 0.0

    domains: dict[str, int] = {}
    for t in traces:
        d = t.get("task_domain", "unknown")
        domains[d] = domains.get(d, 0) + 1

    print(f"[training_export] stats:")
    print(f"  total:         {total}")
    print(f"  sft_eligible:  {sft}  ({sft/total:.0%})")
    print(f"  outcome_pass:  {passed}  ({passed/total:.0%})")
    print(f"  avg_score:     {avg:.3f}")
    print(f"  by_domain:     {dict(sorted(domains.items(), key=lambda x: -x[1]))}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Export BrickLayer campaign traces to the training system."
    )
    parser.add_argument(
        "--bl-root", default=".", help="Path to BrickLayer root directory (default: .)"
    )
    parser.add_argument(
        "--output", default=None, help="Output JSONL path (default: {bl-root}/training/export.jsonl)"
    )
    parser.add_argument(
        "--db", default=None,
        help="Training SQLite path (default: $BRICKLAYER_TRAINING_DB or skip)"
    )
    parser.add_argument(
        "--project", default=None,
        help="Export single project dir only (e.g. projects/bl2)"
    )
    parser.add_argument(
        "--min-score", type=float, default=0.0,
        help="Only export traces with trajectory_score >= this value (default: 0, export all)"
    )
    args = parser.parse_args()

    exporter = BLTrainingExporter(
        bl_root=args.bl_root,
        output_path=args.output,
        db_path=args.db,
        min_score=args.min_score,
    )

    project_dir = Path(args.bl_root) / args.project if args.project else None
    count = exporter.export_all(project_dir=project_dir)
    print(f"\n[training_export] done. {count} traces exported.")
