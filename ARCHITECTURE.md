# BrickLayer 2.0 — Architecture

> Tier 1 document. Human-only edits. Ground truth for the project.

---

## Overview

BrickLayer 2.0 is a full project lifecycle system that orchestrates every phase of software development — from hypothesis generation through production deployment and ongoing maintenance. It runs alongside Claude Code as a parallel layer, using a Python engine (`bl/`), a tmux-based agent dispatch layer, and a JavaScript hook system (Masonry) that bridges Claude Code with the BrickLayer runtime. The system is designed for long-running research campaigns, autonomous heal loops, and multi-agent parallel builds.

---

## Three-Layer Model

```
Claude Code
     ↕
  Masonry          ← bridge: MCP server, hooks, routing engine, schemas
     ↕
 BrickLayer        ← framework: campaigns, simulations, agent fleet, builds
```

- **BrickLayer** — the framework. Research campaigns, simulations, agent fleet, findings, synthesis, builds, heal loops.
- **Masonry** — the bridge. MCP server, typed payload schemas, hooks, DSPy optimization, routing engine.
- **Mortar** — the entry point for campaigns, research, and docs. Dev tasks go directly to rough-in.

---

## Agent Dispatch Hierarchy

```
Main session
├── rough-in          ← Dev tasks (build, fix, refactor, feature) — direct dispatch
├── mortar            ← Campaigns, research, docs — routes internally to:
│   ├── trowel        ← Campaign conductor (full BL 2.0 research loop)
│   └── karen         ← Documentation (changelog, roadmap, folder audits)
└── @agent-name:      ← Self-invoke bypass — any prompt starting with @agentname: 
                         skips all routing and spawns that agent directly
```

Routing is enforced by two hooks:
- `masonry-prompt-router.js` (UserPromptSubmit) — detects intent and injects routing hint
- `masonry-mortar-enforcer.js` (PreToolUse:Agent) — enforces dispatch hierarchy at call time

As of 2026-04-04, the mortar enforcer allows any recognized registry agent to be spawned directly from the main session. The old rule requiring all tasks to route through Mortar first has been relaxed — dev tasks go to rough-in directly, docs go to karen directly, and `@agent-name:` bypasses routing entirely.

---

## Project Structure

| Path | Purpose |
|------|---------|
| `bl/` | The engine — Python. Runners, tmux dispatch, heal loop, Recall bridge |
| `bl/runners/` | 15 evidence-collection runners (agent, swarm, benchmark, contract, browser, etc.) |
| `bl/tmux/` | Agent orchestration — pane spawn, wave dispatch, signal coordination |
| `bl/healloop.py` | Self-healing: diagnose → fix → verify, up to N cycles |
| `bl/recall_bridge.py` | Inter-agent memory — agents share context via Recall |
| `bl/crucible.py` | Agent benchmarking — promote/flag/retire based on eval scores |
| `masonry/` | Masonry orchestration system — hooks, MCP server, routing engine |
| `masonry/src/hooks/` | All Claude Code lifecycle hooks |
| `masonry/agent_registry.yml` | Authoritative agent list (100+ agents) |
| `projects/` | Active projects managed by BrickLayer |
| `bricklayer-v2/` | BL2 self-audit campaign (14+ waves complete) |
| `recall-arch-frontier/` | 256-question frontier research → Recall 2.0 architecture |
| `template-frontier/` | Template for new frontier projects |
| `docs/` | Documentation and repo research |
| `findings/` | Cross-project findings |
| `.claude/agents/` | Agent definition files (frontmatter + prompt) |

---

## Engine Modules (`bl/`)

| Module | Purpose |
|--------|---------|
| `tmux/core.py` | Spawn agents in tmux panes with live streaming; per-spawn gate via `BL_GATE_FILE` |
| `tmux/wave.py` | Parallel wave dispatch — multiple agents simultaneously |
| `tmux/pane.py` | Pane capture using `$TMUX_PANE`; falls back to subprocess |
| `runners/agent.py` | Single-agent evidence collection |
| `runners/swarm.py` | Multi-agent parallel dispatch with verdict aggregation |
| `runners/benchmark.py` | Quantitative baseline measurement |
| `runners/correctness.py` | Correctness proof verification; Linux + Windows path regex |
| `runners/scout.py` | Reconnaissance/exploration runner |
| `healloop.py` | Automated diagnose→fix→verify cycles |
| `recall_bridge.py` | Recall API integration for inter-agent memory sharing |
| `crucible.py` | Agent scoring, promotion, and retirement |
| `nl_entry.py` | Natural language → research question generation |
| `campaign_context.py` | Campaign state and cross-question context |
| `findings.py` | Finding storage, verdict tracking, results.tsv management |
| `synthesizer.py` | Cross-finding synthesis |
| `config.py` | Project configuration; reads `RECALL_SRC`, `RECALL_HOST` env vars |

---

## Dual-Engine Architecture

BrickLayer uses two engines. The split is permanent — both engines have structural constraints that make migration impractical.

### JS Engine (Hot Path)
- `masonry/src/hooks/*.js` — Claude Code hooks (fire on every tool use)
- `masonry/src/engine/cli/` — CLI wrappers callable via subprocess from Python
- MCP fast-path tools: `masonry_route`, `masonry_status`, `masonry_registry_list`
- Post-verdict: `masonry_run_question` calls `cli/healloop.js` for FAILURE/DIAGNOSIS_COMPLETE

**Why JS:** Hooks fire on every tool use — 50-100ms cold-start vs 300-400ms for Python subprocess. Node.js has no cold-start when already running in the hook system.

### Python Engine (Campaign Path)
- `bl/runners/` — evidence-collection runners (15 types)
- `bl/tmux/` — agent orchestration via tmux panes
- `bl/crucible.py` — agent benchmarking + promotion/retirement
- DSPy pipeline, scoring, training export

**Why Python:** DSPy/ML, GPU inference via Ollama, tmux process spawning, SQLAlchemy — all require Python ecosystem.

### Wiring Diagram

```
Claude Code → MCP server (Python/FastMCP)
                ↓ subprocess.run(["node", "cli/X.js", ...], timeout=10-300s)
              Node.js CLI wrapper (masonry/src/engine/cli/*.js)
                ↓ require()
              JS engine module (masonry/src/engine/*.js)
                ↓ reads
              YAML / JSON / MD files on disk

              On subprocess failure → Python fallback (silent, returns same schema)
```

### Decision Criteria

| Concern | Use Node.js | Use Python |
|---------|-------------|------------|
| Cold-start latency | 50-100ms | 300-400ms |
| Claude Code hook system | Native | Not available |
| MCP tool integration | Via CLI wrapper | Native FastMCP |
| DSPy / ML optimization | Not available | Required |
| tmux agent spawn | Not available | Required |
| File I/O (YAML, JSON, MD) | Fast | Fine |
| GPU / Ollama inference | Via HTTP only | Preferred |

---

## Masonry Hooks

| Hook | Event | Purpose |
|------|-------|---------|
| `masonry-prompt-router.js` | UserPromptSubmit | Intent detection; injects routing hint; `@agent-name:` self-invoke bypass |
| `masonry-mortar-enforcer.js` | PreToolUse:Agent | Enforces dispatch hierarchy; allows direct specialist spawns from main session |
| `masonry-session-start.js` | SessionStart | Restore autopilot/UI/campaign context |
| `masonry-pre-protect.js` | PreToolUse (Write/Edit) | Pre-edit protection + session lock |
| `masonry-approver.js` | PreToolUse (Write/Edit/Bash) | Auto-approve writes in build/fix/compose mode |
| `masonry-content-guard.js` | PreToolUse (Write/Edit) | Config protection + secret scanner |
| `masonry-style-checker.js` | PostToolUse (Write/Edit) | Lint enforcement (ruff, prettier, eslint) |
| `masonry-observe.js` | PostToolUse (Write/Edit) | Campaign state observation (async) |
| `masonry-build-outcome.js` | PostToolUse (Write) | Watch `.autopilot/progress.json` for DONE/FAILED transitions; calls pattern promote/demote; infers agent type from `[mode:X]` annotations |
| `masonry-tool-failure.js` | PostToolUseFailure | Error tracking + 3-strike escalation |
| `masonry-subagent-tracker.js` | SubagentStart | Track active agent spawns (async) |
| `masonry-agent-onboard.js` | PostToolUse (Write/Edit) | Auto-onboard new agents to registry (async) |
| `masonry-context-safety.js` | PreToolUse (ExitPlanMode) | Block plan-mode exit during active build or high context |
| `masonry-stop-guard.js` | Stop | Block Stop on uncommitted git changes |
| `masonry-build-guard.js` | Stop | Block Stop if autopilot has pending tasks |
| `masonry-ui-compose-guard.js` | Stop | Block Stop if `.ui/` compose has pending tasks |
| `masonry-context-monitor.js` | Stop | Warn on context > 150K tokens; semantic degradation detection via Ollama |
| `masonry-tdd-enforcer.js` | PostToolUse (Write/Edit) | Enforce TDD — block writes without corresponding test files |

---

## Masonry MCP Tools

| Tool | Purpose |
|------|---------|
| `masonry_status` | Campaign status — state, question counts, wave for a project dir |
| `masonry_questions` | List questions from questions.md, filtered by status |
| `masonry_nl_generate` | Generate BL research questions from plain English |
| `masonry_weights` | Question weight report — high priority, prunable, retry flags |
| `masonry_git_hypothesis` | Analyze recent git diffs and generate targeted questions |
| `masonry_run_question` | Run a single BL question by ID, return verdict envelope |
| `masonry_fleet` | List fleet agents and performance scores from registry + agent_db |
| `masonry_recall` | Search Recall for memories relevant to a query |
| `masonry_route` | Route a request through the four-layer pipeline |
| `masonry_onboard` | Trigger agent auto-onboarding for new .md files |
| `masonry_drift_check` | Run drift detection across all registry agents |
| `masonry_registry_list` | List agents from registry YAML, filtered by tier or mode |
| `masonry_pattern_promote` | Promote an agent pattern +20% headroom in pattern confidence store |
| `masonry_pattern_demote` | Demote an agent pattern -15% (floor 0.1) in pattern confidence store |

---

## Mode System (9 Modes)

| Mode | Verdicts | Use |
|------|----------|-----|
| Frontier | PROMISING, WEAK, BLOCKED | Blue-sky hypothesis generation |
| Research | HEALTHY, WARNING, FAILURE | Evidence-based stress testing |
| Validate | HEALTHY, WARNING, FAILURE | Design verification |
| Benchmark | CALIBRATED, UNCALIBRATED, NOT_MEASURABLE | Baseline measurement |
| Diagnose | DIAGNOSIS_COMPLETE, HEALTHY, WARNING, FAILURE | Fault detection |
| Fix | FIXED, FIX_FAILED | Automated repair |
| Audit | COMPLIANT, NON_COMPLIANT, PARTIAL | Compliance check |
| Evolve | IMPROVEMENT, REGRESSION, WARNING | Continuous improvement |
| Predict | IMMINENT, PROBABLE, POSSIBLE, UNLIKELY | Risk forecasting |
| Monitor | OK, DEGRADED, ALERT | Ongoing health monitoring |

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `RECALL_SRC` | Path to the Recall source repo | None (optional) |
| `RECALL_HOST` | Recall API base URL for trowel agent | None |
| `BL_GATE_FILE` | Per-spawn Masonry gate file path | `/tmp/masonry-gate-{agent_id}.json` |
| `BL_MASONRY_STATE` | Override path for masonry-state.json | `<cwd>/masonry/masonry-state.json` |

---

## Network Infrastructure

Full network topology is maintained in `~/.claude/rules/network-map.md` (single source of truth). Key nodes:

| Host | Role | Access |
|------|------|--------|
| farmstand (CasaOS) | Docker host, primary homelab server | `nerfherder@farmstand` or `192.168.50.19` |
| ubuntu-claude | Claude Code runner (Proxmox VM 103) | `nerfherder@100.79.9.122` (Tailscale) |
| recall-ollama | System-Recall stack (Proxmox VM 102) | `100.70.195.84` |
| ollama-vm | GPU inference (RTX 3090) | `192.168.50.62:11434` |

The homelab skill (`~/.claude/skills/homelab/SKILL.md`) and `~/.claude/agents/self-host.md` are thin references that point to `network-map.md` for all topology details.

---

## Tech Stack

- **Engine**: Python 3.11+
- **Hooks/MCP**: Node.js (CommonJS)
- **Agent definitions**: Markdown with YAML frontmatter
- **Routing**: 4-layer pipeline — deterministic → semantic (Ollama embeddings) → LLM (Claude Haiku) → fallback
- **Memory**: System-Recall (FastAPI + Qdrant + Neo4j + Ollama), API at `http://100.70.195.84:8200`
- **Orchestration**: tmux (visible panes with live streaming), subprocess fallback
- **Version control**: Git, branch `bricklayer-v2/mar24-parallel` (current)
