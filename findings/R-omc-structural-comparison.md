# R-omc-structural-comparison: OMC Architecture vs. Masonry/BL 2.0 Structural Comparison

**Status**: HEALTHY (research complete — structural gaps identified)
**Date**: 2026-03-19
**Agent**: research-analyst

---

## Hypothesis Under Test

OMC (oh-my-claudecode) solved a different set of orchestration problems than Masonry. Identifying
structural gaps — places where OMC's architecture makes a different choice — reveals what Masonry
may be under-building or building unnecessarily.

---

## Evidence Sources

All evidence is primary — sourced directly from OMC's `.omc/` state directory left intact at
`C:/Users/trg16/Dev/Bricklayer2.0/.omc/` and from complete inspection of Masonry's source code
in `masonry/src/`. No external search tools were available; GitHub/web search was denied. This
makes the comparison unusually reliable: it is based on observed runtime behavior, not documentation.

---

## OMC Architecture — What the Evidence Shows

### State Directory Layout

OMC persists all session state in a `.omc/` directory local to the project root:

```
.omc/
  project-memory.json          ← project scan: tech stack, directory map, hot paths
  plans/                       ← per-build plan files (masonry-phase2.md observed)
  scientist/reports/           ← long-running analysis reports (named by date + question IDs)
  sessions/                    ← per-session summaries (UUID-named .json files)
  state/
    subagent-tracking.json     ← agent registry: type, started_at, duration_ms, status
    agent-replay-{uuid}.jsonl  ← JSONL event stream per session (agent_start/stop, keyword events, skill invocations)
    checkpoints/               ← periodic state snapshots (~every minute during active sessions)
    hud-state.json             ← HUD overlay state (backgroundTasks, sessionId)
    last-tool-error.json       ← tool failure tracker (retry_count, fingerprint)
    sessions/{uuid}/           ← per-session signal state (cancel-signal-state.json observed)
```

### Agent Type System

From `subagent-tracking.json` and `agent-replay-*.jsonl`, OMC uses a **typed agent pool** with a
small fixed vocabulary:

| Agent Type | Role |
|---|---|
| `oh-my-claudecode:planner` | Plans a build task — writes .omc/plans/{name}.md |
| `oh-my-claudecode:executor` | Executes a planned task |
| `oh-my-claudecode:explore` | Codebase exploration without modification |
| `oh-my-claudecode:analyze` | Triggered by keyword detection (see below) |
| `document-specialist` | Document-focused work |
| `general-purpose` | Fallback for uncategorized agent calls |

Agent types use a namespaced format (`oh-my-claudecode:{type}`) which is distinct from Masonry's
approach of named markdown agents (`name:` frontmatter). OMC's types are a closed enum baked into
the hook system. Masonry's agents are an open, user-extensible catalog.

### Keyword-Triggered Skill Invocation

From `agent-replay-4a7667fb-aeeb-47ce-a5f0-86c1c1ca52e9.jsonl`, line 14:

```json
{"t":0,"agent":"system","event":"keyword_detected","keyword":"analyze"}
{"t":0,"agent":"system","event":"skill_invoked","skill_name":"oh-my-claudecode:analyze"}
```

OMC has a **keyword interception layer** in its hook pipeline. When specific words appear in
conversation (e.g., "analyze"), OMC automatically invokes a corresponding skill. This happens at
the `system` level — below the agent level — without the user explicitly invoking a slash command.

This is fundamentally different from Masonry's approach, where skill invocation is always explicit
(`/skill-name` by the user) or deliberate by an agent prompt.

### Project Memory Model

From `project-memory.json`:

OMC performs an **automated project scan** on session start that produces:
- `techStack` (languages, frameworks, packageManager, runtime)
- `build` (buildCommand, testCommand, lintCommand, devCommand)
- `conventions` (namingStyle, importStyle, testPattern, fileOrganization)
- `structure` (isMonorepo, workspaces, mainDirectories, gitBranches)
- `directoryMap` (purpose, fileCount, keyFiles per directory)
- `hotPaths` (access frequency counts per file/directory, updated in real time)
- `userDirectives` (explicit user-provided notes about the project)

The `hotPaths` field is notable: OMC tracks how frequently Claude accesses each path across all
sessions and surfaced this at session start. In the observed data, `projects/bl2/questions.md`
had 131 access hits — the highest of any file. OMC uses this to prioritize context injection.

Masonry has no equivalent. It uses `masonry-state.json` for campaign progress state, and
relies on Recall (external) for cross-session memory. There is no in-process file access
frequency tracker.

### Checkpoint System

OMC writes periodic checkpoint files to `.omc/state/checkpoints/` approximately every 60–90
seconds during active sessions. The observed checkpoint schema:

```json
{
  "created_at": "ISO-8601",
  "trigger": "auto",
  "active_modes": {},
  "todo_summary": { "pending": 0, "in_progress": 0, "completed": 0 },
  "wisdom_exported": false,
  "background_jobs": { "active": [], "recent": [], "stats": null }
}
```

Key fields: `active_modes` tracks build/fix/verify mode state. `todo_summary` integrates with
Claude Code's native `/todo` system. `wisdom_exported` tracks whether session learnings were
persisted to long-term memory. `background_jobs` tracks async agents.

The checkpoint frequency is far higher than Masonry's equivalent. Masonry writes `masonry-state.json`
at question boundaries (not on a timer). OMC writes on a wall-clock interval regardless of activity.

### Session Tracking

OMC writes a session summary JSON on every session exit:
```json
{
  "session_id": "UUID",
  "ended_at": "ISO-8601",
  "reason": "prompt_input_exit",
  "agents_spawned": 9,
  "agents_completed": 9,
  "modes_used": []
}
```

The `reason` field classifies why a session ended: `prompt_input_exit` (user typed exit),
`context_limit`, `tool_failure`, etc. Masonry has no equivalent exit-reason classification.

### Scientist Agent

OMC had a `scientist/` subdirectory under `.omc/` for long-running analysis reports. The reports
observed (`20260314_q10.2_q10.3_q10.4_report.md`, `20260316_recall_health_audit.md`) are
structured multi-question analysis documents with `[OBJECTIVE]`, `[DATA]`, `[FINDING]`,
`[STAT:n]` tags. This appears to be OMC's analog to BL 2.0's specialist agents, but consolidated
into one "scientist" role per report. Masonry uses per-question specialist agents; OMC's scientist
batches multiple questions into one report.

### HUD (Heads-Up Display)

OMC maintained a real-time `hud-state.json` tracking `backgroundTasks` and `sessionStartTimestamp`.
Masonry has a HUD status line (`masonry-statusline.js`) but it is driven by `masonry-state.json`
rather than a separate HUD state file. The separation in OMC makes the HUD independently updatable
without touching campaign state.

### Cancel Signal Architecture

OMC had per-session cancel signal state in `.omc/state/sessions/{uuid}/cancel-signal-state.json`.
This enables a mid-session abort of a background agent without killing the entire session.
Masonry has no equivalent — stopping a background agent requires either waiting for it or
killing the whole subprocess.

### Tool Error Tracking

OMC's `last-tool-error.json` tracks `tool_name`, `tool_input_preview`, `error`, `timestamp`, and
`retry_count`. This is functionally equivalent to Masonry's `masonry-tool-failure.js` hook which
writes to `~/.masonry/state/last-error.json`. The key difference: OMC stores the last error
globally per project (in `.omc/`), Masonry stores it globally per machine (in `~/.masonry/`).
Masonry's approach can confuse errors across concurrent sessions on different projects.

---

## Masonry Architecture — Key Properties

For comparison, the complete Masonry structural model:

### Hook Architecture

Masonry hooks are wired into `settings.json` against Claude Code lifecycle events:

| Event | Hook | What It Does |
|---|---|---|
| SessionStart | `masonry-session-start.js` | Restores autopilot/UI/campaign mode; snapshots dirty files |
| UserPromptSubmit | `masonry-register.js` | Registers session in MCP |
| PreToolUse (Write/Edit/Bash) | `masonry-approver.js` | Auto-approves if active build (freshness-guarded) |
| PreToolUse (ExitPlanMode) | `masonry-context-safety.js` | Blocks exit during active build or high context |
| PostToolUse (Write/Edit) | `masonry-observe.js` | Detects findings → Recall; scans code diffs for functions |
| PostToolUse (Write/Edit) | `masonry-lint-check.js` | ruff + prettier + eslint |
| PostToolUse (Write/Edit) | `masonry-design-token-enforcer.js` | Warns on hardcoded hex |
| PostToolUse (Write/Edit) | `masonry-guard.js` | Campaign file edit guard |
| PostToolUse (Write/Edit) | `masonry-tdd-enforcer.js` | TDD discipline signal |
| PostToolUseFailure | `masonry-tool-failure.js` | Error tracking + 3-strike escalation |
| SubagentStart | `masonry-subagent-tracker.js` | Tracks active agent spawns |
| Stop | `masonry-stop-guard.js` | Blocks if session-modified files uncommitted |
| Stop | `masonry-build-guard.js` | Blocks if autopilot has pending tasks |
| Stop | `masonry-ui-compose-guard.js` | Blocks if UI compose pending |
| Stop | `masonry-session-summary.js` | Summarizes session |
| Stop | `masonry-handoff.js` | Handoff record if context high |

### Agent Architecture

Masonry agents are open markdown files with YAML frontmatter (`name`, `model`, `description`, `tier`).
Any `.md` file in `.claude/agents/` is auto-discoverable via `registry.js`. No closed enum.

The agent catalog is two-tiered:
1. **Infrastructure agents** (run by Trowel loop): quantitative-analyst, regulatory-researcher,
   competitive-analyst, research-analyst, hypothesis-generator-bl2, synthesizer-bl2, peer-reviewer,
   forge-check, skill-forge, agent-auditor, overseer, mcp-advisor, git-nerd
2. **Dev agents** (invoked directly by user/Mortar): spec-writer, developer, test-writer,
   code-reviewer, diagnose-analyst, fix-implementer, uiux-master, kiln-engineer, karen,
   frontier-analyst

### Routing Architecture

Masonry has a two-level router:
- **Mortar** (session-level): detects campaign vs. dev vs. conversational context; delegates to Trowel or specialist
- **Trowel** (campaign-level): owns the full research loop, routes per-question to specialists

OMC's equivalent is a single-level planner (`oh-my-claudecode:planner`) that writes a plan, then
dispatches executors. There is no campaign concept — OMC does not have a structured multi-question
loop with wave sentinels, hypothesis generators, or forced synthesis.

### Memory Architecture

Masonry uses Recall (external, self-hosted Qdrant + Neo4j at `100.70.195.84:8200`) for:
- Cross-session inter-agent memory (tagged by `agent:`, `project:`, `type:`)
- Skill surfacing (Recall query → relevant past skills)
- Campaign checkpointing by Trowel (every 10 questions)
- Auto-storage of findings by `masonry-observe.js`

Masonry also uses `masonry-state.json` (in-project, ephemeral) for live campaign state (current
question, active agent, verdict counts) visible to the status line HUD.

### Skill Architecture

Masonry skills are markdown files in `~/.claude/skills/{name}/SKILL.md`. They have frontmatter
(`name`, `description`, `campaign_origin`, `source_finding`). Skills are invoked by users as
`/skill-name` or by agents via the skill-surface mechanism (Recall query for `masonry:skill` tag).

OMC skills are namespaced strings (`oh-my-claudecode:analyze`) triggered by the keyword detection
system. Skills are built into OMC, not generated by campaigns.

---

## Structural Comparison Matrix

| Dimension | OMC | Masonry/BL 2.0 |
|---|---|---|
| **Agent type model** | Closed enum (`planner`, `executor`, `explore`, `analyze`) | Open catalog (any .md in `.claude/agents/`) |
| **Agent routing** | Single-level: planner writes plan, executor runs it | Two-level: Mortar (context) → Trowel (campaign loop) |
| **Skill invocation** | Keyword interception (automatic, system-level) | Explicit `/command` or deliberate agent invocation |
| **Skill origin** | Built into OMC hooks | Forged from campaign evidence (skill-forge agent) |
| **Campaign concept** | None — per-task model | Core primitive: waves, questions.md, findings/, synthesis |
| **Project memory** | In-project `project-memory.json` (tech stack, hot paths, conventions) | External Recall + in-project `masonry-state.json` |
| **File access tracking** | Yes — hotPaths with access counts per file | No |
| **Checkpoint frequency** | Timer-based (~60s), wall-clock | Event-based (question boundary) |
| **Session exit reason** | Classified and stored (`prompt_input_exit`, `context_limit`) | Not tracked |
| **Cancel signals** | Per-session per-agent cancel signal state | Not implemented |
| **HUD state** | Separate `hud-state.json` from campaign state | Combined in `masonry-state.json` |
| **Tool error scope** | Per-project (`.omc/state/last-tool-error.json`) | Per-machine (`~/.masonry/state/last-error.json`) |
| **Plan persistence** | Plans written to `.omc/plans/` as markdown | Plans written to `.autopilot/spec.md` |
| **Background job tracking** | In checkpoint `background_jobs.active` array | In `~/.masonry/state/agents.json` |
| **Agent performance scoring** | Not observed in state files | Yes — `agent_db.json` tracks verdict history per agent |
| **Self-improvement loop** | Not observed | Yes — forge-check → skill-forge → overseer escalation |
| **Research loop** | Scientist batches multiple questions into one report | Per-question specialist agents, all questions independent |
| **Synthesis** | Not observed as structural primitive | synthesizer-bl2 writes `findings/synthesis.md`, mandatory |

---

## Structural Gaps — Where OMC Has Something Masonry Lacks

### Gap 1: Keyword-Triggered Skill Invocation

OMC intercepts keywords in conversation and auto-invokes skills without explicit slash commands.
The event stream shows: `system:keyword_detected → system:skill_invoked`. This creates ambient
competence — Claude can "notice" it should do something and act on it without the user framing
it as a command.

**Masonry gap**: Masonry skill invocation is always explicit. The `skill-surface.js` module can
surface relevant skills via Recall query, but the agent must choose to read and apply them. There
is no hook-level keyword detection that auto-invokes a skill.

**Value of closing this gap**: Medium. For BL 2.0 campaigns, questions already have `**Mode**:`
fields that route to specialists. The campaign loop is explicit by design. For conversational
(non-campaign) sessions, keyword detection could auto-route to Mortar without the user needing
to know agent names.

### Gap 2: Hot Path Tracking (File Access Frequency)

OMC tracks how frequently each file is accessed across all sessions and accumulates this in
`project-memory.json`. The most accessed file (`projects/bl2/questions.md`, 131 hits) is the
most critical campaign artifact. OMC can inject this context preferentially at session start.

**Masonry gap**: Masonry's session start restores campaign mode and progress, but does not know
which files were most consulted in prior sessions. It cannot prioritize context injection based
on access patterns.

**Value of closing this gap**: High for long campaigns. When a BL 2.0 campaign spans 20+ sessions,
knowing that `questions.md` and `findings/synthesis.md` are the hot paths would allow session-start
to pre-inject their content rather than waiting for the agent to discover them.

### Gap 3: Timer-Based Checkpoints

OMC checkpoints on a wall-clock interval (~60s). Masonry only checkpoints at campaign event
boundaries (question complete, wave sentinel). If a session crashes mid-question, Masonry's
state shows the question still PENDING, but any in-flight work is lost. OMC's checkpoints
would capture the `todo_summary.in_progress` count, signaling that work was interrupted.

**Masonry gap**: No timer-based state persistence. The `masonry-state.json` `active_agent` field
covers this partially, but it is only updated at question boundaries, not continuously.

**Value of closing this gap**: Medium. Most useful for very long-running specialist agent invocations.

### Gap 4: Cancel Signals Per Agent

OMC maintained per-session cancel signal state enabling mid-session abort of a specific background
agent. Masonry's background agents (forge-check, peer-reviewer, skill-forge) are fire-and-forget
with no mechanism to cancel a specific one.

**Masonry gap**: No per-agent cancellation. A runaway background agent can only be terminated
by killing the entire subprocess.

**Value of closing this gap**: Low in current architecture — background agents are typically fast
(< 60s). Becomes relevant if long-running background agents are added (e.g., crawling research).

### Gap 5: Session Exit Reason Classification

OMC classifies session endings (`prompt_input_exit`, `context_limit`, etc.). This allows
post-session analysis of why sessions ended and pattern detection (if 40% of sessions end at
context limit, that is a structural signal).

**Masonry gap**: No exit reason classification. The `masonry-handoff.js` hook fires at Stop but
does not classify the reason. Masonry knows a session ended, not why.

**Value of closing this gap**: Low for individual sessions, high for fleet-level analysis. If
Masonry ever builds session telemetry, this is the missing field.

### Gap 6: Per-Project vs. Per-Machine Error State

OMC stores tool errors in `.omc/state/last-tool-error.json` (project-scoped). Masonry stores
tool errors in `~/.masonry/state/last-error.json` (machine-scoped). On a machine running two
concurrent Masonry sessions in different project directories, the second session's errors will
overwrite the first's, breaking the 3-strike detection.

**Masonry gap**: Tool error state is not project-scoped. This is an active correctness bug for
concurrent multi-project use (the "casaclaude"/"proxyclaude" workflow Tim uses).

**Value of closing this gap**: High for concurrent session users. Fix is simple: use
`path.join(cwd, '.masonry', 'state', 'last-error.json')` instead of the home directory path.

---

## Structural Gaps — Where Masonry Has Something OMC Lacks

### Masonry Advantage 1: Campaign Primitive

OMC has no concept of a research campaign: no `questions.md`, no `findings/`, no structured
verdict system, no multi-wave hypothesis generation, no synthesis as a structural endpoint.
OMC operates per-task. Masonry operates per-campaign.

This is the core architectural divergence. OMC is a session-level quality layer (hooks, memory,
approval flows). Masonry is a research-system operator (questions → specialists → findings → synthesis → skills).

### Masonry Advantage 2: Agent Performance Scoring

Masonry tracks per-agent verdict history in `agent_db.json`, powers confidence-weighted routing
in Trowel, and can escalate to overseer if the fleet is underperforming. OMC's subagent tracking
records only `started_at`, `completed_at`, and `duration_ms` — no verdict or quality signal.

### Masonry Advantage 3: Self-Improvement Loop

Masonry has a complete self-improvement cycle:
1. forge-check (every 5 questions) — detects fleet gaps, writes FORGE_NEEDED.md
2. skill-forge (wave end) — distills findings into reusable `~/.claude/skills/` files
3. agent-auditor (every 10 questions) — scores fleet performance
4. overseer — intervenes when fleet is underperforming

OMC has no equivalent. Skills are fixed at install time. Agents cannot be added by the running system.

### Masonry Advantage 4: Domain-Scoped Memory

Masonry's Recall integration scopes all memories by `domain={project}-bricklayer`. Agents
from different campaigns cannot contaminate each other's memory. OMC's project memory
(`project-memory.json`) is per-project but flat — no tagging, no domain isolation, no
cross-project retrieval.

---

## Residual OMC References in Masonry

Two places where OMC references survive in Masonry code:

1. `/c/Users/trg16/Dev/Bricklayer2.0/masonry/src/hooks/masonry-tool-failure.js` line 93:
   "Spawn a research agent (oh-my-claudecode:debugger or oh-my-claudecode:build-fixer) to
   investigate the root cause before attempting again."
   — This references OMC agent types that no longer exist. Should be updated to reference
   Masonry agents (diagnose-analyst, fix-implementer).

2. `/c/Users/trg16/Dev/Bricklayer2.0/.claude/CLAUDE.md` still contains `DISABLE_OMC=1`
   instructions in the "Starting the Research Loop" section. These are dead instructions
   since OMC is uninstalled, but they will confuse future readers of the documentation.

---

## Confidence

Evidence quality: HIGH
Reasoning: All evidence is primary. OMC's architecture is reconstructed from live runtime state
files (`project-memory.json`, `subagent-tracking.json`, `agent-replay-*.jsonl`, checkpoint files)
left intact in `.omc/`. Masonry's architecture is reconstructed from complete source code
inspection. No documentation was inferred or assumed.

The one limitation: OMC's hook source code (`.mjs` files) is not available — OMC is uninstalled.
The keyword detection mechanism is inferred from the JSONL event stream, not from hook source.
The exact list of intercepted keywords is unknown.

---

## What Would Change This Verdict

- Reading OMC's actual hook `.mjs` source files (if they exist elsewhere, e.g., npm cache or
  another machine) would fill in the keyword list and exact approval flow logic
- OMC's `wisdom_exported` field (seen in checkpoints, always `false` in observations) suggests
  a learning/wisdom export mechanism that was never triggered in the observed sessions — what
  "wisdom" contains is unknown from state files alone

---

## Actionable Findings Summary

| Priority | Action | Gap |
|---|---|---|
| HIGH (bug fix) | Scope tool error state to project directory in `masonry-tool-failure.js` | Gap 6 |
| HIGH (cleanup) | Remove `DISABLE_OMC=1` instructions from `.claude/CLAUDE.md` | Residual reference |
| HIGH (cleanup) | Replace OMC agent references in `masonry-tool-failure.js` with Masonry equivalents | Residual reference |
| MEDIUM | Add hot path tracking to `masonry-observe.js` (increment file access counter) | Gap 2 |
| MEDIUM | Add keyword detection hook for common Masonry intents (e.g., "run campaign", "research") | Gap 1 |
| LOW | Timer-based checkpoint writes (every 60s of active session) | Gap 3 |
| LOW | Classify session exit reasons in `masonry-stop-guard.js` or `masonry-session-summary.js` | Gap 5 |

---

## resume_after

Not applicable — verdict is not INCONCLUSIVE. Full evidence was available locally.
