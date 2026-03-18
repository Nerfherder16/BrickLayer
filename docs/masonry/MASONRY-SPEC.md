# Masonry — Framework Specification

**Version**: 0.1.1 — Post-Review Addendum Applied
**Date**: 2026-03-17
**Status**: Draft for Review
**Location**: Moved to `masonry/MASONRY-SPEC.md` — this copy is the canonical version

> Masonry = BrickLayer 2.0 (research engine) + OMC Teams (parallel execution) + Mnemonics (onboarding/hooks) + Recall (memory-native)
> The research loop IS the engine. Everything else orbits it.

---

## Table of Contents

1. [Vision](#vision)
2. [What Masonry Is Not](#what-masonry-is-not)
3. [What BL2 Already Solved (Preserve Exactly)](#what-bl2-already-solved)
4. [Gaps in BL2 That Masonry Addresses](#gaps-in-bl2-that-masonry-addresses)
5. [Architecture](#architecture)
6. [The Agent Fleet](#the-agent-fleet)
7. [Mode System](#mode-system)
8. [The Loop Engine](#the-loop-engine)
9. [Teams — Parallel Wave Execution](#teams--parallel-wave-execution)
10. [Recall Integration (Memory-Native)](#recall-integration-memory-native)
11. [Hook System](#hook-system)
12. [Onboarding Wizard](#onboarding-wizard)
13. [Skills System](#skills-system)
14. [Fleet Management](#fleet-management)
15. [Cross-Project Intelligence](#cross-project-intelligence)
16. [Dashboard Integration](#dashboard-integration)
17. [Implementation Phases](#implementation-phases)
18. [Migration from BL2](#migration-from-bl2)

---

## Vision

BrickLayer 2.0 is an exceptional research engine with a serious operational problem:
it requires `DISABLE_OMC=1` to run because the orchestration layer it depends on
actively hijacks its agents. It is powerful but isolated.

Masonry is the platform that BrickLayer 2.0 deserves. It:
- Eliminates the `DISABLE_OMC=1` requirement entirely
- Adds parallel team execution (multiple agents per wave)
- Makes Recall the memory foundation, not an optional bolt-on
- Gives BL2's agent fleet a proper home with auto-discovery
- Provides a zero-friction onboarding wizard
- Scales across ALL research domains — not just finance

**Name rationale**: A mason works with the same raw material as a bricklayer but
with greater precision, scope, and craft. The bricks (research units) are the same.
The work is more capable.

---

## What Masonry Is Not

- Not a replacement for BrickLayer 2.0's core evaluation logic — that logic is excellent
- Not OMC with a different name — OMC is general-purpose; Masonry is research-first
- Not domain-specific — Masonry works for code, science, legal, finance, systems, anything
- Not a monolith — core is lean; domain intelligence lives in packs

---

## What BL2 Already Solved

**Preserve all of this exactly. Do not reinvent.**

### The Research Loop Fundamentals
- `questions.md` as the work queue with PENDING/DONE/terminal status
- `results.tsv` as the append-only verdict ledger
- `findings/{qid}.md` as structured evidence records
- `history.db` (SQLite) for regression detection
- `project-brief.md` as highest-authority source (ground truth, human-only)
- `constants.py` as immutable rules (never agent-editable)

### The Verdict System
- Full verdict vocabulary (HEALTHY, FAILURE, WARNING, NON_COMPLIANT, DIAGNOSIS_COMPLETE, FIXED, FIX_FAILED, HEAL_EXHAUSTED, BLOCKED, INCONCLUSIVE, REGRESSION, etc.)
- Three-tier verdict classification: success (1.0) / partial (0.5) / failure (0.0)
- Multi-layer evaluation: failure classification + confidence assessment + result scoring
- Scoring formula: `(evidence_quality × 0.4) + (clarity × 0.4) + (execution_success × 0.2)`
- Code-audit verdict constraint (C-30): HEALTHY downgraded to WARNING for static analysis

### The Evaluation Pipeline
- `findings.py`: classify_failure_type, classify_confidence, score_result
- `history.py`: verdict_history SQLite with regression detection
- `agent_db.py`: per-agent verdict-based scoring
- `crucible.py`: 8-scorer rubric benchmarking (correctness, robustness, precision, recall, latency, completeness, clarity, actionability)
- `local_inference.py`: Ollama fallback-first classification (192.168.50.62:11434)

### The Self-Healing Loop
- BL 2.0 healloop: FAILURE → diagnose-analyst → DIAGNOSIS_COMPLETE → fix-implementer → FIXED/FIX_FAILED
- Max 3 cycles (configurable BRICKLAYER_HEAL_MAX_CYCLES)
- HEAL_EXHAUSTED written to results.tsv when cycles exhausted
- Distinct from legacy fixloop (BL 1.x, max 2 attempts)

### The Question Generation System
- `hypothesis.py`: wave-to-wave adaptive question generation
- `followup.py`: drill-down sub-questions from FAILURE/WARNING (max 1 level depth, C-04)
- `goal.py`: goal-directed questions from goal.md (C-03)
- Single-level depth enforcement (Q2.4 → Q2.4.1, Q2.4.2 — never Q2.4.1.1)

### The Synthesis Engine
- `synthesizer.py`: CONTINUE | STOP | PIVOT recommendation
- Severity-aware corpus truncation (max 12,000 chars; high-severity retained first)
- Feeds next-wave question generation

### The Background Agent Pattern
- peer-reviewer: spawned async after every finding (CONFIRMED/CONCERNS/OVERRIDE)
- forge-check: runs every 5 questions, identifies agent fleet gaps, creates FORGE_NEEDED.md
- agent-auditor: runs every 10 questions, RETIRE/PROMOTE/UPDATE recommendations
- Wave-start sentinel check: reads FORGE_NEEDED.md + AUDIT_REPORT.md + OVERRIDE findings before each question
- **This is the killer feature of BL2's loop** — do not weaken it

### The Mode System
Ten operational modes, each with its own loop instructions in `modes/{mode}.md`:
- `diagnose` — root cause investigation
- `fix` — implement remediation from DIAGNOSIS_COMPLETE
- `audit` — compliance verification against explicit standard
- `validate` — acceptance test / feature gate
- `monitor` — runtime health observation
- `frontier` — unexplored territory discovery (novelty × evidence × feasibility)
- `predict` — forecasting and trend analysis
- `research` — exploratory investigation
- `evolve` — improvement/optimization analysis
- `benchmark` — performance baselines and regression detection

### The Frontier Mode (Special Case)
Frontier has its own agent types not in the standard fleet:
- `adjacent-field-researcher` — mines non-AI fields for mechanisms
- `absence-mapper` — verifies no production implementation exists
- `taboo-architect` — designs from first principles with forbidden words
- `adversarial-pair` — opposing priors synthesized to the middle
- `physics-ceiling` — theoretical minimums, gap analysis
- `time-shifted` — retrospective from future vantage point
- `convergence-analyst` — filters all findings through current stack, ranks buildable ideas
- Pre-steps: web search for ADJACENT/ABSENCE, Python REPL benchmark for PHYSICS
- Scoring: novelty × evidence × feasibility (not the standard verdict vocabulary)

### The Template
Full project template at `template/` with all files needed to start any project:
- `simulate.py` (SCENARIO PARAMETERS section — only agent-editable part)
- `constants.py` (immutable)
- `program.md` (loop instructions — human authority)
- `questions.md` (question bank)
- `results.tsv` (verdict ledger)
- `findings/` (evidence records)
- `goal.md`, `ideas.md`, `audit-checklist.md`, `failure-cascade-map.md`, `monitor-targets.md`
- `benchmarks.json`, `ARCHITECTURE.md`, `CHANGELOG.md`
- `evaluate.py`, `analyze.py`
- `.claude/agents/` (full agent fleet)
- `modes/` (10 mode instruction files)

### The Recall Bridge (recall_bridge.py)
- `store_finding()`: posts to Recall when verdict in RECALL_STORE_VERDICTS
- `search_before_question()`: queries Recall for prior findings, injects as session context
- Graceful degradation: if Recall unavailable, loop continues (non-fatal)
- Tags: `bl:mode:{op_mode}`, `bl:verdict:{verdict}`, `bricklayer`

### The Skill Forge
- `skill_forge.py`: auto-creates skills from FIXED verdicts
- Skills stored: `~/.claude/skills/{name}/SKILL.md`
- Project registry: `{project_dir}/skill_registry.json`
- Tracks: created, last_updated, description, source_finding, campaign, repair_count

### Authority Hierarchy
| Tier | Source | Who edits |
|------|--------|-----------|
| 1 | `project-brief.md`, `docs/` | Human only — ground truth |
| 2 | `constants.py` | Human only — immutable rules |
| 3 | `simulate.py` | Agent edits SCENARIO PARAMETERS only |
| 4 | `findings/`, `questions.md` | Agent output — lower authority |

---

## Gaps in BL2 That Masonry Addresses

### Gap 1: `DISABLE_OMC=1` Requirement
**Problem**: OMC hooks intercept agent spawns and replace BL2's domain agents with generic ones.
**Solution**: Masonry IS the platform. No OMC, no conflict. BL2 agents are Masonry's first-class citizens.

### Gap 2: Single-Threaded Wave Execution
**Problem**: Each wave processes questions sequentially. One agent, one question at a time.
**Solution**: Masonry Teams — parallel wave execution with multiple agents per wave.
Independent questions run simultaneously. Wave completes when all agents report back.

### Gap 3: Manual Onboarding
**Problem**: QUICKSTART.md is a wall of text. New projects require manual file setup.
**Solution**: `/masonry-init` wizard (from Mnemonics architecture) — interactive, idempotent, mode-aware.

### Gap 4: Recall as Optional Bolt-On
**Problem**: `recall_bridge.py` is optional and gracefully silent when unavailable.
Session start has no memory hydration — each session rediscovers context from files.
**Solution**: Masonry hooks hydrate every session from Recall at start. The loop IS memory-native.

### Gap 5: No Cross-Project Learning
**Problem**: Recall is tagged per-project. Findings from one project never surface in another.
**Solution**: Cross-project query pattern in the Recall bridge — before each question,
query both current project AND analogous findings from all projects.

### Gap 6: Agent Fleet is Static
**Problem**: Agents live in `template/.claude/agents/` and are copied manually.
New agents require human action (copy file). forge-check creates FORGE_NEEDED.md
but Forge must be invoked manually.
**Solution**: Agent discovery system — Masonry scans `{project}/.claude/agents/`,
`~/.masonry/packs/{pack}/agents/`, and `~/.claude/agents/` in priority order.
forge-check writes directly to the scan path. No manual steps.

### Gap 7: Skills Forged But Not Surfaced
**Problem**: `skill_forge.py` writes skills to `~/.claude/skills/` but they're never
retrieved and injected into future campaigns on the same domain.
**Solution**: `masonry-register` hook (at session start) queries skill registry for
current project domain and injects relevant skills into agent preambles.

### Gap 8: Mode Selection is Manual
**Problem**: You must know modes exist, know which mode fits your project, and manually
structure your `program.md` and `questions.md` accordingly.
**Solution**: `/masonry-init` presents mode selection, configures program.md and the
agent fleet for the selected mode, and generates an appropriate starter question bank.

### Gap 9: Dashboard Disconnected from Loop
**Problem**: Dashboard (FastAPI + React, port 8100/3100) is a separate process.
No integration between loop state and dashboard in real time.
**Solution**: Loop engine emits state events that dashboard subscribes to via WebSocket.
Campaign progress, current agent, latest verdict — all live in dashboard.

### Gap 10: No Session Context Compression
**Problem**: Long campaigns accumulate large question banks and findings/ directories.
Session context approaches limits, requiring `DISABLE_OMC=1` partial workarounds.
**Solution**: Mnemonics-style handoff at 70% context — package current state to Recall,
continue in fresh session. Masonry-handoff runs as detached background process.

---

## Architecture

```
~/.masonry/
  core/
    loop-engine.py          ← wave-aware research loop (replaces manual program.md execution)
    team-composer.py        ← assembles parallel agent teams per wave
    registry.py             ← scans + indexes all available agents
    recall-bridge.py        ← Recall integration (replaces BL2's recall_bridge.py)
    session-manager.py      ← hydration at start, handoff at 70%
    setup-wizard.py         ← onboarding (Mnemonics architecture)
    skill-surface.py        ← retrieves + injects relevant skills into agent preambles

  packs/
    masonry-core/           ← default pack: all BL2 template agents
      agents/               ← all 22 BL2 agents as Masonry first-class citizens
      modes/                ← all 10 mode instruction files
      templates/            ← simulate.py, constants.py, questions.md, etc.
      pack.json             ← version, dependencies, default mode
    masonry-frontier/       ← frontier discovery agents
      agents/               ← 7 frontier-specific agents
      pack.json
    {user-created}/         ← drop a folder here, auto-discovered

  registry.json             ← auto-generated from agent scan, never hand-edit
  config.json               ← install state, active packs, Recall host, Ollama host

{project}/
  .claude/agents/           ← project-specific agents (highest priority in scan)
  masonry.json              ← project manifest (domain, mode, pack overrides)
  findings/
  results.tsv
  questions.md
  history.db
  skill_registry.json
  ... (standard BL2 layout)

~/.claude/
  skills/
    {name}/SKILL.md         ← auto-created by skill_forge, surfaced by skill-surface.py
  settings.json             ← Masonry hooks registered here
  skills/
    masonry-init.md         ← /masonry-init skill
    masonry-run.md          ← /masonry-run skill
    masonry-wave.md         ← /masonry-wave skill
    masonry-team.md         ← /masonry-team skill (inspect/override team composition)
    masonry-synth.md        ← /masonry-synth skill
    masonry-report.md       ← /masonry-report skill
    masonry-fleet.md        ← /masonry-fleet skill (agent audit/management)
    masonry-status.md       ← /masonry-status skill
```

---

## The Agent Fleet

### Core Evaluation Agents (from BL2 template)
| Agent | Mode(s) | Role |
|-------|---------|------|
| `question-designer` | all | Initial question bank generation |
| `question-designer-bl2` | all | BL2-aware question design with mode routing |
| `hypothesis-generator` | research, diagnose, frontier | Wave-to-wave adaptive questions |
| `hypothesis-generator-bl2` | all | BL2-integrated wave generation |
| `quantitative-analyst` | research, validate, benchmark | Quantitative investigation |
| `regulatory-researcher` | audit | Legal/compliance research |
| `competitive-analyst` | research, frontier | Market and analogues analysis |
| `benchmark-engineer` | benchmark, validate | Live service benchmarking |
| `research-analyst` | research | General exploratory investigation |
| `diagnose-analyst` | diagnose, healloop | Root cause analysis |
| `fix-implementer` | fix, healloop | Remediation implementation |
| `compliance-auditor` | audit | Standards compliance checking |
| `design-reviewer` | evolve, validate | Design pattern review |
| `health-monitor` | monitor | Runtime health observation |
| `cascade-analyst` | diagnose, frontier | Failure cascade mapping |
| `evolve-optimizer` | evolve | Improvement/optimization analysis |
| `synthesizer` | all (end-of-wave) | CONTINUE/STOP/PIVOT recommendation |
| `synthesizer-bl2` | all | BL2-integrated synthesizer |

### Fleet Management Agents (meta-agents)
| Agent | Role | Trigger |
|-------|------|---------|
| `overseer` | Reviews underperforming agents (score < 0.40, runs ≥ 3) | Every 10 questions |
| `skill-forge` | Creates skills from FIXED verdicts | After each FIXED verdict |
| `mcp-advisor` | Recommends MCP tools for question types | forge-check trigger |
| `git-nerd` | Git operations (commit, branch, diff) | Loop commit steps |
| `peer-reviewer` | Independent verification of each finding | After every finding (async) |

### Frontier Agents (masonry-frontier pack)
| Agent | Question Type | Role |
|-------|--------------|------|
| `adjacent-field-researcher` | [ADJACENT] | Mine non-AI fields for mechanisms |
| `absence-mapper` | [ABSENCE] | Verify no production implementation exists |
| `taboo-architect` | [TABOO] | First-principles design with forbidden words |
| `adversarial-pair` | [ADVERSARIAL] | Opposing priors synthesized to middle |
| `physics-ceiling` | [PHYSICS] | Theoretical minimums + gap analysis |
| `time-shifted` | [TIMESHIFTED] | Retrospective from future vantage point |
| `convergence-analyst` | [CONVERGENCE] | Rank buildable ideas from current stack |

### Agent Frontmatter (discovery metadata)
Every agent `.md` gets a frontmatter block that enables auto-discovery and routing:

```markdown
---
name: quantitative-analyst
description: Quantitative failure boundary and sensitivity analysis
modes: [research, validate, benchmark, frontier]
question-types: [quantitative, simulation, stress-test, behavioral]
operational-modes: [diagnose, research, predict]
requires: []
pairs-with: [benchmark-engineer, regulatory-researcher]
tier: primary
---
```

The registry scanner reads this frontmatter. New agents auto-register by dropping a `.md` file
in any scanned directory. No code changes required.

---

## Mode System

### Mode Configuration
Each mode has a `modes/{mode}.md` file with loop instructions. Masonry's loop engine
reads the active mode from `masonry.json` and applies the appropriate loop instructions.

| Mode | Question Source | Verdict Vocabulary | Stop Condition |
|------|----------------|-------------------|----------------|
| `diagnose` | hypothesis-driven | FAILURE, DIAGNOSIS_COMPLETE, HEALTHY | Root cause confirmed |
| `fix` | DIAGNOSIS_COMPLETE inputs | FIXED, FIX_FAILED, HEAL_EXHAUSTED | All FIX questions resolved |
| `audit` | checklist-driven | COMPLIANT, NON_COMPLIANT, PARTIAL, NOT_APPLICABLE | All checklist items answered |
| `validate` | acceptance criteria | HEALTHY, FAILURE, WARNING | All acceptance gates passed |
| `monitor` | scheduled/triggered | HEALTHY, WARNING, ALERT, REGRESSION | Ongoing (no natural stop) |
| `frontier` | hypothesis + wave-mid | BREAKTHROUGH, PROMISING, SPECULATIVE, INCREMENTAL | Convergence wave complete |
| `predict` | scenario-driven | forecast verdicts | Scenario space covered |
| `research` | hypothesis-driven | full vocabulary | Synthesis recommends STOP |
| `evolve` | improvement-driven | IMPROVEMENT, DEGRADED, CALIBRATED | Optimization plateau |
| `benchmark` | baseline-driven | HEALTHY, REGRESSION, DEGRADED | Baseline established + validated |

### Mixed-Mode Projects
`masonry.json` can declare multiple active modes per project:
```json
{
  "name": "recall-autoresearch",
  "modes": ["diagnose", "benchmark"],
  "primary_mode": "diagnose",
  "domain": "recall-autoresearch",
  "pack": "masonry-core"
}
```
Questions tagged with their mode. Loop routes each question to the correct mode instructions.

---

## The Loop Engine

The loop engine is the heart of Masonry. It replaces the manual execution of `program.md`
with an orchestrated, mode-aware, parallel-capable loop.

```
masonry-run
│
├── [HYDRATE] recall-bridge.search_session(project, domain)
│     → inject prior findings, active skills, agent memories into context
│
├── [QUEUE] read questions.md → find all PENDING questions
│
├── [WAVE] for each wave of PENDING questions:
│
│     ├── [SENTINEL CHECK] before every question:
│     │     ├── FORGE_NEEDED.md exists? → invoke Forge synchronously
│     │     ├── AUDIT_REPORT.md exists? → apply RETIRE/PROMOTE/UPDATE
│     │     └── Any OVERRIDE in findings? → insert re-exam question
│     │
│     ├── [TEAM COMPOSE] assemble team for this wave batch
│     │     ├── read question metadata (mode, type, constraints)
│     │     ├── query registry for matching agents
│     │     └── group independent questions for parallel execution
│     │
│     ├── [PARALLEL EXECUTE] run team (see Teams section)
│     │     ├── each agent: recall.search_before_question() → inject prior context
│     │     ├── each agent: skill-surface.inject_relevant_skills()
│     │     └── each agent: run question → verdict
│     │
│     ├── [CLASSIFY] for each verdict:
│     │     ├── classify_failure_type (Ollama → heuristic fallback)
│     │     ├── classify_confidence (Ollama → mode-specific heuristic)
│     │     └── score_result (Ollama → weighted formula)
│     │
│     ├── [PERSIST] for each verdict:
│     │     ├── write findings/{qid}.md
│     │     ├── append results.tsv
│     │     ├── update questions.md status
│     │     ├── record history.db (regression detection)
│     │     ├── record agent_db (performance tracking)
│     │     └── crucible.apply_rubric (benchmarking)
│     │
│     ├── [STORE] recall.store_finding() if verdict in RECALL_STORE_VERDICTS
│     │
│     ├── [ROUTE] verdict routing:
│     │     ├── FAILURE/DIAGNOSIS_COMPLETE → healloop (if enabled)
│     │     ├── FAILURE/WARNING/NON_COMPLIANT → followup.generate_subquestions()
│     │     └── FIXED → skill_forge.create_from_repair()
│     │
│     ├── [BACKGROUND] spawn async agents (non-blocking):
│     │     ├── peer-reviewer (after every finding)
│     │     ├── forge-check (every 5 questions)
│     │     └── agent-auditor (every 10 questions)
│     │
│     └── [COMMIT] git commit after each question (tagged with qid + verdict)
│
├── [SYNTHESIZE] after each wave:
│     ├── synthesizer.synthesize_campaign()
│     ├── CONTINUE → hypothesis.generate_next_wave()
│     ├── STOP → end loop
│     └── PIVOT → goal.regenerate_focused_questions()
│
├── [CONTEXT CHECK] before each question:
│     └── context > 70%? → masonry-handoff.py (detached) → continue in fresh session
│
└── NEVER STOP (until manually interrupted or synthesis recommends STOP)
```

---

## Teams — Parallel Wave Execution

This is the biggest capability gap between BL2 and Masonry.

### How Teams Work in Masonry

BL2 processes questions one at a time. Masonry groups independent questions into
parallel batches and runs them simultaneously using Claude Code native Teams.

**Team Composition Rules:**
```
1. Questions with the same mode and no data dependencies → parallel
2. Questions where Q2.4 depends on Q2 result → sequential
3. Diagnostic follow-ups (Q2.4.1, Q2.4.2) → parallel with each other, sequential after Q2.4
4. Frontier ADVERSARIAL questions → always parallel (by design — opposing priors)
5. Max parallel agents per wave: configurable (default 4, max 8)
```

**Team Lifecycle (per wave):**
```
TeamCreate("masonry-wave-{N}")
  → TaskCreate × (parallel question count)
  → Task(agent) × N spawns
  → each agent: claims question, executes, returns verdict
  → SendMessage(shutdown_request) when all tasks terminal
  → TeamDelete
```

**Team Types:**

| Team Type | Use Case | Composition |
|-----------|----------|-------------|
| Standard wave | Mixed independent questions | 2-4 domain agents |
| Adversarial | Frontier ADVERSARIAL questions | 2 agents with opposing priors |
| Audit sweep | Audit mode checklist batch | 2-4 compliance-auditor instances |
| Repair team | FAILURE → diagnose + fix | diagnose-analyst + fix-implementer sequenced |
| Oversight | Every 10 questions | overseer + peer-reviewer reviewing accumulated findings |

**Team State (masonry-state.json):**
```json
{
  "wave": 3,
  "team_name": "masonry-wave-3",
  "active_questions": ["D7", "D8", "D9"],
  "completed_questions": ["D1", "D2", "D3", "D4", "D5", "D6"],
  "pending_teams": [],
  "current_phase": "team-exec",
  "fix_loop_count": 0,
  "session_id": "{sessionId}",
  "context_pct": 45
}
```

---

## Recall Integration (Memory-Native)

Recall replaces BL2's `recall_bridge.py` as the memory foundation.
Every session is fully hydrated. Every finding is automatically stored.

### Session Hydration (masonry-register hook)
```javascript
// Runs on UserPromptSubmit
async function masonryRegister(session) {
  const project = readMasonryJson();

  // Pull project findings
  const projectMemory = await recall_search({
    query: project.name,
    domain: `${project.name}-autoresearch`,
    limit: 20
  });

  // Pull cross-project analogues
  const analogues = await recall_search({
    query: project.domain + " failure patterns",
    limit: 10
  });

  // Pull relevant skills
  const skills = await recall_search({
    query: project.domain,
    tags: ["masonry:skill"],
    limit: 5
  });

  // Inject into session context
  injectContext({ projectMemory, analogues, skills });
}
```

### Finding Storage (masonry-observe hook)
```javascript
// Runs on PostToolUse when findings/*.md written
async function masonryObserve(toolResult) {
  if (isNewFinding(toolResult)) {
    const finding = parseFinding(toolResult);
    await recall_store({
      content: finding.summary,
      domain: `${project.name}-autoresearch`,
      tags: [
        "masonry",
        `project:${project.name}`,
        `wave:${finding.wave}`,
        `qid:${finding.qid}`,
        `verdict:${finding.verdict}`,
        `mode:${finding.mode}`,
        `severity:${finding.severity}`
      ],
      importance: finding.severity === "Critical" ? 0.95 :
                  finding.severity === "High" ? 0.85 :
                  finding.severity === "Medium" ? 0.65 : 0.45
    });
  }
}
```

### Recall Tags Schema
```
masonry                          — all Masonry findings
project:{name}                   — project-scoped
wave:{N}                         — which wave
qid:{id}                         — question ID
verdict:{HEALTHY|FAILURE|...}    — outcome
mode:{diagnose|audit|...}        — operational mode
severity:{Critical|High|...}     — finding severity
agent:{name}                     — which agent produced this
masonry:skill                    — auto-created skills
masonry:synthesis                — wave synthesis reports
masonry:handoff                  — session handoffs
```

### Before-Question Injection
Before every question execution, masonry pulls context:
```python
def search_before_question(question, project):
    # Current project findings on this topic
    project_findings = recall_search(
        query=question.hypothesis,
        domain=f"{project.name}-autoresearch",
        limit=5
    )
    # Cross-project analogues (same domain, any project)
    analogues = recall_search(
        query=question.hypothesis,
        tags=["masonry"],
        limit=3
    )
    return format_context(project_findings, analogues)
```

---

## Hook System

Masonry hooks replace the OMC hooks in `~/.claude/settings.json`.

| Hook | Event | Purpose |
|------|-------|---------|
| `masonry-register.js` | UserPromptSubmit | Session hydration from Recall + skill injection |
| `masonry-observe.js` | PostToolUse (async) | Extract findings from file writes, store to Recall |
| `masonry-guard.js` | PostToolUse (async) | Error pattern detection (3-strike rule) |
| `masonry-stop.js` | Stop | Session summary to Recall + auto-commit |
| `masonry-statusline.js` | statusLine | Context % + active agent + current question |
| `masonry-handoff.js` | detached process | Package session at 70% context |

### Status Line
```
[Masonry] Wave 3 | Q7/24 | diagnose-analyst | 45% ctx | FAILURE×2 HEALTHY×4
```

### Error Guard (3-Strike Rule)
If the same error pattern appears 3 times:
1. Pause loop (do not retry)
2. Write `ERROR_PATTERN.md` with fingerprint
3. Inject warning into next prompt: "3-strike pattern detected: {error}. Investigate root cause before continuing."

---

## Onboarding Wizard

`/masonry-init` — interactive wizard adapted from Mnemonics 11-step flow.

### Steps

1. **Idempotency check** — reads `~/.masonry/config.json`; if installed, offers reconfigure
2. **Install scope** — global vs. project-local
3. **Recall host** — URL prompt, default `http://192.168.50.19:8200`
4. **Recall API key** — none / enter now / env var
5. **Ollama host** — URL prompt, default `http://192.168.50.62:11434`
6. **Pack selection** — which domain packs to install (shows available packs)
7. **New project?** — yes → runs project scaffold wizard (below)
8. **Status bar** — offers Masonry statusline; skips if one exists
9. **Connection test** — pings Recall health check + Ollama health check
10. **Write files** — merges hooks into settings.json, copies skills to ~/.claude/skills/
11. **CLAUDE.md injection** — appends Masonry context block (with backup)

### Project Scaffold Wizard (step 7 expansion)
When creating a new project:
```
1. Project name → masonry.json
2. Mode selection → "What are you researching?"
   [diagnose] [audit] [research] [benchmark] [frontier] [monitor] [validate] [evolve] [predict] [fix]
3. Domain pack → filters agent fleet to relevant agents
4. Project brief interview → fills in project-brief.md sections interactively
5. Starter question bank → question-designer generates Wave 1 questions from brief
6. Simulate.py scaffold → creates domain-appropriate simulate.py stub
7. Constants.py scaffold → sets sensible defaults for chosen domain
8. Git init + initial commit
9. Branch → masonry/{project}/{date}
```

### Skills Installed
```
~/.claude/skills/
  masonry-init.md       — /masonry-init (this wizard)
  masonry-run.md        — /masonry-run (start/resume loop)
  masonry-wave.md       — /masonry-wave (generate next wave)
  masonry-team.md       — /masonry-team (inspect team composition)
  masonry-synth.md      — /masonry-synth (run synthesizer)
  masonry-report.md     — /masonry-report (generate PDF)
  masonry-fleet.md      — /masonry-fleet (agent audit)
  masonry-status.md     — /masonry-status (project health check)
```

---

## Skills System

### Auto-Creation (from BL2's skill_forge.py)
When a question verdict is FIXED:
1. `skill_forge.create_from_repair()` extracts the repair approach
2. Writes `~/.claude/skills/{skill-name}/SKILL.md`
3. Registers in `{project}/skill_registry.json`
4. Stores to Recall with tag `masonry:skill`

### Auto-Surfacing (new in Masonry)
`masonry-register.js` queries for relevant skills at session start:
```javascript
const skills = await recall_search({
  query: project.domain,
  tags: ["masonry:skill"],
  limit: 5
});
// Injects skill names + descriptions into context
// Agents can read SKILL.md by name
```

### Skill Registry Format
```json
{
  "skills": [
    {
      "name": "fix-recall-memory-decay",
      "description": "Fixes double-decay bug in memory scoring",
      "created": "2026-03-17T00:00:00Z",
      "source_finding": "D14.2",
      "campaign": "recall-autoresearch",
      "domain": "recall-autoresearch",
      "repair_count": 0
    }
  ]
}
```

---

## Fleet Management

### forge-check (every 5 questions)
Scans `findings/` for question types that have no matching agent in `.claude/agents/`.
Creates `FORGE_NEEDED.md` with gap description.
Wave-start sentinel reads this and invokes Forge synchronously.

**Forge creates agents by:**
1. Reading the gap description in FORGE_NEEDED.md
2. Looking at similar agents for format reference
3. Writing a new `.md` with correct frontmatter
4. Registering in Masonry's registry.json

### agent-auditor (every 10 questions)
Reads `agent_db.json` + `crucible history.db` + recent findings.
Writes `AUDIT_REPORT.md` with:
- RETIRE: agents with score < 0.20 over ≥ 5 runs (delete file)
- PROMOTE: agents with score > 0.85 over ≥ 10 runs (update `tier: elite`)
- UPDATE TRIGGERS: agents whose trigger patterns miss questions they should handle

Wave-start sentinel applies recommendations immediately.

### overseer (every 10 questions, blocking)
Reviews agents with score < 0.40 AND runs ≥ 3.
Produces intervention plan (repair, retrain, or retire).
Different from agent-auditor: overseer is an active agent that makes decisions,
auditor is an analysis report.

### /masonry-fleet skill
Interactive fleet management:
```
/masonry-fleet status      — show all agents with scores
/masonry-fleet audit       — run agent-auditor now
/masonry-fleet forge       — run forge-check now
/masonry-fleet add {name}  — scaffold new agent interactively
/masonry-fleet retire {name} — remove agent from fleet
```

---

## Cross-Project Intelligence

BL2 siloes findings per project. Masonry makes findings available across all projects.

### How It Works
Every finding stored to Recall gets `project:{name}` tag.
When searching before a question, Masonry queries:
1. `project:{current}` — current project's history
2. All projects (no project filter) — analogues from any project

### Use Cases
- Working on a new API? Query: "api authentication failure patterns" → surfaces findings from all past API projects
- Starting a compliance audit? Query: "GDPR non-compliant findings" → surfaces past compliance issues across all projects
- Benchmarking a new system? Query: "latency regression patterns" → finds similar issues from past benchmarks

### Similarity Scoring
Recall's semantic search handles this naturally. No extra logic needed — just query without project filter.

---

## Dashboard Integration

BL2's dashboard (FastAPI port 8100, React port 3100) becomes Masonry's live monitoring surface.

### New in Masonry Dashboard
- **Team view**: shows which agents are currently running, which questions they're on
- **Wave timeline**: visual wave-by-wave progression with verdict distribution
- **Cross-project view**: findings from all projects, filterable by domain/verdict/severity
- **Skills registry**: view auto-created skills from FIXED verdicts
- **Fleet health**: agent scores from agent_db, crucible benchmarks
- **Live context meter**: session context % with handoff indicator

### Loop → Dashboard Bridge
The loop engine writes `masonry-dashboard-state.json` after each verdict:
```json
{
  "project": "recall-autoresearch",
  "wave": 3,
  "active_team": "masonry-wave-3",
  "current_questions": ["D7", "D8"],
  "active_agents": ["diagnose-analyst", "research-analyst"],
  "last_verdict": {"qid": "D6", "verdict": "FAILURE", "severity": "High"},
  "totals": {"PENDING": 17, "DONE": 6, "FAILURE": 2, "HEALTHY": 4},
  "context_pct": 45,
  "updated_at": "2026-03-17T..."
}
```
Dashboard backend polls this file (or subscribes via WebSocket).

---

## Implementation Phases

### Phase 1 — Zero-Config BL2 (2-3 days)
Goal: eliminate `DISABLE_OMC=1` requirement, no other changes.

1. Write `~/.claude/settings.json` hook config that replaces OMC for Masonry sessions
2. Write `masonry-register.js` hook (session hydration)
3. Write `masonry-observe.js` hook (finding storage)
4. Write `masonry-stop.js` hook (session summary)
5. Add frontmatter to all 22 BL2 agents
6. Write `/masonry-run` skill (thin wrapper over existing BL2 loop)
7. Test: run a BL2 project without `DISABLE_OMC=1`

**Success criteria**: BL2 campaign completes without agent hijacking, findings stored to Recall automatically.

### Phase 2 — Onboarding + Skills Surface (1 week)
Goal: zero-friction project creation and skill reuse.

1. Write setup-wizard.py (Mnemonics 11-step flow, Masonry-adapted)
2. Write project scaffold wizard (mode selection → question-designer → initial questions)
3. Write skill-surface.py (retrieve + inject relevant skills)
4. Write `/masonry-init`, `/masonry-status`, `/masonry-fleet` skills
5. Write `masonry.json` project manifest schema
6. Write `registry.json` auto-generation from agent scan

**Success criteria**: New project created in < 5 minutes via wizard, past skills surface automatically.

### Phase 3 — Teams (1-2 weeks)
Goal: parallel wave execution.

1. Write team-composer.py (dependency detection + parallel grouping)
2. Write loop-engine.py (wave-aware loop with TeamCreate/TaskCreate/Team lifecycle)
3. Write team state management (masonry-state.json)
4. Write `/masonry-team` skill
5. Test: 3-question wave runs in parallel, verdicts collected, synthesis triggered

**Success criteria**: Wave with 4 independent questions completes 4× faster than sequential.

### Phase 4 — Dashboard + Cross-Project (1 week)
Goal: live monitoring and cross-project intelligence.

1. Add team view + wave timeline to dashboard frontend
2. Add masonry-dashboard-state.json loop bridge
3. Update Recall bridge to query cross-project analogues
4. Add skills registry view to dashboard
5. Add fleet health view to dashboard

**Success criteria**: Dashboard shows live team execution, cross-project findings surface in agent context.

### Phase 5 — Pack System + Frontier (1-2 weeks)
Goal: domain packs, independent versioning, frontier as first-class.

1. Write pack.json schema
2. Scaffold masonry-core pack from BL2 template
3. Scaffold masonry-frontier pack from frontier agents
4. Write pack installer (masonry install {pack-name})
5. Write masonry update command
6. Add frontier agents to agent fleet (7 agents)

**Success criteria**: masonry install masonry-frontier adds frontier agents to any project.

---

## Migration from BL2

Existing BL2 projects work with Masonry with zero changes.

### What Masonry Adds to Existing Projects
1. Add `masonry.json` to project root (auto-created by `/masonry-status`)
2. Add frontmatter to `.claude/agents/*.md` (auto-updated by `/masonry-fleet`)
3. Masonry hooks replace `DISABLE_OMC=1` requirement

### Backward Compatibility
- `questions.md` format: unchanged
- `results.tsv` format: unchanged
- `findings/*.md` format: unchanged
- `history.db` schema: unchanged
- `agent_db.json` format: unchanged
- `recall_bridge.py`: replaced by Masonry hook layer, same Recall API
- All BL2 Python modules (campaign.py, findings.py, etc.): unchanged

### Migration Command
```bash
masonry migrate {project-path}
```
1. Reads existing `program.md` to detect mode
2. Creates `masonry.json`
3. Adds frontmatter to all agents
4. Registers project in Masonry registry
5. Does NOT modify any BL2 files

---

## Open Questions for Review

1. **Loop engine as Python or as Claude Code skill?**
   BL2's loop is currently driven by `claude --dangerously-skip-permissions "Read program.md..."`.
   Masonry could replace this with a Python loop engine that spawns agents via subprocess,
   OR keep the manual-invoke pattern but wrap it in `/masonry-run`.
   Recommendation: keep manual-invoke for Phase 1, build Python loop engine in Phase 3.

2. **Team size limits**
   How many parallel agents per wave? Too many = context/API pressure. Recommend default 4, max 8, configurable per project in masonry.json.

3. **Frontier mode in masonry-core or masonry-frontier pack?**
   Frontier agents are specialized and not needed for most projects.
   Recommendation: separate pack, opt-in install.

4. **Dashboard: keep existing or rewrite for Masonry schema?**
   Existing dashboard is tightly coupled to BL2's API.
   Recommendation: extend (not replace) — add Masonry views as new tabs.

5. **Masonry as npm package (like Mnemonics) or as local install?**
   npm package enables `masonry-setup.js` as a binary.
   Local install is simpler but harder to version.
   Recommendation: npm package for Phase 2+. Phase 1 is local scripts only.

---

## Files Created by Agent (Review Before Using)

The Explore agent created two preliminary analysis files during the codebase scan:
- `ARCHITECTURE-SUMMARY.md` — accurate BL2 technical reference (keep as reference)
- `MASONRY-FRAMEWORK.md` — early design sketch (superseded by this spec)

Recommend: delete MASONRY-FRAMEWORK.md, keep ARCHITECTURE-SUMMARY.md as reference.

---

## Addendum — Post-Review Gaps (v0.1.1)

### A1. `evaluate.py` — The Non-Simulation Scaffold

`simulate.py` is not universal. BL2's template includes `evaluate.py` for modes where
there is no simulation to run — you are measuring a live system or analyzing evidence directly.

```python
# evaluate.py scaffold (research, audit, diagnose modes)
EVALUATION_NAME = "Baseline — describe what is being evaluated"
TARGET_ENDPOINT = ""   # HTTP endpoint to probe, or "" if not applicable
TARGET_FILE = ""       # File path to analyze, or "" if not applicable
TARGET_COMMAND = ""    # Shell command to run, or "" if not applicable
```

**Wizard scaffold decision tree:**
```
Mode selected:
  benchmark, evolve     → scaffold simulate.py  (simulation-driven)
  research, audit,
  diagnose, validate    → scaffold evaluate.py  (evidence-driven)
  monitor               → scaffold evaluate.py  (live system probe)
  frontier              → scaffold simulate.py  (IDEAS scoring model)
  predict               → scaffold simulate.py  (scenario modeling)
  fix                   → neither (runs tests directly)
```

Both files can coexist in a project. `program.md` references whichever applies per question.
The wizard scaffolds the primary one and leaves a stub of the other for optional use.

---

### A2. `--dangerously-skip-permissions` in `/masonry-run`

Autonomous loop operation requires Claude to run without permission prompts.
Every `/masonry-run` invocation must include this flag.

**`/masonry-run` skill invocation pattern:**
```bash
# New campaign
cd {project-path}
git checkout -b masonry/{project}/$(date +%b%d | tr '[:upper:]' '[:lower:]')
claude --dangerously-skip-permissions \
  "Read program.md, masonry.json, and questions.md. \
   Begin the Masonry research loop from the first PENDING question. \
   Apply mode instructions from modes/{mode}.md. \
   Follow all sentinel checks before each question. \
   Store findings to Recall. Commit after each verdict. NEVER STOP."

# Resume existing campaign
claude --dangerously-skip-permissions \
  "Read program.md, masonry.json, questions.md, and findings/synthesis.md. \
   Resume the Masonry research loop from the first PENDING question. \
   Prior session context available in Recall under domain: {project}-autoresearch. \
   NEVER STOP."
```

**The skill also:**
- Sets `RECALL_API_KEY` from `~/.masonry/config.json` before invocation
- Passes `--project {project-path}` for multi-project setups
- Logs the session start to Recall with tag `masonry:session-start`

**Windows PowerShell equivalent (in `/masonry-run` skill):**
```powershell
$env:RECALL_API_KEY="..."; claude --dangerously-skip-permissions "..."
```

---

### A3. Long-Campaign Context Handoff Schema

BL2 campaigns run 18+ waves. The Mnemonics-style 70% context handoff must preserve
enough state that the next session resumes without re-reading large file sets.

**Handoff payload written to Recall (tag: `masonry:handoff`, importance: 0.95):**
```json
{
  "type": "masonry:handoff",
  "session_id": "{sessionId}",
  "project": "recall-autoresearch",
  "timestamp": "ISO-8601",
  "context_pct_at_handoff": 71,

  "loop_state": {
    "wave": 3,
    "next_question_id": "D9",
    "pending_count": 14,
    "done_count": 8,
    "active_mode": "diagnose"
  },

  "recent_findings": [
    {"qid": "D8", "verdict": "FAILURE", "severity": "High",
     "summary": "Memory decay double-counting on re-score"},
    {"qid": "D7", "verdict": "HEALTHY", "severity": "Info",
     "summary": "Vector index intact after restart"},
    {"qid": "D6", "verdict": "WARNING", "severity": "Medium",
     "summary": "Floor clamping applied to 1 memory"}
  ],

  "agent_scores": {
    "diagnose-analyst": 0.82,
    "research-analyst": 0.75,
    "fix-implementer": 0.90
  },

  "last_synthesis": {
    "recommendation": "CONTINUE",
    "next_focus": "memory decay edge cases under concurrent writes",
    "confidence": 0.85,
    "wave": 2
  },

  "pending_sentinels": {
    "forge_needed": false,
    "audit_report_pending": false,
    "override_verdicts": []
  },

  "resume_prompt": "Resuming wave 3 from question D9. Last synthesis: CONTINUE — focus on memory decay edge cases under concurrent writes. Recent high-severity finding: D8 FAILURE (double-counting on re-score). 14 questions pending."
}
```

**Resume behavior (`masonry-register.js` hook):**
```javascript
// On session start, check for recent handoff
const handoff = await recall_search({
  query: project.name,
  tags: ["masonry:handoff"],
  limit: 1
});

if (handoff && isRecent(handoff, hours=24)) {
  // Inject resume_prompt + recent_findings into context
  // Restore loop_state into masonry-state.json
  // No need to re-read all findings/ — handoff has the summary
}
```

**Handoff trigger:** `masonry-statusline.js` fires `masonry-handoff.js` as detached process
when context exceeds `MASONRY_HANDOFF_THRESHOLD` (default: 70%, configurable in `masonry.json`).

---

### A4. Windows Path Handling

Masonry runs on Windows (primary dev environment: `C:/Users/trg16/`).
All hook scripts and CLI binaries must handle Windows paths explicitly.

**Node.js binary resolution (from Mnemonics):**
```javascript
// In all hook scripts and bin/ files
const isWindows = process.platform === 'win32';
const NODE_BIN = isWindows
  ? 'C:/Program Files/nodejs/node.exe'
  : 'node';
const NPX_BIN = isWindows
  ? 'C:/Program Files/nodejs/npx.cmd'
  : 'npx';
```

**Path normalization:**
```javascript
const path = require('path');

// Always normalize paths — handles both forward and back slashes
function normalizePath(p) {
  return path.normalize(p).replace(/\\/g, '/');
}

// MASONRY_ROOT resolution
const MASONRY_ROOT = normalizePath(
  process.env.MASONRY_ROOT ||
  path.join(require('os').homedir(), '.masonry')
);
```

**`hooks.json` variable substitution:**
```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "command": "C:/Program Files/nodejs/node.exe",
      "args": ["${MASONRY_ROOT}/src/hooks/masonry-register.js"],
      "env": {
        "MASONRY_ROOT": "${MASONRY_ROOT}",
        "RECALL_API_KEY": "${RECALL_API_KEY}"
      }
    }]
  }
}
```

**`masonry-setup.js` path detection:**
```javascript
// Auto-detect Node.js installation on Windows
function detectNodePath() {
  const candidates = [
    'C:/Program Files/nodejs/node.exe',
    'C:/Program Files (x86)/nodejs/node.exe',
    process.execPath  // current node binary (most reliable)
  ];
  return candidates.find(p => require('fs').existsSync(p)) || 'node';
}
```

**settings.json hook entries must use absolute paths on Windows:**
```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "C:/Program Files/nodejs/node.exe C:/Users/trg16/.masonry/src/hooks/masonry-register.js"
      }]
    }]
  }
}
```

The setup wizard (`masonry-setup.js`) auto-detects the Node.js path and writes
the correct absolute path into `settings.json`. Never relies on `node` or `npx` being in PATH.
