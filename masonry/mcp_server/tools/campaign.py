"""masonry/mcp_server/tools/campaign.py — Campaign-related MCP tool implementations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from masonry.mcp_server.js_engine import _call_js_engine, _REPO_ROOT


def _tool_masonry_status(args: dict) -> dict:
    """Return current campaign status for a project directory."""
    project_dir = Path(args.get("project_dir", os.getcwd()))

    # Try JS engine first
    js_result = _call_js_engine("status.js", ["--project-dir", str(project_dir)], timeout=10)
    if js_result is not None:
        return js_result

    # Python fallback
    state_file = project_dir / "masonry-state.json"
    questions_file = project_dir / "questions.md"

    result: dict[str, Any] = {
        "project_dir": str(project_dir),
        "has_campaign": state_file.exists(),
    }

    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            result["state"] = state
        except Exception:
            result["state"] = {}

    if questions_file.exists():
        text = questions_file.read_text(errors="replace")
        lines = text.splitlines()
        q_total = sum(
            1 for ln in lines
            if ln.startswith("### Q") or (ln.startswith("## ") and len(ln) > 3 and ln[3].isupper() and ln[4].isdigit())
        )
        waves = sum(1 for ln in lines if ln.lower().startswith("## wave"))
        pending = sum(1 for ln in lines if "**Status" in ln and "PENDING" in ln)
        done = sum(1 for ln in lines if "**Status" in ln and ln.strip().endswith("DONE"))
        result["questions"] = {
            "total": q_total,
            "waves": waves,
            "pending": pending,
            "done": done,
        }

    mas_dir = project_dir / ".mas"
    if mas_dir.is_dir():
        mas_data: dict[str, Any] = {}
        for fname, key in [
            ("session.json", "session"),
            ("open_issues.json", "open_issues"),
            ("agent_scores.json", "agent_scores"),
        ]:
            fpath = mas_dir / fname
            if fpath.exists():
                try:
                    mas_data[key] = json.loads(fpath.read_text())
                except Exception:
                    pass
        pulse_file = mas_dir / "pulse.jsonl"
        if pulse_file.exists():
            try:
                lines_raw = pulse_file.read_text().strip().splitlines()
                if lines_raw:
                    mas_data["last_pulse"] = json.loads(lines_raw[-1])
            except Exception:
                pass
        errors_file = mas_dir / "errors.jsonl"
        if errors_file.exists():
            try:
                error_lines = errors_file.read_text().strip().splitlines()
                mas_data["error_count"] = len([ln for ln in error_lines if ln.strip()])
            except Exception:
                pass
        if mas_data:
            result["mas"] = mas_data

    return result


def _tool_masonry_questions(args: dict) -> dict:
    """List questions from questions.md, optionally filtered by status."""
    project_dir = Path(args.get("project_dir", os.getcwd()))
    status_filter = args.get("status")
    limit = int(args.get("limit", 20))

    questions_file = project_dir / "questions.md"
    if not questions_file.exists():
        return {"error": "questions.md not found", "project_dir": str(project_dir)}

    from bl.questions import load_questions  # noqa: PLC0415

    try:
        qs = load_questions(str(questions_file))
        if status_filter:
            qs = [q for q in qs if q.get("status", "").upper() == status_filter.upper()]
        qs = qs[:limit]
        return {"questions": qs, "count": len(qs)}
    except Exception as e:
        return {"error": str(e)}


def _tool_masonry_nl_generate(args: dict) -> dict:
    """Generate research questions from a natural language description."""
    description = args.get("description", "")
    project_dir = args.get("project_dir")
    append = bool(args.get("append", False))

    if not description:
        return {"error": "description is required"}

    from bl.nl_entry import generate_from_description, format_preview, quick_campaign  # noqa: PLC0415

    if append and project_dir:
        result = quick_campaign(description, project_dir=project_dir)
        return result
    else:
        questions = generate_from_description(description)
        return {
            "questions": questions,
            "preview": format_preview(questions),
            "count": len(questions),
        }


def _tool_masonry_weights(args: dict) -> dict:
    """Show question weight report for a project."""
    project_dir = args.get("project_dir", os.getcwd())

    from bl.question_weights import weight_report  # noqa: PLC0415

    try:
        report = weight_report(project_dir)
        return {"report": report}
    except Exception as e:
        return {"error": str(e)}


def _tool_masonry_git_hypothesis(args: dict) -> dict:
    """Generate hypotheses from recent git diff."""
    project_dir = args.get("project_dir", os.getcwd())
    commits = int(args.get("commits", 5))
    max_questions = int(args.get("max_questions", 10))
    dry_run = bool(args.get("dry_run", True))

    from bl.git_hypothesis import (  # noqa: PLC0415
        get_recent_diff,
        parse_diff_files,
        match_patterns,
        generate_questions,
        append_to_questions_md,
    )

    diff = get_recent_diff(commits=commits, cwd=project_dir)
    if not diff:
        return {"error": "No diff found or not a git repository", "questions": []}

    files = parse_diff_files(diff)
    matches = match_patterns(diff, files)
    questions = generate_questions(matches)[:max_questions]

    if not dry_run:
        questions_md = Path(project_dir) / "questions.md"
        if questions_md.exists():
            appended = append_to_questions_md(questions, str(questions_md))
            return {"questions": questions, "appended": appended, "count": len(questions)}

    return {
        "questions": questions,
        "count": len(questions),
        "dry_run": dry_run,
        "files_analyzed": files,
        "patterns_matched": [m["pattern"] for m in matches],
    }


def _store_question_finding(result: dict, question: dict, project_dir: Path) -> None:
    """Fire-and-forget: store question verdict to Recall."""
    try:
        verdict = result.get("verdict", "")
        summary = result.get("summary", "")
        if not verdict or not summary:
            return

        project_json = project_dir / "project.json"
        project_name = project_dir.name
        if project_json.exists():
            try:
                pcfg = json.loads(project_json.read_text(encoding="utf-8"))
                project_name = pcfg.get("name") or pcfg.get("display_name", project_dir.name)
            except Exception:
                pass

        from bl.recall_bridge import store_finding  # noqa: PLC0415

        question_id = question.get("id", "unknown")
        agent_name = question.get("agent_name") or question.get("mode", "runner")
        store_finding(
            question_id=question_id,
            verdict=verdict,
            summary=summary,
            project=project_name,
            tags=[f"agent:{agent_name}", "type:finding"],
        )
    except Exception:
        pass  # Never block a campaign


def _tool_masonry_run_question(args: dict) -> dict:
    """Run a single BL question by ID and return the verdict envelope."""
    project_dir = args.get("project_dir", os.getcwd())
    question_id = args.get("question_id", "")

    if not question_id:
        return {"error": "question_id is required"}

    from bl.questions import load_questions  # noqa: PLC0415
    from bl.runners import run_question  # noqa: PLC0415

    questions_file = Path(project_dir) / "questions.md"
    if not questions_file.exists():
        return {"error": "questions.md not found"}

    qs = load_questions(str(questions_file))
    q = next((q for q in qs if q.get("id") == question_id), None)
    if q is None:
        return {"error": f"Question {question_id!r} not found"}

    try:
        result = run_question(q)
        _store_question_finding(result, q, Path(project_dir))
        response = {"question_id": question_id, "result": result}

        # Trigger JS heal loop for failure verdicts
        verdict = result.get("verdict", "") if isinstance(result, dict) else ""
        if verdict in ("FAILURE", "DIAGNOSIS_COMPLETE"):
            heal_result = _call_js_engine(
                "healloop.js",
                ["--project-dir", str(project_dir), "--question-id", question_id, "--verdict", verdict],
                timeout=300,
            )
            if heal_result is not None:
                response["heal_loop"] = heal_result

        return response
    except Exception as e:
        return {"error": str(e), "question_id": question_id}
