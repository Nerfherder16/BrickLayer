# Masonry Architecture

## System Overview

Masonry is the orchestration platform sitting between Claude Code and BrickLayer 2.0. It is a Node.js MCP server combined with a Python routing engine, a hook system, and a fleet management layer. Claude Code talks to Masonry via MCP tool calls and Claude Code hook events; Masonry in turn routes work to the appropriate BrickLayer agent fleet and provides memory persistence via Recall.

The three-layer model:

```
Claude Code (UI + REPL)
      |
   Masonry           -- MCP server, hooks, routing engine, DSPy, agent registry
      |
 BrickLayer 2.0      -- research campaigns, simulations, findings, synthesis
```

Masonry does not replace BrickLayer 2.0's core evaluation logic. It provides the platform layer: session continuity, intelligent routing, auto-approval during builds, agent quality tracking, and memory bridging to Recall.

---

## Component Map

```
masonry/
  mcp_server/
    server.py             MCP server — 14 tools, dual transport (SDK + raw JSON-RPC)
  src/
    core/
      config.js           Config loader (~/.masonry/config.json with env-var overrides)
      state.js            masonry-state.json read/write (shallow-merge, always non-fatal)
      recall.js           Recall HTTP client (storeMemory, searchMemory, isAvailable; 3s timeout)
      registry.js         Agent registry generator (scans .claude/agents/*.md, writes registry.json)
      skill-surface.js    Recall skill retriever (project-scoped + global dedup)
    hooks/                Claude Code hook scripts (Node.js, one file per hook event)
    routing/
      router.py           Orchestrating four-layer router (always returns RoutingDecision)
      deterministic.py    Layer 1 — slash commands, state files, Mode field (0 LLM calls)
      semantic.py         Layer 2 — Ollama cosine similarity (qwen3-embedding:0.6b, threshold=0.70)
      llm_router.py       Layer 3 — Claude haiku subprocess, JSON-constrained output
    schemas/
      payloads.py         Pydantic v2 payload contracts (QuestionPayload, FindingPayload, etc.)
      registry_loader.py  YAML registry parser + mode/name lookup helpers
    dspy_pipeline/
      signatures.py       DSPy Signature classes (ResearchAgentSig, DiagnoseAgentSig, etc.)
      optimizer.py        MIPROv2 optimization runner (heuristic metric, no LLM judge)
      training_extractor.py  Extracts training examples from BL2 finding .md files
      drift_detector.py   Agent quality drift detection (verdict scoring + DriftReport)
      generated/          Auto-generated DSPy signature stubs per agent
    scoring/
      rubrics.py          Canonical scoring rubrics per agent category (hardcoded invariants)
  scripts/
    onboard_agent.py      Full onboarding pipeline (detect, extract, upsert, stub)
    validate_agents.py    Frontmatter schema validator (read-only, report-only)
    backfill_agent_fields.py  Backfills runtime state fields into existing registry entries
    backfill_registry.py  Batch registry refresh from agent .md frontmatter
    score_findings.py     Findings-category agent scorer
    score_code_agents.py  Code-category agent scorer
    score_ops_agents.py   Ops-category agent scorer
    score_routing.py      Routing decision scorer
    score_all_agents.py   Unified scorer: aggregates all signals, updates registry last_score
    run_vigil.py          Vigil health monitor (continuous drift + alert polling)
  bin/
    masonry-setup.js      Interactive installer: config, plugin registration, settings.json merge
    masonry-mcp.js        MCP server entry point wrapper
    masonry-init-wizard.js  /masonry-init interactive project scaffold wizard
    masonry-fleet-cli.js  Fleet CLI: status / add / retire / regen
  skills/                 /skill-name.md definitions (13 skills)
  agent_registry.yml      Declarative agent registry (46 agents, YAML, Pydantic-validated)
  hooks.json              Hook manifest (consumed by masonry-setup.js installer)
  package.json            Node.js package (name: masonry-mcp, version: 0.1.0, no runtime deps)
  requirements.txt        Python dependencies (pydantic, httpx, PyYAML, dspy)
```

---

## Four-Layer Routing Pipeline

The routing engine (`src/routing/`) resolves every incoming request to a named agent. Layers execute in priority order; the first layer that produces a match short-circuits the chain.

```
Request text + project_dir
         |
  Layer 1: Deterministic  (0 LLM calls, confidence=1.0)
         |  -- slash command table: /plan, /build, /fix, /verify, /masonry-run, /bl-run
         |  -- .autopilot/mode file: build, fix, verify
         |  -- masonry-state.json: campaign active_agent field
         |  -- .ui/mode file: compose, review
         |  -- question **Mode**: field regex
         | returns RoutingDecision or None
         |
  Layer 2: Semantic  (0 LLM calls, requires Ollama at 192.168.50.62:11434)
         |  -- agent corpus = description + capabilities (space-joined)
         |  -- model: qwen3-embedding:0.6b
         |  -- batch embeds all uncached agents in one Ollama call (session cache)
         |  -- cosine similarity; threshold=0.70; confidence=similarity score
         |  -- returns None if Ollama unavailable or no agent exceeds threshold
         |
  Layer 3: LLM  (1 Claude haiku call, subprocess, timeout=8s)
         |  -- prompt: agent list + user request, JSON-only output required
         |  -- parses JSON from stdout; regex extraction fallback
         |  -- confidence=0.6 (fixed)
         |  -- returns None on timeout, non-zero exit, or parse failure
         |
  Layer 4: Fallback  (always resolves)
           -- target_agent="user", confidence=0.0
           -- triggers human clarification
```

The deterministic layer handles the majority of real-world requests. The semantic and LLM layers handle novel or ambiguous requests.

---

## Hook System

Hooks are Node.js scripts invoked by Claude Code on specific events. They communicate via stdin/stdout JSON and stderr for messages. All hooks are graceful: any unhandled error results in process.exit(0), never blocking Claude Code.

### Hook Event Map

| Hook file | Event | Async | Behavior |
|-----------|-------|-------|----------|
| `masonry-session-start.js` | SessionStart | no | Restore autopilot/UI/campaign context; auto-resume interrupted builds; snapshot dirty files for stop-guard |
| `masonry-approver.js` | PreToolUse (Write/Edit/Bash) | no | Auto-approve when build or UI mode active; freshness guard: progress.json must be < 30 min old |
| `masonry-context-safety.js` | PreToolUse (ExitPlanMode) | no | Block if autopilot build active or context >= 80% |
| `masonry-lint-check.js` | PostToolUse (Write/Edit) | no | ruff (background format, warn-only check) for .py; prettier + eslint (background) for .ts/.tsx/.js/.jsx; skip in build/fix |
| `masonry-design-token-enforcer.js` | PostToolUse (Write/Edit) | no | Warn on hardcoded hex + banned fonts in UI files; silent in compose/fix |
| `masonry-tdd-enforcer.js` | PostToolUse (Write/Edit) | no | Block (exit 2) in build mode if impl file has no test file; warn-only otherwise |
| `masonry-observe.js` | PostToolUse | yes | Finding detection, Recall storage, activity log |
| `masonry-guard.js` | PostToolUse | yes | 3-strike error fingerprinting; per-project+tool error state |
| `masonry-agent-onboard.js` | PostToolUse (Write/Edit) | yes | Triggers onboard_agent.py as detached subprocess when agents/*.md written |
| `masonry-tool-failure.js` | PostToolUseFailure | no | Error fingerprinting + retry counting; 3-strike escalates to diagnose-analyst |
| `masonry-subagent-tracker.js` | SubagentStart | yes | Writes to ~/.masonry/state/agents.json; 1-hour stale eviction; updates campaign active_agent |
| `masonry-context-monitor.js` | PostToolUse | yes | Estimates context size from transcript file; warns on approach to limit |
| `masonry-stop-guard.js` | Stop | no | Blocks on uncommitted session files; session snapshot primary, mtime fallback; skips gitignored |
| `masonry-build-guard.js` | Stop | no | Blocks if .autopilot/mode=build with pending tasks |

### BL Subprocess Detection

All hooks that would interfere with BrickLayer's autonomous loop detect BL projects by checking for both `program.md` and `questions.md` in cwd and immediately exit 0. This is how `DISABLE_OMC=1` becomes unnecessary for BL subprocesses.

### Execution Order (synchronous hooks per event)

The `hooks.json` manifest defines registration order. Within a single event, hooks run in the order listed. The hooks.json manifest currently registers PostToolUse hooks in this order: masonry-observe, masonry-guard, masonry-agent-onboard (all async). The main settings.json used by Claude Code extends this with additional hooks added by masonry-setup.js.

---

## DSPy Optimization Pipeline

The pipeline improves agent prompt quality using campaign findings as training data. No LLM judge is required — quality is assessed by a heuristic metric.

### Flow

```
BL2 findings/*.md
       |
  training_extractor.py   -- extract verdict, severity, evidence, mitigation per finding
       |                  -- quality-weight by agent score: gold >= 0.8, silver >= 0.5, exclude < 0.5
       |
  optimizer.py            -- MIPROv2(num_threads=1, max_bootstrapped_demos=3, max_labeled_demos=3)
       |                  -- heuristic metric: verdict_match(0.4) + evidence_quality(0.4) + confidence_calibration(0.2)
       |                  -- requires >= 5 training examples per agent; skips agents below threshold
       |                  -- falls back to unoptimized module on MIPROv2 failure
       |
  optimized_prompts/{agent}.json  -- saved optimized DSPy module + score + timestamp
```

Optimized prompts are injected by Mortar when invoking specialist agents. Kiln provides an OPTIMIZE button trigger; `masonry_optimize_agent` MCP tool provides the programmatic trigger.

### Drift Detection

`drift_detector.py` computes agent quality drift against stored baselines:
- Verdicts mapped to scores: OK-class = 1.0, PARTIAL-class = 0.5, all others = 0.0
- Alert levels: drift < 10% = ok, 10–25% = warning, > 25% = critical
- `masonry_drift_check` MCP tool exposes this to Kiln

---

## Agent Registry

`agent_registry.yml` is the single source of truth for the Masonry fleet. It is consumed by the router, the onboarding pipeline, the scorer, and the MCP server.

### Entry Schema (AgentRegistryEntry)

```yaml
name: agent-name              # unique identifier, matches .md filename stem
file: path/to/agent.md        # relative or absolute path; ~ expanded
model: sonnet                  # haiku | sonnet | opus
description: "..."             # free text; used as semantic routing corpus
modes: [simulate, research]    # BL2 operational modes this agent handles
capabilities: [...]            # capability tags; appended to semantic corpus
input_schema: QuestionPayload  # QuestionPayload | DiagnosePayload
output_schema: FindingPayload  # FindingPayload | DiagnosisPayload
tier: draft                    # draft | candidate | trusted | retired
# Runtime state (written by onboard, updated by scorer):
dspy_status: not_optimized
drift_status: ok
last_score: null
runs_since_optimization: 0
registrySource: frontmatter
```

### Tier Semantics

| Tier | Meaning |
|------|---------|
| draft | Auto-onboarded; not yet evaluated; DSPy not optimized |
| candidate | Has been evaluated; score meets minimum threshold; considered for optimization |
| trusted | Validated over multiple campaigns; used as reliable training source |
| retired | No longer active; kept for history; excluded from routing |

### Auto-Onboarding Flow

When any `agents/*.md` file is written or edited:
1. `masonry-agent-onboard.js` hook fires, spawns `onboard_agent.py` as detached process
2. `onboard_agent.py` reads YAML frontmatter (no body inference)
3. Calls `upsert_registry_entry` (idempotent — same result run twice)
4. Writes runtime state fields for new entries only (preserves existing scores on update)
5. Calls `generate_dspy_signature_stub` — writes `src/dspy_pipeline/generated/{name}.py`

The `masonry_onboard` MCP tool exposes this pipeline for on-demand invocation from Kiln.

---

## MCP Server

`mcp_server/server.py` exposes Masonry capabilities to any MCP client (Claude Code, Kiln, CI tooling).

### Transport Strategy

Primary: MCP Python SDK (`mcp` package, stdio transport). If `mcp` is not installed, falls back to a hand-written JSON-RPC 2.0 reader/writer over stdin/stdout — no dependencies required.

### Tool Reference

| Tool | Purpose |
|------|---------|
| `masonry_status` | Campaign state + question counts from masonry-state.json + questions.md |
| `masonry_questions` | List questions from questions.md with optional status filter |
| `masonry_nl_generate` | Generate research questions from natural language description |
| `masonry_weights` | Question weight report (priority, prunable, retry candidates) |
| `masonry_git_hypothesis` | Analyze recent git diff, generate targeted questions for changed code |
| `masonry_run_question` | Run a single BL question by ID, return verdict envelope |
| `masonry_fleet` | List fleet agents + performance scores from registry.json + agent_db.json |
| `masonry_recall_search` | Search Recall for memories relevant to a query |
| `masonry_route` | Route request through four-layer engine, return RoutingDecision |
| `masonry_optimization_status` | DSPy optimization scores from optimized_prompts/*.json |
| `masonry_onboard` | Detect and register new agent .md files not yet in registry |
| `masonry_drift_check` | Drift detection for all registry agents with verdict history |
| `masonry_registry_list` | List agents from agent_registry.yml with optional tier/mode filter |

Several tools (`masonry_questions`, `masonry_nl_generate`, `masonry_weights`, `masonry_git_hypothesis`, `masonry_run_question`, `masonry_recall_search`) delegate to `bl.*` Python modules that are part of the BrickLayer 2.0 Python package, not Masonry itself. These tools will fail gracefully if the BL package is not installed.

### Registration

```json
"masonry": {
    "command": "python",
    "args": ["-m", "masonry.mcp_server.server"],
    "cwd": "C:/Users/trg16/Dev/Bricklayer2.0"
}
```

---

## Data Flow

```
User types in Claude Code
        |
   SessionStart hook
   (masonry-session-start.js)
   -- restores autopilot/UI/campaign context
   -- injects pending question count if BL project
        |
   UserPromptSubmit hook
   (masonry-register.js)
   -- Recall context injection
   -- guard flush on resume
        |
   Claude processes request
        |
   masonry_route MCP tool (optional explicit routing)
   OR
   Mortar agent reads request and dispatches agents directly
        |
   Write/Edit/Bash tool calls trigger PostToolUse hooks:
   -- masonry-approver   (auto-approve in build/UI mode)
   -- masonry-lint-check (ruff/prettier/eslint)
   -- masonry-observe    (finding detection, Recall storage)
   -- masonry-guard      (error tracking)
   -- masonry-agent-onboard (registry sync on agent .md writes)
        |
   Session ends:
   -- masonry-stop-guard (block if uncommitted session files)
   -- masonry-build-guard (block if pending build tasks)
   -- masonry-stop       (session summary → Recall via Ollama)
```

---

## External Dependencies

| Service | URL | Used by |
|---------|-----|---------|
| Recall (System-Recall) | http://100.70.195.84:8200 | recall.js, masonry-observe.js, skill-surface.js, masonry-stop.js |
| Ollama | http://192.168.50.62:11434 | semantic.py (qwen3-embedding:0.6b), config.js (qwen3:14b for summaries) |
| Claude API (Anthropic) | via claude subprocess | llm_router.py (haiku), optimizer.py (sonnet via DSPy) |

All external service calls are wrapped with timeouts (2–15s) and fail gracefully. Masonry remains functional if any service is unavailable.

---

## Python Package Layout

```
masonry/
  __init__.py
  src/
    __init__.py
    core/    (JS only — no Python __init__)
    hooks/   (JS only)
    routing/
      __init__.py
      router.py, deterministic.py, semantic.py, llm_router.py
    schemas/
      __init__.py    (re-exports AgentRegistryEntry, all payloads)
      payloads.py, registry_loader.py
    dspy_pipeline/
      __init__.py
      signatures.py, optimizer.py, training_extractor.py, drift_detector.py
      generated/     (auto-generated stubs)
    scoring/
      __init__.py
      rubrics.py
  scripts/     (standalone Python CLI scripts, importable as masonry.scripts.*)
  mcp_server/
    __init__.py
    server.py
```

Python package root is the `Bricklayer2.0/` directory. Import as `from masonry.src.routing.router import route`.

---

## Key Findings

- **R22.1** [WARNING] Wave 22: DSPy + Ollama smoke test PASSED (qwen3:14b produces valid structured output) but configure_dspy() defaults to wrong model name when backend="ollama"
- **D22.1** [DIAGNOSIS_COMPLETE] Wave 22: confidence_calibration band [0.5, 0.95] creates 30-pt cliff for confidence > 0.95, suppresses 40 training records (14.4%); fix spec complete
- **F22.1** [FIX_APPLIED] Wave 22: Ollama backend wired into optimizer.py, run_optimization.py CLI, and mcp_server/server.py with backend="ollama" parameter

## Open Items

| ID | Verdict | Summary |
|----|---------|---------|
| R22.1 | WARNING | configure_dspy(backend="ollama") defaults to model="claude-sonnet-4-6"; 1-line fix needed in optimizer.py:38 |
| D22.1 | DIAGNOSIS_COMPLETE | confidence_calibration band [0.5, 0.95] suppresses 40 training records; fix: widen to [0.5, 1.0] in score_findings.py:178 |
| R22.2 | PENDING | Full MIPROv2 trial deferred; blocked on R22.1 default model fix |
