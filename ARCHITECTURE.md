# BrickLayer 2.0 — Build Reference

**Last updated**: 2026-03-16
**Branch**: `recall/mar14` (active development)
**Self-audit campaign**: `projects/bl2/` — Wave 4 complete, 7 open bugs fixed

---

## What BrickLayer 2.0 Is

BrickLayer is an autonomous research loop that runs structured question campaigns against a
target codebase or live system. BL 2.0 adds a **9-mode lifecycle ontology** on top of the
BL 1.x engine, a **self-healing code loop**, an **agent fleet with performance tracking**,
and a **knowledge crystallization pipeline** that turns campaign findings into reusable skills.

---

## Architecture Overview

```
Campaign Loop (campaign.py)
  │
  ├── parse_questions() → PENDING questions
  │     └── _reactivate_pending_external()   # BL 2.0
  │
  ├── check_sentinels()
  │     ├── FORGE_NEEDED.md → forge.md (blocking, BL 1.x)
  │     ├── AUDIT_REPORT.md → display advisory
  │     └── OVERRIDE verdicts → inject re-exam questions
  │
  ├── _preflight_mode_check()                # blocks unknown modes/missing agents
  │
  └── for each question:
        ├── _load_mode_context()             # BL 2.0: modes/{mode}.md
        ├── inject session_context           # BL 2.0: last 2000 chars of session-context.md
        ├── Recall search (optional)         # BL 2.0: recall_bridge.py
        ├── run_question()                   # routes to runner (agent/http/subprocess/correctness)
        ├── write_finding() + update_results_tsv()
        ├── record_verdict() + detect_regression()
        ├── generate_followup()              # C-04: drill-down on FAILURE/WARNING
        ├── run_fix_loop()                   # BL 1.x: BRICKLAYER_FIX_LOOP=1
        ├── run_heal_loop()                  # BL 2.0: BRICKLAYER_HEAL_LOOP=1
        ├── append session-context insight
        ├── store_finding() to Recall        # BL 2.0: optional
        ├── agent_db.record_run()            # BL 2.0: score tracking
        └── spawn peer-reviewer (background)

  Wave-end (every N questions + completion):
        ├── [5q]  forge-check (background)
        ├── [10q] agent-auditor (background)
        ├── [10q] overseer if underperformers (background)   # BL 2.0
        ├── [end] overseer (background)                      # BL 2.0
        ├── [end] skill-forge (background)                   # BL 2.0
        ├── [end] mcp-advisor (background)                   # BL 2.0
        ├── [end] git-nerd (background) → GITHUB_HANDOFF.md # BL 2.0
        ├── [end] synthesize() + parse_recommendation()
        └── [end] generate_hypotheses() if bank exhausted
```

---

## Module Status

### Core Engine (`bl/`)

| Module | Status | Description |
|--------|--------|-------------|
| `config.py` | ✅ Fixed | Config singleton. Fixed: `agents_dir` now set in `init_project()`, `recall_src`/`target_git` dual-key support |
| `campaign.py` | ✅ Complete | Main campaign loop. BL 2.0: mode context, session context, Recall bridge, heal loop wiring, agent_db recording, overseer/skill-forge/mcp-advisor spawning |
| `questions.py` | ✅ Complete | BL 2.0: `operational_mode` field (default `"diagnose"`), `resume_after`, `_PARKED_STATUSES` (12 verdicts), `_reactivate_pending_external()` |
| `findings.py` | ✅ Fixed | BL 2.0: `_NON_FAILURE_VERDICTS` (18 verdicts — DEGRADED, ALERT, UNKNOWN, BLOCKED added in Wave 2), `severity_map` (32 entries), `_VERDICT_CLARITY` (35 entries) |
| `healloop.py` | ✅ Fixed | Self-healing state machine. 6 bugs fixed via self-audit campaign (D2.3 alias, D2.5/D2.6 last_cycle tracker, D2.5 short_type ID, D2.4 identity check, D2.1 verdict coverage) |
| `recall_bridge.py` | ✅ Complete | Optional Recall integration. Graceful-fail: `_HTTPX_AVAILABLE` flag, 2s health timeout, 5s op timeout. `_STORE_VERDICTS` frozenset (WARNING note: not in constants.py yet) |
| `agent_db.py` | ✅ New | Agent performance tracking. Score 0.0–1.0 (success/partial/failure verdict weighting). Underperformer threshold: 0.40, min 3 runs. JSON-backed at `{project}/agent_db.json` |
| `skill_forge.py` | ✅ New | Skill registry. Tracks campaign-created skills in `skill_registry.json`. `write_skill()`, `list_project_skills()`, `global_skill_inventory()` |
| `runners/agent.py` | ✅ Fixed | BL 2.0: `session_ctx_block` injected between `mode_ctx_block` and `doctrine_prefix`. Fixed: `_verdict_from_agent_output()` now accepts all 30 BL 2.0 verdicts via `_ALL_VERDICTS` frozenset (was only 4) |
| `fixloop.py` | ✅ Unchanged | BL 1.x fix loop. Still active via `BRICKLAYER_FIX_LOOP=1`. Independent of BL 2.0 |
| `history.py` | ✅ Unchanged | Verdict history ledger, regression detection |
| `synthesizer.py` | ✅ Unchanged | Wave-end synthesis, STOP/PIVOT/CONTINUE recommendation |
| `hypothesis.py` | ✅ Unchanged | Next-wave hypothesis generation |
| `followup.py` | ✅ Unchanged | Adaptive drill-down on FAILURE/WARNING |
| `quality.py` | ✅ Unchanged | Quality scoring |
| `crucible.py` | ✅ Unchanged | Campaign health aggregate |

### Mode System (`{project}/modes/`)

9 mode program files — loaded by `_load_mode_context()` and injected into agent prompt:

| Mode | Verdict Vocab | File | Status |
|------|--------------|------|--------|
| `diagnose` | HEALTHY / FAILURE / DIAGNOSIS_COMPLETE / PENDING_EXTERNAL | `diagnose.md` | ✅ |
| `fix` | FIXED / FIX_FAILED / INCONCLUSIVE | `fix.md` | ✅ |
| `research` | HEALTHY / WARNING / FAILURE / INCONCLUSIVE | `research.md` | ✅ |
| `audit` | COMPLIANT / NON_COMPLIANT / PARTIAL / NOT_APPLICABLE | `audit.md` | ✅ |
| `validate` | HEALTHY / WARNING / FAILURE / INCONCLUSIVE | `validate.md` | ✅ |
| `benchmark` | CALIBRATED / UNCALIBRATED / NOT_MEASURABLE | `benchmark.md` | ✅ |
| `evolve` | IMPROVEMENT / REGRESSION / INCONCLUSIVE | `evolve.md` | ✅ |
| `monitor` | OK / DEGRADED / DEGRADED_TRENDING / ALERT / UNKNOWN | `monitor.md` | ✅ |
| `predict` | IMMINENT / PROBABLE / POSSIBLE / UNLIKELY | `predict.md` | ✅ |
| `frontier` | PROMISING / BLOCKED / WEAK / INCONCLUSIVE | `frontier.md` | ✅ |

### Agent Fleet (`template/.claude/agents/`)

#### BL 1.x Agents (pre-existing, unchanged)
| Agent | Purpose |
|-------|---------|
| `forge.md` | Creates missing agents from FORGE_NEEDED.md briefs |
| `forge-check.md` | Scans fleet for gaps, writes FORGE_NEEDED.md |
| `peer-reviewer.md` | Reviews fixes, appends CONFIRMED/CONCERNS/OVERRIDE |
| `agent-auditor.md` | Fleet health report → AUDIT_REPORT.md |
| `fix-agent.md` | BL 1.x generic fix agent |
| `retrospective.md` | End-of-session improvement synthesis |
| `question-designer.md` | BL 1.x question bank generation |
| `hypothesis-generator.md` | BL 1.x next-wave hypotheses |
| `synthesizer.md` | Wave-end synthesis |
| `quantitative-analyst.md` | Simulation/financial questions |
| `regulatory-researcher.md` | Legal/compliance questions |
| `competitive-analyst.md` | Market/competitor questions |
| `benchmark-engineer.md` | Live service benchmarking |

#### BL 2.0 Agents (new)
| Agent | Mode | Purpose | Status |
|-------|------|---------|--------|
| `diagnose-analyst.md` | diagnose | Root cause analysis → DIAGNOSIS_COMPLETE with Fix Spec | ✅ |
| `fix-implementer.md` | fix | Applies Fix Spec → FIXED or FIX_FAILED | ✅ |
| `research-analyst.md` | research | Evidence-based assumption testing | ✅ |
| `compliance-auditor.md` | audit | Checklist compliance → COMPLIANT/NON_COMPLIANT/PARTIAL | ✅ |
| `design-reviewer.md` | validate | Pre-build design review → HEALTHY/WARNING/FAILURE | ✅ |
| `evolve-optimizer.md` | evolve | Optimization with measurement → IMPROVEMENT/REGRESSION | ✅ |
| `health-monitor.md` | monitor | Live metric checks → OK/DEGRADED/ALERT | ✅ |
| `cascade-analyst.md` | predict | Cascade risk projection → IMMINENT/PROBABLE/POSSIBLE | ✅ |
| `question-designer-bl2.md` | — | Generates BL 2.0 question banks (all 9 modes) | ✅ |
| `hypothesis-generator-bl2.md` | — | Next-wave hypotheses for BL 2.0 campaigns | ✅ |

#### BL 2.0 Meta-Agents (new — fleet management)
| Agent | Trigger | Purpose | Status |
|-------|---------|---------|--------|
| `overseer.md` | Every 10q + wave end | Repairs underperforming agents + stale skills | ✅ |
| `skill-forge.md` | Wave end | Campaign findings → `~/.claude/skills/` | ✅ |
| `mcp-advisor.md` | Wave end | INCONCLUSIVE failures → MCP recommendations | ✅ |
| `synthesizer-bl2.md` | Wave end | Writes synthesis.md + maintains CHANGELOG/ARCHITECTURE/ROADMAP + commits | ✅ |
| `git-nerd.md` | Wave end + on-demand | Autonomous GitHub ops — commits, PR create/update, writes `GITHUB_HANDOFF.md` | ✅ |

### Skills (`~/.claude/skills/`)

| Skill | Invoke | Purpose | Status |
|-------|--------|---------|--------|
| `bl-init` | `/bl-init` | Bootstrap a new BL 2.0 project (mode selection, template copy, question design) | ✅ |
| `bl-run` | `/bl-run` | Detect project, print exact launch command with env vars | ✅ |
| `bl-status` | `/bl-status` | Show questions.md progress table + open PENDING/FAILURE items | ✅ |
| Campaign-derived skills | `/auto-generated` | Created by skill-forge at wave end based on findings | 🔄 In progress |

---

## BL 2.0 Key Invariants

From `project-brief.md` — these must never be violated:

1. Campaign loop never raises — all errors caught, logged, turned into INCONCLUSIVE
2. `session-context.md` writes use `open(..., "a")` — append-only
3. Recall bridge always wrapped in `try/except Exception: pass`
4. Heal loop exits after `max_cycles` — no infinite loop
5. Heal intermediate IDs (`_heal{n}_diag`, `_heal{n}_fix`) are unique — no collisions with real question IDs
6. `_PARKED_STATUSES` is a strict superset of `_PRESERVE_AS_IS`
7. `operational_mode` defaults to `"diagnose"` — BL 1.x backwards compat

---

## Self-Healing Loop

```
Activated by: BRICKLAYER_HEAL_LOOP=1
Max cycles: BRICKLAYER_HEAL_MAX_CYCLES (default 3)

FAILURE ──→ diagnose-analyst ──→ DIAGNOSIS_COMPLETE ──→ fix-implementer ──→ FIXED ✓
                                                                           ↓
                                                                      FIX_FAILED
                                                                           ↓
                                  ←──────────── next cycle ──────────────←┘
                                  (uses fix finding with Root Cause Update as context)

On FIXED: updates original question's results.tsv row to FIXED
On exhaustion: appends "## Heal Cycle N — EXHAUSTED" to original finding
```

**Bugs fixed by bl2 self-audit campaign:**
- `D2.3` Fix: `current_result = dict(fix_result)` — was alias, mutated fix_result verdict
- `D2.5` Fix: `short_type` computed from agent_name (was hardcoded)
- `D2.6` Fix: `last_cycle` tracker (EXHAUSTED note now shows actual exit cycle)
- `D2.4` Fix: identity check `healed_result is not result` (was verdict comparison)
- `D2.1` Fix: `_verdict_from_agent_output()` accepts all 30 BL 2.0 verdicts
- `D2.2` Fix: DEGRADED/ALERT/UNKNOWN/BLOCKED added to `_NON_FAILURE_VERDICTS`

---

## Agent Performance System

```
Per-run: agent_db.record_run(project_root, agent_name, verdict)
  → updates agent_db.json with verdict history and recalculated score

Score = (success_verdicts * 1.0 + partial_verdicts * 0.5) / total_runs
  Success: HEALTHY, FIXED, COMPLIANT, CALIBRATED, IMPROVEMENT, OK, PROMISING, DIAGNOSIS_COMPLETE, NOT_APPLICABLE, DONE
  Partial: WARNING, PARTIAL, WEAK, DEGRADED, DEGRADED_TRENDING, FIX_FAILED, PENDING_EXTERNAL, BLOCKED
  Failure: FAILURE, INCONCLUSIVE, NON_COMPLIANT, ALERT, UNKNOWN, UNCALIBRATED, REGRESSION

Underperformer: score < 0.40 AND runs >= 3
  → Overseer spawned (background) to diagnose and repair
```

---

## Self-Audit Campaign Status (`projects/bl2/`)

**Scope**: 22 questions (D1–D10 diagnose + A1–A12 audit) targeting `bl/` source
**Recall source**: `C:/Users/trg16/Dev/autosearch`

| Wave | Questions | Fixed | Status |
|------|-----------|-------|--------|
| Wave 1 | D1–D10, A1–A12 | — | 7 FAILURE, 1 WARNING, 1 NON_COMPLIANT |
| Wave 2 | F2.1–F2.6 fix wave | 6 fixes | All FIXED |
| Wave 3 | M2.x monitor, A5.1 | 3 secondary | _STORE_VERDICTS extracted, print fix |
| Wave 4 | D3.1, D3.2, D4.x | 6 fixes | parse_questions regex critical fix + 5 secondary |

**Open items** (from results.tsv):
- `D4` FAILURE — `_reactivate_pending_external()` location discrepancy (spec says `questions.py`, implemented in `campaign.py`) — informational, both work
- `D7` WARNING — `_STORE_VERDICTS` not in `constants.py` (no enforcement test exists)
- `M2.1` WARNING — `RECALL_STORE_VERDICTS` not in `constants.py`

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `BRICKLAYER_HEAL_LOOP` | unset | Enable BL 2.0 self-healing loop |
| `BRICKLAYER_HEAL_MAX_CYCLES` | `3` | Max heal cycles before EXHAUSTED |
| `BRICKLAYER_FIX_LOOP` | unset | Enable BL 1.x fix loop (independent) |
| `DISABLE_OMC` | unset | Must be `1` when launching campaigns — prevents OMC hooks from intercepting agent spawns |

---

## File Layout

```
autosearch/
  bl/                      — Engine source (Python package)
    agent_db.py            — Agent performance tracking [BL 2.0]
    campaign.py            — Campaign orchestration loop
    config.py              — Config singleton (fixed: agents_dir, recall_src)
    findings.py            — Finding writer, verdict classifier (fixed: _NON_FAILURE_VERDICTS)
    fixloop.py             — BL 1.x fix loop
    healloop.py            — BL 2.0 self-healing loop (fixed: 6 bugs)
    hypothesis.py          — Next-wave generation
    questions.py           — Question parser (BL 2.0: operational_mode, _PARKED_STATUSES)
    recall_bridge.py       — Optional Recall integration [BL 2.0]
    runners/
      agent.py             — Agent runner (fixed: _verdict_from_agent_output)
      ...
    skill_forge.py         — Skill registry [BL 2.0]
    synthesizer.py         — Wave-end synthesis

  template/                — Copy this to start a new project
    .claude/agents/        — 22 agents (13 BL 1.x + 4 BL 2.0 + 5 meta)
    modes/                 — 9 mode program files [BL 2.0]
    project-brief.md       — Fill in for each project
    questions.md           — Template question bank
    constants.py           — Template constants

  projects/bl2/            — BL 2.0 self-audit campaign
    .claude/agents/        — 22 agents (copy of template)
    findings/              — 35+ finding files
    modes/                 — 9 mode files
    results.tsv            — Campaign results (all waves)
    agent_db.json          — Agent scores (populated during campaign)
    skill_registry.json    — Campaign-created skills

  dashboard/               — Web UI (FastAPI + React)

  ~/.claude/skills/        — Claude Code skills (global)
    bl-init/               — Bootstrap new BL 2.0 project
    bl-run/                — Launch/resume campaign
    bl-status/             — Show campaign progress
```
