"""
simulate.py — BrickLayer CLI entry point.

Thin dispatcher: parses args, initialises project config, delegates to bl/.
"""

import argparse
import sys

# Force UTF-8 on Windows stdout/stderr so Unicode in question titles doesn't crash.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from bl.campaign import (
    run_campaign,
    run_single,
    run_retrospective,
)
from bl.config import cfg, init_project
from bl.questions import parse_questions
from bl.runners.agent import run_scout_for_project


def main() -> None:
    parser = argparse.ArgumentParser(description="BrickLayer autoresearch runner")
    parser.add_argument("--project", "-p", help="Project name (e.g. recall, adbp)")
    parser.add_argument("--question", "-q", help="Question ID to run (e.g. Q1.1)")
    parser.add_argument(
        "--campaign",
        "-c",
        action="store_true",
        help="Run all PENDING questions in sequence",
    )
    parser.add_argument("--list", "-l", action="store_true", help="List all questions")
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse questions only, don't run"
    )
    parser.add_argument(
        "--scout",
        "-s",
        action="store_true",
        help="Run Scout to regenerate questions.md for the project",
    )
    parser.add_argument(
        "--retro",
        "-r",
        action="store_true",
        help="Run end-of-session retrospective to improve BrickLayer",
    )
    args = parser.parse_args()

    init_project(args.project)

    _DEFAULT_KEY = "recall-admin-key-change-me"
    if cfg.base_url not in ("none", "None", "") and cfg.api_key == _DEFAULT_KEY:
        print(
            "Warning: using default API key — set api_key in project.json before targeting a live service.",
            file=sys.stderr,
        )

    if args.scout:
        run_scout_for_project()
        return

    if args.retro:
        run_retrospective()
        return

    if args.list:
        questions = parse_questions()
        print(f"{'ID':<8} {'STATUS':<15} {'MODE':<15} {'TITLE'}")
        print("-" * 80)
        for q in questions:
            print(f"{q['id']:<8} {q['status']:<15} {q['mode']:<15} {q['title']}")
        return

    if args.campaign:
        run_campaign()
        return

    run_single(args.question, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
