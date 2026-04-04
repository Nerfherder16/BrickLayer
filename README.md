# BrickLayer 2.0

A full project lifecycle system — from first idea to running production code to ongoing maintenance.

BrickLayer is NOT just a research tool. It orchestrates every phase: hypothesis generation, evidence-based validation, agent-driven builds, automated heal loops, and continuous monitoring.

---

## Research Campaigns

BrickLayer asks: *what kills this?* — not *what is optimal?*

```
Claude Code
     ↕
  Masonry     ← bridge (MCP server, hooks, routing engine)
     ↕
 BrickLayer   ← framework (campaigns, builds, agent fleet, simulations)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full architecture reference.

---

## Quick Start

**Prerequisites:** Python 3.11+, Node.js 18+, Claude Code with BrickLayer 2.0, tmux

**Start a research campaign:**
```bash
claude --dangerously-skip-permissions
# Then: /masonry-run
```

**Check campaign status:**
```bash
# In Claude Code:
/masonry-status
```

**Run a single question:**
```python
from bl.runners.agent import run_question
result = run_question("Q1", project_dir="./projects/myproject")
```

**Spawn an agent directly:**
```python
from bl.tmux.core import spawn_agent, wait_for_agent
handle = spawn_agent("rough-in", "Task: ...", cwd="/path/to/project")
result = wait_for_agent(handle)
```

---

## Agent Dispatch

| Task Type | Route |
|-----------|-------|
| Dev tasks (build, fix, feature) | rough-in directly |
| Campaigns / research | mortar → trowel |
| Documentation | karen |
| Any agent directly | `@agent-name: <task>` |

---

## Key Directories

| Path | What's in it |
|------|-------------|
| `bl/` | Python engine — runners, tmux, heal loop, Recall bridge |
| `masonry/` | Masonry bridge — hooks, MCP server, routing |
| `projects/` | Active BrickLayer projects |
| `bricklayer-v2/` | BL2 self-audit campaign (14+ waves) |
| `recall-arch-frontier/` | Frontier research → Recall 2.0 architecture |
| `findings/` | Cross-project findings |
| `docs/` | Documentation and repo research |

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, module reference, hook list |
| [ROADMAP.md](ROADMAP.md) | Wave progress, open items, planned work |
| [CHANGELOG.md](CHANGELOG.md) | Change history by date |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Per-module stability status |
| [CLAUDE.md](CLAUDE.md) | Session context for Claude Code (routing rules, engine API) |

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `RECALL_SRC` | Path to Recall source repo (optional) |
| `RECALL_HOST` | Recall API base URL |
| `BL_GATE_FILE` | Per-spawn Masonry gate file |
| `BL_MASONRY_STATE` | Override path for masonry-state.json |
