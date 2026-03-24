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
  requirements.txt        Python dependencies (pydantic, httpx, PyYAML)
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

## Agent Prompt Optimization

Agent prompts are improved via an eval → optimize → compare loop using `claude -p`. No DSPy, Ollama, or external API key is required.

### Flow

```
BL2 findings/*.md
       |
  score_findings.py / score_all_agents.py
       |  -- heuristic scoring: verdict_match + evidence_quality + confidence_calibration
       |  -- appends scored records to scored_all.jsonl
       |
  improve_agent.py   -- eval → optimize_with_claude → compare loop
       |  -- eval_agent.py: runs agent prompt via `claude -p`, scores against held-out jsonl
       |  -- optimize_with_claude.py: generates improved instructions from high/low examples
       |  -- reverts if score regresses; saves history to agent_snapshots/{agent}/history/
       |
  writeback.py   -- injects instructions into ## DSPy Optimized Instructions section
                 -- updates all copies of agent .md (project-level + ~/.claude/agents/)
                 -- updates agent_registry.yml last_score
```

Run `python masonry/scripts/improve_agent.py {agent-name}` from the repo root.

### Drift Detection

`masonry_drift_check` MCP tool runs drift detection against stored baselines. Requires a `drift_detector` module to be available (not currently installed).

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
| Claude API (Anthropic) | via claude subprocess | llm_router.py (haiku), improve_agent.py (eval + optimize loop) |

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

- **D24.1** [FIX_APPLIED] Wave 24: training_extractor.py Agent field extraction added; 603 cross-project training records now recoverable; primary attribution source is finding file, qid_map is fallback
- **R24.1** [WARNING] Wave 24: Phase 17 metric ceiling revised to 70-73% (was 75-80%); verdict accuracy ~35-40% is the binding constraint, not evidence quality scoring
- **V24.1** [NOT_VALIDATED] Wave 24: karen (191 records) structurally incompatible with ResearchAgentSig; KarenSig definition required before multi-agent optimization

## Open Items

| ID | Verdict | Summary |
|----|---------|---------|
| D24.2 | DIAGNOSIS_COMPLETE | score_routing.py awards 70pts by checking if dispatched agent is recognized (trivially true); no ground-truth target_agent exists; fix: capture request_text in routing log + ground-truth-aware scoring |
| R24.1 | WARNING | Phase 17 metric changes yield +1-4pts (69-73%), not +5-8pts (75-80%); verdict accuracy is binding constraint; D24.1 attribution fix is higher leverage than metric weight changes |
| V24.1 | NOT_VALIDATED | karen 191 training records use ops-domain schema; ResearchAgentSig incompatible; KarenSig + metric + loader needed |
