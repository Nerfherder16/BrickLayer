"""masonry/scripts/gen_training_data.py

Generate training data for Masonry agents using mock question banks.

Loads synthetic questions with known expected verdicts from
masonry/training_data/mock_questions/{agent}.json, runs each question
through the agent via `claude -p`, scores the output (including
verdict_match), and appends new records to scored_all.jsonl.

This is the primary way to build training contrast (high >= 75, low < 50)
for agents that have no existing scored data or only mid-range scores.

Usage:
    python masonry/scripts/gen_training_data.py quantitative-analyst
    python masonry/scripts/gen_training_data.py research-analyst --limit 10
    python masonry/scripts/gen_training_data.py --all
    python masonry/scripts/gen_training_data.py competitive-analyst --dry-run

Options:
    --all           Run all agents that have a mock question bank
    --limit N       Max questions to run per agent (default: all)
    --dry-run       Show what would run without calling claude
    --model MODEL   Claude model (default: claude-haiku-4-5-20251001)
    --base-dir DIR  BrickLayer root (default: cwd)
    --force         Re-run questions that already exist in scored_all.jsonl
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

from masonry.src.metrics import build_karen_metric, build_metric  # noqa: E402

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_CLAUDE_CMD = ["claude.cmd" if platform.system() == "Windows" else "claude"]

_RESEARCH_JSON_INSTRUCTION = (
    "You are being evaluated on a research assessment task. "
    "You are given a question_text describing a hypothesis or claim to stress-test. "
    "Based ONLY on your knowledge and the provided context, assess whether the claim holds. "
    "Respond ONLY with a valid JSON object and no other text. "
    "The JSON must have exactly these keys: "
    '"verdict" (one of: "HEALTHY", "WARNING", "FAILURE", "INCONCLUSIVE", "PROMISING"), '
    '"summary" (1-2 sentence summary of your assessment), '
    '"evidence" (detailed evidence string, minimum 300 characters, include specific numbers or thresholds), '
    '"confidence" (decimal string 0.0-1.0 reflecting your certainty).'
)

# Agents that use the karen metric/signature
_KAREN_AGENTS: set[str] = {"karen"}

# Agents that use research metric
_RESEARCH_AGENTS: set[str] = {
    "quantitative-analyst",
    "research-analyst",
    "competitive-analyst",
    "regulatory-researcher",
    "mortar",
    "synthesizer-bl2",
    "frontier-analyst",
    "design-reviewer",
}


def _find_agent_md(base_dir: Path, agent_name: str) -> str:
    """Return agent prompt text from the first found .md file."""
    candidates = [
        base_dir / ".claude" / "agents" / f"{agent_name}.md",
        Path.home() / ".claude" / "agents" / f"{agent_name}.md",
    ]
    for child in base_dir.iterdir():
        if child.is_dir() and not child.name.startswith("."):
            p = child / ".claude" / "agents" / f"{agent_name}.md"
            if p.exists():
                candidates.append(p)
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    return ""


def _run_agent(agent_prompt: str, question_text: str, model: str) -> str:
    """Run agent on a single question, return raw output text."""
    user_msg = f"{_RESEARCH_JSON_INSTRUCTION}\n\nInput:\n{json.dumps({'question_text': question_text})}"

    _WIN_THRESHOLD = 8192
    if platform.system() == "Windows" and len(agent_prompt.encode("utf-8")) > _WIN_THRESHOLD:
        sp_file = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        )
        sp_file.write(agent_prompt)
        sp_file.flush()
        sp_file.close()
        sysprompt_args = ["--system-prompt-file", sp_file.name]
    else:
        sp_file = None
        sysprompt_args = ["--system-prompt", agent_prompt] if agent_prompt else []

    try:
        proc = subprocess.run(
            _CLAUDE_CMD + [
                "--print", "--model", model,
                *sysprompt_args,
                "--output-format", "json",
                "--setting-sources", "",
                "--no-session-persistence",
            ],
            input=user_msg,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
    finally:
        if sp_file is not None:
            Path(sp_file.name).unlink(missing_ok=True)

    raw = proc.stdout
    try:
        envelope = json.loads(raw)
        if isinstance(envelope, dict) and "result" in envelope:
            raw = envelope["result"]
    except (json.JSONDecodeError, ValueError):
        pass

    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[: raw.rfind("```")]
        raw = raw.strip()

    return raw


def _score_output(raw_output: str, expected_verdict: str, metric_fn) -> float:
    """Score agent output against expected verdict using heuristic metric."""
    try:
        predicted = json.loads(raw_output)
    except (json.JSONDecodeError, ValueError):
        # Prose response — check evidence quality only
        text = raw_output.strip()
        has_numbers = bool(re.search(r"\d+\.?\d*", text))
        keywords = ("threshold", "baseline", "%", "ms", "pts", "seconds", "viable", "risk")
        has_keywords = any(kw in text.lower() for kw in keywords)
        return 0.2 if (len(text) > 300 and (has_numbers or has_keywords)) else 0.1

    # Build expected object with the known verdict
    expected = {
        "verdict": expected_verdict,
        "confidence": "0.8",
        "evidence": "x" * 350,  # placeholder — metric only checks format/length
    }

    pred_ns = SimpleNamespace(**predicted)
    exp_ns = SimpleNamespace(**expected)

    try:
        return float(metric_fn(exp_ns, pred_ns))
    except Exception:
        return 0.0


def _load_existing_ids(scored_path: Path, agent_name: str) -> set[str]:
    """Return set of question_ids already in scored_all.jsonl for this agent."""
    if not scored_path.exists():
        return set()
    ids = set()
    for line in scored_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if rec.get("agent") == agent_name:
                ids.add(rec.get("question_id", ""))
        except json.JSONDecodeError:
            continue
    return ids


def run_agent(
    agent_name: str,
    base_dir: Path,
    model: str = _DEFAULT_MODEL,
    limit: int | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    """Generate training data for one agent. Returns summary dict."""
    questions_file = base_dir / "masonry" / "training_data" / "mock_questions" / f"{agent_name}.json"
    scored_path = base_dir / "masonry" / "training_data" / "scored_all.jsonl"

    if not questions_file.exists():
        print(f"[{agent_name}] No mock question bank found at {questions_file}")
        return {"agent": agent_name, "added": 0, "skipped": 0, "error": "no_question_bank"}

    questions = json.loads(questions_file.read_text(encoding="utf-8"))
    if limit:
        questions = questions[:limit]

    existing_ids = set() if force else _load_existing_ids(scored_path, agent_name)
    agent_prompt = _find_agent_md(base_dir, agent_name)

    if not agent_prompt:
        print(f"[{agent_name}] WARNING: No agent .md file found — using empty prompt")

    metric_fn = build_karen_metric() if agent_name in _KAREN_AGENTS else build_metric(object)

    added = 0
    skipped = 0
    scores = []

    print(f"\n[{agent_name}] {len(questions)} questions | model={model}")
    print("=" * 60)

    for q in questions:
        qid = q["question_id"]
        question_text = q["question_text"]
        expected_verdict = q.get("expected_verdict", "INCONCLUSIVE")

        if qid in existing_ids:
            print(f"  SKIP {qid} (already in corpus)")
            skipped += 1
            continue

        if dry_run:
            print(f"  DRY  {qid} | expected={expected_verdict} | {question_text[:60]}...")
            continue

        print(f"  RUN  {qid} | expected={expected_verdict}...", end=" ", flush=True)

        try:
            raw_output = _run_agent(agent_prompt, question_text, model)
        except subprocess.TimeoutExpired:
            print("TIMEOUT")
            continue
        except Exception as e:
            print(f"ERROR: {e}")
            continue

        # Parse predicted verdict for display
        predicted_verdict = "?"
        try:
            parsed = json.loads(raw_output)
            predicted_verdict = parsed.get("verdict", "?")
        except (json.JSONDecodeError, ValueError):
            predicted_verdict = "PROSE"

        score = _score_output(raw_output, expected_verdict, metric_fn)
        score_int = int(score * 100)
        match = "OK" if predicted_verdict == expected_verdict else "XX"
        print(f"score={score_int} | got={predicted_verdict} {match}")
        scores.append(score_int)

        # Parse full output for storage
        try:
            output_obj = json.loads(raw_output)
        except (json.JSONDecodeError, ValueError):
            output_obj = {"raw": raw_output}

        record = {
            "agent": agent_name,
            "question_id": qid,
            "input": {
                "question_text": question_text,
                "question_id": qid,
            },
            "output": output_obj,
            "expected_verdict": expected_verdict,
            "score": score_int,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "mock_campaign",
        }

        with scored_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        added += 1

    if not dry_run and scores:
        avg = sum(scores) / len(scores)
        high = sum(1 for s in scores if s >= 75)
        low = sum(1 for s in scores if s < 50)
        print(f"\n[{agent_name}] Done: {added} added | avg={avg:.0f} | high(≥75)={high} | low(<50)={low}")

    return {
        "agent": agent_name,
        "added": added,
        "skipped": skipped,
        "scores": scores,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate mock training data for Masonry agents."
    )
    parser.add_argument("agent_name", nargs="?", help="Agent to generate data for")
    parser.add_argument("--all", action="store_true", help="Run all agents with question banks")
    parser.add_argument("--limit", type=int, default=None, help="Max questions per agent")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without running")
    parser.add_argument("--force", action="store_true", help="Re-run already-scored questions")
    parser.add_argument("--model", default=_DEFAULT_MODEL)
    parser.add_argument("--base-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()

    base_dir = args.base_dir.resolve()
    mock_dir = base_dir / "masonry" / "training_data" / "mock_questions"

    if args.all:
        agents = [p.stem for p in sorted(mock_dir.glob("*.json"))]
    elif args.agent_name:
        agents = [args.agent_name]
    else:
        parser.error("Provide an agent name or --all")
        return

    import shutil
    if not args.dry_run and not shutil.which("claude"):
        print("ERROR: 'claude' binary not found on PATH. Install Claude Code CLI first.")
        sys.exit(1)

    results = []
    for agent in agents:
        result = run_agent(
            agent_name=agent,
            base_dir=base_dir,
            model=args.model,
            limit=args.limit,
            dry_run=args.dry_run,
            force=args.force,
        )
        results.append(result)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total_added = 0
    for r in results:
        added = r.get("added", 0)
        total_added += added
        scores = r.get("scores", [])
        if scores:
            high = sum(1 for s in scores if s >= 75)
            low = sum(1 for s in scores if s < 50)
            print(f"  {r['agent']:30s}  +{added:3d} records  high={high}  low={low}")
        else:
            print(f"  {r['agent']:30s}  +{added:3d} records")
    print(f"\nTotal added: {total_added} records to scored_all.jsonl")


if __name__ == "__main__":
    main()
