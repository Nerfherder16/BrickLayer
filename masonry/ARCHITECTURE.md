# Masonry Architecture

## System Overview

Masonry is the orchestration platform sitting between Claude Code and BrickLayer 2.0. It is a Node.js MCP server combined with a Python routing engine, a hook system, a background daemon layer, and a fleet management layer. Claude Code talks to Masonry via MCP tool calls and Claude Code hook events; Masonry in turn routes work to the appropriate BrickLayer agent fleet and provides memory persistence via Recall.

The three-layer model:

```
Claude Code (UI + REPL)
      |
   Masonry           -- Node.js MCP server, hooks, routing engine, agent registry, daemon workers
      |
 BrickLayer 2.0      -- research campaigns, simulations, findings, synthesis
```

Masonry does not replace BrickLayer 2.0's core evaluation logic. It provides the platform layer: session continuity, intelligent routing, auto-approval during builds, agent quality tracking, memory bridging to Recall, and background intelligence workers.

---

## Component Map

```
masonry/
  bin/
    masonry-mcp.js            MCP server — 22 tools, JSON-RPC over stdio (Node.js, no runtime deps)
    masonry-setup.js          Interactive installer: config, hooks, settings.json merge
    masonry-init-wizard.js    /masonry-init interactive project scaffold wizard
    masonry-fleet-cli.js      Fleet CLI: status / add / retire / regen
  src/
    core/
      config.js               Config loader (~/.masonry/config.json with env-var overrides)
      state.js                masonry-state.json read/write (shallow-merge, always non-fatal)
      recall.js               Recall HTTP client (storeMemory, searchMemory, isAvailable; 3s timeout)
      registry.js             Agent registry generator (scans .claude/agents/*.md, writes registry.json)
      skill-surface.js        Recall skill retriever (project-scoped + global dedup)
      mas.js                  Shared helpers (isResearchProject, findProjectRoot, httpRequest, etc.)
    hooks/                    32 Claude Code hook scripts (Node.js, one file per hook event)
    daemon/
      daemon-manager.sh       Starts all 9 background workers as detached processes
      worker-testgaps.js      Finds implementation files missing test coverage
      worker-optimize.js      Triggers agent prompt optimization cycles
      worker-consolidate.js   Deduplicates Recall build patterns (limit 100, domains array)
      worker-deepdive.js      Deep research on high-priority flagged questions
      worker-ultralearn.js    Extracts and stores patterns from session findings
      worker-map.js           Codebase topology mapping to Recall
      worker-document.js      Docstring/JSDoc gap analysis for changed files
      worker-refactor.js      God file detection, duplicate blocks, deep nesting (>5 levels)
      worker-benchmark.js     Test suite timing baselines + regression detection (>20% slower)
    routing/
      router.py               Orchestrating four-layer router (always returns RoutingDecision)
      deterministic.py        Layer 1 — slash commands, state files, Mode field (0 LLM calls)
      semantic.py             Layer 2 — Ollama cosine similarity (qwen3-embedding:0.6b, threshold=0.70)
      llm_router.py           Layer 3 — Claude haiku subprocess, JSON-constrained output
    schemas/
      payloads.py             Pydantic v2 payload contracts (QuestionPayload, FindingPayload, etc.)
      registry_loader.py      YAML registry parser + mode/name lookup helpers
    scoring/
      rubrics.py              Canonical scoring rubrics per agent category
  scripts/
    improve_agent.py          The loop: eval → optimize → compare, keep if improved else revert
    eval_agent.py             Held-out eval: runs agent prompt via `claude -p`, scores against jsonl
    optimize_with_claude.py   Generates improved instructions from high/low quality examples
    writeback.py              Injects instructions into ## DSPy Optimized Instructions section
    onboard_agent.py          Full onboarding pipeline (detect, extract, upsert, stub)
    validate_agents.py        Frontmatter schema validator (read-only)
    backfill_agent_fields.py  Backfills runtime state fields into existing registry entries
    backfill_registry.py      Batch registry refresh from agent .md frontmatter
    score_findings.py         Findings-category agent scorer
    score_code_agents.py      Code-category agent scorer
    score_ops_agents.py       Ops-category agent scorer
    score_routing.py          Routing decision scorer
    score_all_agents.py       Unified scorer: aggregates all signals, updates registry last_score
  skills/                     /skill-name.md definitions (22 skills)
  agent_registry.yml          80-agent declarative registry (YAML, Pydantic-validated)
  hooks.json                  Hook manifest (consumed by masonry-setup.js installer)
  package.json                Node.js package (name: masonry-mcp, version: 0.1.0, no runtime deps)
  requirements.txt            Python dependencies (pydantic, httpx, PyYAML)
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
         |  -- 40+ keyword patterns (git, UI, security, diagnose, refactor, etc.)
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

The deterministic layer handles ~91% of real-world requests. The semantic and LLM layers handle novel or ambiguous requests.

---

## MCP Server

`bin/masonry-mcp.js` is a Node.js JSON-RPC 2.0 server over stdio. No runtime npm dependencies — all stdlib. Handles async tool dispatch with a `pendingRequests` counter that defers process exit until all in-flight HTTP calls complete.

### Tool Reference (22 tools)

| Tool | Purpose |
|------|---------|
| `masonry_status` | Campaign state + question counts from masonry-state.json + questions.md |
| `masonry_questions` | List questions from questions.md with optional status filter |
| `masonry_findings` | List findings from findings/ with verdict/severity filter |
| `masonry_run` | Run the research loop for a project directory |
| `masonry_nl_generate` | Generate BL research questions from natural language |
| `masonry_weights` | Question weight report (priority, prunable, retry candidates) |
| `masonry_git_hypothesis` | Analyze recent git diff, generate targeted questions for changed code |
| `masonry_run_question` | Run a single BL question by ID, return verdict envelope |
| `masonry_run_simulation` | Run simulate.py with given scenario parameters |
| `masonry_sweep` | Parameter sweep across scenario space |
| `masonry_fleet` | List fleet agents + performance scores from registry + agent_db |
| `masonry_recall` | Search Recall for memories relevant to a query |
| `masonry_route` | Route request through four-layer engine, return RoutingDecision |
| `masonry_pattern_store` | Store a build pattern to Recall |
| `masonry_pattern_search` | Search stored build patterns by query string |
| `masonry_worker_status` | Check daemon worker PID status and output file freshness |
| `masonry_task_assign` | Assign a pending autopilot task to a worker agent |
| `masonry_agent_health` | Agent health: score, drift status, run history |
| `masonry_wave_validate` | Validate a completed campaign wave for quality gates |
| `masonry_swarm_init` | Initialize a parallel agent swarm for a build task |
| `masonry_consensus_check` | Multi-agent consensus vote on a decision |
| `masonry_doctor` | System health check: Recall API, daemon PIDs, hooks, registry, training data |

### Registration

```json
"masonry": {
    "command": "node",
    "args": ["C:/Users/trg16/Dev/Bricklayer2.0/masonry/bin/masonry-mcp.js"]
}
```

---

## Hook System

Hooks are Node.js scripts invoked by Claude Code on specific events. They communicate via stdin/stdout JSON and stderr for messages. All hooks are graceful: any unhandled error exits 0, never blocking Claude Code.

### Hook Event Map (32 hooks)

| Hook file | Event | Async | Behavior |
|-----------|-------|-------|----------|
| `masonry-config-protection.js` | PreToolUse (Write/Edit) | no | Block writes to .eslintrc/prettier/pyproject lint sections without LINT_CONFIG_OVERRIDE token |
| `masonry-block-no-verify.js` | PreToolUse (Bash) | no | Block `git commit --no-verify` and `git push --force` |
| `masonry-session-start.js` | SessionStart | no | Restore autopilot/UI/campaign context; auto-start daemon workers; write session lock |
| `masonry-register.js` | UserPromptSubmit | no | Register prompt for routing; Recall context injection |
| `masonry-prompt-router.js` | UserPromptSubmit | no | Auto-route prompt to specialist via intent detection |
| `masonry-session-lock.js` | PreToolUse (Write/Edit) | no | Block writes to files owned by another session |
| `masonry-approver.js` | PreToolUse (Write/Edit/Bash) | no | Auto-approve when build or UI mode active |
| `masonry-context-safety.js` | PreToolUse (ExitPlanMode) | no | Block if autopilot build active or context ≥80% |
| `masonry-mortar-enforcer.js` | PreToolUse (Agent) | no | Block generic agent spawns; force Mortar routing |
| `masonry-preagent-tracker.js` | PreToolUse (Agent) | no | Track agent spawns before they start |
| `masonry-observe.js` | PostToolUse (Write/Edit) | yes | Finding detection, Recall storage, activity log |
| `masonry-lint-check.js` | PostToolUse (Write/Edit) | no | ruff for .py; prettier + eslint for .ts/.tsx/.js |
| `masonry-design-token-enforcer.js` | PostToolUse (Write/Edit) | no | Warn on hardcoded hex + banned fonts in UI files |
| `masonry-guard.js` | PostToolUse (Write/Edit) | yes | 3-strike error fingerprinting per project+tool |
| `masonry-tdd-enforcer.js` | PostToolUse (Write/Edit) | no | Block in build mode if impl file has no test file |
| `masonry-agent-onboard.js` | PostToolUse (Write/Edit) | yes | Triggers onboard_agent.py when agents/*.md written |
| `masonry-build-patterns.js` | PostToolUse (Write/Edit) | yes | Extract build patterns, store to Recall |
| `masonry-pulse.js` | PostToolUse (Write/Edit) | no | Session heartbeat to `.mas/pulse.jsonl` (rate-limited) |
| `masonry-tool-failure.js` | PostToolUseFailure | no | Error fingerprinting + retry counting; 3-strike escalates |
| `masonry-subagent-tracker.js` | SubagentStart | yes | Writes to ~/.masonry/state/agents.json; 1h stale eviction |
| `masonry-teammate-idle.js` | TeammateIdle / TaskCompleted | yes | Auto-assign pending tasks to idle agents |
| `masonry-session-end.js` | SessionEnd | no | Bayesian trust score update; release session lock |
| `masonry-pre-compact.js` | PreCompact | no | Preserve autopilot/campaign state before compaction |
| `masonry-stop-guard.js` | Stop | no | Blocks on uncommitted session files |
| `masonry-session-summary.js` | Stop | no | Write session summary |
| `masonry-handoff.js` | Stop | yes | Write handoff notes for context continuation |
| `masonry-context-monitor.js` | Stop | yes | Warn when context exceeds 750K tokens |
| `masonry-build-guard.js` | Stop | no | Blocks if .autopilot/mode=build with pending tasks |
| `masonry-ui-compose-guard.js` | Stop | no | Blocks if .ui/ compose has pending tasks |
| `masonry-score-trigger.js` | Stop | yes | Trigger agent scoring if training data >24h stale |
| `masonry-system-status.js` | Stop | no | Write system health snapshot at session end |
| `masonry-training-export.js` | Stop | no | Export session findings to training data corpus |
| `masonry-statusline.js` | statusLine | no | Live status in the Claude Code status bar |

### BL Subprocess Detection

All hooks that would interfere with BrickLayer's autonomous loop detect BL projects by checking for both `program.md` and `questions.md` in cwd and immediately exit 0. This eliminates the need for `DISABLE_OMC=1`.

---

## Background Daemon Workers

Nine workers run between sessions, triggered by `daemon-manager.sh` or auto-started by `masonry-session-start.js`. Each writes a PID file to `masonry/src/daemon/pids/` and outputs to `.autopilot/` or Recall.

| Worker | Output | Purpose |
|--------|--------|---------|
| `worker-testgaps.js` | `.autopilot/test-gaps.md` | Finds impl files with no test coverage |
| `worker-optimize.js` | registry score updates | Triggers agent optimization cycles |
| `worker-consolidate.js` | Recall dedup | Removes duplicate build patterns (limit 100) |
| `worker-deepdive.js` | findings/ | Deep research on flagged high-priority questions |
| `worker-ultralearn.js` | Recall patterns | Stores new patterns from session findings |
| `worker-map.js` | Recall topology | Codebase structure + dependency mapping |
| `worker-document.js` | Recall gaps | Docstring/JSDoc gap analysis for changed files |
| `worker-refactor.js` | `.autopilot/refactor-candidates.md` | God files, duplicates, deep nesting |
| `worker-benchmark.js` | `.autopilot/benchmark.md` | Test timing baselines + regression detection |

Workers use Recall endpoints: `POST /memory/store`, `POST /search/query`, `DELETE /memory/{id}`.

---

## Agent Prompt Optimization

Agent prompts improve via an eval → optimize → compare loop using `claude -p`. No DSPy, Ollama, or external API key required.

```
BL2 findings/*.md
       |
  score_all_agents.py
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

Agent scoring is triggered automatically at session end via `masonry-score-trigger.js` (rate-limited to once per 24h).

---

## Agent Registry

`agent_registry.yml` is the single source of truth for the Masonry fleet (80 agents). Consumed by the router, onboarding pipeline, scorer, and MCP server.

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
dspy_status: not_optimized
drift_status: ok
last_score: null
runs_since_optimization: 0
registrySource: frontmatter
```

### Tier Semantics

| Tier | Meaning |
|------|---------|
| draft | Auto-onboarded; not yet evaluated |
| candidate | Evaluated; score meets minimum threshold |
| trusted | Validated over multiple campaigns; used as training source |
| retired | No longer active; excluded from routing |

### Auto-Onboarding Flow

When any `agents/*.md` file is written or edited:
1. `masonry-agent-onboard.js` hook fires, spawns `onboard_agent.py` as detached process
2. `onboard_agent.py` reads YAML frontmatter
3. Calls `upsert_registry_entry` (idempotent)
4. Writes runtime state fields for new entries only (preserves existing scores on update)

---

## Session Ownership Locks

Parallel Claude sessions on the same machine used to conflict silently. The session lock system prevents this.

On `SessionStart`: write `{session_id, started_at, cwd, branch}` to `.mas/session.lock`. Skipped if a non-stale lock from a different session already exists (stale threshold: 4h).

On `PreToolUse` (Write/Edit): `masonry-session-lock.js` checks if the target file is protected AND a different session holds a fresh lock → blocks with `decision: "block"` and names the owning session.

On `SessionEnd`: release the lock if `session_id` matches.

Protected files: `masonry-state.json`, `.autopilot/{progress.json,mode,compact-state.json}`, `questions.md`, `findings/*.md`

---

## Data Flow

```
User types in Claude Code
        |
   SessionStart hook (masonry-session-start.js)
   -- restores autopilot/UI/campaign context
   -- auto-starts daemon workers if not running
   -- writes session ownership lock
        |
   UserPromptSubmit hooks
   -- masonry-register: Recall context injection
   -- masonry-prompt-router: intent detection → specialist routing
        |
   Claude processes request
        |
   masonry_route MCP tool (explicit routing)
   OR Mortar agent dispatches specialists directly
        |
   Write/Edit/Bash tool calls trigger PostToolUse hooks:
   -- masonry-approver   (auto-approve in build/UI mode)
   -- masonry-lint-check (ruff/prettier/eslint)
   -- masonry-observe    (finding detection, Recall storage)
   -- masonry-guard      (error tracking)
   -- masonry-build-patterns (pattern extraction)
   -- masonry-agent-onboard (registry sync on agent .md writes)
        |
   Session ends (Stop hooks fire in order):
   -- masonry-stop-guard (block if uncommitted session files)
   -- masonry-build-guard (block if pending build tasks)
   -- masonry-session-summary (write session summary)
   -- masonry-score-trigger (agent scoring if training data stale)
   -- masonry-system-status (health snapshot)
   -- masonry-training-export (export to training corpus)
   SessionEnd hook:
   -- masonry-session-end (trust score update; release lock)
```

---

## Typed Payload Contracts

All agent-to-agent communication uses strict Pydantic v2 schemas (`extra="forbid"`). No implicit fields.

| Schema | Direction | Key fields |
|--------|-----------|-----------|
| `QuestionPayload` | → specialist | `question_id`, `mode`, `context`, `priority`, `wave` |
| `FindingPayload` | ← specialist | `verdict`, `severity`, `summary` (≤200 chars), `evidence`, `confidence` (0–1) |
| `RoutingDecision` | routing output | `target_agent`, `layer`, `confidence`, `reason` |
| `DiagnosePayload` | → diagnose-analyst | diagnosis request contract |
| `DiagnosisPayload` | ← diagnose-analyst | diagnosis + recommended fix |
| `AgentRegistryEntry` | registry | `name`, `file`, `model`, `modes`, `capabilities`, `tier`, `last_score` |

Source: `masonry/src/schemas/payloads.py`

---

## External Dependencies

| Service | URL | Used by |
|---------|-----|---------|
| Recall (System-Recall) | http://100.70.195.84:8200 | recall.js, hooks, all daemon workers |
| Ollama | http://192.168.50.62:11434 | semantic.py (qwen3-embedding:0.6b) |
| Claude API (Anthropic) | via claude subprocess | llm_router.py (haiku), improve_agent.py |

All external service calls are wrapped with timeouts (2–15s) and fail gracefully. Masonry remains fully functional if any service is unavailable.

---

## Python Package Layout

```
masonry/
  __init__.py
  src/
    __init__.py
    core/    (JS only — no Python __init__)
    hooks/   (JS only)
    daemon/  (JS only)
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
```

Python package root is `Bricklayer2.0/`. Import as `from masonry.src.routing.router import route`.

---

## Phase 6 Additions — Dev Execution Loop Upgrades (2026-03-28)

### New Agents (6)

| Agent | Role |
|-------|------|
| `spec-reviewer` | Read-only spec compliance gate in /build pipeline — emits COMPLIANT / OVER_BUILT / UNDER_BUILT / SCOPE_DRIFT |
| `verification-analyst` | 6-gate false positive pipeline (Trail of Bits pattern): Process / Reachability / Real Impact / PoC / Math Bounds / Environment |
| `mcp-developer` | MCP server authoring specialist — fills BL's MCP-native blind spot |
| `chaos-engineer` | Fault injection and resilience testing specialist |
| `penetration-tester` | Authorized security testing — requires explicit authorization context before running |
| `scientific-literature-researcher` | Peer-reviewed literature research and fact-grounding specialist |

### New Skills (9)

| Skill | Purpose |
|-------|---------|
| `/debug` | 8-step structured diagnosis loop for broken code or failing tests |
| `/aside` | Freeze an active /build task, answer a read-only question, resume |
| `/visual-diff` | Self-contained HTML before/after diff artifact — writes to `~/.agent/diagrams/` |
| `/visual-plan` | Self-contained HTML task dependency graph from spec.md |
| `/visual-recap` | Self-contained HTML session summary with action timeline and re-entry context |
| `/spec-mine` | Inverse spec-writer: mines existing code into `.autopilot/spec.md` |
| `/release-manager` | Semantic versioning + CHANGELOG generation from conventional commits |
| `/discover` | JTBD discovery + assumption mapping + experiment design |
| `/parse-prd` | Parse a PRD into `.autopilot/spec.md` with SPARC mode annotations |

### New Hooks (2)

| Hook | Event | Behavior |
|------|-------|----------|
| `masonry-config-protection.js` | PreToolUse (Write/Edit) | Blocks writes to `.eslintrc` / `prettier` / `pyproject` lint sections without `LINT_CONFIG_OVERRIDE` token |
| `masonry-block-no-verify.js` | PreToolUse (Bash) | Blocks `git commit --no-verify` and `git push --force` |

### Hook Upgrades

| Hook | Change |
|------|--------|
| `masonry-pre-compact.js` | Now saves full build state + campaign state before compaction (not just autopilot mode) |
| `masonry-context-monitor.js` | Now detects 4 semantic degradation patterns via Ollama cosine similarity: lost-in-middle, poisoning, distraction, clash |

### /build Pipeline Upgrades

- **Guard/Verify split**: Guard = full regression suite (blocker); Verify = task-specific metric (experimental, non-blocking)
- **Spec-reviewer gate (Step 5a)**: After code-reviewer, before commit — COMPLIANT/OVER_BUILT/UNDER_BUILT/SCOPE_DRIFT blocks SCOPE_DRIFT and OVER_BUILT by default

### fix-implementer Upgrade

- **Commit-before-verify+revert pattern**: Every attempt is committed as `experiment:` prefix. On Guard FAIL the commit is reverted. On success the commit is relabeled `fix:`.

### uiux-master Upgrades

- **7-point AI slop self-evaluation gate**: Must score ≥86% before delivery
- **Domain exploration forcing function (Phase 0)**: 5+ domain concepts, 5+ domain colors, 3 rejected defaults, WHY per component required before any code is written
