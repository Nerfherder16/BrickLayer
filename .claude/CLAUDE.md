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
  dashboard/          — Web UI for monitoring (FastAPI + React)
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
questions.md          — Question bank (agent + human via dashboard)
results.tsv           — Tab-separated run log
findings/             — Per-question findings (*.md)
findings/synthesis.md — End-of-session synthesis
docs/                 — Supporting documents (human authority)
project-brief.md      — Ground truth (highest authority, human only)
.claude/agents/       — Specialist agents
reports/              — Generated PDF reports (python analyze.py)
```

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
7. Generate questions (tell Claude):
   ```
   Act as the question-designer agent in .claude/agents/question-designer.md.
   Read project-brief.md, all files in docs/, constants.py, and simulate.py.
   Generate the initial question bank in questions.md.
   ```
8. Init git and start the loop (see below)

---

## Starting the Dashboard

In a separate terminal (use Git Bash or WSL — not PowerShell):
```bash
bash C:/Users/trg16/Dev/Bricklayer2.0/dashboard/start.sh C:/Users/trg16/Dev/Bricklayer2.0/{project}
```

Or manually in two PowerShell terminals:

**Backend:**
```powershell
cd C:\Users\trg16\Dev\Bricklayer2.0\dashboard\backend
$env:AUTOSEARCH_PROJECT="C:/Users/trg16/Dev/Bricklayer2.0/{project}"; uvicorn main:app --host 0.0.0.0 --port 8100 --reload
```

**Frontend:**
```powershell
cd C:\Users\trg16\Dev\Bricklayer2.0\dashboard\frontend
npm run dev
```

Open: http://localhost:3100

---

## Starting the Research Loop

> **IMPORTANT — always set `DISABLE_OMC=1` before launching BrickLayer.**
> BrickLayer runs in its own isolated `claude` subprocess. Without this, OMC hooks in the
> parent session will intercept agent spawns and replace BrickLayer's domain-specific agents
> (benchmark-engineer, quantitative-analyst, etc.) with OMC's generic agents, breaking the loop.

**New project — after question bank is ready:**
```bash
cd C:/Users/trg16/Dev/Bricklayer2.0/{project}
git init && git add . && git commit -m "chore: init {project} autoresearch"
git checkout -b {project}/$(date +%b%d | tr '[:upper:]' '[:lower:]')
DISABLE_OMC=1 claude --dangerously-skip-permissions "Read program.md and questions.md. Begin the research loop from the first PENDING question. If any file edit fails, follow the self-recovery steps in program.md immediately — do not pause. NEVER STOP."
```

**Resuming an existing project:**
```bash
cd C:/Users/trg16/Dev/Bricklayer2.0/{project}
git checkout -b {project}/$(date +%b%d | tr '[:upper:]' '[:lower:]')
DISABLE_OMC=1 claude --dangerously-skip-permissions "Read program.md, questions.md, and findings/synthesis.md. Resume the research loop from the first PENDING question. If any file edit fails, follow the self-recovery steps in program.md immediately — do not pause. NEVER STOP."
```

**PowerShell equivalent (Windows):**
```powershell
$env:DISABLE_OMC=1; claude --dangerously-skip-permissions "Read program.md and questions.md. Begin the research loop from the first PENDING question. NEVER STOP."
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
| `question-designer` | `.claude/agents/question-designer.md` | Once at init — generates questions.md |
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

## Common Issues

**`./start.sh` not recognized in PowerShell**: Use `bash start.sh ...` or run manually (see above).

**Loop stopped asking questions**: questions.md has no PENDING questions. Invoke `hypothesis-generator`.

**Simulation always HEALTHY**: SCENARIO PARAMETERS aren't stressed enough. Check `constants.py` thresholds.

**Finding is wrong**: Flag via dashboard or append `## Human Correction` block to the finding file, then add the correct understanding to `project-brief.md`.

**Edit to simulate.py keeps failing**: Run `git reset --hard HEAD` and retry. See loop self-recovery above.

**Dashboard not loading**: Make sure both backend (port 8100) and frontend (port 3100) are running.
Frontend must be built first: `cd dashboard/frontend && npm run build`.
