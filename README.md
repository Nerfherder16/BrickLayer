# BrickLayer 2.0

Autonomous AI research and development framework built on top of Claude Code.

BrickLayer started as a failure-boundary research loop — run an AI agent against a simulation, map every parameter combination that breaks it, write structured findings. It has since grown into a three-layer platform that handles the complete software development lifecycle alongside campaign research, with 67 specialized agents, a four-layer routing engine, a session lifecycle hook system, and a self-improvement pipeline that optimizes agent prompts without requiring an API key or labeled dataset.

---

## System Architecture

```
  You / Claude Code
        ↕
     Masonry          ← bridge layer: MCP server, hooks, typed schemas, routing engine
        ↕
   BrickLayer         ← research + dev engine: campaigns, simulations, agent fleet, findings
```

**Claude Code** is where you work. Every request — coding, research, git, UI, campaigns — enters here.

**Masonry** is the bridge. It does not do work itself. It routes requests to the right specialist, enforces lifecycle guardrails via hooks, passes typed payload contracts between agents, and continuously scores and optimizes the fleet.

**BrickLayer** is the research engine. It runs question campaigns against any target system — business models, codebases, APIs, smart contracts — maps failure boundaries, and produces structured findings. The loop is fully autonomous.

**Mortar** is the executive router inside Masonry. Every request lands at Mortar first. Mortar reads the request, decides which agent(s) own the work, and dispatches in parallel. Mortar does not do the work itself.

**Kiln** (BrickLayerHub) is the Electron desktop app for monitoring campaigns, managing question queues, viewing agent scores, and triggering optimization runs.

---

## Research Campaigns

BrickLayer asks: *what kills this?* — not *what is optimal?*

```
questions.md → Trowel picks question → specialist agent → simulate.py → verdict
     ↑                                                                       ↓
hypothesis-generator ←──── findings/*.md ←── FindingPayload written to disk
```

Every question maps to a failure hypothesis. Every run either confirms the system survives or finds the exact parameter values that collapse it. The loop never stops until you tell it to.

**10 operational modes**: `simulate` · `diagnose` · `fix` · `research` · `audit` · `validate` · `benchmark` · `evolve` · `monitor` · `predict`

**30+ verdict types**: `HEALTHY` · `FAILURE` · `WARNING` · `INCONCLUSIVE` · `DIAGNOSIS_COMPLETE` · `FIXED` · `FIX_FAILED` · `COMPLIANT` · `NON_COMPLIANT` · `CALIBRATED` · `IMPROVEMENT` · `REGRESSION` · `IMMINENT` · `PROBABLE` · `DEGRADED` · `ALERT` · and more.

### Source Authority Hierarchy

| Tier | Source | Who edits |
|------|--------|-----------|
| Tier 1 | `project-brief.md`, `docs/` | Human only — ground truth |
| Tier 2 | `constants.py`, `simulate.py` | Human (constants) / Agent (scenario params only) |
| Tier 3 | `findings/`, `questions.md` | Agent output — lower authority than Tier 1/2 |

If Tier 1 and Tier 3 conflict, Tier 1 wins.

---

## Development Workflow

When not running campaigns, Masonry drives full software development through Mortar:

| Skill | What it does |
|-------|-------------|
| `/plan` | Explore codebase, write `.autopilot/spec.md`, wait for approval |
| `/build` | Orchestrate worker agents, TDD cycle, commit per task |
| `/ultrawork` | All independent tasks dispatched simultaneously |
| `/verify` | Independent review — reads everything, modifies nothing |
| `/fix` | Targeted fix, max 3 cycles, auto-re-verify |
| `/pipeline` | Chain agents/skills in a DAG via `.pipeline/{name}.yml` |
| `/masonry-team` | Partition build across N coordinated Claude instances |
| `/ui-init` | Design system init (tokens, fonts, palette, Figma extraction) |
| `/ui-compose` | Agent-mode UI build from design brief |
| `/ui-review` | Visual QA and design compliance |
| `/masonry-run` | Start or resume a BrickLayer research campaign |
| `/masonry-status` | Campaign progress, question counts, findings summary |
| `/masonry-fleet` | Agent fleet health — scores, drift detection, add/retire |

---

## Four-Layer Routing

Every request routes through four layers. The first match wins. No layer is called unless the previous one fails to match.

```
Layer 1: Deterministic   ─── 91% hit rate, 0 LLM calls
          ↓ (no match)
Layer 2: Semantic         ─── Ollama cosine similarity, 0 LLM calls
          ↓ (no match)
Layer 3: Structured LLM  ─── 1 Haiku call, JSON-constrained output
          ↓ (no match)
Layer 4: Fallback         ─── returns target_agent="user", asks for clarification
```

**Layer 1 — Deterministic** handles: slash commands, 40+ keyword patterns (git, UI, security, diagnose, refactor, architecture, Solana, campaign, research, benchmark, etc.), autopilot state files, campaign state files, UI compose/review state, and question `**Mode**:` field extraction. Routing confidence is always 1.0 on any deterministic match.

The deterministic layer was measured at 61% before recent work and brought to **91%** by fixing the diagnose pattern and adding four new patterns (developer, test-writer, explain, and an expanded diagnose matcher).

**Layer 2 — Semantic** uses Ollama at `192.168.50.62:11434` with cosine similarity threshold 0.70. Falls back gracefully if Ollama is unreachable.

**Layer 3 — Structured LLM** uses a single Haiku call with JSON-constrained output. The model is configurable via `MASONRY_LLM_MODEL` env var. Pre-flight check confirms `claude` CLI is on PATH; 1 retry with 2s backoff on timeout.

**Layer 4 — Fallback** never guesses. Returns `target_agent="user"` and asks for clarification.

Use `masonry_route` MCP tool or `masonry/src/routing/router.py` directly.

---

## Hook System

26 JavaScript hook files covering the full session lifecycle. Active hooks in `masonry/hooks/hooks.json`:

| Event | Hook(s) | What it does |
|-------|---------|--------------|
| `SessionStart` | `masonry-session-start` | Restore autopilot/UI/campaign context; write session ownership lock |
| `UserPromptSubmit` | `masonry-register` | Register prompt for routing |
| `PreToolUse` (Write/Edit) | `masonry-session-lock` | Block writes to protected files owned by another session |
| `PreToolUse` (Write/Edit/Bash) | `masonry-approver` | Auto-approve writes in build/fix/compose mode |
| `PreToolUse` (ExitPlanMode) | `masonry-context-safety` | Block plan-mode exit during active build or high context |
| `PreToolUse` (Agent) | `masonry-preagent-tracker` | Track agent spawns before they start |
| `PostToolUse` (Write/Edit) | `masonry-observe` | Campaign state observation (async) |
| `PostToolUse` (Write/Edit) | `masonry-lint-check` | ruff + prettier + eslint after every write |
| `PostToolUse` (Write/Edit) | `masonry-design-token-enforcer` | Warn on hardcoded hex/banned fonts in UI files |
| `PostToolUse` (Write/Edit) | `masonry-guard` | 3-strike error fingerprinter (async) |
| `PostToolUse` (Write/Edit) | `masonry-tdd-enforcer` | Block writes that lack corresponding test files |
| `PostToolUse` (Write/Edit) | `masonry-agent-onboard` | Auto-onboard new agents to registry (async) |
| `PostToolUseFailure` | `masonry-tool-failure` | Error tracking + 3-strike escalation |
| `SubagentStart` | `masonry-subagent-tracker` | Track active agent spawns |
| `SessionEnd` | `masonry-session-end` | Release session ownership lock |
| `PreCompact` | `masonry-pre-compact` | Context compaction preparation |
| `Stop` | `masonry-stop-guard` | Block stop on uncommitted git changes |
| `Stop` | `masonry-session-summary` | Write session summary |
| `Stop` | `masonry-handoff` | Write handoff notes for context continuation (async) |
| `Stop` | `masonry-context-monitor` | Warn when context exceeds 150K tokens |
| `Stop` | `masonry-build-guard` | Block stop if `.autopilot/` has pending tasks |
| `Stop` | `masonry-ui-compose-guard` | Block stop if `.ui/` compose has pending tasks |
| `Stop` | `masonry-score-trigger` | Trigger agent scoring run if training data is >24h stale (async) |
| `statusLine` | `masonry-statusline` | Live status in the Claude Code status bar |

All hooks use `${CLAUDE_PLUGIN_ROOT}/...` portable paths. Fresh installs get the full manifest — no manual hook injection required.

---

## Agent Fleet (67 agents)

67 agents declared in `masonry/agent_registry.yml`. Every agent declares `model:` (opus/sonnet/haiku) in frontmatter, a tier (`trusted`/`candidate`/`draft`), supported modes, and capabilities. New agents are auto-onboarded when their `.md` file is written.

**Orchestration**: `mortar` · `trowel`

**Research specialists**: `quantitative-analyst` · `regulatory-researcher` · `competitive-analyst` · `benchmark-engineer` · `research-analyst` · `compliance-auditor` · `cascade-analyst` · `evolve-optimizer` · `health-monitor` · `frontier-analyst` · `diagnose-analyst` · `fix-implementer`

**Campaign meta-agents**: `planner` · `question-designer-bl2` · `hypothesis-generator-bl2` · `synthesizer-bl2` · `peer-reviewer` · `overseer` · `agent-auditor`

**Dev workflow**: `spec-writer` · `developer` · `test-writer` · `code-reviewer` · `refactorer` · `security` · `architect` · `prompt-engineer` · `uiux-master` · `karen` · `git-nerd` · `kiln-engineer` · `solana-specialist`

**Utility**: `skill-forge` · `mcp-advisor` · `pointer` · `forge-check` · `e2e` · `design-reviewer` · `retrospective`

---

## Self-Improvement Pipeline

Agents improve via an eval → optimize → compare loop using `claude -p`. No API key, Ollama, or external eval service required.

```
eval_agent.py          ─── held-out eval: run agent prompt, score against scored_all.jsonl
     ↓
optimize_with_claude.py ─── generate improved instructions from high/low quality examples
     ↓
improve_agent.py        ─── the loop: eval → optimize → compare, keep if improved else revert
```

Scoring uses three heuristic metrics: verdict match, evidence quality, and confidence calibration. Scores are stored in `masonry/agent_snapshots/{agent}/eval_latest.json` and in `masonry/agent_registry.yml`. Each cycle's history is preserved so regressions are always recoverable.

Optimized instructions are injected into all `{agent}.md` copies under a `## DSPy Optimized Instructions` delimited section and take effect at next agent spawn.

```bash
# Single optimization cycle
python masonry/scripts/improve_agent.py research-analyst

# Multiple cycles
python masonry/scripts/improve_agent.py research-analyst --loops 3

# Baseline eval only, no changes
python masonry/scripts/improve_agent.py research-analyst --dry-run

# Karen uses a specialized scoring signature
python masonry/scripts/improve_agent.py karen --signature karen
```

Agent scoring is triggered automatically at session end via `masonry-score-trigger.js` (async Stop hook, rate-limited to once per 24h). Scores appear as a sparkline in Kiln's Agents view.

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

## Session Ownership Locks (T4.1)

Parallel Claude sessions on the same machine — a real operational pattern here — used to conflict silently. The session lock system prevents this.

On `SessionStart`: write `{session_id, started_at, cwd, branch}` to `.mas/session.lock`. Skipped if a non-stale lock from a different session already exists (stale threshold: 4h).

On `PreToolUse` (Write/Edit): `masonry-session-lock.js` checks if the target file is protected AND a different session holds a fresh lock → blocks with `decision: "block"` and names the owning session.

On `SessionEnd`: release the lock if `session_id` matches.

Protected files: `masonry-state.json`, `.autopilot/{progress.json,mode,compact-state.json}`, `questions.md`, `findings/*.md`

BL research subprocesses skip this check (detected via `program.md` + `questions.md` sentinel).

---

## E2E Verification

The `e2e` agent runs 10 checks after any infrastructure change to confirm nothing is broken:

| Check | What it verifies |
|-------|-----------------|
| 1. LLM router pytest | Full 11-test suite for T1.3 hardening (env var model, preflight, retry logic) |
| 2. Hook JS syntax | Every hook file in hooks.json exists and passes `node --check` |
| 3. hooks.json → settings.json | All event types covered, all referenced files exist |
| 4. MCP server + tools | Server imports cleanly, all 9 expected tools registered |
| 5. Deterministic routing | 5 canonical patterns match expected agents |
| 6. LLM router preflight + env var | `claude` CLI found, `MASONRY_LLM_MODEL` override applies |
| 7. Session lock wired | `masonry-session-lock.js` exists, referenced in all 3 lifecycle hooks |
| 8. Agent registry coverage | Every agent in registry has a `.md` file at declared path |
| 9. Training data | `scored_all.jsonl` exists, ≥10 records, ≤7 days old |
| 10. Score trigger wired | `masonry-score-trigger.js` exists, in Stop hooks, calls `score_all_agents.py` |

```
Act as the e2e agent in .claude/agents/e2e.md.
BL root: /path/to/Bricklayer2.0
```

---

## MCP Tools

The Python MCP server exposes these tools to Claude Code:

| Tool | Purpose |
|------|---------|
| `masonry_status` | Campaign state, question counts, wave for a project dir |
| `masonry_questions` | List questions from questions.md, filtered by status |
| `masonry_nl_generate` | Generate BL research questions from plain English |
| `masonry_weights` | Question weight report — high priority, prunable, retry flags |
| `masonry_git_hypothesis` | Analyze recent git diffs, generate targeted questions |
| `masonry_run_question` | Run a single BL question by ID, return verdict envelope |
| `masonry_fleet` | Agent list with performance scores from registry + agent_db |
| `masonry_recall` | Search Recall for memories relevant to a query |
| `masonry_route` | Route a request through the four-layer pipeline |

---

## Quick Start

### New Research Campaign

```bash
cp -r template/ myproject/
cd myproject/

# 1. Edit project-brief.md — what the system does, key invariants
# 2. Drop specs/docs into docs/
# 3. Edit constants.py — set real thresholds
# 4. Edit simulate.py — replace stub with actual model
# 5. Verify baseline: python simulate.py → verdict: HEALTHY

# Generate question bank (in Claude Code):
# Act as the planner agent in .claude/agents/planner.md.
# Act as the question-designer-bl2 agent in .claude/agents/question-designer-bl2.md.

# Start the autonomous loop
git init && git add . && git commit -m "chore: init campaign"
claude --dangerously-skip-permissions \
  "Read program.md and questions.md. Begin the research loop from the first PENDING question. NEVER STOP."
```

### Resuming a Campaign

```bash
claude --dangerously-skip-permissions \
  "Read program.md, questions.md, and findings/synthesis.md. Resume the research loop from the first PENDING question. NEVER STOP."
```

### Starting Wave 2 (question bank exhausted)

```
Act as the hypothesis-generator agent in .claude/agents/hypothesis-generator-bl2.md.
Read findings/synthesis.md and the 5 most recent findings in findings/.
Generate Wave 2 questions and add them to questions.md.
```

Then start the loop as above.

### Generate End-of-Session Report

```
Act as the synthesizer-bl2 agent in .claude/agents/synthesizer-bl2.md.
Read all findings in findings/. Write synthesis to findings/synthesis.md.
```

```bash
python analyze.py   # PDF saved to reports/
```

### Software Development

Open Claude Code in any project. Use `/plan` to start. Mortar handles routing to the right agents automatically.

---

## Loop Self-Recovery

If `simulate.py` edit fails, do not pause:

1. `git status` — check for dirty state
2. `git reset --hard HEAD` — clear stuck state
3. Re-attempt the edit
4. If it fails again — rewrite the full file preserving all logic, only changing SCENARIO PARAMETERS
5. Continue the loop

---

## Requirements

- Claude Code CLI
- Python 3.11+ with `pydantic>=2`, `reportlab`, `uvicorn`, `fastapi`, `httpx`, `pyyaml`
- Node.js 18+ (Masonry hooks)
- Ollama at `192.168.50.62:11434` (semantic routing — optional, degrades gracefully to Layer 3)
- [System-Recall](https://github.com/Nerfherder16/System-Recall) (optional — cross-session memory at `100.70.195.84:8200`)
- Kiln (BrickLayerHub) — Electron desktop app, primary campaign monitoring UI

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
