"""Backfill **Agent**: field in existing finding files that lack attribution.

Infers agent from question_id prefix using a configurable domain map.
Only patches files where **Agent**: is absent or set to 'unknown'.

Usage:
    python masonry/scripts/backfill_agent_fields.py [--base-dir DIR] [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

# Default question_id prefix → agent mapping
# First matching prefix wins. More specific prefixes first.
DEFAULT_PREFIX_MAP: list[tuple[str, str]] = [
    # bricklayer-meta campaign prefixes
    ("Q1.", "quantitative-analyst"),
    ("Q2.", "regulatory-researcher"),
    ("Q3.", "competitive-analyst"),
    ("Q4.", "research-analyst"),
    ("Q5.", "quantitative-analyst"),
    ("Q6.", "synthesizer-bl2"),
    ("D1.", "quantitative-analyst"),
    ("D2.", "regulatory-researcher"),
    ("D3.", "competitive-analyst"),
    ("D4.", "research-analyst"),
    ("D5.", "quantitative-analyst"),
    ("B.", "benchmark-engineer"),
    ("R.", "research-analyst"),
    ("M.", "health-monitor"),
    ("S.", "synthesizer-bl2"),
    # Generic fallbacks by letter
    ("Q", "quantitative-analyst"),
    ("D", "diagnose-analyst"),
    ("R", "research-analyst"),
    ("B", "benchmark-engineer"),
]

_RE_AGENT = re.compile(r"^\*\*Agent\*\*\s*:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
_RE_QUESTION = re.compile(r"^\*\*Question\*\*\s*:", re.MULTILINE | re.IGNORECASE)
_RE_VERDICT = re.compile(r"^\*\*Verdict\*\*\s*:", re.MULTILINE | re.IGNORECASE)
_RE_HEADER_ID = re.compile(r"^#\s+Finding\s*:\s*([^\s—–\-][^\s]*)", re.IGNORECASE | re.MULTILINE)


def infer_agent(question_id: str, prefix_map: list[tuple[str, str]]) -> str | None:
    """Return the best-matching agent name for a question_id, or None."""
    for prefix, agent in prefix_map:
        if question_id.upper().startswith(prefix.upper()):
            return agent
    return None


def extract_question_id(path: Path, text: str) -> str:
    """Extract question_id from finding content or filename."""
    m = _RE_HEADER_ID.search(text)
    if m:
        return m.group(1).strip()
    return path.stem


def needs_backfill(text: str) -> bool:
    """Return True if the file is missing or has unknown **Agent**: field."""
    m = _RE_AGENT.search(text)
    if not m:
        return True
    return m.group(1).strip().lower() in ("unknown", "", "[unknown]", "n/a")


def insert_agent_field(text: str, agent_name: str) -> str:
    """Insert **Agent**: after **Question**: line if present, else after **Verdict**:."""
    # Prefer inserting after **Question**:
    q_match = _RE_QUESTION.search(text)
    if q_match:
        # Find end of the **Question**: line
        end = text.find("\n", q_match.end())
        if end == -1:
            end = len(text)
        return text[: end + 1] + f"**Agent**: {agent_name}\n" + text[end + 1 :]

    # Fallback: insert after first metadata line (any **X**: pattern)
    v_match = _RE_VERDICT.search(text)
    if v_match:
        end = text.find("\n", v_match.end())
        if end == -1:
            end = len(text)
        return text[: end + 1] + f"**Agent**: {agent_name}\n" + text[end + 1 :]

    # Last resort: prepend after first line
    lines = text.split("\n")
    lines.insert(1, f"**Agent**: {agent_name}")
    return "\n".join(lines)


def patch_agent_field(text: str, agent_name: str) -> str:
    """Replace existing unknown **Agent**: value with agent_name."""
    return _RE_AGENT.sub(f"**Agent**: {agent_name}", text, count=1)


def discover_findings(base_dir: Path) -> list[Path]:
    """Discover all finding .md files under base_dir."""
    found: list[Path] = []

    def _collect(findings_dir: Path) -> None:
        if not findings_dir.is_dir():
            return
        for p in findings_dir.iterdir():
            if p.suffix == ".md" and p.name not in ("synthesis.md",):
                found.append(p)

    _collect(base_dir / "findings")
    for child in base_dir.iterdir():
        if child.is_dir() and child.name not in ("findings", "masonry", ".git"):
            _collect(child / "findings")

    return found


def run(
    base_dir: Path,
    prefix_map: list[tuple[str, str]] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Backfill **Agent**: fields across all findings.

    Returns summary: {scanned, patched, skipped_no_map, unchanged, dry_run}
    """
    if prefix_map is None:
        prefix_map = DEFAULT_PREFIX_MAP

    paths = discover_findings(base_dir)
    patched = 0
    skipped_no_map = 0
    unchanged = 0

    for finding_path in paths:
        try:
            text = finding_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not needs_backfill(text):
            unchanged += 1
            continue

        qid = extract_question_id(finding_path, text)
        agent = infer_agent(qid, prefix_map)

        if not agent:
            skipped_no_map += 1
            continue

        # Determine if we're inserting or replacing
        has_field = bool(_RE_AGENT.search(text))
        if has_field:
            new_text = patch_agent_field(text, agent)
        else:
            new_text = insert_agent_field(text, agent)

        if not dry_run:
            finding_path.write_text(new_text, encoding="utf-8")
        patched += 1

    return {
        "scanned": len(paths),
        "patched": patched,
        "skipped_no_map": skipped_no_map,
        "unchanged": unchanged,
        "dry_run": dry_run,
    }


def _main() -> None:
    parser = argparse.ArgumentParser(description="Backfill **Agent**: fields in finding files.")
    parser.add_argument("--base-dir", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true", help="Report without modifying files")
    args = parser.parse_args()

    summary = run(base_dir=args.base_dir, dry_run=args.dry_run)
    mode = "[DRY RUN] " if summary["dry_run"] else ""
    print(f"{mode}Scanned: {summary['scanned']} findings")
    print(f"{mode}Patched: {summary['patched']}")
    print(f"{mode}Skipped (no prefix map): {summary['skipped_no_map']}")
    print(f"{mode}Already attributed: {summary['unchanged']}")


if __name__ == "__main__":
    _main()
