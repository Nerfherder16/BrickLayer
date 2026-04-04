"""bl/runners/scout.py — Scout agent runner for question generation."""

import json

from bl.config import cfg
from bl.frontmatter import strip_frontmatter
from bl.tmux import spawn_agent, wait_for_agent


def run_scout_for_project() -> None:
    """Invoke the Scout agent to regenerate questions.md."""
    scout_path = cfg.agents_dir / "scout.md"
    if not scout_path.exists():
        print(json.dumps({"error": "scout.md not found in agents/"}))
        return

    body = strip_frontmatter(scout_path.read_text(encoding="utf-8"))

    project_cfg: dict = {}
    cfg_path = cfg.project_root / "project.json"
    if cfg_path.exists():
        project_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    docs_dir = cfg.project_root / "docs"
    docs_content = ""
    if docs_dir.exists():
        for doc in sorted(docs_dir.iterdir()):
            if doc.is_file():
                try:
                    docs_content += f"\n\n### {doc.name}\n{doc.read_text(encoding='utf-8', errors='ignore')[:3000]}"
                except Exception as exc:  # noqa: BLE001
                    import sys

                    print(f"[scout] skipping {doc.name}: {exc}", file=sys.stderr)

    prompt = f"""{body}

---

## Your Assignment

**Project**: {project_cfg.get("display_name", "Unknown")}
**Target git**: {cfg.recall_src}
**Stack**: {", ".join(project_cfg.get("stack", [])) or "unknown"}
**Live service**: {project_cfg.get("target_live_url", "none")}
**Docs folder**: {docs_dir}
{f"**Supporting docs content**:{docs_content}" if docs_content else "**Docs folder**: empty — scan the codebase only"}

Scan the target codebase now and output the complete questions.md content."""

    print("Running Scout — scanning codebase to generate questions...", flush=True)
    try:
        scout_spawn = spawn_agent(
            agent_name="scout",
            prompt=prompt,
            dangerously_skip_permissions=True,
            output_format=None,
        )
    except FileNotFoundError:
        print(json.dumps({"error": "claude CLI not found"}))
        return

    scout_result = wait_for_agent(scout_spawn, timeout=300)

    if scout_result.exit_code == -1:
        print(json.dumps({"error": "Scout timed out after 300s"}))
        return

    output = scout_result.stdout.strip()
    idx = output.find("# BrickLayer Campaign Questions")
    if idx == -1:
        print(json.dumps({"error": "Scout output not recognized", "raw": output[:500]}))
        return

    questions_md = output[idx:]
    cfg.questions_md.write_text(questions_md, encoding="utf-8")
    count = questions_md.count("## Q")
    print(
        json.dumps(
            {"status": "ok", "questions_written": count, "path": str(cfg.questions_md)}
        )
    )
