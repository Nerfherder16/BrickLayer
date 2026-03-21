# BrickLayer 2.0 — Platform Architecture

**Last updated**: 2026-03-21
**Branch**: `bricklayer-meta/mar21`

---

## What This Is

BrickLayer 2.0 is a three-layer AI development platform built on top of Claude Code. It started as
a research loop for stress-testing business models and has grown into a full orchestration platform
combining autonomous campaign research, typed agent-to-agent communication, prompt optimization,
and a complete development workflow.

The three layers are distinct but integrated:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Claude Code                                    │
│                        (the interface / runtime)                            │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                               MASONRY                                       │
│   The bridge / device layer                                                 │
│   • 22 Claude Code hooks (session lifecycle, guards, lint, observe)         │
│   • MCP server (masonry_mcp tools exposed to Claude and Kiln)               │
│   • Typed Pydantic v2 payload schemas (QuestionPayload, FindingPayload, …)  │
│   • Four-layer routing engine (deterministic → semantic → LLM → fallback)   │
│   • DSPy MIPROv2 prompt optimization pipeline                               │
│   • Agent registry (agent_registry.yml — declarative, YAML)                │
│   • Plugin pack architecture (packs/masonry-core/, packs/masonry-frontier/) │
└───────────┬─────────────────────────────────────────────────┬───────────────┘
            │                                                 │
┌───────────▼──────────────┐                 ┌───────────────▼───────────────┐
│        BRICKLAYER        │                 │            MORTAR             │
│   Research / campaign    │                 │      Executive router         │
│   engine                 │                 │                               │
│   • 10-mode question     │                 │   Every Claude Code request   │
│     campaign system      │                 │   routes through Mortar first │
│   • simulate.py runner   │                 │   Mortar dispatches to        │
│   • Specialist agent     │                 │   specialist agents in        │
│     fleet (30+ agents)   │                 │   parallel                    │
│   • Wave-based research  │                 │                               │
│   • findings/ + synthesis│                 │   Four routing layers:        │
│   • DSPy training data   │                 │   1. Deterministic (60%+)     │
│     extracted from       │                 │   2. Semantic (Ollama)        │
│     findings/            │                 │   3. LLM (Haiku)              │
└──────────────────────────┘                 │   4. Fallback (→ user)        │
                                             └───────────────────────────────┘
                                                           │
                                             ┌─────────────▼─────────────────┐
                                             │            KILN               │
                                             │  (BrickLayerHub Electron app) │
                                             │  • Campaign monitoring        │
                                             │  • Question queue management  │
                                             │  • Findings feed              │
                                             │  • DSPy optimization trigger  │
                                             │  • Agent fleet health         │
                                             └───────────────────────────────┘
```

---

## Layer 1: BrickLayer — Research / Campaign Engine

### Campaign Loop

The core loop lives in `bl/campaign.py`. It drives autonomous research by iterating a question
bank, routing each question to a specialist agent, recording the verdict, and generating follow-up
questions from findings.

```
Campaign Loop (bl/campaign.py)
  │
  ├── parse_questions()            → PENDING questions from questions.md
  │     └── _reactivate_pending_external()   # BL 2.0: surfaces PENDING_EXTERNAL
  │
  ├── check_sentinels()
  │     ├── FORGE_NEEDED.md → forge.md (blocking)
  │     ├── AUDIT_REPORT.md → display advisory
  │     └── OVERRIDE verdicts → inject re-exam questions
  │
  ├── _preflight_mode_check()      # blocks unknown modes / missing agents
  │
  └── for each question:
        ├── _load_mode_context()   # loads modes/{mode}.md into agent prompt
        ├── inject session_context # last 2000 chars of session-context.md
        ├── Recall search          # optional: prior findings from System-Recall
        ├── run_question()         # routes to runner (agent/simulate/http/subprocess)
        ├── write_finding()        # findings/{question_id}.md
        ├── update_results_tsv()   # results.tsv append
        ├── record_verdict()       # history.db + regression detection
        ├── generate_followup()    # adaptive drill-down on FAILURE/WARNING
        ├── run_heal_loop()        # BRICKLAYER_HEAL_LOOP=1: self-healing
        ├── store_finding()        # Recall bridge (optional)
        ├── agent_db.record_run()  # score tracking
        └── spawn peer-reviewer   # background quality check

  Wave-end (every N questions + completion):
        ├── [5q]  forge-check (background)
        ├── [10q] agent-auditor (background)
        ├── [10q] overseer if underperformers (background)
        ├── [end] overseer + skill-forge + mcp-advisor (background)
        ├── [end] git-nerd (background) → GITHUB_HANDOFF.md
        ├── [end] synthesize() + parse_recommendation()
        └── [end] generate_hypotheses() if bank exhausted
```

### 10 Operational Modes

Each question in `questions.md` declares a `**Mode**:` field. The runner dispatches to the
corresponding specialist agent with mode-appropriate verdict vocabulary.

| Mode | Verdict Vocabulary | Agent |
|------|--------------------|-------|
| `simulate` | HEALTHY / WARNING / FAILURE / INCONCLUSIVE | quantitative-analyst |
| `diagnose` | DIAGNOSIS_COMPLETE / PENDING_EXTERNAL / INCONCLUSIVE | diagnose-analyst |
| `fix` | FIXED / FIX_FAILED / INCONCLUSIVE | fix-implementer |
| `research` | HEALTHY / WARNING / FAILURE / INCONCLUSIVE | research-analyst |
| `audit` | COMPLIANT / NON_COMPLIANT / PARTIAL / NOT_APPLICABLE | compliance-auditor |
| `validate` | HEALTHY / WARNING / FAILURE / INCONCLUSIVE | design-reviewer |
| `benchmark` | CALIBRATED / UNCALIBRATED / NOT_MEASURABLE | benchmark-engineer |
| `evolve` | IMPROVEMENT / REGRESSION / INCONCLUSIVE | evolve-optimizer |
| `monitor` | OK / DEGRADED / DEGRADED_TRENDING / ALERT / UNKNOWN | health-monitor |
| `predict` | IMMINENT / PROBABLE / POSSIBLE / UNLIKELY | cascade-analyst |
| `frontier` | PROMISING / BLOCKED / WEAK / INCONCLUSIVE | frontier-analyst |

### Core Engine Modules (`bl/`)

| Module | Purpose |
|--------|---------|
| `campaign.py` | Main loop — picks questions, routes runners, records verdicts |
| `questions.py` | questions.md parser, results.tsv I/O, PENDING_EXTERNAL reactivation |
| `config.py` | Project config singleton, `init_project()` |
| `findings.py` | Finding schema, verdict/severity mappings (30+ verdicts, 32 severity entries) |
| `healloop.py` | Self-healing state machine (BRICKLAYER_HEAL_LOOP=1) |
| `recall_bridge.py` | Optional System-Recall integration. Graceful-fail with 2s health timeout |
| `agent_db.py` | Agent performance tracking. Score 0.0–1.0, underperformer threshold 0.40 |
| `skill_forge.py` | Skill registry — distills findings into `~/.claude/skills/` |
| `history.py` | Verdict history ledger (SQLite), regression detection |
| `synthesizer.py` | Wave-end synthesis, STOP/PIVOT/CONTINUE recommendation |
| `hypothesis.py` | Next-wave hypothesis generation (local Ollama LLM) |
| `followup.py` | Adaptive drill-down on FAILURE/WARNING (Q2.4 → Q2.4.1) |
| `crucible.py` | Agent benchmarking via structural rubrics |
| `goal.py` | Goal-directed campaigns from `goal.md` |
| `runners/agent.py` | Spawns specialist agents via `claude -p` |
| `runners/performance.py` | Async HTTP load sweeps |
| `runners/correctness.py` | pytest subprocess runner |
| `runners/http.py` | Single HTTP request checks |
| `runners/subprocess_runner.py` | Arbitrary subprocess with verdict parsing |

### Specialist Agent Fleet

**Domain Agents** (run questions directly):

| Agent | Mode | Description |
|-------|------|-------------|
| `quantitative-analyst` | simulate | Simulations, parameter sweeps, boundary-finding |
| `regulatory-researcher` | research | Legal/compliance research, live web sources |
| `competitive-analyst` | research | Market mapping, analogues, fee benchmarks |
| `benchmark-engineer` | benchmark | Live service benchmarking, performance baselines |
| `diagnose-analyst` | diagnose | Root cause analysis → DIAGNOSIS_COMPLETE + Fix Spec |
| `fix-implementer` | fix | Applies Fix Spec → FIXED or FIX_FAILED |
| `research-analyst` | research | Evidence-based assumption testing |
| `compliance-auditor` | audit | Checklist compliance → COMPLIANT/NON_COMPLIANT/PARTIAL |
| `design-reviewer` | validate | Pre-build design review |
| `evolve-optimizer` | evolve | Optimization with measurement |
| `health-monitor` | monitor | Live metric checks → OK/DEGRADED/ALERT |
| `cascade-analyst` | predict | Cascade risk projection |
| `frontier-analyst` | frontier | Possibility mapping, analogue identification |

**Meta-Agents** (fleet management, wave-end):

| Agent | Trigger | Purpose |
|-------|---------|---------|
| `overseer` | Every 10q + wave end | Repairs underperforming agents, reviews stale skills |
| `skill-forge` | Wave end | Distills findings into `~/.claude/skills/` |
| `mcp-advisor` | Wave end | Maps INCONCLUSIVE/FAILURE patterns → MCP recommendations |
| `synthesizer-bl2` | Wave end | Writes synthesis.md, maintains CHANGELOG/ARCHITECTURE/ROADMAP |
| `git-nerd` | Wave end + on-demand | Commits changes, creates/updates campaign PR, writes GITHUB_HANDOFF.md |
| `planner` | Campaign init | Domain risk ranking (D1–D6), writes CAMPAIGN_PLAN.md |
| `question-designer-bl2` | Campaign init | Generates questions.md with all 10 modes |
| `hypothesis-generator-bl2` | Bank exhausted | Generates Wave N+1 questions from findings |

**Dev Workflow Agents** (spawned by Mortar):

| Agent | Trigger | Purpose |
|-------|---------|---------|
| `spec-writer` | `/plan` | Explores codebase, writes `.autopilot/spec.md` |
| `test-writer` | `/build` per-task | Writes failing tests (RED phase) |
| `developer` | `/build` per-task | Implements code to pass tests (GREEN phase) |
| `code-reviewer` | After developer | Pre-commit quality gate |
| `diagnose-analyst` | DEV_ESCALATE | Root cause on build failures |
| `fix-implementer` | After diagnosis | Targeted fix |

### Source Authority Hierarchy

| Tier | Source | Who edits |
|------|--------|-----------|
| Tier 1 | `project-brief.md`, `docs/` | Human only — ground truth |
| Tier 2 | `constants.py`, `simulate.py` | Human (constants) / Agent (scenario params only) |
| Tier 3 | `findings/`, `questions.md` | Agent output — lower authority |

Tier 1 always overrides Tier 3. If they conflict, the agent writes `CONFLICTS.md`.

---

## Layer 2: Masonry — The Bridge

Masonry is the communication layer between BrickLayer and Claude Code. It handles typed
payloads, routing, hooks, and prompt optimization.

### Typed Payload System (`masonry/src/schemas/payloads.py`)

All agent-to-agent communication uses strict Pydantic v2 models with `extra="forbid"`.

| Schema | Direction | Key Fields |
|--------|-----------|-----------|
| `QuestionPayload` | → specialist agent | `question_id`, `mode`, `wave`, `priority`, `context`, `constraints` |
| `FindingPayload` | ← specialist agent | `verdict`, `severity`, `summary` (≤200 chars), `evidence`, `confidence` |
| `RoutingDecision` | router output | `target_agent`, `layer`, `confidence`, `reason`, `fallback_agents` |
| `DiagnosePayload` | → diagnose-analyst | `symptoms`, `affected_files`, `prior_attempts` |
| `DiagnosisPayload` | ← diagnose-analyst | `root_cause`, `fix_strategy`, `affected_scope`, `confidence` |
| `AgentRegistryEntry` | registry loader | `name`, `model`, `modes`, `capabilities`, `tier`, `optimized_prompt` |

30 valid verdict strings are enforced by `VALID_VERDICTS` frozenset. Passing an invalid verdict
raises a `ValueError` at the model boundary before any agent executes.

### Four-Layer Routing Engine (`masonry/src/routing/`)

Every request routes through four layers in order. The first layer to produce a decision wins.

```
Request text
     │
     ▼
Layer 1: Deterministic (router.py → deterministic.py)
  Handles 60%+ of all requests with zero LLM calls.
  Checks (in order):
    1. Slash command table (/plan → spec-writer, /build → build-workflow, etc.)
    2. .autopilot/mode state file
    3. masonry-state.json campaign state
    4. .ui/mode state file
    5. **Mode**: field extraction from question text
  confidence=1.0 on any match, returns immediately.
     │ (no match)
     ▼
Layer 2: Semantic (semantic.py)
  Ollama cosine similarity at http://192.168.50.62:11434
  Model: qwen3-embedding:0.6b
  Threshold: 0.70
  Computes embeddings for agent descriptions (cached per session).
  Returns best-matching agent if similarity > threshold.
     │ (no match above threshold)
     ▼
Layer 3: Structured LLM (llm_router.py)
  Single Haiku call with JSON-constrained output.
  Selects from registered agents in agent_registry.yml.
  Used for ambiguous requests that don't match deterministic patterns.
     │ (no match or LLM error)
     ▼
Layer 4: Fallback
  target_agent="user", confidence=0.0
  Returns to Claude with request for clarification.
```

### Agent Registry (`masonry/agent_registry.yml`)

Declarative YAML registry for all agents. Each entry contains:

```yaml
- name: quantitative-analyst
  file: agents/quantitative-analyst.md
  model: sonnet          # opus | sonnet | haiku
  description: "..."
  modes: [simulate]
  capabilities: [simulation, parameter-sweep, boundary-finding]
  input_schema: QuestionPayload
  output_schema: FindingPayload
  tier: trusted          # draft | candidate | trusted | retired
  optimized_prompt: null # path to MIPROv2-optimized JSON, if any
```

Tiers progress from `draft` (new, unoptimized) → `candidate` (some campaign runs) → `trusted`
(proven, optimized) → `retired` (replaced or deprecated).

Auto-onboarding: when any `.md` file is written to `agents/` or `~/.claude/agents/`, the
`masonry-agent-onboard.js` hook triggers `masonry/scripts/onboard_agent.py` which extracts
frontmatter and appends a new `AgentRegistryEntry` (tier: "draft") to `agent_registry.yml`.

### DSPy Prompt Optimization Pipeline (`masonry/src/dspy_pipeline/`)

BrickLayer campaigns generate training data that can be used to optimize agent prompts via
MIPROv2, without requiring a separate labeled dataset.

```
Campaign findings (findings/*.md)
         │
         ▼
training_extractor.py
  Parses finding files → extracts:
    question_id, verdict, severity, evidence, summary
  Quality-weighted by agent_db scores
  Output: training_data/{agent}.jsonl
         │
         ▼
signatures.py
  DSPy Signature class per agent:
    Input fields: question_id, question_text, context
    Output fields: verdict, severity, summary, evidence, confidence
  Auto-generated stubs in dspy_pipeline/generated/{agent}.py
         │
         ▼
optimizer.py (MIPROv2)
  Heuristic metric (no LLM judge, keeps cost low):
    - verdict_match   (0.4 weight): exact string match
    - evidence_quality (0.4 weight): length > 100 chars
    - confidence_calibration (0.2 weight): |predicted - 0.75|
  Optimized prompt JSON written to:
    masonry/optimized_prompts/{agent}.json
         │
         ▼
Mortar injects optimized_prompt into agent spawn prompt
  (when AgentRegistryEntry.optimized_prompt is set)
         │
         ▼
drift_detector.py
  Compares current agent outputs to training distribution.
  Flags agents whose verdict distribution has shifted > threshold.
  Surfaced in Kiln as "drift detected" badge.
```

Optimization is triggered from Kiln's "OPTIMIZE" button or via `masonry_optimize_agent` MCP tool.
A DSPy signature stub is auto-generated at agent onboarding time.

### 22 Masonry Hooks

All hooks live in `masonry/src/hooks/`. They fire on Claude Code lifecycle events.
Kill switch: `DISABLE_OMC=1` (env var) disables all hooks — required when running BrickLayer
campaigns in a subprocess `claude` to prevent hook interference.

The kill switch is complemented by auto-detection: hooks also detect whether the current project
is a BrickLayer research project (via `simulate.py`, `questions.md`, or `.claude/agents/` sentinel)
and self-disable for non-BL contexts.

| Hook | Event | Purpose |
|------|-------|---------|
| `masonry-session-start.js` | SessionStart | Restore `.autopilot/`, `.ui/`, campaign mode context. Snapshot dirty files for stop-guard. |
| `masonry-approver.js` | PreToolUse (Write/Edit/Bash) | Auto-approve writes when build/fix/compose mode is active (checks `.autopilot/mode`, `.ui/mode`). 30-min freshness window on progress.json. |
| `masonry-context-safety.js` | PreToolUse (ExitPlanMode) | Block plan-mode exit during active build or high context |
| `masonry-lint-check.js` | PostToolUse (Write/Edit) | ruff + prettier + eslint after every write. Runs formatters in background (non-blocking) to avoid VS Code scroll resets. |
| `masonry-design-token-enforcer.js` | PostToolUse (Write/Edit) | Warn on hardcoded hex colors or banned fonts in UI files |
| `masonry-observe.js` | PostToolUse (Write/Edit) | Async: detect finding files written → extract facts → store to Recall. Activity log. |
| `masonry-guard.js` | PostToolUse (Write/Edit) | Async: 3-strike error fingerprinting. Same error pattern 3x → escalate. |
| `masonry-tool-failure.js` | PostToolUseFailure | Error tracking + 3-strike escalation on tool failures |
| `masonry-subagent-tracker.js` | SubagentStart | Async: track active agent spawns |
| `masonry-agent-onboard.js` | PostToolUse (Write/Edit) | Detect new `agents/*.md` writes → trigger onboard_agent.py → append to registry |
| `masonry-tdd-enforcer.js` | PostToolUse (Write/Edit) | Warn when implementation file is written without corresponding test file |
| `masonry-stop-guard.js` | Stop | Block stop when files modified THIS session are uncommitted. Uses session-start snapshot to distinguish session files from pre-existing dirty state. |
| `masonry-build-guard.js` | Stop | Block stop if `.autopilot/` has PENDING tasks |
| `masonry-ui-compose-guard.js` | Stop | Block stop if `.ui/` compose has pending tasks |
| `masonry-context-monitor.js` | Stop | Async: warn when context exceeds 150K tokens |
| `masonry-statusline.js` | StatusLine | ANSI 24-bit campaign status bar: progress, verdicts, context %, Recall memory count |
| `masonry-register.js` | UserPromptSubmit | Recall context injection, resume detection, guard state flush |
| `masonry-session-end.js` | Stop | Structured session summary → Recall |
| `masonry-session-summary.js` | Stop | Rich session summary extraction |
| `masonry-handoff.js` | Stop | Handoff notes for cross-session continuity |
| `masonry-recall-check.js` | UserPromptSubmit | Pre-prompt Recall health check |
| `masonry-pre-compact.js` | PreCompact | Mid-session checkpoint to Recall (includes assistant responses) |

### MCP Server (`masonry/mcp_server/server.py`)

Exposes BrickLayer campaign operations via Model Context Protocol. Any MCP client (Claude Code,
Kiln, CI tooling) can query and control campaigns without knowing the file layout.

Transport: MCP Python SDK (stdio) with raw JSON-RPC 2.0 fallback (no deps required).

| Tool | Purpose |
|------|---------|
| `masonry_route` | Route a request through the four-layer pipeline |
| `masonry_status` | Current campaign status for a project directory |
| `masonry_optimization_status` | DSPy optimization status for all agents |
| `masonry_onboard` | Trigger agent auto-onboarding for new .md files |
| `masonry_drift_check` | Run drift detection across all registry agents |
| `masonry_optimize_agent` | Trigger MIPROv2 optimization for a specific agent |
| `masonry_registry_list` | List all agents with scores from agent_db.json |

### Plugin Pack Architecture (`masonry/packs/`)

Masonry supports loadable plugin packs. Pack resolution order is defined in
`~/.masonry/config.json` under `activePacks`.

```
packs/
  masonry-core/       — core BL 2.0 skills and agents
    pack.json
    skills/
    agents/
  masonry-frontier/   — frontier-mode exploration extensions
    pack.json
    skills/
    agents/
```

---

## Layer 3: Mortar — Executive Router

Mortar is the entry point for every Claude Code request. It reads the request, determines the
right agents, and dispatches in parallel. Nothing bypasses Mortar for complex work.

```
Every request lands at Mortar
         │
         ├── /plan → spec-writer
         ├── /build → test-writer + developer + code-reviewer (parallel)
         ├── /fix → diagnose-analyst → fix-implementer
         ├── /verify → verify-workflow (read-only)
         ├── /ultrawork → all independent tasks simultaneously
         ├── /pipeline → agent DAG from .pipeline/{name}.yml
         ├── /masonry-run → campaign-conductor (Trowel)
         ├── /masonry-team → N coordinated Claude instances
         ├── coding task → developer + test-writer + code-reviewer (parallel)
         ├── research question → research-analyst + competitive-analyst + others
         ├── campaign / simulation → Trowel (owns full BL 2.0 loop)
         ├── git hygiene → git-nerd
         ├── folder/docs → karen
         ├── UI/design → uiux-master
         └── debugging → diagnose-analyst
```

Mortar uses the same four-layer routing engine as Masonry to determine agent dispatch.

---

## Kiln — BrickLayerHub (Electron App)

Kiln replaces the old web dashboard entirely. It is the primary monitoring and control UI.

Key capabilities:
- Live campaign monitoring: question counts by status, verdict distribution
- Question queue management: add questions mid-loop without touching files
- Findings feed: sorted by severity, click to read full finding
- Agent fleet health: tier filter pills, score cards, verdict accuracy sparkline
- DSPy optimization: "OPTIMIZE" button per agent, drift detection badges
- SignalBar weight visualization: question weight distribution
- RunnerModePills: mode distribution across the question bank

Kiln communicates with BrickLayer through the Masonry MCP server.

---

## Project Directory Structure

```
Bricklayer2.0/
├── bl/                         # Campaign engine (Python package)
│   ├── campaign.py             # Main loop
│   ├── questions.py            # questions.md parser + results.tsv I/O
│   ├── findings.py             # Finding schema, verdict/severity maps
│   ├── healloop.py             # Self-healing state machine
│   ├── recall_bridge.py        # Optional Recall integration
│   ├── agent_db.py             # Agent performance tracking
│   ├── skill_forge.py          # Skill crystallization pipeline
│   ├── history.py              # Verdict history + regression detection
│   ├── synthesizer.py          # Wave-end synthesis
│   ├── hypothesis.py           # Next-wave hypothesis generation
│   ├── followup.py             # Adaptive follow-up question generation
│   ├── crucible.py             # Agent benchmarking
│   ├── goal.py                 # Goal-directed campaigns
│   └── runners/                # Mode-specific runners
│       ├── agent.py
│       ├── performance.py
│       ├── correctness.py
│       ├── http.py
│       └── subprocess_runner.py
├── masonry/                    # Masonry bridge layer
│   ├── src/
│   │   ├── schemas/
│   │   │   ├── payloads.py     # Pydantic v2 payload contracts
│   │   │   └── registry_loader.py
│   │   ├── routing/
│   │   │   ├── router.py       # Four-layer orchestrator
│   │   │   ├── deterministic.py
│   │   │   ├── semantic.py     # Ollama embedding similarity
│   │   │   └── llm_router.py   # Haiku fallback
│   │   ├── dspy_pipeline/
│   │   │   ├── signatures.py   # DSPy Signature classes per agent
│   │   │   ├── training_extractor.py
│   │   │   ├── optimizer.py    # MIPROv2 optimizer
│   │   │   ├── drift_detector.py
│   │   │   └── generated/      # Auto-generated DSPy stubs (one per agent)
│   │   ├── hooks/              # 22 Claude Code lifecycle hooks
│   │   └── scoring/
│   │       └── rubrics.py
│   ├── mcp_server/
│   │   └── server.py           # Masonry MCP server (dual-transport)
│   ├── agent_registry.yml      # Declarative agent registry
│   ├── optimized_prompts/      # MIPROv2-optimized prompt JSON files
│   ├── training_data/          # DSPy training examples (from findings)
│   ├── packs/                  # Plugin packs
│   └── scripts/
│       └── onboard_agent.py    # Auto-onboarding script
├── template/                   # Copy to start a new campaign project
│   ├── simulate.py             # The model (agent edits SCENARIO PARAMETERS only)
│   ├── constants.py            # Immutable rules
│   ├── program.md              # Loop instructions
│   ├── questions.md            # Question bank
│   ├── project-brief.md        # Human ground truth (Tier 1)
│   ├── docs/                   # Supporting documents
│   ├── findings/               # Per-question findings (*.md)
│   ├── results.tsv             # Run log
│   ├── analyze.py              # PDF report generator
│   ├── modes/                  # Mode context files (diagnose.md, fix.md, etc.)
│   └── .claude/agents/         # Project-specific agents
├── .claude/agents/             # Global agent fleet (shared across all campaigns)
├── docs/
│   ├── architecture/
│   │   └── ARCHITECTURE.md     # This file
│   └── guides/
│       ├── QUICKSTART.md
│       └── FRAMEWORK.md
├── dashboard/                  # Legacy web dashboard (superseded by Kiln)
├── tests/                      # Engine test suite
├── README.md
├── CHANGELOG.md
├── ROADMAP.md
└── PROJECT_STATUS.md
```

---

## Key Invariants

These must never be violated:

1. Campaign loop never raises — all errors are caught, logged, and turned into INCONCLUSIVE
2. `session-context.md` writes use `open(..., "a")` — append-only
3. Recall bridge always wrapped in `try/except Exception: pass`
4. Heal loop exits after `max_cycles` — no infinite loop possible
5. Heal intermediate IDs (`_heal{n}_diag`, `_heal{n}_fix`) never collide with real question IDs
6. `_PARKED_STATUSES` is a strict superset of `_PRESERVE_AS_IS`
7. `operational_mode` defaults to `"diagnose"` — maintains BL 1.x backwards compatibility
8. All payload schemas use `extra="forbid"` — unknown fields are rejected at agent boundaries
9. Routing always returns a `RoutingDecision` — Layer 4 fallback guarantees this
