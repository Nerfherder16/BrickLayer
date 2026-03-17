"""
bl/config.py — Mutable config singleton for BrickLayer.

All modules import `cfg` and read its attributes. `init_project()` mutates
the singleton before any runner runs, so all modules see the updated values.
"""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

# ---------------------------------------------------------------------------
# API route constants (project-agnostic)
# ---------------------------------------------------------------------------

SEARCH_ROUTE = "/search/query"
STORE_ROUTE = "/memory/store"
HEALTH_ROUTE = "/health"
CONSOLIDATE_ROUTE = "/admin/consolidate"

# ---------------------------------------------------------------------------
# Config singleton
# ---------------------------------------------------------------------------

_autosearch_root = Path(__file__).parent.parent  # autosearch/

cfg = SimpleNamespace(
    base_url="http://192.168.50.19:8200",
    api_key="recall-admin-key-change-me",  # noqa: secrets — placeholder, overridden by project.json
    request_timeout=10.0,
    local_ollama_url="http://192.168.50.62:11434",
    local_model="qwen2.5:7b",
    recall_src=Path("C:/Users/trg16/Dev/Recall"),
    autosearch_root=_autosearch_root,
    project_root=_autosearch_root,
    findings_dir=_autosearch_root / "findings",
    results_tsv=_autosearch_root / "results.tsv",
    questions_md=_autosearch_root / "questions.md",
    history_db=_autosearch_root / "history.db",
    agents_dir=_autosearch_root / "agents",
)


def auth_headers() -> dict:
    """Return current auth headers (re-evaluated on every call so api_key changes are picked up)."""
    return {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Project loader
# ---------------------------------------------------------------------------


def init_project(project_name: str | None) -> None:
    """Load project config from project.json and update cfg."""
    if project_name:
        candidates = [
            cfg.autosearch_root / "projects" / project_name,
            cfg.autosearch_root / project_name,
        ]
        project_dir: Path | None = None
        for candidate in candidates:
            if (candidate / "project.json").exists():
                project_dir = candidate
                break

        if project_dir is None:
            print(f"Error: project '{project_name}' not found.", file=sys.stderr)
            for c in candidates:
                print(f"  Checked: {c / 'project.json'}", file=sys.stderr)
            print("\nRun: python onboard.py  to create a new project.", file=sys.stderr)
            sys.exit(1)

        project_cfg = json.loads(
            (project_dir / "project.json").read_text(encoding="utf-8")
        )
        # Support both "recall_src" (BL 2.0) and legacy "target_git" field names
        recall_src_raw = project_cfg.get("recall_src") or project_cfg.get("target_git")
        if recall_src_raw:
            cfg.recall_src = Path(recall_src_raw)
        cfg.base_url = project_cfg.get("target_live_url", cfg.base_url)
        cfg.api_key = project_cfg.get("api_key", cfg.api_key)
        cfg.project_root = project_dir
        cfg.findings_dir = project_dir / "findings"
        cfg.results_tsv = project_dir / "results.tsv"
        cfg.questions_md = project_dir / "questions.md"
        cfg.history_db = project_dir / "history.db"
        cfg.agents_dir = project_dir / ".claude" / "agents"
    else:
        project_dir = _autosearch_root
        cfg.project_root = project_dir
        cfg.findings_dir = project_dir / "findings"
        cfg.results_tsv = project_dir / "results.tsv"
        cfg.questions_md = project_dir / "questions.md"
        cfg.history_db = project_dir / "history.db"
        cfg.agents_dir = project_dir / ".claude" / "agents"

    cfg.findings_dir.mkdir(exist_ok=True)
