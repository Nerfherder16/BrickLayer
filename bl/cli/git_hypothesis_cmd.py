"""
bl/cli/git_hypothesis_cmd.py — CLI for git-diff hypothesis generation.

Usage:
    python -m bl.cli.git_hypothesis_cmd [--project .] [--commits 3] [--max 5] [--dry-run]

Options:
    --project   Path to the BrickLayer project directory (default: current dir)
    --commits   Number of commits to diff against HEAD (default: 3)
    --max       Maximum number of questions to generate (default: 5)
    --dry-run   Print questions without appending to questions.md
    --json      Output questions as JSON (implies --dry-run for display)
"""

import argparse
import json
import sys
from pathlib import Path

# Allow running as `python -m bl.cli.git_hypothesis_cmd` from any cwd
_here = Path(__file__).resolve().parent.parent.parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from bl.git_hypothesis import (  # noqa: E402  (import after sys.path fixup)
    append_to_questions_md,
    generate_questions,
)


def _print_question(q: dict, q_num: int) -> None:
    """Pretty-print a single question dict to stdout."""
    print(f"\n### Q{q_num} — {q['title']}")
    print(f"  ID:       {q['id']}")
    print(f"  Domain:   {q['domain']}")
    print(f"  Mode:     {q['mode']}")
    print(f"  Priority: {q['priority'].upper()}")
    print(f"  Commit:   {q['commit_sha']}")
    print(f"  Question: {q['question']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate BrickLayer 2.0 research questions from recent git diffs.",
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
        "--commits",
        type=int,
        default=3,
        metavar="N",
        help="Number of commits to diff (HEAD~N..HEAD). Default: 3",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=5,
        metavar="N",
        help="Maximum questions to generate. Default: 5",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print questions but do not append to questions.md",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Print questions as JSON array (does not append to questions.md)",
    )
    parser.add_argument(
        "--wave-label",
        default="Auto (git)",
        metavar="LABEL",
        help='Wave header label in questions.md. Default: "Auto (git)"',
    )

    args = parser.parse_args(argv)

    project_dir = str(Path(args.project).resolve())

    print(
        f"[git_hypothesis] Analyzing last {args.commits} commit(s) in {project_dir}...",
        file=sys.stderr,
    )

    questions = generate_questions(
        repo_path=project_dir,
        commits=args.commits,
        max_questions=args.max,
    )

    if not questions:
        print(
            "[git_hypothesis] No matching patterns found in recent diff.",
            file=sys.stderr,
        )
        print(
            "  Tip: ensure the target directory is a git repo with recent commits.",
            file=sys.stderr,
        )
        return 0

    if args.output_json:
        print(json.dumps(questions, indent=2))
        return 0

    # Pretty-print questions
    print(f"\n[git_hypothesis] Found {len(questions)} question(s):\n")
    for i, q in enumerate(questions, start=1):
        _print_question(q, i)

    if args.dry_run:
        print(
            f"\n[git_hypothesis] DRY RUN — {len(questions)} question(s) NOT written to questions.md",
            file=sys.stderr,
        )
        return 0

    # Append to questions.md
    appended = append_to_questions_md(
        project_dir=project_dir,
        questions=questions,
        wave_label=args.wave_label,
    )

    if appended:
        questions_path = Path(project_dir) / "questions.md"
        print(
            f"\n[git_hypothesis] Appended {appended} question(s) to {questions_path}",
            file=sys.stderr,
        )
    else:
        print(
            "\n[git_hypothesis] Nothing appended (questions.md not found or empty list).",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
