"""bl/cli/gh_issues_cmd.py — Ingest GitHub issues as BrickLayer research questions.

Fetches open issues from a GitHub repo and converts each one into a BL 2.0
question using nl_entry.generate_from_description, then appends them to
questions.md.

Usage:
    python -m bl.cli.gh_issues_cmd --project ./projects/myproject
    python -m bl.cli.gh_issues_cmd --project . --repo owner/repo --limit 20
    python -m bl.cli.gh_issues_cmd --project . --state all --dry-run
    python -m bl.cli.gh_issues_cmd --project . --json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from bl.git_hypothesis import append_to_questions_md
from bl.nl_entry import generate_from_description


def fetch_issues(
    repo: str | None = None,
    limit: int = 20,
    state: str = "open",
    label: str | None = None,
) -> list[dict]:
    """Fetch issues from GitHub via gh CLI. Returns list of issue dicts."""
    cmd = [
        "gh", "issue", "list",
        "--limit", str(limit),
        "--state", state,
        "--json", "number,title,body,labels,url",
    ]
    if repo:
        cmd += ["--repo", repo]
    if label:
        cmd += ["--label", label]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"[gh_issues] gh error: {result.stderr.strip()}", file=sys.stderr)
        return []

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print("[gh_issues] Failed to parse gh output", file=sys.stderr)
        return []


def issue_to_description(issue: dict) -> str:
    """Build a plain-English description from an issue for nl_entry."""
    title = issue.get("title", "")
    body = (issue.get("body") or "").strip()
    # Use title + first 300 chars of body for context
    if body:
        snippet = body[:300].replace("\n", " ").strip()
        return f"{title}. {snippet}"
    return title


def issues_to_questions(issues: list[dict], max_per_issue: int = 2) -> list[dict]:
    """Convert a list of GitHub issues to BL question dicts."""
    questions: list[dict] = []
    for issue in issues:
        description = issue_to_description(issue)
        if not description.strip():
            continue

        generated = generate_from_description(description, max_questions=max_per_issue)

        # Tag each question with the source issue
        for q in generated:
            q["source"] = f"gh_issue#{issue['number']}"
            q["title"] = f"#{issue['number']} — {q['title']}"

        questions.extend(generated)

    return questions


def _print_question(q: dict, n: int) -> None:
    print(f"  Q{n}. [{q['priority'].upper()}] {q['title']}")
    print(f"       Mode: {q['mode']}  Domain: {q['domain']}")
    print(f"       {q['question'][:120]}...")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ingest GitHub issues as BrickLayer research questions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--project",
        default=".",
        metavar="DIR",
        help="BrickLayer project directory (must contain questions.md). Default: .",
    )
    parser.add_argument(
        "--repo",
        default=None,
        metavar="OWNER/REPO",
        help="GitHub repo (e.g. Nerfherder16/Recall). Default: auto-detect from git remote.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        metavar="N",
        help="Max issues to fetch. Default: 20.",
    )
    parser.add_argument(
        "--state",
        default="open",
        choices=["open", "closed", "all"],
        help="Issue state to fetch. Default: open.",
    )
    parser.add_argument(
        "--label",
        default=None,
        metavar="LABEL",
        help="Filter issues by label.",
    )
    parser.add_argument(
        "--max-per-issue",
        type=int,
        default=2,
        metavar="N",
        help="Max BL questions to generate per issue. Default: 2.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print questions but do not append to questions.md.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Print questions as JSON array (implies --dry-run).",
    )

    args = parser.parse_args(argv)

    project_dir = str(Path(args.project).resolve())

    print(
        f"[gh_issues] Fetching {args.state} issues"
        + (f" from {args.repo}" if args.repo else "")
        + f" (limit={args.limit})...",
        file=sys.stderr,
    )

    issues = fetch_issues(
        repo=args.repo,
        limit=args.limit,
        state=args.state,
        label=args.label,
    )

    if not issues:
        print("[gh_issues] No issues found.", file=sys.stderr)
        return 0

    print(f"[gh_issues] Fetched {len(issues)} issue(s). Generating questions...", file=sys.stderr)

    questions = issues_to_questions(issues, max_per_issue=args.max_per_issue)

    if not questions:
        print("[gh_issues] No questions generated.", file=sys.stderr)
        return 0

    if args.output_json:
        print(json.dumps(questions, indent=2))
        return 0

    print(f"\n[gh_issues] Generated {len(questions)} question(s):\n")
    for i, q in enumerate(questions, start=1):
        _print_question(q, i)

    if args.dry_run:
        print(
            f"[gh_issues] DRY RUN — {len(questions)} question(s) NOT written to questions.md",
            file=sys.stderr,
        )
        return 0

    # Append to questions.md using git_hypothesis's formatter
    # Inject a commit_sha placeholder so append_to_questions_md is happy
    repo_ref = args.repo or "github"
    for q in questions:
        q.setdefault("commit_sha", repo_ref)

    appended = append_to_questions_md(
        project_dir=project_dir,
        questions=questions,
        wave_label="Auto (gh-issues)",
    )

    if appended:
        questions_path = Path(project_dir) / "questions.md"
        print(
            f"\n[gh_issues] Appended {appended} question(s) to {questions_path}",
            file=sys.stderr,
        )
    else:
        print(
            "\n[gh_issues] Nothing appended (questions.md not found or empty list).",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
