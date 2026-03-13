# BrickLayer — Session Context Brief

Read this file at the start of every BrickLayer session before doing anything else.

---

## What BrickLayer Is

BrickLayer is an autonomous failure-boundary research framework. It runs structured
question campaigns against a live codebase to find bugs, coverage gaps, type errors,
race conditions, and security issues — then dispatches specialist agents to fix them.

**Current target**: Bricklayer

---

## Directory Layout

```
C:/Users/trg16/Dev/autosearch/
  simulate.py              # Main dispatcher (run from autosearch/ root)
  onboard.py               # Project setup tool
  agents/                  # Agent catalog — all always available
  handoffs/                # Cross-project change requests
  projects/
    bricklayer/                # This project's working directory
      project.json         # Project config
      questions.md         # Campaign question bank
      results.tsv          # Running verdict log (append-only)
      findings/            # Per-question detail reports (Q*.md)
      prepare.md           # This file
      .claude.json         # Per-project MCP isolation
```

---

## Starting Prompt (use at the top of every BrickLayer session)

```
Working directory: C:/Users/trg16/Dev/autosearch/

You are running BrickLayer against: **Bricklayer**
Target git: C:\Users\trg16\Dev\autosearch
Target live service: none

Read projects/bricklayer/prepare.md before doing anything else.
Confirm the git boundary rule before proceeding.

All findings stay in autosearch/projects/bricklayer/.
Fix agents operate within the target git only.
Cross-project changes go to autosearch/handoffs/ — never applied directly.

Start by reading your memory, then explore the target before designing questions.
```

---

## Target System

- **Codebase**: `C:\Users\trg16\Dev\autosearch`
- **Live service**: `none`
- **Stack** (auto-detected): Python

---

## Git Boundary Rule (HARD RULE — READ BEFORE EVERY RUN)

BrickLayer NEVER commits to any git repo other than the **target project** being analyzed.

| Role | Git repo | What lives here |
|------|----------|-----------------|
| BrickLayer framework | `autosearch/` | simulate.py, agents/, projects/, handoffs/ |
| Target project | `C:\Users\trg16\Dev\autosearch` | Source code being analyzed and fixed |
| Handoffs | `autosearch/handoffs/` | Cross-project change requests |

**Fix agents** read and modify only the **target project's git**.
**Cross-project changes**: create `autosearch/handoffs/handoff-{project}-{date}.md` instead.
**At end of every run**: check — were any cross-project changes needed? If yes, create the handoff doc.

---

## How to Run

```bash
cd C:/Users/trg16/Dev/autosearch

python recall/simulate.py --project bricklayer --list
python recall/simulate.py --project bricklayer --question Q1.1
python recall/simulate.py --project bricklayer --campaign
```

---

## Agent Catalog

All agents in `autosearch/agents/` are always available. The agent used for each
question is specified in that question's `**Agent**:` field. You do not need to
pre-configure which agents are enabled — just write the question to use the right one.

| Agent | Use for |
|-------|---------|
| security-hardener | Silent swallows, bare excepts, injection risks, missing validation |
| test-writer | Adding test coverage, characterizing bugs via tests |
| type-strictener | mypy errors, Any types, missing annotations |
| perf-optimizer | Slow endpoints, N+1 queries, inefficient loops |
| forge | Generating new questions from codebase scan |
