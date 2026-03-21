# BrickLayer 2.0

**Autonomous research + full AI development platform for Claude Code.**

BrickLayer started as a failure-boundary research loop — run an AI agent against a simulation,
map every parameter combination that breaks it, write findings. It has since grown into a
three-layer platform that orchestrates the entire development workflow alongside campaign research.

---

## The Three Layers

```
Claude Code
     ↕
  Masonry          ← the bridge (hooks, routing, typed payloads, DSPy, MCP)
     ↕
 BrickLayer        ← the research engine (campaigns, simulations, agent fleet)
```

**BrickLayer** is the research engine. It runs question campaigns against any target system —
business models, codebases, APIs, smart contracts — maps failure boundaries, and produces
structured findings and synthesis reports. The loop is fully autonomous.

**Masonry** is the bridge between BrickLayer and Claude Code. It carries typed payloads between
agents, routes every request through a four-layer routing engine, fires 22 lifecycle hooks that
manage session state and guardrails, and continuously optimizes agent prompts via DSPy MIPROv2.

**Mortar** is the executive router. Every Claude Code request — coding, research, git, docs,
UI, campaigns — lands at Mortar first. Mortar dispatches to the right specialists in parallel.

**Kiln** (BrickLayerHub) is the Electron desktop app for monitoring campaigns, managing question
queues, viewing findings, and triggering DSPy optimization. It replaced the old web dashboard.

---

## What It Does

### Research Campaigns

BrickLayer asks: *what kills this?* — not *what is optimal?*

```
questions.md → agent picks question → simulate.py → verdict
     ↑                                                  ↓
hypothesis-generator ← findings/*.md ← finding written
```

Every question maps to a failure hypothesis. Every run either confirms the system survives or
finds the exact parameter values that collapse it. The loop never stops until you tell it to.

**10 operational modes**: simulate · diagnose · fix · research · audit · validate · benchmark ·
evolve · monitor · predict · frontier

**30+ verdict types**: HEALTHY · FAILURE · WARNING · INCONCLUSIVE · DIAGNOSIS_COMPLETE ·
FIXED · FIX_FAILED · COMPLIANT · NON_COMPLIANT · CALIBRATED · IMPROVEMENT · REGRESSION ·
IMMINENT · PROBABLE · OK · DEGRADED · ALERT · PROMISING · BLOCKED · and more.

### Development Workflow

When not running campaigns, Masonry drives full software development through Mortar:

| Skill | What it does |
|-------|-------------|
| `/plan` | Explore codebase → write `.autopilot/spec.md` |
| `/build` | Orchestrate worker agents, TDD cycle, commit per task |
| `/ultrawork` | All independent tasks simultaneously |
| `/verify` | Independent review — reads everything, modifies nothing |
| `/fix` | Targeted fix → max 3 cycles → auto-re-verify |
| `/pipeline` | Chain agents/skills in a DAG via `.pipeline/{name}.yml` |
| `/masonry-team` | Partition build across N coordinated Claude instances |
| `/ui-init` | Design system init (tokens, fonts, palette) |
| `/ui-compose` | Agent-mode UI build from design brief |
| `/ui-review` | Visual QA and design compliance |
| `/masonry-run` | Start or resume a BrickLayer 2.0 research campaign |
| `/masonry-status` | Campaign progress, question counts, findings summary |
| `/masonry-fleet` | Agent fleet health — scores, add/retire |

---

## Architecture

Full architecture documentation: [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md)

### Masonry Routing (Four Layers)

Every request routes through four layers. The first match wins:

1. **Deterministic** — slash commands, state files, `**Mode**:` field extraction. Handles 60%+
   of all routing with zero LLM calls.
2. **Semantic** — Ollama cosine similarity (qwen3-embedding:0.6b, threshold 0.70). Zero LLM calls.
3. **Structured LLM** — single Haiku call, JSON-constrained output, for ambiguous requests.
4. **Fallback** — returns `target_agent="user"`, asks for clarification.

### Typed Payload Contracts

All agent-to-agent communication uses strict Pydantic v2 schemas (`extra="forbid"`):

- `QuestionPayload` — input to every specialist agent
- `FindingPayload` — output from every specialist agent (verdict + severity + evidence + confidence)
- `RoutingDecision` — output of the four-layer router
- `DiagnosePayload` / `DiagnosisPayload` — diagnose/fix cycle contracts
- `AgentRegistryEntry` — agent metadata in `masonry/agent_registry.yml`

### DSPy Prompt Optimization

Campaign findings are automatically extracted as DSPy training data. Agents can be optimized via
MIPROv2 — no manually labeled dataset required. Optimized prompts are stored in
`masonry/optimized_prompts/` and injected automatically when agents are spawned.

Trigger from Kiln's "OPTIMIZE" button or via `masonry_optimize_agent` MCP tool.

### 22 Lifecycle Hooks

Active hooks fire on every Claude Code session event:

| Category | Hooks |
|----------|-------|
| Session lifecycle | `masonry-session-start`, `masonry-session-end`, `masonry-session-summary`, `masonry-handoff`, `masonry-pre-compact` |
| Pre-tool guards | `masonry-approver`, `masonry-context-safety` |
| Post-tool actions | `masonry-lint-check`, `masonry-observe`, `masonry-guard`, `masonry-tool-failure`, `masonry-design-token-enforcer`, `masonry-tdd-enforcer`, `masonry-agent-onboard`, `masonry-subagent-tracker`, `masonry-recall-check` |
| Stop guards | `masonry-stop-guard`, `masonry-build-guard`, `masonry-ui-compose-guard`, `masonry-context-monitor` |
| Status | `masonry-statusline` |

Kill switch: `DISABLE_OMC=1` — disables all Masonry hooks. Required when running BrickLayer
campaigns in a subprocess `claude` instance.

---

## Agent Fleet (30+ Agents)

**Research agents**: quantitative-analyst · regulatory-researcher · competitive-analyst ·
benchmark-engineer · research-analyst · compliance-auditor · design-reviewer · evolve-optimizer ·
health-monitor · cascade-analyst · frontier-analyst · diagnose-analyst · fix-implementer

**Meta-agents**: overseer · skill-forge · mcp-advisor · synthesizer-bl2 · git-nerd ·
planner · question-designer-bl2 · hypothesis-generator-bl2

**Dev workflow agents**: spec-writer · developer · test-writer · code-reviewer ·
prompt-engineer · refactorer · security · architect · karen · uiux-master

**Utility**: peer-reviewer · agent-auditor · forge-check · pointer · trowel · mortar

Every agent declares `model:` (opus/sonnet/haiku) in frontmatter. New agents are auto-onboarded
to `masonry/agent_registry.yml` when their `.md` file is written.

---

## Getting Started

### New Research Campaign

```bash
cp -r template/ myproject/
cd myproject/

# 1. Edit project-brief.md
# 2. Drop specs/docs into docs/
# 3. Edit constants.py — real thresholds
# 4. Edit simulate.py — your actual model
# 5. Verify: python simulate.py → should print verdict: HEALTHY

# Generate question bank (in Claude Code):
# Act as the planner agent in .claude/agents/planner.md. [...]
# Act as the question-designer-bl2 agent in .claude/agents/question-designer-bl2.md. [...]

# Start the loop
cd myproject/
git init && git add . && git commit -m "chore: init campaign"
DISABLE_OMC=1 claude --dangerously-skip-permissions \
  "Read program.md and questions.md. Begin the research loop from the first PENDING question. NEVER STOP."
```

### Development Workflow

Open Claude Code in any project and use `/plan` to start. Mortar handles routing to the
right agents automatically.

---

## Requirements

- Claude Code CLI
- Python 3.11+ with `pydantic>=2`, `dspy-ai`, `reportlab`, `uvicorn`, `fastapi`, `httpx`
- Node.js 18+ (Masonry hooks)
- Ollama at `192.168.50.62:11434` (semantic routing — optional, falls back gracefully)
- [System-Recall](https://github.com/Nerfherder16/System-Recall) (optional — cross-session memory at `100.70.195.84:8200`)
- Kiln (BrickLayerHub) — Electron app, primary campaign monitoring UI

---

## Documentation

- [Architecture](docs/architecture/ARCHITECTURE.md) — full three-layer platform architecture
- [Quickstart](docs/guides/QUICKSTART.md) — campaign setup reference
- [Roadmap](ROADMAP.md) — what's built, what's next
- [Changelog](CHANGELOG.md) — all notable changes
- [Project Status](PROJECT_STATUS.md) — active campaigns and branch state

---

## License

MIT
