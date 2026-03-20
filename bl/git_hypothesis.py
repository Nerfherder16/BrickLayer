"""
bl/git_hypothesis.py — Automatic hypothesis generation from git diffs.

Analyzes recent commits and produces BL 2.0 research questions targeting
changed code paths. When code changes, new failure modes are introduced —
this module maps diff patterns to domain-specific question templates.

Stdlib only: subprocess, re, pathlib, json.
"""

import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

DIFF_PATTERNS = [
    {
        "name": "concurrency",
        "pattern": r"concurrent|asyncio|threading|lock|mutex|race",
        "domain": "D4",
        "mode": "diagnose",
        "template": "Does {file} handle concurrent access safely? What happens under {pattern} conditions at high load?",
        "priority": "high",
    },
    {
        "name": "fee_calculation",
        "pattern": r"def.*fee|fee.*calc|rate.*calc|calc.*rate|commission|royalt",
        "domain": "D1",
        "mode": "quantitative",
        "template": "What are the boundary conditions for the fee calculation in {file}? Sweep parameters to find where the formula produces unexpected results.",
        "priority": "high",
    },
    {
        "name": "schema_migration",
        "pattern": r"migration|ALTER TABLE|schema.*change|add.*column|drop.*column",
        "domain": "D2",
        "mode": "validate",
        "template": "Does the schema change in {file} maintain backward compatibility? What happens to existing data during migration?",
        "priority": "high",
    },
    {
        "name": "auth_access_control",
        "pattern": r"auth|permission|role|access.*control|require.*login|jwt|token",
        "domain": "D3",
        "mode": "audit",
        "template": "Does the auth change in {file} maintain proper access control? What happens if {pattern} is bypassed or malformed?",
        "priority": "high",
    },
    {
        "name": "cache",
        "pattern": r"cache|redis|memcache|ttl|expire|invalidat",
        "domain": "D4",
        "mode": "diagnose",
        "template": "What happens when the cache in {file} is cold, stale, or evicted under load? Does the system degrade gracefully?",
        "priority": "medium",
    },
    {
        "name": "resilience",
        "pattern": r"retry|backoff|timeout|circuit.*break|fallback",
        "domain": "D4",
        "mode": "diagnose",
        "template": "Does the retry/resilience logic in {file} work correctly under sustained failure? What is the failure cascade if {pattern} fails permanently?",
        "priority": "medium",
    },
    {
        "name": "dependency",
        "pattern": r"import|require|dependency|package|version",
        "domain": "D5",
        "mode": "research",
        "template": "Does the new dependency in {file} introduce any known vulnerabilities or breaking changes in recent versions?",
        "priority": "low",
    },
]

# Priority sort order for deduplication and capping
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Git diff retrieval
# ---------------------------------------------------------------------------


def get_recent_diff(repo_path: str, commits: int = 3) -> str:
    """
    Run git diff HEAD~{commits}..HEAD and return the diff text.
    Returns "" if not a git repo or git unavailable.
    Uses subprocess with 10s timeout.
    """
    try:
        result = subprocess.run(
            ["git", "diff", f"HEAD~{commits}..HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            # May be a shallow clone or insufficient history — try HEAD~1
            if commits > 1:
                return get_recent_diff(repo_path, commits=1)
            return ""
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def _get_head_sha(repo_path: str) -> str:
    """Return the short SHA of HEAD, or 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return "unknown"


# ---------------------------------------------------------------------------
# Diff parser
# ---------------------------------------------------------------------------


def parse_diff_files(diff_text: str) -> list[dict]:
    """
    Parse unified diff into list of file dicts:
    {file: str, added_lines: [str], removed_lines: [str], is_new_file: bool}
    """
    if not diff_text:
        return []

    files: list[dict] = []
    current: dict | None = None

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            # Extract the b/ path (destination file)
            m = re.search(r" b/(.+)$", line)
            filename = m.group(1) if m else line
            current = {
                "file": filename,
                "added_lines": [],
                "removed_lines": [],
                "is_new_file": False,
            }
            files.append(current)
        elif line.startswith("new file mode") and current is not None:
            current["is_new_file"] = True
        elif (
            line.startswith("+") and not line.startswith("+++") and current is not None
        ):
            current["added_lines"].append(line[1:])
        elif (
            line.startswith("-") and not line.startswith("---") and current is not None
        ):
            current["removed_lines"].append(line[1:])

    return files


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------


def match_patterns(diff_files: list[dict]) -> list[dict]:
    """
    For each file, check added_lines against DIFF_PATTERNS.
    Returns list of matches:
      {file, pattern_name, template, domain, mode, priority, matched_text}
    Deduplicated: one match per (file, pattern_name) pair.
    """
    seen: set[tuple[str, str]] = set()
    matches: list[dict] = []

    for file_info in diff_files:
        filename = file_info["file"]
        added_text = "\n".join(file_info["added_lines"])

        for pat in DIFF_PATTERNS:
            key = (filename, pat["name"])
            if key in seen:
                continue

            compiled = re.compile(pat["pattern"], re.IGNORECASE | re.MULTILINE)
            m = compiled.search(added_text)
            if m:
                seen.add(key)
                matches.append(
                    {
                        "file": filename,
                        "pattern_name": pat["name"],
                        "template": pat["template"],
                        "domain": pat["domain"],
                        "mode": pat["mode"],
                        "priority": pat["priority"],
                        "matched_text": m.group(0),
                    }
                )

    return matches


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------


def generate_questions(
    repo_path: str, commits: int = 3, max_questions: int = 5
) -> list[dict]:
    """
    Full pipeline: diff → parse → match → generate question dicts.

    Returns list of BL 2.0 question dicts:
    {
        "id": "GH-{sha[:6]}-{n}",
        "title": "...",
        "mode": "diagnose",
        "domain": "D4",
        "status": "PENDING",
        "priority": "high",
        "source": "git_hypothesis",
        "commit_sha": "...",
        "question": "full question text"
    }
    Sorted by priority (high first), capped at max_questions.
    """
    diff_text = get_recent_diff(repo_path, commits)
    if not diff_text:
        return []

    diff_files = parse_diff_files(diff_text)
    if not diff_files:
        return []

    pattern_matches = match_patterns(diff_files)
    if not pattern_matches:
        return []

    # Sort by priority
    pattern_matches.sort(key=lambda m: _PRIORITY_ORDER.get(m["priority"], 99))

    sha = _get_head_sha(repo_path)

    questions: list[dict] = []
    for n, match in enumerate(pattern_matches[:max_questions], start=1):
        # Render the template
        question_text = match["template"].format(
            file=match["file"],
            pattern=match["matched_text"],
        )

        # Derive a short title from the pattern name and file basename
        basename = Path(match["file"]).name
        title = f"{match['pattern_name'].replace('_', ' ').title()} risk in {basename}"

        questions.append(
            {
                "id": f"GH-{sha}-{n}",
                "title": title,
                "mode": match["mode"],
                "domain": match["domain"],
                "status": "PENDING",
                "priority": match["priority"],
                "source": "git_hypothesis",
                "commit_sha": sha,
                "question": question_text,
            }
        )

    return questions


# ---------------------------------------------------------------------------
# Append to questions.md
# ---------------------------------------------------------------------------


def _get_next_q_number(questions_md_text: str) -> int:
    """
    Parse all existing ### QN headers (and BL 2.0 ## ID headers) to find
    the highest sequential question number, then return next.
    Falls back to counting existing GH- entries.
    """
    # Match ### Q42 — Title style
    section_pattern = re.compile(r"^###\s+Q(\d+)\s+", re.MULTILINE)
    # Also match BL 2.0 ## GH- style to avoid collision
    gh_pattern = re.compile(r"^##\s+GH-\S+-(\d+)\s", re.MULTILINE)

    nums: list[int] = []
    for m in section_pattern.finditer(questions_md_text):
        try:
            nums.append(int(m.group(1)))
        except ValueError:
            pass
    for m in gh_pattern.finditer(questions_md_text):
        try:
            nums.append(int(m.group(1)))
        except ValueError:
            pass

    return (max(nums) + 1) if nums else 1


def append_to_questions_md(
    project_dir: str, questions: list[dict], wave_label: str = "Auto (git)"
) -> int:
    """
    Append generated questions to questions.md under a new wave header.
    Returns count of questions appended.
    Only appends if questions list is non-empty.

    Format matches the BL 2.0 questions.md style:
    ### QN — Title
    **Status**: PENDING
    **Mode**: ...
    etc.
    """
    if not questions:
        return 0

    questions_path = Path(project_dir) / "questions.md"
    if not questions_path.exists():
        print(
            f"[git_hypothesis] questions.md not found at {questions_path}",
            file=sys.stderr,
        )
        return 0

    existing_text = questions_path.read_text(encoding="utf-8")
    next_q = _get_next_q_number(existing_text)

    lines: list[str] = [
        "",
        "---",
        "",
        f"## {wave_label}",
        "",
        f"**Source**: git diff — {questions[0]['commit_sha']}",
        f"**Generated**: {len(questions)} question(s) from changed code patterns",
        "",
    ]

    for i, q in enumerate(questions):
        q_num = next_q + i
        lines.append(f"### Q{q_num} — {q['title']}")
        lines.append("")
        lines.append(f"**Status**: {q['status']}")
        lines.append(f"**Operational Mode**: {q['mode']}")
        lines.append(f"**Priority**: {q['priority'].upper()}")
        lines.append(f"**Domain**: {q['domain']}")
        lines.append(f"**Source**: {q['source']} ({q['commit_sha']})")
        lines.append(f"**Question**: {q['question']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    append_text = "\n".join(lines)

    with open(questions_path, "a", encoding="utf-8") as f:
        f.write(append_text)

    return len(questions)


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------


def run(
    project_dir: str = ".",
    commits: int = 3,
    max_questions: int = 5,
    dry_run: bool = False,
    wave_label: str = "Auto (git)",
) -> list[dict]:
    """
    Convenience entry point: generate questions for the project at project_dir
    and optionally append them to questions.md.

    Returns the list of generated question dicts.
    """
    questions = generate_questions(
        project_dir, commits=commits, max_questions=max_questions
    )

    if not questions:
        print(
            "[git_hypothesis] No matching patterns found in recent diff.",
            file=sys.stderr,
        )
        return []

    if dry_run:
        return questions

    appended = append_to_questions_md(project_dir, questions, wave_label=wave_label)
    print(
        f"[git_hypothesis] Appended {appended} question(s) to questions.md",
        file=sys.stderr,
    )
    return questions
