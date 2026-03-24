"""masonry/scripts/eval_agent.py

Held-out eval engine that runs agent prompts through ``claude -p`` and scores
the results against expected outputs from scored_all.jsonl.

Usage:
    python masonry/scripts/eval_agent.py karen --signature karen --eval-size 20
    python masonry/scripts/eval_agent.py research-analyst --eval-size 10

Output:
    score=0.87 (17/20 passed), per-example breakdown
    Writes: masonry/agent_snapshots/{agent}/eval_latest.json
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

# On Windows, npm CLIs are installed as .cmd files and require shell=True
# (or explicit .cmd extension) to be found by subprocess.
_CLAUDE_CMD = ["claude.cmd" if platform.system() == "Windows" else "claude"]

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent.parent  # blRoot
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

from masonry.src.metrics import build_karen_metric, build_metric  # noqa: E402

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"

_KAREN_JSON_INSTRUCTION = (
    "\n\nYou are being evaluated on a classification task. "
    "You are given a commit_subject and files_modified from a real git commit. "
    "Based ONLY on these fields, decide what documentation action is needed. "
    "Do NOT say 'no changes detected' - the commit happened and the files listed were changed. "
    "Apply your decision rules: feat/fix/refactor/docs/perf/test commits -> action='updated'; "
    "revert commits -> action='reverted'; chore-bot commits -> action='skipped'. "
    "Write a realistic changelog_entry for what this commit did, based on the commit subject. "
    "Respond ONLY with a valid JSON object and no other text. "
    "The JSON must have exactly these keys: "
    '"action" (one of: "updated", "created", "reverted", "skipped"), '
    '"doc_updates" (comma-separated doc file paths or empty string), '
    '"changelog_entry" (single-line summary string), '
    '"quality_score" (decimal string 0.0-1.0).'
)

_RESEARCH_JSON_INSTRUCTION = (
    "\n\nYou are being evaluated on a research assessment task. "
    "You are given a question_text describing a hypothesis or claim to stress-test. "
    "Based ONLY on your knowledge and the provided context, assess whether the claim holds. "
    "Respond ONLY with a valid JSON object and no other text. "
    "The JSON must have exactly these keys: "
    '"verdict" (one of: "HEALTHY", "WARNING", "FAILURE", "INCONCLUSIVE"), '
    '"summary" (1-2 sentence summary of your assessment), '
    '"evidence" (detailed evidence string, minimum 300 characters, include specific numbers or thresholds), '
    '"confidence" (decimal string 0.0-1.0 reflecting your certainty).'
)


# ── Data loading ──────────────────────────────────────────────────────────────


def _load_records(data_file: Path, agent_name: str) -> list[dict]:
    """Load and filter records from scored_all.jsonl for the given agent."""
    if not data_file.exists():
        return []
    records: list[dict] = []
    for line in data_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("agent") == agent_name:
            records.append(rec)
    return records


# ── Agent prompt discovery ────────────────────────────────────────────────────


def _find_agent_md_files(base_dir: Path, agent_name: str) -> list[Path]:
    """Locate agent .md files — same logic as optimize_claude.py."""
    candidates = [
        base_dir / ".claude" / "agents" / f"{agent_name}.md",
        Path.home() / ".claude" / "agents" / f"{agent_name}.md",
    ]
    for child in base_dir.iterdir():
        if child.is_dir() and not child.name.startswith("."):
            p = child / ".claude" / "agents" / f"{agent_name}.md"
            if p.exists():
                candidates.append(p)

    seen: set[Path] = set()
    unique: list[Path] = []
    for c in candidates:
        resolved = c.resolve() if c.exists() else c
        if resolved not in seen:
            seen.add(resolved)
            unique.append(c)
    return [p for p in unique if p.exists()]


def _load_agent_prompt(base_dir: Path, agent_name: str) -> str:
    """Return the contents of the first found agent .md file, or empty string."""
    found = _find_agent_md_files(base_dir, agent_name)
    if found:
        return found[0].read_text(encoding="utf-8")
    return ""


# ── Scoring ───────────────────────────────────────────────────────────────────


def _score_example(
    record: dict,
    predicted_raw: str,
    metric_fn: Any,
) -> tuple[float, dict]:
    """Score one example. Returns (score, predicted_dict)."""
    try:
        predicted = json.loads(predicted_raw)
    except (json.JSONDecodeError, ValueError):
        return 0.0, {}

    expected = record.get("expected", record.get("output", {}))

    # Metric functions expect objects with attributes
    pred_ns = SimpleNamespace(**predicted) if isinstance(predicted, dict) else predicted
    example_ns = SimpleNamespace(**expected) if isinstance(expected, dict) else expected

    try:
        raw_score = metric_fn(example_ns, pred_ns)
    except Exception:
        raw_score = 0.0

    return float(raw_score), predicted


# ── Core eval function ────────────────────────────────────────────────────────


def run_eval(
    agent: str,
    data_file: Path,
    snapshot_dir: Path,
    signature: str = "research",
    eval_size: int = 20,
    model: str = _DEFAULT_MODEL,
    base_dir: Path | None = None,
) -> dict:
    """Run held-out eval for the given agent.

    Parameters
    ----------
    agent:
        Agent name (e.g. "karen", "research-analyst").
    data_file:
        Path to scored_all.jsonl.
    snapshot_dir:
        Directory where ``{agent}/eval_latest.json`` will be written.
    signature:
        Metric signature to use — "karen" or "research".
    eval_size:
        Number of held-out examples (last N records).
    model:
        Claude model to use for inference.
    base_dir:
        BrickLayer root (used to locate agent .md files). Defaults to
        the repository root derived from this script's location.
    """
    if base_dir is None:
        base_dir = _SCRIPT_ROOT

    # Load records
    records = _load_records(data_file, agent)
    held_out = records[-eval_size:] if len(records) >= eval_size else records

    # Load agent prompt
    agent_prompt = _load_agent_prompt(base_dir, agent)

    # Build metric — build_metric requires a signature class; passing object as
    # a sentinel when we only need the returned callable (not DSPy bootstrapping).
    if signature == "karen":
        metric_fn = build_karen_metric()
    else:
        metric_fn = build_metric(object)  # type: ignore[arg-type]  # sentinel for non-DSPy eval

    # Evaluate each held-out example
    examples_out: list[dict] = []
    passed = 0
    failed = 0

    for i, record in enumerate(held_out, 1):
        inp = record.get("input", {})
        commit_subject = inp.get("commit_subject", "") if isinstance(inp, dict) else ""

        json_instruction = _KAREN_JSON_INSTRUCTION if signature == "karen" else _RESEARCH_JSON_INSTRUCTION
        # Use --system-prompt for agent instructions so Claude treats them as the
        # system context, not as user input. The -p user message contains only the
        # JSON output instruction + input payload.
        user_msg = f"{json_instruction.strip()}\n\nInput:\n{json.dumps(inp)}"
        # Pass user_msg via stdin (--print mode) instead of -p argument to avoid
        # Windows cp1252 argument encoding issues with special chars in JSON strings.
        # For long system prompts (>8KB), use --system-prompt-file to avoid Windows
        # "command line too long" errors (32KB cmd.exe limit).
        _WIN_SYSPROMPT_THRESHOLD = 8192
        if platform.system() == "Windows" and len(agent_prompt.encode("utf-8")) > _WIN_SYSPROMPT_THRESHOLD:
            sp_file = tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".txt", delete=False
            )
            sp_file.write(agent_prompt)
            sp_file.flush()
            sp_file.close()
            sysprompt_args = ["--system-prompt-file", sp_file.name]
        else:
            sp_file = None
            sysprompt_args = ["--system-prompt", agent_prompt]

        try:
            proc = subprocess.run(
                _CLAUDE_CMD + [
                    "--print", "--model", model,
                    *sysprompt_args,
                    "--output-format", "json",
                    # skip all settings (disables hooks) and don't resume previous sessions
                    "--setting-sources", "",
                    "--no-session-persistence",
                ],
                input=user_msg,
                capture_output=True,
                text=True,
            )
        finally:
            if sp_file is not None:
                Path(sp_file.name).unlink(missing_ok=True)

        # --output-format json wraps the response: {"type":"result","result":"...","is_error":...}
        # Extract result text, then strip any markdown code fences Claude adds.
        raw_output = proc.stdout
        try:
            envelope = json.loads(raw_output)
            if isinstance(envelope, dict) and "result" in envelope:
                raw_output = envelope["result"]
        except (json.JSONDecodeError, ValueError):
            pass  # not a JSON envelope — use stdout as-is

        # Strip markdown code fences (```json ... ``` or ``` ... ```)
        raw_output = raw_output.strip()
        if raw_output.startswith("```"):
            raw_output = raw_output.split("\n", 1)[-1]  # drop opening fence line
            if raw_output.endswith("```"):
                raw_output = raw_output[: raw_output.rfind("```")]
            raw_output = raw_output.strip()

        score, predicted = _score_example(record, raw_output, metric_fn)
        passes = score >= 0.5

        if passes:
            passed += 1
        else:
            failed += 1

        subject_preview = str(commit_subject)[:50]
        print(f"[{i}/{len(held_out)}] score={score:.2f}  commit: {subject_preview}")

        examples_out.append({
            "input": inp,
            "expected": record.get("expected", record.get("output", {})),
            "predicted": predicted,
            "score": score,
        })

    total = len(held_out)
    overall_score = passed / total if total > 0 else 0.0

    print(f"score={overall_score:.2f} ({passed}/{total} passed)")

    # Write eval_latest.json
    out_dir = snapshot_dir / agent
    out_dir.mkdir(parents=True, exist_ok=True)
    evaluated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    result: dict = {
        "agent": agent,
        "score": overall_score,
        "eval_size": total,
        "passed": passed,
        "failed": failed,
        "evaluated_at": evaluated_at,
        "model": model,
        "examples": examples_out,
    }

    out_path = out_dir / "eval_latest.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    return result


# ── CLI ───────────────────────────────────────────────────────────────────────


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Run held-out eval for a Masonry agent using claude -p."
    )
    parser.add_argument("agent_name", help="Name of the agent to evaluate")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.cwd(),
        help="BrickLayer root directory (default: cwd)",
    )
    parser.add_argument(
        "--signature",
        default="research",
        choices=["research", "karen"],
        help='Metric signature: "research" (default) or "karen"',
    )
    parser.add_argument(
        "--eval-size",
        type=int,
        default=20,
        help="Number of held-out examples to evaluate (default: 20)",
    )
    parser.add_argument(
        "--model",
        default=_DEFAULT_MODEL,
        help=f"Claude model to use (default: {_DEFAULT_MODEL})",
    )
    args = parser.parse_args()

    base_dir = args.base_dir.resolve()
    td_self = base_dir / "training_data"
    td_normal = base_dir / "masonry" / "training_data"
    td_dir = td_self if td_self.exists() else td_normal
    data_file = td_dir / "scored_all.jsonl"

    snapshot_dir = base_dir / "masonry" / "agent_snapshots"

    run_eval(
        agent=args.agent_name,
        data_file=data_file,
        snapshot_dir=snapshot_dir,
        signature=args.signature,
        eval_size=args.eval_size,
        model=args.model,
        base_dir=base_dir,
    )


if __name__ == "__main__":
    _main()
