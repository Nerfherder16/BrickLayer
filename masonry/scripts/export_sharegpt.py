"""masonry/scripts/export_sharegpt.py

Convert scored_all.jsonl → ShareGPT conversation format for SFT fine-tuning.

Output: masonry/training_data/sharegpt_train.jsonl
Format per line:
  {"conversations": [
    {"from": "system", "value": "<agent .md instructions>"},
    {"from": "human", "value": "<question or task description>"},
    {"from": "gpt", "value": "<JSON output string>"}
  ]}

Filters:
  - score >= min_score (default 80)
  - Skips records with empty human turn
  - Loads agent .md from ~/.claude/agents/ or project agents/ dir

Usage:
    python masonry/scripts/export_sharegpt.py
    python masonry/scripts/export_sharegpt.py --min-score 90 --output custom.jsonl
    python masonry/scripts/export_sharegpt.py --agents research-analyst,architect
    python masonry/scripts/export_sharegpt.py --stats
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_BL_ROOT = Path(__file__).resolve().parent.parent.parent
_SCORED_PATH = _BL_ROOT / "masonry" / "training_data" / "scored_all.jsonl"
_DEFAULT_OUTPUT = _BL_ROOT / "masonry" / "training_data" / "sharegpt_train.jsonl"

# Agents where input is {question_text, question_id}
_RESEARCH_AGENTS = frozenset({
    "research-analyst", "architect", "competitive-analyst", "devops",
    "overseer", "quantitative-analyst", "refactorer", "regulatory-researcher",
    "security", "uiux-master", "mortar", "fix-implementer", "cascade-analyst",
    "design-reviewer", "synthesizer-bl2", "frontier-analyst",
})

# Agents where input is a task dict (not question_text based)
_TASK_AGENTS = frozenset({
    "karen", "git-nerd", "developer", "test-writer",
})


def _find_agent_md(agent_name: str) -> str:
    """Load agent .md from global or project agents dir."""
    candidates = [
        Path.home() / ".claude" / "agents" / f"{agent_name}.md",
        _BL_ROOT / ".claude" / "agents" / f"{agent_name}.md",
    ]
    # Also check project-level agents dirs
    for child in _BL_ROOT.iterdir():
        if child.is_dir() and not child.name.startswith("."):
            p = child / ".claude" / "agents" / f"{agent_name}.md"
            if p.exists():
                candidates.append(p)
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace")
    return ""


def _format_human_turn(record: dict) -> str:
    """Format the input dict as a human-readable prompt."""
    agent = record.get("agent", "")
    inp = record.get("input", {})

    if agent in _RESEARCH_AGENTS:
        qt = inp.get("question_text", "").strip()
        return qt if qt else ""

    if agent == "karen":
        subject = inp.get("commit_subject", "")
        files = inp.get("files_modified", [])
        if not subject:
            return ""
        files_str = "\n".join(f"  - {f}" for f in files) if files else "  (none)"
        return f"New commit landed:\n  {subject}\n\nFiles modified:\n{files_str}\n\nDecide which docs to update."

    if agent == "git-nerd":
        subject = inp.get("commit_subject", "")
        if not subject:
            return ""
        return f"Commit: {subject}\n\nDecide whether to commit or revert based on the commit message."

    # Generic fallback: serialize input as JSON
    inp_str = json.dumps(inp, ensure_ascii=False)
    return inp_str if inp_str != "{}" else ""


def _format_gpt_turn(record: dict) -> str:
    """Format the output as the assistant response."""
    out = record.get("output", {})
    if not out:
        return ""
    return json.dumps(out, ensure_ascii=False, indent=None)


def convert(
    scored_path: Path = _SCORED_PATH,
    output_path: Path = _DEFAULT_OUTPUT,
    min_score: int = 80,
    agent_filter: set[str] | None = None,
    verbose: bool = False,
) -> int:
    """Convert scored_all.jsonl to ShareGPT format. Returns count written."""

    # Cache agent .md files
    agent_md_cache: dict[str, str] = {}

    def get_system(agent: str) -> str:
        if agent not in agent_md_cache:
            agent_md_cache[agent] = _find_agent_md(agent)
        return agent_md_cache[agent]

    records = []
    with open(scored_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    skipped_score = 0
    skipped_empty = 0
    skipped_agent = 0
    written = 0
    agent_counts: Counter = Counter()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as out_f:
        for rec in records:
            score = rec.get("score", 0)
            agent = rec.get("agent", "unknown")

            if score < min_score:
                skipped_score += 1
                continue

            if agent_filter and agent not in agent_filter:
                skipped_agent += 1
                continue

            human = _format_human_turn(rec)
            if not human:
                skipped_empty += 1
                continue

            gpt = _format_gpt_turn(rec)
            if not gpt or gpt == "{}":
                skipped_empty += 1
                continue

            system = get_system(agent)

            conversation = {
                "conversations": [
                    {"from": "system", "value": system},
                    {"from": "human", "value": human},
                    {"from": "gpt", "value": gpt},
                ]
            }

            out_f.write(json.dumps(conversation, ensure_ascii=False) + "\n")
            written += 1
            agent_counts[agent] += 1

    print(f"[export_sharegpt] Written: {written} conversations → {output_path}")
    print(f"[export_sharegpt] Skipped: score<{min_score}={skipped_score}, empty={skipped_empty}, agent_filter={skipped_agent}")
    print("[export_sharegpt] By agent:")
    for agent, count in agent_counts.most_common():
        md_len = len(get_system(agent))
        md_status = f"{md_len} chars" if md_len else "NO .md FOUND"
        print(f"  {agent:30s}  {count:4d}  system={md_status}")

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Export ShareGPT training data from scored_all.jsonl")
    parser.add_argument("--min-score", type=int, default=80, help="Minimum score threshold (default: 80)")
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT, help="Output JSONL path")
    parser.add_argument("--agents", default=None, help="Comma-separated agent filter (default: all)")
    parser.add_argument("--stats", action="store_true", help="Print stats only, don't write")
    args = parser.parse_args()

    agent_filter = set(args.agents.split(",")) if args.agents else None

    if args.stats:
        # Stats mode — just read and report
        from collections import Counter
        agents: Counter = Counter()
        empty = 0
        with open(_SCORED_PATH, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    score = rec.get("score", 0)
                    if score >= args.min_score:
                        human = _format_human_turn(rec)
                        if human:
                            agents[rec.get("agent", "unknown")] += 1
                        else:
                            empty += 1
                except json.JSONDecodeError:
                    continue
        print(f"Convertible records (score>={args.min_score}, non-empty): {sum(agents.values())}")
        print(f"Empty/unconvertible: {empty}")
        for a, c in agents.most_common():
            print(f"  {a}: {c}")
        return

    count = convert(
        scored_path=_SCORED_PATH,
        output_path=args.output,
        min_score=args.min_score,
        agent_filter=agent_filter,
    )
    if count == 0:
        print("[export_sharegpt] No records exported. Run gen_training_data.py --all first.")
        sys.exit(1)


if __name__ == "__main__":
    main()
