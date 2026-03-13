"""
onboard.py — BrickLayer project onboarding tool.

Creates a new project under autosearch/projects/{name}/ by:
  1. Accepting a GitHub URL or local path
  2. Cloning the repo if a URL is given
  3. Auto-detecting the tech stack from repo files
  4. Writing project.json, .claude.json, questions.md, prepare.md

All agents in autosearch/agents/ are always available — no pre-selection needed.
The right agent is called automatically based on what each question requires.

Usage:
    python onboard.py
    python onboard.py --name recall
    python onboard.py --list
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

AUTOSEARCH_ROOT = Path(__file__).parent
PROJECTS_DIR = AUTOSEARCH_ROOT / "projects"
TEMPLATE_DIR = AUTOSEARCH_ROOT / "template"

PREPARE_TEMPLATE = """\
# BrickLayer — Session Context Brief

Read this file at the start of every BrickLayer session before doing anything else.

---

## What BrickLayer Is

BrickLayer is an autonomous failure-boundary research framework. It runs structured
question campaigns against a live codebase to find bugs, coverage gaps, type errors,
race conditions, and security issues — then dispatches specialist agents to fix them.

**Current target**: {display_name}

---

## Directory Layout

```
C:/Users/trg16/Dev/autosearch/
  simulate.py              # Main dispatcher (run from autosearch/ root)
  onboard.py               # Project setup tool
  agents/                  # Agent catalog — all always available
  handoffs/                # Cross-project change requests
  projects/
    {name}/                # This project's working directory
      project.json         # Project config
      questions.md         # Campaign question bank
      results.tsv          # Running verdict log (append-only)
      findings/            # Per-question detail reports (Q*.md)
      prepare.md           # This file
      .claude.json         # Per-project MCP isolation
```

---

## Starting Prompt (use at the top of every BrickLayer session)

```
Working directory: C:/Users/trg16/Dev/autosearch/

You are running BrickLayer against: **{display_name}**
Target git: {target_git}
Target live service: {target_live_url}

Read projects/{name}/prepare.md before doing anything else.
Confirm the git boundary rule before proceeding.

All findings stay in autosearch/projects/{name}/.
Fix agents operate within the target git only.
Cross-project changes go to autosearch/handoffs/ — never applied directly.

Start by reading your memory, then explore the target before designing questions.
```

---

## Target System

- **Codebase**: `{target_git}`
- **Live service**: `{target_live_url}`
- **Stack** (auto-detected): {stack}

---

## Git Boundary Rule (HARD RULE — READ BEFORE EVERY RUN)

BrickLayer NEVER commits to any git repo other than the **target project** being analyzed.

| Role | Git repo | What lives here |
|------|----------|-----------------|
| BrickLayer framework | `autosearch/` | simulate.py, agents/, projects/, handoffs/ |
| Target project | `{target_git}` | Source code being analyzed and fixed |
| Handoffs | `autosearch/handoffs/` | Cross-project change requests |

**Fix agents** read and modify only the **target project's git**.
**Cross-project changes**: create `autosearch/handoffs/handoff-{{project}}-{{date}}.md` instead.
**At end of every run**: check — were any cross-project changes needed? If yes, create the handoff doc.

---

## How to Run

```bash
cd C:/Users/trg16/Dev/autosearch

python simulate.py --project {name} --list
python simulate.py --project {name} --question Q1.1
python simulate.py --project {name} --campaign
```

---

## Agent Catalog

All agents in `autosearch/agents/` are always available. The agent used for each
question is specified in that question's `**Agent**:` field. You do not need to
pre-configure which agents are enabled — just write the question to use the right one.

| Agent | Use for |
|-------|---------|
| security-hardener | Silent swallows, bare excepts, injection risks, missing validation |
| test-writer | Adding test coverage, characterizing bugs via tests |
| type-strictener | mypy errors, Any types, missing annotations |
| perf-optimizer | Slow endpoints, N+1 queries, inefficient loops |
| forge | Generating new questions from codebase scan |
"""

QUESTIONS_TEMPLATE = """\
# BrickLayer Campaign Questions — {display_name}

Questions are organized in waves. Each wave targets blindspots from the prior wave.
Status is tracked in results.tsv — do not edit manually.

---

## Q1.1 [CORRECTNESS] Full test suite baseline
**Mode**: correctness
**Target**: tests/
**Hypothesis**: The full test suite passes with no failures or errors.
**Test**: Run pytest against the full test suite.
**Verdict threshold**:
- HEALTHY: All tests pass (0 failures, 0 errors)
- WARNING: 1-5 test failures
- FAILURE: >5 failures or any import error

---

## Q2.1 [QUALITY] Silent exception swallows in source
**Mode**: quality
**Target**: src/
**Hypothesis**: Source code contains bare `except:` or `except Exception: pass` patterns
that silently swallow errors, hiding bugs and making debugging impossible.
**Verdict threshold**:
- HEALTHY: No bare except/silent swallow patterns found
- WARNING: 1-3 instances found
- FAILURE: >3 instances or any in critical paths
"""


def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  {label}{suffix}: ").strip()
    return val if val else default


_EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    ".venv",
    "__pycache__",
    ".mypy_cache",
}


def _bounded_glob(root: Path, pattern: str, max_depth: int = 4) -> bool:
    """Return True if any file matching pattern exists within max_depth levels of root.

    Skips common vendor/tool directories to avoid traversing the entire tree.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).relative_to(root).parts)
        if depth >= max_depth:
            dirnames.clear()
        else:
            dirnames[:] = [d for d in dirnames if d not in _EXCLUDE_DIRS]
        for fname in filenames:
            if Path(fname).match(pattern):
                return True
    return False


def detect_stack(repo_path: Path) -> list[str]:
    """Auto-detect tech stack from repo files."""
    stack = []

    # Python
    py_indicators = [
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
        "Pipfile",
    ]
    if any((repo_path / f).exists() for f in py_indicators) or any(
        repo_path.glob("*.py")
    ):
        stack.append("Python")
        # Detect Python frameworks
        for fname in ["pyproject.toml", "requirements.txt", "requirements-dev.txt"]:
            fpath = repo_path / fname
            if fpath.exists():
                content = fpath.read_text(errors="ignore").lower()
                if "fastapi" in content:
                    stack.append("FastAPI")
                if "django" in content:
                    stack.append("Django")
                if "flask" in content:
                    stack.append("Flask")
                if "sqlalchemy" in content or "alembic" in content:
                    stack.append("SQLAlchemy")
                if "pydantic" in content:
                    stack.append("Pydantic")
                if "qdrant" in content:
                    stack.append("Qdrant")
                if "redis" in content:
                    stack.append("Redis")
                if "neo4j" in content:
                    stack.append("Neo4j")
                if (
                    "postgresql" in content
                    or "psycopg" in content
                    or "asyncpg" in content
                ):
                    stack.append("PostgreSQL")

    # Node / TypeScript / JavaScript
    pkg_path = repo_path / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text())
            all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "typescript" in all_deps:
                stack.append("TypeScript")
            else:
                stack.append("Node.js")
            if "react" in all_deps:
                stack.append("React")
            if "next" in all_deps:
                stack.append("Next.js")
            if "vite" in all_deps:
                stack.append("Vite")
            if "tailwindcss" in all_deps:
                stack.append("Tailwind")
            if "@anthropic-ai/sdk" in all_deps or "anthropic" in all_deps:
                stack.append("Anthropic SDK")
        except Exception as e:
            print(f"Warning: could not parse package.json: {e}", file=sys.stderr)
            # Do not append Node.js — detection failed

    # Rust
    if (repo_path / "Cargo.toml").exists():
        stack.append("Rust")
        try:
            content = (repo_path / "Cargo.toml").read_text(errors="ignore").lower()
            if "anchor" in content:
                stack.append("Anchor")
            if "solana" in content:
                stack.append("Solana")
        except Exception as e:
            print(f"Warning: could not parse Cargo.toml: {e}", file=sys.stderr)

    # Go
    if (repo_path / "go.mod").exists():
        stack.append("Go")

    # Kotlin / Android / KMP
    if _bounded_glob(repo_path, "build.gradle.kts") or _bounded_glob(repo_path, "*.kt"):
        stack.append("Kotlin")
        if _bounded_glob(repo_path, "AndroidManifest.xml"):
            stack.append("Android")

    # Swift / iOS
    if any(repo_path.glob("*.xcodeproj")) or _bounded_glob(repo_path, "*.swift"):
        stack.append("Swift/iOS")

    # Infrastructure
    if (repo_path / "docker-compose.yml").exists() or (
        repo_path / "docker-compose.yaml"
    ).exists():
        stack.append("Docker Compose")
    if _bounded_glob(repo_path, "*.tf"):
        stack.append("Terraform")

    return list(dict.fromkeys(stack))  # deduplicate preserving order


def clone_repo(url: str, target_dir: Path) -> bool:
    """Clone a GitHub repo to target_dir. Returns True on success."""
    print(f"\n  Cloning {url} → {target_dir} ...")
    result = subprocess.run(
        ["git", "clone", url, str(target_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  Error: {result.stderr.strip()}", file=sys.stderr)
        return False
    print("  Cloned successfully.")
    return True


def cmd_list() -> None:
    if not PROJECTS_DIR.exists():
        print("No projects yet. Run onboard.py to create the first project.")
        return
    projects = [
        d
        for d in sorted(PROJECTS_DIR.iterdir())
        if d.is_dir() and (d / "project.json").exists()
    ]
    if not projects:
        print("No projects found in projects/.")
        return
    print(f"\n{'NAME':<20} {'DISPLAY NAME':<25} {'TARGET GIT'}")
    print("-" * 80)
    for p in projects:
        cfg = json.loads((p / "project.json").read_text())
        session = cfg.get("claude_session_id") or ""
        print(f"{cfg['name']:<20} {cfg['display_name']:<25} {cfg['target_git']}")
        if session:
            print(f"  {'':20} session: {session}")


def run_scout(project_cfg: dict, questions_path: Path) -> bool:
    """Run the Scout agent to generate tailored questions for a new project."""
    import shutil as _shutil

    scout_path = AUTOSEARCH_ROOT / "agents" / "scout.md"
    if not scout_path.exists():
        print("  Scout agent not found — keeping template questions.")
        return False

    # Strip frontmatter
    raw = scout_path.read_text(encoding="utf-8")
    body = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].lstrip("\n")

    docs_dir = questions_path.parent / "docs"
    docs_content = ""
    if docs_dir.exists():
        for doc in sorted(docs_dir.iterdir()):
            if doc.is_file():
                try:
                    docs_content += f"\n\n### {doc.name}\n{doc.read_text(encoding='utf-8', errors='ignore')[:3000]}"
                except Exception as e:
                    print(
                        f"Warning: could not read doc file {doc.name}: {e}",
                        file=sys.stderr,
                    )

    prompt = f"""{body}

---

## Your Assignment

**Project**: {project_cfg["display_name"]}
**Target git**: {project_cfg["target_git"]}
**Stack**: {", ".join(project_cfg.get("stack", [])) or "unknown"}
**Live service**: {project_cfg.get("target_live_url", "none")}
**Docs folder**: {docs_dir}
{f"<docs>{docs_content}\n</docs>" if docs_content else "**Docs folder**: empty — scan the codebase only"}

Scan the target codebase now and output the complete questions.md content."""

    claude_bin = _shutil.which("claude") or "claude"
    child_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    print("\n  Running Scout to generate tailored questions...")
    print("  (This may take a minute — Scout is reading your codebase)\n")

    try:
        proc = subprocess.run(
            [claude_bin, "-p", "-", "--dangerously-skip-permissions"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=child_env,
            timeout=300,
        )
    except FileNotFoundError:
        print("  claude CLI not found — keeping template questions.")
        return False
    except subprocess.TimeoutExpired:
        print("  Scout timed out — keeping template questions.")
        return False

    output = proc.stdout.strip()
    if not output or "# BrickLayer Campaign Questions" not in output:
        print("  Scout output not recognized — keeping template questions.")
        if proc.stderr:
            print(f"  stderr: {proc.stderr[:300]}")
        return False

    # Extract from first # header to end
    idx = output.find("# BrickLayer Campaign Questions")
    questions_md = output[idx:]
    questions_path.write_text(questions_md, encoding="utf-8")
    print(f"  Scout wrote {questions_md.count('## Q')} questions to questions.md")
    return True


def cmd_create(name: str | None) -> None:
    print("\nBrickLayer Project Onboarding")
    print("=" * 40)

    # Project name
    if not name:
        name = _prompt("Project slug (e.g. recall, adbp, familyhub)")
    if not name:
        print("Error: project name required.", file=sys.stderr)
        sys.exit(1)
    name = name.lower().strip()

    project_dir = PROJECTS_DIR / name
    if project_dir.exists() and (project_dir / "project.json").exists():
        print(f"Error: project '{name}' already exists.", file=sys.stderr)
        sys.exit(1)

    # Display name
    display_name = _prompt("Display name", name.replace("-", " ").title())

    # Repo: GitHub URL or local path
    repo_input = _prompt(
        f"GitHub URL or local path (e.g. https://github.com/org/repo or {AUTOSEARCH_ROOT.parent}/MyProject)"
    )
    if not repo_input:
        print("Error: repo required.", file=sys.stderr)
        sys.exit(1)

    is_url = (
        repo_input.startswith("http://")
        or repo_input.startswith("https://")
        or repo_input.startswith("git@")
    )

    if is_url:
        # Derive default clone directory from URL
        repo_slug = repo_input.rstrip("/").split("/")[-1].removesuffix(".git")
        default_clone_dir = f"C:/Users/trg16/Dev/{repo_slug}"
        print(f"\n  Clone destination: {default_clone_dir}")
        alt = input("  Press Enter to use that path, or type a different one: ").strip()
        target_git_path = Path(alt if alt else default_clone_dir)

        if target_git_path.exists():
            print("  Directory already exists — using existing copy.")
        else:
            do_clone = _prompt("Clone now? (y/n)", "y").lower()
            if do_clone == "y":
                if not clone_repo(repo_input, target_git_path):
                    print(
                        "Clone failed. Fix the error above and re-run onboard.py.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
            else:
                print(f"  Skipping clone. Ensure the repo is at: {target_git_path}")
    else:
        target_git_path = Path(repo_input)
        if not target_git_path.exists():
            print(f"  Warning: path does not exist yet: {target_git_path}")
            print(
                "  (The project will be created — point to this path when the repo is ready.)"
            )
            if _prompt("Continue anyway?", "y").lower() != "y":
                sys.exit(0)

    target_git = str(target_git_path)

    # Auto-detect stack
    stack = []
    if target_git_path.exists():
        print("\n  Scanning repo for tech stack ...")
        stack = detect_stack(target_git_path)
        if stack:
            print(f"  Detected: {', '.join(stack)}")
        else:
            print("  Could not detect stack automatically.")

    # Live service URL (optional — used only for performance tests)
    print("\n  Live service URL is optional. Used only for performance/load testing.")
    target_live_url = _prompt("Live service URL (press Enter to skip)", "none")
    if not target_live_url or target_live_url.lower() == "skip":
        target_live_url = "none"

    # Confirm
    print("\n  Summary:")
    print(f"    Project:   {name}")
    print(f"    Display:   {display_name}")
    print(f"    Target:    {target_git}")
    print(f"    Stack:     {', '.join(stack) if stack else '(none detected)'}")
    print(f"    Live URL:  {target_live_url}")
    print("    Agents:    all (catalog — selected per question)")
    if _prompt("\n  Create project?", "y").lower() != "y":
        print("Aborted.")
        sys.exit(0)

    # Create directories
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "findings").mkdir(exist_ok=True)
    (project_dir / "docs").mkdir(exist_ok=True)

    # Write project.json
    project_cfg = {
        "name": name,
        "display_name": display_name,
        "target_git": target_git,
        "target_live_url": target_live_url,
        "stack": stack,
        "fix_branch_prefix": "bricklayer/",
        "claude_session_id": None,
        "last_run": None,
    }
    (project_dir / "project.json").write_text(
        json.dumps(project_cfg, indent=2), encoding="utf-8"
    )

    # Write .claude.json (per-project MCP isolation — no OMC)
    claude_cfg = {
        "mcpServers": {
            "recall": {
                "command": "node",
                "args": ["C:/Users/trg16/Dev/Recall/mcp-server/index.js"],
            },
            "github": {
                "command": "C:/Program Files/nodejs/npx.cmd",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
                },
            },
        }
    }
    (project_dir / ".claude.json").write_text(
        json.dumps(claude_cfg, indent=2), encoding="utf-8"
    )

    # Write questions.md from template or built-in
    template_questions = TEMPLATE_DIR / "questions.md"
    if template_questions.exists():
        shutil.copy(template_questions, project_dir / "questions.md")
    else:
        (project_dir / "questions.md").write_text(
            QUESTIONS_TEMPLATE.format(display_name=display_name, name=name),
            encoding="utf-8",
        )

    # Write results.tsv (header only)
    (project_dir / "results.tsv").write_text(
        "question_id\tverdict\tsummary\ttimestamp\n", encoding="utf-8"
    )

    # Write prepare.md
    (project_dir / "prepare.md").write_text(
        PREPARE_TEMPLATE.format(
            name=name,
            display_name=display_name,
            target_git=target_git,
            target_live_url=target_live_url,
            stack=", ".join(stack)
            if stack
            else "auto-detection found nothing — review manually",
        ),
        encoding="utf-8",
    )

    print(f"\n  Project '{name}' created.")

    # Step 1: Docs folder
    docs_dir = project_dir / "docs"
    print(f"\n  Supporting docs folder: {docs_dir}")
    print("  Drop in architecture notes, API specs, known issues, README excerpts.")
    if _prompt("  Open docs folder now?", "y").lower() == "y":
        subprocess.Popen(f'explorer.exe "{docs_dir}"', shell=True)
    input("\n  Press Enter when you're done adding docs (or to skip) ... ")

    # Step 2: Open VSCode, then run Scout from there
    scout_cmd = f"python simulate.py --project {name} --scout"
    starting_prompt = (
        f"Working directory: {AUTOSEARCH_ROOT}\n\n"
        f"You are running BrickLayer against: **{display_name}**\n"
        f"Target git: {target_git}\n"
        f"Target live service: {target_live_url}\n\n"
        f"Read projects/{name}/prepare.md before doing anything else. "
        f"Confirm the git boundary rule before proceeding.\n\n"
        f"All findings stay in autosearch/projects/{name}/. "
        f"Fix agents operate within the target git only. "
        f"Cross-project changes go to autosearch/handoffs/ — never applied directly.\n\n"
        f"Start by reading your memory, then explore the target before designing questions."
    )

    print(f"\n  Opening VSCode at: {AUTOSEARCH_ROOT}")
    code = shutil.which("code")
    if code:
        subprocess.Popen([code, str(AUTOSEARCH_ROOT)])
    else:
        print("  (code CLI not found — open VSCode manually)")

    # Open terminal with Claude
    wt = shutil.which("wt")
    claude_cmd = "claude --dangerously-skip-permissions"
    cwd = str(AUTOSEARCH_ROOT)
    if wt:
        subprocess.Popen(
            f'wt.exe new-tab --title "BrickLayer" -- cmd.exe /k "cd /d \\"{cwd}\\" && {claude_cmd}"',
            shell=True,
        )
    else:
        subprocess.Popen(
            f'start cmd.exe /k "cd /d \\"{cwd}\\" && {claude_cmd}"', shell=True
        )

    print("\n" + "=" * 50)
    print("  In the VSCode terminal, run Scout first:")
    print(f"\n    {scout_cmd}\n")
    print("  Scout will scan the codebase + your docs and write questions.md.")
    print("  When Scout finishes, start a Claude session and paste this prompt:")
    print("=" * 50)
    print(f"\n{starting_prompt}\n")

    # Copy starting prompt to clipboard
    try:
        subprocess.run("clip", input=starting_prompt.encode("utf-16"), check=False)
        print("  (Starting prompt copied to clipboard)")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="BrickLayer project onboarding tool")
    parser.add_argument("--name", "-n", help="Project slug")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List existing projects"
    )
    args = parser.parse_args()
    PROJECTS_DIR.mkdir(exist_ok=True)
    if args.list:
        cmd_list()
    else:
        cmd_create(args.name)


if __name__ == "__main__":
    main()
