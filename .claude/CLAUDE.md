# Autoresearch System — Master Context

This directory contains the autoresearch framework for business model stress-testing.
Read this file at the start of every session before doing anything else.

## What This System Does

An AI agent iterates on scenario parameters in `simulate.py`, runs simulations,
maps failure boundaries, and writes findings autonomously. The goal is NOT to find
the best-performing scenario — it is to discover which parameter combinations break
the system, and why.

---

## Directory Layout

```
autosearch/
  template/           — Copy this to start a new project
  QUICKSTART.md       — Full reference (read this if unsure)
  FRAMEWORK.md        — System architecture details
  adbp/               — ADBP project (active)
  {other projects}/   — Additional research projects
```

Each project folder contains:
```
simulate.py           — The simulation (agent edits SCENARIO PARAMETERS only)
constants.py          — Immutable rules (never edit)
program.md            — Loop instructions (never edit)
questions.md          — Question bank (agent + human via Kiln)
results.tsv           — Tab-separated run log
findings/             — Per-question findings (*.md)
synthesis.md          — End-of-session synthesis (written to project root)
docs/                 — Supporting documents (human authority)
project-brief.md      — Ground truth (highest authority, human only)
.claude/agents/       — Specialist agents
reports/              — Generated PDF reports (python analyze.py)
masonry/src/schemas/  — Pydantic v2 payload models (QuestionPayload, FindingPayload, etc.)
masonry/src/routing/  — Four-layer routing engine (deterministic → semantic → LLM → fallback)
masonry/src/dspy_pipeline/ — DSPy optimization pipeline (signatures, optimizer, drift detector)
masonry/optimized_prompts/ — Per-agent optimized prompt JSON files
masonry/agent_registry.yml — Declarative agent registry (modes, capabilities, tier)
```

---

## Masonry Orchestration Architecture

### Typed Payload System
All agent-to-agent communication uses structured Pydantic v2 models. Key schemas:
- `QuestionPayload` — question routed to a specialist (question_id, mode, context, priority, wave)
- `FindingPayload` — specialist output (verdict, severity, summary ≤200 chars, evidence, confidence 0-1)
- `RoutingDecision` — routing layer output (target_agent, layer, confidence, reason)
- `DiagnosePayload` / `DiagnosisPayload` — diagnose/fix cycle contracts
- `AgentRegistryEntry` — agent metadata (modes, capabilities, tier, DSPy status)

Source: `masonry/src/schemas/payloads.py`

### Four-Layer Routing
Mortar dispatches requests through four layers in priority order:
1. **Deterministic** (0 LLM calls): slash commands, autopilot state files, `**Mode**:` field
2. **Semantic** (0 LLM calls): Ollama cosine similarity at http://192.168.50.62:11434 (threshold 0.75)
3. **Structured LLM** (1 Haiku call): JSON-constrained routing for ambiguous requests
4. **Fallback**: returns target_agent="user" — asks for clarification

Use `masonry_route` MCP tool or `masonry/src/routing/router.py` directly.

### Agent Prompt Optimization

Agents improve via an eval → optimize → compare loop using `claude -p`. No API key, Ollama, or DSPy required.

**Core scripts:**
- `masonry/src/metrics.py` — heuristic scoring metrics (verdict match, evidence quality, confidence calibration)
- `masonry/src/writeback.py` — write optimized instructions back to all agent `.md` copies; update registry
- `masonry/scripts/eval_agent.py` — held-out eval: runs agent prompt through `claude -p`, scores against `scored_all.jsonl`
- `masonry/scripts/optimize_with_claude.py` — generate improved instructions from high/low-quality examples
- `masonry/scripts/improve_agent.py` — **the loop**: eval → optimize → compare, keep if improved else revert

**The loop (preferred entry point):**

```bash
cd C:/Users/trg16/Dev/Bricklayer2.0

# Single cycle: eval → optimize → compare
python masonry/scripts/improve_agent.py research-analyst
python masonry/scripts/improve_agent.py karen --signature karen

# Multiple cycles
python masonry/scripts/improve_agent.py research-analyst --loops 3

# Baseline eval only (no changes)
python masonry/scripts/improve_agent.py research-analyst --dry-run

# Options
#   --eval-size N      held-out examples per eval (default: 20)
#   --num-examples N   examples per quality tier for optimization (default: 15)
#   --model MODEL      Claude model for eval inference (default: claude-haiku-4-5-20251001)
```

Run from Git Bash (not inside an active Claude session — avoids nested subprocess issues).

**Optimized instructions** are injected into all `{agent}.md` copies under a `## DSPy Optimized Instructions` delimited section and take effect at next agent spawn. If a loop cycle regresses the score, instructions are automatically reverted. Run history is saved to `masonry/agent_snapshots/{agent}/history/`.

### Agent Onboarding (Zero Manual Steps)
When a new `.md` file is written to `agents/` or `~/.claude/agents/`:
1. `masonry-agent-onboard.js` hook detects the Write/Edit event
2. `masonry/scripts/onboard_agent.py` extracts frontmatter metadata
3. New `AgentRegistryEntry` appended to `masonry/agent_registry.yml` with `tier: "draft"`
4. Kiln shows new agent on next refresh as "draft / Not optimized"
6. Run a campaign wave to generate training data, then optimize from Kiln UI

---

## Starting a New Project

```bash
cp -r C:/Users/trg16/Dev/Bricklayer2.0/template/ C:/Users/trg16/Dev/Bricklayer2.0/{project}/
cd C:/Users/trg16/Dev/Bricklayer2.0/{project}/
```

1. Edit `project-brief.md` — what the system does, key invariants, past misunderstandings
2. Drop specs/docs into `docs/` — agents read everything here before generating questions
3. Edit `constants.py` — set real thresholds
4. Edit `simulate.py` — replace stub revenue model with actual model
5. Verify baseline: `python simulate.py` → should print `verdict: HEALTHY`
6. Copy agents: `cp -r ../template/.claude/agents/ .claude/agents/`
7. Generate questions (BL 2.0 workflow):
   ```
   # Step 7a — run planner (recommended for complex projects)
   Act as the planner agent in .claude/agents/planner.md.
   Inputs: project_brief=project-brief.md, docs_dir=docs/, constants_file=constants.py, simulate_file=simulate.py, prior_campaign=none

   # Step 7b — generate question bank
   Act as the question-designer-bl2 agent in .claude/agents/question-designer-bl2.md.
   Read project-brief.md, all files in docs/, constants.py, simulate.py, and CAMPAIGN_PLAN.md (if it exists).
   Generate the initial question bank in questions.md.
   ```
8. Init git and start the loop (see below)

---

## Monitoring Campaigns

Use **Kiln** (BrickLayerHub) to monitor campaigns, view findings, and manage the question queue.
The web dashboard has been retired — all UI goes through Kiln.

---

## Starting the Research Loop

> **Note:** Masonry hooks automatically detect BrickLayer research projects (via `program.md` +
> `questions.md`) and stay silent inside BL subprocesses. No env var needed.

**New project — after question bank is ready:**
```bash
cd C:/Users/trg16/Dev/Bricklayer2.0/{project}
git init && git add . && git commit -m "chore: init {project} autoresearch"
git checkout -b {project}/$(date +%b%d | tr '[:upper:]' '[:lower:]')
claude --dangerously-skip-permissions "Read program.md and questions.md. Begin the research loop from the first PENDING question. If any file edit fails, follow the self-recovery steps in program.md immediately — do not pause. NEVER STOP."
```

**Resuming an existing project:**
```bash
cd C:/Users/trg16/Dev/Bricklayer2.0/{project}
git checkout -b {project}/$(date +%b%d | tr '[:upper:]' '[:lower:]')
claude --dangerously-skip-permissions "Read program.md, questions.md, and findings/synthesis.md. Resume the research loop from the first PENDING question. If any file edit fails, follow the self-recovery steps in program.md immediately — do not pause. NEVER STOP."
```

**PowerShell equivalent (Windows):**
```powershell
claude --dangerously-skip-permissions "Read program.md and questions.md. Begin the research loop from the first PENDING question. NEVER STOP."
```

**Starting Wave 2 (question bank exhausted):**
First generate new questions:
```
Act as the hypothesis-generator agent in .claude/agents/hypothesis-generator.md.
Read findings/synthesis.md and the 5 most recent findings in findings/.
Generate Wave 2 questions and add them to questions.md.
```
Then start the loop as above.

---

## Generating the End-of-Session Report

**Step 1 — Run the synthesizer:**
```
Act as the synthesizer agent in .claude/agents/synthesizer.md.
Read all findings in findings/. Produce a synthesis following the format in synthesizer.md.
Write it to findings/synthesis.md.
```

**Step 2 — Generate PDF:**
```bash
cd C:/Users/trg16/Dev/Bricklayer2.0/{project}
python analyze.py
# PDF saved to reports/
```

---

## Agent Reference

| Agent | File | When to invoke |
|-------|------|----------------|
| `planner` | `.claude/agents/planner.md` | Once at init (before question-designer) — ranks domains, writes CAMPAIGN_PLAN.md |
| `question-designer-bl2` | `.claude/agents/question-designer-bl2.md` | Once at init (after planner) — generates questions.md with BL 2.0 modes |
| `question-designer` | `.claude/agents/question-designer.md` | BL 1.x only |
| `quantitative-analyst` | `.claude/agents/quantitative-analyst.md` | D1/D5 simulation questions |
| `regulatory-researcher` | `.claude/agents/regulatory-researcher.md` | D2 legal/compliance questions |
| `competitive-analyst` | `.claude/agents/competitive-analyst.md` | D3 market/analogues questions |
| `benchmark-engineer` | `.claude/agents/benchmark-engineer.md` | When simulate.py calls a live service |
| `hypothesis-generator` | `.claude/agents/hypothesis-generator.md` | Every 5 questions or when bank is exhausted |
| `synthesizer` | `.claude/agents/synthesizer.md` | At session end before analyze.py |

Invoke any agent:
```
Act as the {agent-name} agent as defined in .claude/agents/{agent-name}.md.
The current question is: {question text}.
```

---

## Loop Self-Recovery (File Edit Failures)

If `simulate.py` edit fails, do NOT pause. Immediately:
1. `git status` — check for dirty state
2. `git reset --hard HEAD` — clear stuck state
3. Re-attempt the edit
4. If it fails again — rewrite the full file preserving all logic, only changing SCENARIO PARAMETERS
5. Continue the loop

---

## Source Authority Hierarchy

| Tier | Source | Who edits |
|------|--------|-----------|
| Tier 1 | `project-brief.md`, `docs/` | Human only — ground truth |
| Tier 2 | `constants.py`, `simulate.py` | Human (constants) / Agent (scenario params only) |
| Tier 3 | `findings/`, `questions.md` | Agent output — lower authority than Tier 1/2 |

If Tier 1 and Tier 3 conflict, Tier 1 wins. Write a `CONFLICTS.md` if contradictions are found between sources.

---

## Global Git Post-Commit Hook

A global post-commit hook lives at `~/.git-hooks/post-commit`. It is activated globally via:

```bash
git config --global core.hooksPath ~/.git-hooks
```

The hook auto-detects BL projects (via `simulate.py`, `questions.md`, or `.claude/agents/` sentinel)
and appends commit entries to the appropriate `CHANGELOG.md`. For non-BL repos it exits silently.

**CHANGELOG target logic:**
- Root is a BL project -> `{repo_root}/CHANGELOG.md`
- Changed files touch exactly one BL subdirectory -> `{project}/CHANGELOG.md`
- Changed files touch multiple BL subdirectories -> `{repo_root}/CHANGELOG.md`
- Non-BL repo -> no CHANGELOG written (exit 0)

**One-time setup** (already active on this machine):
```bash
git config --global core.hooksPath ~/.git-hooks
```

---

## Common Issues

**`./start.sh` not recognized in PowerShell**: Use `bash start.sh ...` or run manually (see above).

**Loop stopped asking questions**: questions.md has no PENDING questions. Invoke `hypothesis-generator`.

**Simulation always HEALTHY**: SCENARIO PARAMETERS aren't stressed enough. Check `constants.py` thresholds.

**Finding is wrong**: Flag via dashboard or append `## Human Correction` block to the finding file, then add the correct understanding to `project-brief.md`.

**Edit to simulate.py keeps failing**: Run `git reset --hard HEAD` and retry. See loop self-recovery above.

**Campaign not visible in Kiln**: Restart the Kiln (BrickLayerHub) desktop app. The web dashboard (ports 3100/8100) has been retired — all monitoring goes through Kiln.
