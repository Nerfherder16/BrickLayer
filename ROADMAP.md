# Masonry / BrickLayer 2.0 — Roadmap

**Masonry** is a research-first orchestration layer for Claude Code combining the BrickLayer 2.0
autoresearch campaign system with full development workflow: planning, building, verification,
code review, security audit, and UI composition. BrickLayer is the research engine underneath —
a universal autonomous framework for mapping failure boundaries in any system.

The human defines what matters. Masonry asks the questions, runs the experiments, and reports
what it found.

---

## Status Legend

| Icon | Meaning |
|------|---------|
| ✅ | Complete — shipped and verified |
| 🔄 | In progress — spec written or partially built |
| 📋 | Planned — on the board, not started |
| 💡 | Idea — directional, not committed |

---

## Phase 1 — BL 2.0 Core + Masonry Foundation ✅

Everything here is complete as of 2026-03-17.

### BL 2.0 Engine
| # | Item | Status |
|---|------|--------|
| 1.01 | Python module split — `campaign.py`, `questions.py`, `findings.py`, `runners/`, etc. | ✅ |
| 1.02 | Runner Registry — `Runner(Protocol)` plugin interface; http, subprocess, static, agent runners | ✅ |
| 1.03 | Goal-directed campaigns via `goal.md` — agent generates question set from target + goal | ✅ |
| 1.04 | Adaptive follow-up — FAILURE/WARNING auto-drills down (Q2.4 → Q2.4.1) | ✅ |
| 1.05 | Verdict history + regression detection — flag HEALTHY→FAILURE regressions | ✅ |
| 1.06 | Fix loop — FAILURE → diagnose-analyst → fix-implementer → FIXED/FIX_FAILED | ✅ |
| 1.07 | Recall bridge — optional memory integration. Graceful-fail with 2s health timeout | ✅ |
| 1.08 | Failure taxonomy — `classify_failure_type()` wired into every result | ✅ |
| 1.09 | Confidence signaling — `high|medium|low|uncertain` → routing decisions | ✅ |
| 1.10 | Eval/scoring harness — `eval_score` column on every result, 8 scorer functions | ✅ |
| 1.11 | Agent model routing — `model:` frontmatter on all agents; `--model` passed to `claude -p` | ✅ |
| 1.12 | Introspection tracer — per-step trace `{thought, tool_call, result, tokens, latency}` | ✅ |
| 1.13 | Self-audit campaign (bl2) — 25 waves, 49 fixes, BL 2.0 eating its own dog food | ✅ |

### BL 2.0 Operational Modes
| # | Mode | Status |
|---|------|--------|
| 1.20 | `diagnose` — root cause analysis | ✅ |
| 1.21 | `fix` — targeted repair | ✅ |
| 1.22 | `research` — external knowledge gathering | ✅ |
| 1.23 | `audit` — compliance and standards checking | ✅ |
| 1.24 | `validate` — invariant verification | ✅ |
| 1.25 | `benchmark` — performance measurement | ✅ |
| 1.26 | `evolve` — improvement optimization | ✅ |
| 1.27 | `monitor` — health tracking | ✅ |
| 1.28 | `predict` — failure forecasting | ✅ |
| 1.29 | `frontier` — blue-sky exploration (FRONTIER_VIABLE/PARTIAL/BLOCKED verdicts) | ✅ |

### Agent Fleet (template/)
| # | Agent | Status |
|---|-------|--------|
| 1.40 | `mortar` — campaign conductor. Owns the loop, routes questions, fires sentinels | ✅ |
| 1.41 | `planner` — pre-campaign strategic planner. Writes CAMPAIGN_PLAN.md | ✅ |
| 1.42 | `question-designer-bl2` — BL 2.0 question bank generator | ✅ |
| 1.43 | `hypothesis-generator-bl2` — wave N+1 question generation from findings | ✅ |
| 1.44 | `synthesizer-bl2` — wave synthesizer. Maintains CHANGELOG/ARCHITECTURE/ROADMAP | ✅ |
| 1.45 | `diagnose-analyst` — root cause analysis specialist | ✅ |
| 1.46 | `fix-implementer` — targeted repair specialist | ✅ |
| 1.47 | `research-analyst` — external knowledge specialist | ✅ |
| 1.48 | `compliance-auditor` — audit mode specialist | ✅ |
| 1.49 | `design-reviewer` — architecture and design validation | ✅ |
| 1.50 | `evolve-optimizer` — improvement optimization specialist | ✅ |
| 1.51 | `health-monitor` — system health tracking | ✅ |
| 1.52 | `cascade-analyst` — failure cascade and dependency analysis | ✅ |
| 1.53 | `frontier-analyst` — exploration epistemology, possibility mapping | ✅ |
| 1.54 | `overseer` — fleet manager meta-agent. Repairs underperformers, reviews skills | ✅ |
| 1.55 | `forge-check` — detects agent fleet gaps, writes FORGE_NEEDED.md sentinel | ✅ |
| 1.56 | `agent-auditor` — audits agent fleet quality, writes AUDIT_REPORT.md | ✅ |
| 1.57 | `peer-reviewer` — re-runs tests, appends CONFIRMED/CONCERNS/OVERRIDE | ✅ |
| 1.58 | `skill-forge` — knowledge crystallization agent. Distills findings into `~/.claude/skills/` | ✅ |
| 1.59 | `mcp-advisor` — tooling gap analyst. Maps failures to missing MCP servers | ✅ |
| 1.60 | `git-nerd` — autonomous GitHub operations. Creates PR, writes GITHUB_HANDOFF.md | ✅ |
| 1.61 | `code-reviewer` — pre-commit quality gate | ✅ |
| 1.62 | `kiln-engineer` — specialist for Kiln (BrickLayerHub Electron app) | ✅ |
| 1.63 | `quantitative-analyst`, `regulatory-researcher`, `competitive-analyst`, `benchmark-engineer` — domain specialists | ✅ |

### Masonry Dev Workflow
| # | Item | Status |
|---|------|--------|
| 1.70 | `/plan` skill — interactive spec creation, writes `.autopilot/spec.md` | ✅ |
| 1.71 | `/build` skill — orchestrator + worker agent pattern, TDD, commits per task | ✅ |
| 1.72 | `/verify` skill — independent verification, never modifies source | ✅ |
| 1.73 | `/fix` skill — targeted fix, max 3 cycles, auto-re-verifies | ✅ |
| 1.74 | `/masonry-run`, `/masonry-status`, `/masonry-init` — campaign lifecycle skills | ✅ |
| 1.75 | `/masonry-fleet` — agent fleet health, add/retire agents | ✅ |
| 1.76 | `/masonry-code-review` — severity-tiered code review | ✅ |
| 1.77 | `/masonry-security-review` — OWASP Top 10 security audit | ✅ |
| 1.78 | `/ui-init`, `/ui-compose`, `/ui-review`, `/ui-fix` — UI design workflow | ✅ |

### Masonry Hooks (active in settings.json)
| # | Hook | Status |
|---|------|--------|
| 1.80 | `masonry-session-start.js` — SessionStart: restore autopilot/UI/campaign mode context | ✅ |
| 1.81 | `masonry-approver.js` — PreToolUse: auto-approve writes in build/fix/compose mode | ✅ |
| 1.82 | `masonry-context-safety.js` — PreToolUse: block plan-mode exit during active build | ✅ |
| 1.83 | `masonry-lint-check.js` — PostToolUse: ruff + prettier + eslint after every write | ✅ |
| 1.84 | `masonry-design-token-enforcer.js` — PostToolUse: warn on hardcoded hex in UI files | ✅ |
| 1.85 | `masonry-observe.js` — PostToolUse: campaign state observation (async) | ✅ |
| 1.86 | `masonry-guard.js` — PostToolUse: edit guard, 3-strike error fingerprinting | ✅ |
| 1.87 | `masonry-tool-failure.js` — PostToolUseFailure: error tracking + 3-strike escalation | ✅ |
| 1.88 | `masonry-subagent-tracker.js` — SubagentStart: track active agent spawns (async) | ✅ |
| 1.89 | `masonry-stop-guard.js` — Stop: block on uncommitted git changes | ✅ |
| 1.90 | `masonry-build-guard.js` — Stop: block if `.autopilot/` has pending tasks | ✅ |
| 1.91 | `masonry-ui-compose-guard.js` — Stop: block if `.ui/` compose has pending tasks | ✅ |
| 1.92 | `masonry-context-monitor.js` — Stop: warn when context window exceeds 150K tokens | ✅ |
| 1.93 | `masonry-statusline.js` — StatusLine: ANSI 24-bit campaign bar with progress, verdicts, context % | ✅ |

### Dashboard
| # | Item | Status |
|---|------|--------|
| 1.95 | FastAPI backend — question bank API, live status, `GET /api/agents` | ✅ |
| 1.96 | React frontend — question queue, findings panel, project switcher | ✅ |
| 1.97 | Agent Fleet tab — tier filter pills, score cards, summary footer | ✅ |

---

## Phase 2 — Masonry Ecosystem Expansion ✅

All 9 tasks complete (shipped across two sessions, Mar 16 2026).

### Rich HUD + Execution Engines
| # | Item | Status |
|---|------|--------|
| ~~2.01~~ | ~~Rich statusline — git branch/dirty, build task, UI mode, active agent count~~ | ✅ |
| ~~2.02~~ | ~~File ownership in `/build` — `owned_by` + `lock_files[]` in progress.json schema~~ | ✅ |
| ~~2.03~~ | ~~`/ultrawork` skill — all independent tasks spawned simultaneously, refill-pool execution~~ | ✅ |
| ~~2.04~~ | ~~`/pipeline` skill — chain agents/skills in a DAG with data passing (`.pipeline/*.yml`)~~ | ✅ |
| ~~2.05~~ | ~~`/masonry-team` skill — partition build across N coordinated Claude instances~~ | ✅ |

### Fleet CLI + Plugin Architecture
| # | Item | Status |
|---|------|--------|
| ~~2.06~~ | ~~`masonry-fleet-cli.js` — `status`, `add`, `retire`, `regen` commands~~ | ✅ |
| ~~2.07~~ | ~~Plugin pack architecture — `packs/masonry-core/`, `packs/masonry-frontier/` with `pack.json`~~ | ✅ |
| ~~2.08~~ | ~~`activePacks` in `~/.masonry/config.json` — pack resolution order~~ | ✅ |

### Skill Catalog Update
| # | Item | Status |
|---|------|--------|
| ~~2.09~~ | ~~`~/.claude/CLAUDE.md` updated with ultrawork/pipeline/masonry-team in skills table~~ | ✅ |
| ~~2.10~~ | ~~Test suite: `test_masonry_hud.js`, `test_masonry_fleet_cli.js` (13 tests passing)~~ | ✅ |

---

## Phase 3 — Target Breadth (Runner Expansion) ✅

Each item adds a new class of targets BrickLayer can run against.

| # | Item | Target Class | Status |
|---|------|-------------|--------|
| ~~3.01~~ | ~~`browser` runner — Playwright-driven UI interaction testing~~ | ~~Web UIs~~ | ✅ |
| ~~3.NEW~~ | ~~`simulate` runner — parameter sweep + boundary finding on simulate.py~~ | ~~BL campaigns~~ | ✅ |
| ~~3.02~~ | ~~`benchmark` runner — ML model ablation, latency, accuracy sweeps~~ | ~~Ollama / OpenAI models~~ | ✅ |
| ~~3.03~~ | ~~`document` runner — completeness/accuracy/consistency checks on docs vs code~~ | ~~API docs, READMEs~~ | ✅ |
| ~~3.04~~ | ~~`contract` runner — Solana/Anchor invariant checking and edge case fuzzing~~ | ~~Smart contracts~~ | ✅ |
| ~~3.05~~ | ~~Baseline anchoring — lock known-good snapshot, every run diffs against it. Deploy gate~~ | ~~All runners~~ | ✅ |
| ~~3.06~~ | ~~Multi-agent swarm — parallel perf/correctness/security/quality campaigns~~ | ~~All runners~~ | ✅ |
| ~~3.07~~ | ~~GitHub Actions hook — run campaign on PR, post findings as review comments~~ | ~~CI/CD~~ | ✅ |

---

## Phase 4 — Masonry Recall Integration ✅

Masonry uses Recall 1.x (the deployed FastAPI + Qdrant + Neo4j system at `100.70.195.84:8200`).
All 5 items shipped Mar 18 2026.

| # | Item | Status |
|---|------|--------|
| ~~4.01~~ | ~~Masonry observe-edit hook — improved fact extraction from file edits~~ | ✅ |
| ~~4.02~~ | ~~Rich session summaries — structured knowledge extraction at session end~~ | ✅ |
| ~~4.03~~ | ~~`masonry-statusline.js` Recall integration — `↑N mem` segment in HUD~~ | ✅ |
| ~~4.04~~ | ~~Cross-project memory transfer — `bl/recall_bridge.py` with search/store/analogous queries~~ | ✅ |
| ~~4.05~~ | ~~Recall-backed question generation — `planner` queries Recall before domain ranking~~ | ✅ |

---

## Phase 5 — Autonomy ✅

| # | Item | Status |
|---|------|--------|
| ~~5.01~~ | ~~Self-improving question banks — `bl/question_weights.py`, verdict history, weight-sorted dispatch~~ | ✅ |
| ~~5.02~~ | ~~Hypothesis generation from git diffs — `bl/git_hypothesis.py` + `bl/cli/git_hypothesis_cmd.py`~~ | ✅ |
| ~~5.03~~ | ~~Natural language entry point — `bl/nl_entry.py`, 16 techs, 10 intents, `/masonry-nl` skill~~ | ✅ |
| ~~5.04~~ | ~~Kiln (BrickLayerHub) — SignalBar weight visualization, RunnerModePills, git hypothesis badge~~ | ✅ |
| ~~5.05~~ | ~~MCP server for Masonry — 8 tools, dual-transport (SDK + raw JSON-RPC 2.0 fallback)~~ | ✅ |

---

## Phase 6 — Campaign Quality Intelligence 📋

Inspired by the NVIDIA Multi-Agent Intelligent Warehouse (MAIW) architecture (Mar 2026).
Goal: make BrickLayer's research loop self-aware about output quality, not just output volume.

**Rated benefit: 7/10.** Phases 1–5 built the engine and expanded reach. Phase 6 makes verdicts
trustworthy at scale — the difference between "we ran 200 questions" and "we ran 200 questions
and we know which ones we can trust." Most impactful when campaigns exceed a single wave.

### 6.01 — Verdict Confidence Tiers 📋

Replace binary verdicts with a confidence-weighted tier system.

| # | Item | Status |
|---|------|--------|
| 6.01a | Add `confidence: 0.0–1.0` field to finding frontmatter | ✅ |
| 6.01b | Add `needs_human: bool` flag — auto-set when confidence < 0.35 | 📋 |
| 6.01c | Kiln: render confidence as fill bar on finding cards | 📋 |
| 6.01d | Dashboard: filter INCONCLUSIVE by confidence band | 📋 |

### 6.02 — LLM-as-Judge (peer reviewer scoring) 📋

`peer-reviewer` currently appends CONFIRMED/CONCERNS/OVERRIDE but assigns no numeric quality
signal. Mortar treats all INCONCLUSIVEs identically regardless of review outcome.

| # | Item | Status |
|---|------|--------|
| 6.02a | Extend `peer-reviewer` to emit `quality_score: 0.0–1.0` in finding frontmatter | 📋 |
| 6.02b | Mortar: re-queue INCONCLUSIVE findings where quality_score < 0.4 with narrowed scope | 📋 |
| 6.02c | `question_weights.py`: incorporate quality_score into weight update formula | 📋 |

### 6.03 — Question Sharpening (feedback loop) 📋

hypothesis-generator currently only appends new questions. Low-confidence findings should
retroactively narrow *remaining PENDING questions* in the same domain.

| # | Item | Status |
|---|------|--------|
| 6.03a | `bl/question_sharpener.py` — reads PENDING questions + recent INCONCLUSIVE findings, rewrites scope | ✅ |
| 6.03b | Wave synthesizer calls sharpener before writing synthesis.md | 📋 |
| 6.03c | Dashboard: show "sharpened" badge on questions that were narrowed | 📋 |

### 6.04 — Shared Campaign Context Injection 📋

Each agent spawned by Mortar currently starts cold, re-reading findings/ and questions.md.
A `campaign-context.md` written at wave start would give all agents consistent shared state.

| # | Item | Status |
|---|------|--------|
| 6.04a | Mortar writes `campaign-context.md` at wave start: project summary + top 5 findings + open hypotheses | 📋 |
| 6.04b | All agent spawn prompts prepend campaign-context.md content | 📋 |
| 6.04c | campaign-context.md auto-refreshed after every 10 findings | 📋 |

### 6.05 — Agent Performance Time-Series 📋

`agent_db.json` stores static scores. No trend data — Kiln can't show if an agent is improving
or drifting. Needed for overseer to make meaningful rewrite decisions.

| # | Item | Status |
|---|------|--------|
| 6.05a | Extend `agent_db.json` schema: `runs: [{timestamp, verdict, duration_ms, quality_score}]` | 📋 |
| 6.05b | Kiln: verdict accuracy sparkline per agent (last 20 runs) | 📋 |
| 6.05c | `agent-auditor`: flag agents with declining accuracy trend (last 5 vs prior 5) | 📋 |

### 6.06 — MCP Tool Manifest 📋

Each agent declares its own tool access independently. Tool descriptions drift. New tools added
to MCP aren't surfaced to existing agents.

| # | Item | Status |
|---|------|--------|
| 6.06a | `template/.claude/agents/tools-manifest.md` — canonical tool list with descriptions | ✅ |
| 6.06b | Agent frontmatter: `tools: [recall, simulate, filesystem]` declaration | 📋 |
| 6.06c | `forge-check` validates agents aren't missing tool declarations | 📋 |

---

## Active Campaigns

| Project | Location | Status | Wave |
|---------|----------|--------|------|
| `bl2` self-audit | `projects/bl2/` | **STOP** — 49 fixes, 25 waves | Wave 25 complete |
| `agent-meta` | `projects/agent-meta/` | **STOP** — 28/28 HEALTHY, 96.1/100 avg | Wave 1+2 complete |
| `recall-arch-frontier` | `recall-arch-frontier/` | **STOP** — build Recall 2.0 | Wave 34 complete |
| `masonry` (bricklayer-meta) | `masonry/` | **STOP** — 28 findings, agent mgmt overhaul shipped | Wave 2 complete (2026-03-21) |

---

## Coordination Board

Items claimed or in active flight. Check before starting new work.

| # | Area | Work Item | Status | Claimed By |
|---|------|-----------|--------|------------|
| C-01 through C-34 | Core engine | See CHANGELOG.md for full history | **ALL DONE** | Various |
| C-35 | Masonry Phase 2 | Ecosystem expansion — ultrawork, pipeline, team, fleet CLI, packs | **SPEC WRITTEN** | conv:mar17 |
| C-36 | Recall 2.0 | Build Recall 2.0 Rust engine | **FREE** | — |
| C-37 | Runners | `browser` runner — Playwright UI testing | **FREE** | — |
| C-38 | Runners | `benchmark` runner — ML model evaluation | **FREE** | — |
| C-39 | Runners | `document` runner — doc accuracy vs code | **FREE** | — |
| C-40 | Runners | `contract` runner — Solana/EVM invariant checking | **FREE** | — |
| C-41 | CI/CD | GitHub Actions hook — campaign on PR | **FREE** | — |
| C-42 | MCP tooling | FastMCP 3.1 Python MCP server for new BL tools | **FREE** | — |

---

## Phase 10 — FastMCP 3.1 Python MCP Tools 💡

**Goal**: Use FastMCP 3.1 (Python) to build new Masonry MCP tools in Python rather than extending
`masonry-mcp.js`. The existing Node.js server stays unchanged — new tools are additive.

**Motivation**: masonry-mcp.js is working but is a maintenance burden in a Python-first project.
FastMCP 3.1 adds composable server mounting (`namespace=`) and `FastMCPOpenAPI` — wrap any REST
API as MCP tools with zero boilerplate. In-process transport enables proper unit testing.

**Candidate new tools** (Python-native, no equivalent in masonry-mcp.js):
- `masonry_karen` — invoke karen agent tasks (init-docs, update-changelog, audit-folder) from MCP
- `masonry_retrospective` — trigger retrospective analysis and return structured findings
- `masonry_registry` — query/rebuild registry.json, list agents with scores from agent_db.json
- `masonry_retro_apply` — read retro-actions.md and generate a spec for /build

**Architecture**: FastMCP 3.1 server at `masonry/src/mcp_python/server.py`, registered separately
in `~/.claude.json`. Does NOT replace masonry-mcp.js — both run in parallel.

**Prerequisite**: `pip install fastmcp>=3.1.0`

| # | Item | Status |
|---|------|--------|
| 10.01 | `masonry/src/mcp_python/server.py` — FastMCP 3.1 server skeleton | 💡 |
| 10.02 | `masonry_karen` tool — wraps karen agent task modes | 💡 |
| 10.03 | `masonry_retrospective` tool — post-campaign quality report | 💡 |
| 10.04 | `masonry_registry` tool — agent catalog queries | 💡 |
| 10.05 | Register in `~/.claude.json` alongside masonry-mcp.js | 💡 |
| 10.06 | In-process tests via FastMCP test transport | 💡 |

---

## Phase 11 — ADBP Monte Carlo Simulation Engine (Rust)

**Goal:** Replace ADBP's deterministic point-estimate simulation with a Rust-powered MC engine that surfaces probability distributions, multi-party scoring, and Pareto-optimal operating conditions.

| ID | Task | Status |
|----|------|--------|
| 11.01 | Classify `adbp_constants.py` into Tier 1 (contract), Tier 2 (policy), Tier 3 (behavioral estimates) | 💡 |
| 11.02 | Create `policy_params.py` and `behavioral_params.py` alongside `adbp_constants.py` | 💡 |
| 11.03 | Scaffold Rust crate (`adbp/mc/`) with maturin + PyO3 | 💡 |
| 11.04 | Port ADBP economic model to Rust (`model.rs`) | 💡 |
| 11.05 | Implement distribution samplers (`distributions.rs`) — lognormal, beta, normal | 💡 |
| 11.06 | MC runner (`runner.rs`) — 10K samples, parallel via rayon | 💡 |
| 11.07 | Multi-objective scoring (`scoring.rs`) — employee/vendor/treasury as continuous 0→1 | 💡 |
| 11.08 | Pareto frontier analysis (`pareto.rs`) | 💡 |
| 11.09 | PyO3 bindings (`lib.rs`) — `import adbp_mc; adbp_mc.run(params, n_samples=10_000)` | 💡 |
| 11.10 | `simulate_mc.py` wrapper — BL-compatible output (p10/p50/p90 per metric) | 💡 |
| 11.11 | BL MCP integration — `masonry_run_simulation` gains `monte_carlo_samples` param | 💡 |

**Architecture:** PyO3 + maturin. Python API unchanged for BL agents. Rust handles all MC computation.
**Prerequisite:** Read `ADBP_Final_Model_Legal_2.pdf` to confirm Tier 1 contract rule classification.

---

## Phase 12 — Mortar/Trowel Split ✅

**Goal:** Split the 599-line monolithic Mortar agent into a lean session router (Mortar) and a dedicated campaign conductor (Trowel). Fixes Mortar never activating — it was too heavy to apply to every prompt.

| ID | Task | Status |
|----|------|--------|
| 12.01 | Rewrite Mortar as ~120-line lean session router — detects campaign vs. dev context, hands campaigns to Trowel immediately | ✅ |
| 12.02 | Create Trowel agent (~350 lines) — owns full BL 2.0 research loop, wave sentinels, agent tracking, wave-end sequence | ✅ |
| 12.03 | Sync both agents to `template/.claude/agents/`, `.claude/agents/`, `projects/bl2/.claude/agents/` | ✅ |
| 12.04 | Wire `/hats` (Six Thinking Hats) into Trowel Strategic Decision Support section | ✅ |

---

## Phase 13 — BL Structural Gaps 📋

**Goal:** Close three structural gaps identified from campaign feedback: missing model design log, no model versioning to correlate findings with sim state, and no sweep validation gate.

| ID | Task | Status |
|----|------|--------|
| 13.01 | `model_assumptions.md` pattern — Trowel writes/maintains a design decisions log per project; agents append when they change model logic; helps future agents understand why the model is structured the way it is | 📋 |
| 13.02 | Model versioning — compute a hash of `simulate.py` + `constants.py` state at question time; embed in each finding as `**Model hash**:`; enables correlation between findings and the model version that produced them | 📋 |
| 13.03 | Sweep validation gate — before running any sweep, verify the parameter exists in `simulate.py`'s SCENARIO PARAMETERS block; block with clear error if not found; prevents "finding" on a parameter that never wired up | 📋 |

---

## Phase 14 — Campaign Working Memory 📋

**Goal:** Close the context pressure and inter-agent communication gaps identified in research finding R-shared-scratchpad. BL 2.0's blackboard architecture is correct in shape but needs mid-wave compression, a typed signal board, and Recall enforcement to scale past ~30 questions per campaign without quality degradation.

**New agent**: `pointer` — lightweight mid-wave summarizer. Named after the masonry pointing tool that finishes mortar joints. Fires every 8 questions, produces a compact checkpoint file that subsequent agents read instead of the full findings corpus.

| ID | Task | Status |
|----|------|--------|
| 14.01 | `scratch.md` — typed signal board at project root; 4 signal types (WATCH, BLOCK, DATA, RESOLVED); rolling 15-entry cap; Trowel trims RESOLVED rows after each question completes | ✅ |
| 14.02 | `pointer` agent (~80 lines) — mid-wave summarizer; reads findings since last checkpoint; produces `findings/checkpoints/wave{N}-q{K}.md` with verdicts table, failure boundaries, cross-domain conflicts, and priorities for remaining questions | ✅ |
| 14.03 | Trowel sentinel: fire Pointer every 8 questions; subsequent agents receive latest checkpoint + last 3 full findings + domain findings — not the full corpus | 📋 |
| 14.04 | File structure reorganization — wave-partitioned findings (`findings/wave{N}/`), `findings/checkpoints/`, `findings/synthesis/`; `brief/`, `sim/`, `campaign/` subdirs; enforced agent read order in Trowel spawn prompts | ✅ |
| 14.05 | Recall as orchestrator hook — move `recall_store` out of agent prompts into Trowel post-finding sequence; store executes from parsed JSON block regardless of agent behavior | ✅ |
| 14.06 | JSON output validation — Trowel parses JSON block before marking DONE; malformed → `INCONCLUSIVE-FORMAT-ERROR` + single re-invoke; prevents silent findings corpus corruption | ✅ |

---

## Phase 15 — Session Intelligence 📋

**Goal:** Close structural gaps identified in the OMC comparison (R-omc-structural-comparison.md). OMC's session-quality layer has two capabilities BL 2.0 lacks: hot-path awareness (which files are touched most, cross-session) and dead-reference hygiene. These are low-cost, high-signal additions that improve agent context quality.

| ID | Task | Status |
|----|------|--------|
| 15.01 | Hot path tracker — `masonry-session-start.js` accumulates a file access frequency map across sessions to `~/.masonry/state/{slug}/hotpaths.json`; top-5 most-edited files injected into session context at startup; helps agents avoid re-discovering the same structural facts | 📋 |
| 15.02 | Dead reference audit — scan all agent `.md` files, hooks, and CLAUDE.md for references to removed tools/agents/env vars (e.g. `oh-my-claudecode`, `DISABLE_OMC`); auto-flag on `masonry-session-start.js`; emit `[Masonry] STALE_REF:` warning | 📋 |

---

## Phase 16 — Full-Fleet DSPy Training ✅

**Shipped**: 2026-03-21

**Goal:** Extend the existing DSPy training pipeline (score_findings.py → training_extractor.py → optimizer.py) to cover ALL 46 agents, not just findings-writing agents. Previously ~20 agents had no training signal and remained at `tier: draft` indefinitely.

**What already exists (do NOT rebuild):**
- `masonry/scripts/score_findings.py` — findings-based scoring ✅
- `masonry/src/dspy_pipeline/training_extractor.py` — findings → DSPy training JSONL ✅
- `masonry/src/dspy_pipeline/optimizer.py` — MIPROv2 optimization ✅
- `masonry/src/dspy_pipeline/drift_detector.py` — performance drift monitoring ✅
- `masonry/scripts/run_vigil.py` — VIGIL fleet health (Roses/Buds/Thorns) ✅
- `masonry/src/dspy_pipeline/generated/` — 46 DSPy signature stubs (one per agent) ✅
- Kiln OPTIMIZE button + `optimize-agent` IPC handler ✅

**What's missing:**

### 16.01 — Hardcode Scoring Rubrics 📋
`masonry/src/scoring/rubrics.py` — canonical scoring invariants per agent category. These NEVER change without human review — they are the definition of "good output" for each type.

| # | Item | Status |
|---|------|--------|
| 16.01a | `rubrics.py` — findings category: confidence calibration (40), evidence quality (40), verdict clarity (20), min_score=60 | ✅ |
| 16.01b | `rubrics.py` — code category: tests_pass (50), lint_clean (20), no_regression (30), min_score=70 | ✅ |
| 16.01c | `rubrics.py` — ops category: operation_succeeded (60), human_accepted (40), min_score=60 | ✅ |
| 16.01d | `rubrics.py` — routing category: correct_agent_dispatched (70), downstream_success (30), min_score=65 | ✅ |

### 16.02 — Backfill Agent Attribution 📋
Existing findings from bricklayer-meta and prior campaigns show `agent: unknown` in scored_findings.jsonl because the `**Agent**:` field wasn't in the finding template until Wave 3.

| # | Item | Status |
|---|------|--------|
| 16.02a | `masonry/scripts/backfill_agent_fields.py` — reads each finding, infers agent from question_id domain prefix (Q1.x→quantitative-analyst, Q2.x→regulatory-researcher, Q3.x→competitive-analyst, etc.), patches `**Agent**:` line if missing | ✅ |
| 16.02b | Re-run `score_findings.py` after backfill — verify attributed count > 0 per agent | ✅ |

### 16.03 — Code Agent Signal 📋
Agents: `developer`, `test-writer`, `fix-implementer`, `code-reviewer`
Signal source: `.autopilot/progress.json` + `build.log` across all git branches

| # | Item | Status |
|---|------|--------|
| 16.03a | `masonry/scripts/score_code_agents.py` — walks all branches for `.autopilot/` dirs, scores developer on test pass rate, code-reviewer on catch rate (issues found / issues actually present) | ✅ |
| 16.03b | Extend `masonry-subagent-tracker.js` to append to `masonry/routing_log.jsonl` on every SubagentStart | ✅ |

### 16.04 — Ops Agent Signal 📋
Agents: `git-nerd`, `karen`, `forge-check`, `overseer`
Signal source: git log outcomes, FORGE_NEEDED.md acceptance history, AUDIT_REPORT.md action rate

| # | Item | Status |
|---|------|--------|
| 16.04a | `masonry/scripts/score_ops_agents.py` — reads git log for commit success from git-nerd; reads whether FORGE_NEEDED.md recommendations were acted on (agent files created); reads whether AUDIT_REPORT.md retirements were applied | ✅ |
| 16.04b | karen scoring: track whether docs written by karen (CHANGELOG, ARCHITECTURE, ROADMAP) were committed without human edits (proxy for acceptance) | ✅ |

### 16.05 — Routing Signal 📋
Agents: `mortar`, `trowel`
Signal source: `masonry/routing_log.jsonl` (needs 16.03b), downstream outcome

| # | Item | Status |
|---|------|--------|
| 16.05a | `masonry/scripts/score_routing.py` — reads routing_log.jsonl, checks whether dispatched agent produced a finding/commit/artifact (downstream success), scores mortar/trowel on accuracy | ✅ |
| 16.05b | Extend `masonry-subagent-tracker.js` to write routing_log.jsonl start entries per SubagentStart | ✅ |

### 16.06 — Unified Aggregator 📋

| # | Item | Status |
|---|------|--------|
| 16.06a | `masonry/scripts/score_all_agents.py` — calls all four scorers, merges output into `masonry/training_data/scored_all.jsonl`, updates `last_score` in `agent_registry.yml` | ✅ |
| 16.06b | Kiln: wire "Score All" button to `score_all_agents.py` via new `score-all-agents` IPC handler | ✅ |
| 16.06c | `masonry/scripts/run_vigil.py` extended to read `scored_all.jsonl` — VIGIL health for ALL 46 agents | ✅ |

**Initial training run sequence** (once 16.01–16.06 are built):
```bash
# 1. Backfill agent attribution in existing findings
python masonry/scripts/backfill_agent_fields.py

# 2. Score all agents across all signal types
python masonry/scripts/score_all_agents.py
# → masonry/training_data/scored_all.jsonl

# 3. Run VIGIL to see fleet health baseline
python masonry/scripts/run_vigil.py

# 4. From Kiln: OPTIMIZE each agent with ≥10 training examples
# (Use Kiln fleet page → OPTIMIZE button per agent)

# 5. Run drift detector to validate improvement
python masonry/src/dspy_pipeline/drift_detector.py
```

**Prerequisite**: Run at least one full campaign after the `**Agent**:` field requirement was added (2026-03-21) to accumulate attributed findings before step 1 is useful.

---

## Training Branch — BL Fine-Tuning Pipeline 📋

**Goal:** Wire BrickLayer's campaign output into a fine-tuning pipeline that trains agent-specific
LoRA adapters on real campaign examples, then loads them into Ollama for local inference. The Windows
side installs bridge files and patches existing scripts; the Linux LXC side runs the actual training.

**Plan source:** `TRAINING_BRANCH_PLAN.md` (created 2026-03-25)

**Execution order:** B4 → A1 → A2 → A3 → B5 → B6

| ID | Task | Scope | Status |
|----|------|-------|--------|
| B4 | Install bridge files — `bl/training_schema.py`, `bl/training_export.py`, `masonry/src/hooks/masonry-training-export.js` | Windows | 📋 |
| A1 | Simplify Mortar dispatch to 5-condition binary — remove routing tables, output `{ target, reason }` | Windows | 📋 |
| A2 | Create `rough-in` agent — dev workflow orchestrator mirroring Trowel; register in `agent_registry.yml` | Windows | 📋 |
| A3 | Intra-campaign Recall feedback loop — `get_campaign_context()` + `_write_recall_degraded()` in `bl/recall_bridge.py`; inject prior findings into Trowel question dispatch | Windows | 📋 |
| B5 | Patch `masonry/scripts/score_all_agents.py` — add auto-export block after scoring when `BRICKLAYER_TRAINING_DB` is set | Windows | 📋 |
| B6 | Register `masonry-training-export.js` in Stop hooks array in `~/.claude/settings.json` (async, 65s timeout) | Windows | 📋 |

**Out of scope for this repo** (Linux LXC / System-Recall): B1 env checks, B2 pytest setup,
B3 .env config, B7–B11 smoke tests through adapter load, A4 importance-weighted retrieval.

---

## Design Principles

1. **Universal verdict envelope.** Every runner, every target, every question type produces the same `{verdict, summary, data, details}` shape.
2. **Questions are the product.** The question bank has compounding value. A good question asked 100 times across 100 projects is worth more than 100 one-off tests.
3. **Humans set goals, agents set questions.** The human knows what matters. The agent knows what to ask technically.
4. **Verdicts must be falsifiable.** HEALTHY requires specific evidence. FAILURE requires a reproduction path.
5. **Cheap at scale beats thorough occasionally.** 500 fast questions overnight finds more than 5 exhaustive questions quarterly.
6. **Failure boundaries, not pass/fail.** The goal is not "does it work?" — it's "where does it stop working?"
7. **Lightest path that preserves quality.** Direct action for trivial tasks, agents for substantive work.

---

## Target Universe

| Category | Examples |
|----------|---------|
| **APIs** | REST, GraphQL, WebSocket, gRPC |
| **Codebases** | Python, Rust, Kotlin, TypeScript, Solidity |
| **Test suites** | pytest, cargo test, jest, go test, anchor test |
| **ML models** | Ollama, OpenAI, HuggingFace — accuracy, latency, regression |
| **Documents** | API docs, READMEs, legal specs, architecture docs |
| **Smart contracts** | Anchor programs, EVM contracts, invariant checking |
| **Web UIs** | Playwright-driven interaction and visual regression |
| **Simulations** | Business models, financial projections, game theory |
| **Pipelines** | CI/CD, data pipelines, ETL |
| **Infrastructure** | Docker, Proxmox, CasaOS — health and config drift |

---

## Current Integrations

- **Recall** (FastAPI + Qdrant + Neo4j, Tailscale `100.70.195.84:8200`) — memory backbone
- **Exa MCP** — semantic research for question generation and finding enrichment
- **Firecrawl MCP** — documentation crawling for document runner
- **GitHub MCP** — PR creation and campaign result posting

## Planned Integrations

- **Recall 2.0** (Rust) — replacement for current FastAPI Recall
- **GitHub Actions** — run campaign on every PR, post findings as review comments
- **BrowserMCP** — browser runner for web portal testing
- **ADBP Solana programs** — contract runner against benefit-credits and redemption programs
