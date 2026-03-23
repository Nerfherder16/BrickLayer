"""masonry/scripts/optimize_claude.py

Claude-native few-shot demo selector for Masonry agents.

No DSPy, no API key needed — uses existing scored training data from
scored_all.jsonl (already collected during campaigns). Selects diverse,
high-scoring examples and injects them as a ``## Few-Shot Examples``
section into agent .md files.

Equivalent to dspy.BootstrapFewShot but runs entirely inside a Claude Code
chat session using your existing subscription.

Usage:
    python masonry/scripts/optimize_claude.py karen --signature karen
    python masonry/scripts/optimize_claude.py karen --signature karen --num-demos 4
    python masonry/scripts/optimize_claude.py research-analyst
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent.parent  # blRoot
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

_SECTION_HEADER = "## Few-Shot Examples"
_SECTION_END = "<!-- /Few-Shot Examples -->"

_DEFAULT_NUM_DEMOS = 4


# ── Data loading ─────────────────────────────────────────────────────────────


def _load_raw(scored_all_path: Path, agent_name: str) -> list[dict]:
    if not scored_all_path.exists():
        return []
    records = []
    for line in scored_all_path.read_text(encoding="utf-8").splitlines():
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


# ── Diversity selection ───────────────────────────────────────────────────────


def _commit_prefix(subject: str) -> str:
    """Extract conventional commit prefix (feat/fix/chore/docs/etc.)."""
    m = re.match(r"^([a-zA-Z]+)[\(:]", subject.strip())
    return m.group(1).lower() if m else "other"


def _select_diverse_karen(
    records: list[dict],
    num_demos: int,
) -> list[dict]:
    """Select diverse karen examples across commit types and outcomes.

    Strategy:
    - Always include at least 1 negative example (score=0, reverted) if available.
    - Pick top example per commit prefix from high-scorers.
    - Fill remaining slots with highest-score examples not already selected.
    """
    positives = [r for r in records if r.get("score", 0) > 0]
    negatives = [r for r in records if r.get("score", 0) == 0]

    selected: list[dict] = []

    # 1 negative slot (revert case)
    if negatives:
        selected.append(negatives[0])

    # Group positives by commit prefix, pick highest score per group
    by_prefix: dict[str, list[dict]] = {}
    for r in positives:
        subj = (r.get("input") or {}).get("commit_subject", "")
        prefix = _commit_prefix(subj)
        by_prefix.setdefault(prefix, []).append(r)

    # Sort each group by score desc, take top 1 per non-chore prefix first
    priority_prefixes = [p for p in by_prefix if p != "chore"]
    for prefix in priority_prefixes:
        group = sorted(by_prefix[prefix], key=lambda r: r.get("score", 0), reverse=True)
        candidate = group[0]
        if candidate not in selected:
            selected.append(candidate)
        if len(selected) >= num_demos:
            break

    # Fill remaining from chore or any high-score example
    remaining = [r for r in positives if r not in selected]
    remaining.sort(key=lambda r: r.get("score", 0), reverse=True)
    for r in remaining:
        if len(selected) >= num_demos:
            break
        selected.append(r)

    return selected[:num_demos]


def _select_diverse_research(
    records: list[dict],
    num_demos: int,
) -> list[dict]:
    """Select diverse research-analyst examples across verdict types.

    Strategy:
    - Pick top example per verdict (PASS, FAIL, INCONCLUSIVE, BLOCKED, etc.)
    - Fill remaining slots with highest-score examples.
    """
    selected: list[dict] = []
    by_verdict: dict[str, list[dict]] = {}
    for r in records:
        verdict = (r.get("output") or {}).get("verdict", "UNKNOWN")
        by_verdict.setdefault(str(verdict).upper(), []).append(r)

    for verdict in sorted(by_verdict.keys()):
        group = sorted(by_verdict[verdict], key=lambda r: r.get("score", 0), reverse=True)
        candidate = group[0]
        if candidate not in selected:
            selected.append(candidate)
        if len(selected) >= num_demos:
            break

    remaining = [r for r in records if r not in selected]
    remaining.sort(key=lambda r: r.get("score", 0), reverse=True)
    for r in remaining:
        if len(selected) >= num_demos:
            break
        selected.append(r)

    return selected[:num_demos]


# ── Formatting ────────────────────────────────────────────────────────────────


def _format_karen_example(rec: dict, index: int) -> str:
    inp = rec.get("input") or {}
    out = rec.get("output") or {}
    score = rec.get("score", 0)
    source = rec.get("source", "")

    commit_subject = inp.get("commit_subject", "")
    files_modified = inp.get("files_modified") or []
    if isinstance(files_modified, str):
        files_modified = [files_modified]
    files_str = ", ".join(str(f) for f in files_modified if f) or "(none)"

    reverted = bool(out.get("reverted"))
    doc_files = int(out.get("doc_files_written") or 0)
    action = "reverted" if reverted else ("updated" if doc_files > 0 else "skipped")

    score_note = f"score: {score}"
    if source:
        score_note += f", source: {source}"

    return (
        f"### Example {index} ({score_note})\n"
        f"**Commit:** `{commit_subject}`  \n"
        f"**Files modified:** `{files_str}`  \n"
        f"**Expected action:** {action}  \n"
        f"**Doc files written:** {doc_files}  \n"
        f"**Reverted:** {reverted}\n"
    )


def _format_research_example(rec: dict, index: int) -> str:
    inp = rec.get("input") or {}
    out = rec.get("output") or {}
    score = rec.get("score", 0)

    question = inp.get("question_text") or inp.get("question_id") or ""
    verdict = out.get("verdict", "")
    severity = out.get("severity", "")
    confidence = out.get("confidence", "")
    evidence = (out.get("evidence") or "")[:200]
    if len(out.get("evidence") or "") > 200:
        evidence += "..."

    return (
        f"### Example {index} (score: {score})\n"
        f"**Question:** {question}  \n"
        f"**Verdict:** {verdict}  \n"
        f"**Severity:** {severity}  \n"
        f"**Confidence:** {confidence}  \n"
        f"**Evidence (excerpt):** {evidence}\n"
    )


def _build_section(
    examples: list[dict],
    signature: str,
    generated_at: str,
) -> str:
    formatter = _format_karen_example if signature == "karen" else _format_research_example
    lines = [
        f"\n{_SECTION_HEADER}",
        f"<!-- auto-generated by optimize_claude.py on {generated_at} — edit manually to refine -->",
        f"<!-- {len(examples)} examples selected from scored_all.jsonl by diversity + score -->",
        "",
    ]
    for i, rec in enumerate(examples, 1):
        lines.append(formatter(rec, i))
    lines.append(_SECTION_END)
    return "\n".join(lines) + "\n"


# ── Write-back ────────────────────────────────────────────────────────────────


def _find_agent_md_files(base_dir: Path, agent_name: str) -> list[Path]:
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


def _writeback(
    base_dir: Path,
    agent_name: str,
    section_text: str,
) -> list[Path]:
    section_pattern = re.compile(
        rf"{re.escape(_SECTION_HEADER)}.*?{re.escape(_SECTION_END)}\n?",
        re.DOTALL,
    )
    updated: list[Path] = []
    for md_path in _find_agent_md_files(base_dir, agent_name):
        content = md_path.read_text(encoding="utf-8")
        if section_pattern.search(content):
            new_content = section_pattern.sub(section_text.lstrip("\n"), content)
        else:
            new_content = content.rstrip("\n") + "\n" + section_text
        md_path.write_text(new_content, encoding="utf-8")
        updated.append(md_path)
    return updated


# ── Main ──────────────────────────────────────────────────────────────────────


def run(
    agent_name: str,
    base_dir: Path,
    signature: str = "research",
    num_demos: int = _DEFAULT_NUM_DEMOS,
) -> int:
    print(f"[init] Agent: {agent_name}")
    print(f"[init] Base dir: {base_dir}")
    print(f"[init] Signature: {signature}")
    print(f"[init] Num demos to select: {num_demos}")

    # Locate scored_all.jsonl
    _self_td = base_dir / "training_data"
    _normal_td = base_dir / "masonry" / "training_data"
    td_dir = _self_td if _self_td.exists() else _normal_td
    scored_path = td_dir / "scored_all.jsonl"

    print(f"[data] Loading from {scored_path} ...")
    records = _load_raw(scored_path, agent_name)
    if not records:
        print(f"[error] No records found for agent '{agent_name}' in scored_all.jsonl.")
        print(f"[error] Run 'Score All' in Kiln first to populate training data.")
        return 1

    print(f"[data] Found {len(records)} records.")
    scores = [r.get("score", 0) for r in records]
    print(f"[data] Score range: {min(scores):.0f} – {max(scores):.0f}")
    print(f"[data] Score > 0: {sum(1 for s in scores if s > 0)}  |  Score = 0: {sum(1 for s in scores if s == 0)}")

    # Select diverse demos
    if signature == "karen":
        selected = _select_diverse_karen(records, num_demos)
    else:
        selected = _select_diverse_research(records, num_demos)

    print(f"[select] Selected {len(selected)} diverse examples:")
    for i, rec in enumerate(selected, 1):
        subj = (rec.get("input") or {}).get("commit_subject") or (rec.get("input") or {}).get("question_text") or ""
        print(f"  {i}. score={rec.get('score', 0):>5}  {subj[:70]}")

    # Build section text
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    section_text = _build_section(selected, signature, generated_at)

    # Write back to agent .md files
    updated = _writeback(base_dir, agent_name, section_text)
    if updated:
        for p in updated:
            print(f"[writeback] Injected {len(selected)} examples into: {p}")
    else:
        print(f"[warn] No agent .md files found for '{agent_name}'. Nothing written.")
        print(f"[info] Expected: {base_dir / '.claude' / 'agents' / (agent_name + '.md')}")
        print(f"[info] or:       {Path.home() / '.claude' / 'agents' / (agent_name + '.md')}")
        return 1

    print(f"[done] Few-shot examples injected. No API key or DSPy needed.")
    return 0


def _main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Select diverse few-shot examples from scored_all.jsonl and inject "
            "them into agent .md files. No DSPy, no API key — runs directly in "
            "Claude Code chats using existing training data."
        )
    )
    parser.add_argument("agent_name", help="Name of the agent to optimize")
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
        help='Signature type: "research" (default) or "karen"',
    )
    parser.add_argument(
        "--num-demos",
        type=int,
        default=_DEFAULT_NUM_DEMOS,
        help=f"Number of few-shot examples to inject (default: {_DEFAULT_NUM_DEMOS})",
    )
    args = parser.parse_args()
    sys.exit(run(
        agent_name=args.agent_name,
        base_dir=args.base_dir.resolve(),
        signature=args.signature,
        num_demos=args.num_demos,
    ))


if __name__ == "__main__":
    _main()
