# BrickLayer — Session Context Brief

Read this file at the start of every BrickLayer session before doing anything else.
It tells you what BrickLayer is, where everything lives, and how to resume work.

---

## What BrickLayer Is

BrickLayer is an autonomous failure-boundary research framework. It runs structured
question campaigns against a live codebase to find bugs, coverage gaps, type errors,
race conditions, and security issues — then dispatches specialist agents to fix them.

**This is a general-purpose tool.** It can target any Python codebase. The current
target system is Recall (see below), but the framework is not Recall-specific.

---

## Directory Layout

```
C:/Users/trg16/Dev/autosearch/
  recall/
    simulate.py          # Main dispatcher — runs questions, records verdicts
    questions.md         # Campaign question bank (all waves)
    results.tsv          # Running verdict log (append-only)
    findings/            # Per-question detail reports (Q*.md)
    prepare.md           # This file — session context brief
  agents/
    SCHEMA.md            # Agent tier definitions (draft/candidate/trusted)
    forge.md             # Generates new questions from codebase scan
    crucible.md          # Benchmarks agent quality on known-answer cases
    security-hardener.md # Fixes silent swallows, bare excepts, injection risks
    test-writer.md       # Adds test coverage, characterizes bugs via tests
    type-strictener.md   # Narrows Any types, adds missing annotations
    perf-optimizer.md    # Identifies and fixes performance bottlenecks
```

---

## Starting Prompt Template (use this at the top of every BrickLayer session)

```
Working directory: C:/Users/trg16/Dev/autosearch/recall/

You are running BrickLayer against: **[TARGET PROJECT NAME]**
Target git: [TARGET GIT PATH]
Target live service (if applicable): [URL or "none"]

Read prepare.md before doing anything else. Confirm the git boundary rule before proceeding.
All findings stay in autosearch/. Fix agents operate within the target git only.
Cross-project changes go to autosearch/handoffs/ — never applied directly.

Start by reading your memory, then explore the target before designing questions.
```

---

## Target System (Current)

- **Codebase**: `C:/Users/trg16/Dev/Recall/`
- **Live service**: `http://192.168.50.19:8200`
- **Stack**: FastAPI, Qdrant, Neo4j, Redis, PostgreSQL, Ollama

Check service health before running performance questions:
```bash
curl http://192.168.50.19:8200/health
```

Performance questions (Q1.x) require the live service. All other modes work
against the local source and tests with no network dependency.

---

## Git Boundary Rule (HARD RULE — READ BEFORE EVERY RUN)

BrickLayer NEVER commits to any git repo other than the **target project** being analyzed.

| Role | Git repo | What lives here |
|------|----------|-----------------|
| BrickLayer framework | `autosearch/` | simulate.py, agents/, questions.md, results.tsv, findings/, prepare.md |
| Target project | e.g. `Dev/Recall/` or `Dev/autosearch/` | Source code being analyzed and fixed |
| Handoffs | `autosearch/handoffs/` | Cross-project change requests |

**Fix agents** (security-hardener, test-writer, etc.) operate entirely within the **target project's git**. BrickLayer does not touch their code — it reads, analyzes, and proposes. If an agent produces a fix, that commit belongs to the target project, not autosearch.

**Cross-project changes**: If a campaign against project X reveals that project Y also needs a change, do NOT make it. Instead:
1. Create `autosearch/handoffs/handoff-{project-Y}-{YYYY-MM-DD}.md` describing the required change
2. Note it explicitly in the end-of-run summary
3. The handoff doc is the trigger for the next BrickLayer run against project Y

**At end of every campaign run**: explicitly check — were any cross-project changes needed? If yes, create the handoff doc before ending the session.

---

## How to Run

```bash
cd C:/Users/trg16/Dev/autosearch/recall

# List all questions and their current status
python simulate.py --list

# Run a specific question
python simulate.py --question Q6.1

# Run all PENDING questions in a wave (manual loop for now)
for q in Q6.1 Q6.2 Q6.3; do python simulate.py --question $q; done
```

Modes: `performance` (load tests), `correctness` (pytest), `quality` (code analysis),
`agent` (dispatches a specialist agent to fix a finding).

---

## Campaign Status Reference

Waves are cumulative — each wave targets blindspots and follow-ups from the prior wave.

| Wave | Questions | Focus |
|------|-----------|-------|
| Wave 1 (Q1–Q4) | Q1.1–Q4.6 | Initial baseline: load, correctness, quality, agent fixes |
| Wave 2 (Q5) | Q5.1–Q5.7 | Follow-up on Wave 1 failures + new blindspot areas |
| Wave 3 (Q6) | Q6.1–Q6.7 | Post-fix audit: caller contracts, deprecations, async safety |

Check `python simulate.py --list` for live status. Do not re-run HEALTHY questions
unless you have reason to believe the underlying code changed.

---

## Agent Dispatch Rules

When a Q1–Q3 question returns FAILURE or WARNING, create a matching Q4/Q5/Q6 agent
question in `questions.md` using this pattern:

```markdown
## Q{N} [AGENT] {agent-name} → {short description}
**Mode**: agent
**Agent**: {security-hardener | test-writer | type-strictener | perf-optimizer}
**Finding**: {source question ID}
**Source**: {file or directory path}
**Hypothesis**: {what the agent will do}
**Verdict threshold**:
- HEALTHY: {evidence of success}
- WARNING: {partial success}
- INCONCLUSIVE: agent produced no structured output
```

Agent selection guide:
- Silent swallows, bare excepts, missing validation → `security-hardener`
- Missing test coverage, characterizing a bug via tests → `test-writer`
- mypy errors, `Any` types, missing annotations → `type-strictener`
- Slow endpoints, N+1 queries, inefficient loops → `perf-optimizer`

---

## Known Architectural Debt (Do Not Re-Investigate Without New Evidence)

- **Q3.3 / write_guard TOCTOU**: False positive. `write_guard.py` has no Redis SETNX.
  The actual concurrent write guard is the asyncio.Lock on `/admin/consolidate` (Q4.4).
- **Q3.5 / API error handling**: Partially fixed by Q4.1 (18 swallows hardened).
  Remaining inconsistencies are architectural — require route redesign, not a quick fix.
- **Q4.3 / consolidation graph cycles**: False positive. Neither `consolidation.py` nor
  `auto_linker.py` traverses the graph. Only `neo4j_store.find_related()` does, and it
  has three independent cycle guards.

---

## What to Work On Next (Backlog)

1. **`forge` agent integration** — auto-generate Q questions from codebase scan instead
   of hand-authoring them. `forge.md` exists in agents/ but is not wired into simulate.py.

2. **Inter-agent handoffs** — agents currently run in isolation. The output of
   security-hardener (which files were changed, which paths were added) should feed
   directly into test-writer as input context for the next question.

3. **`--campaign` flag** — run all PENDING questions in sequence without manual
   `--question` calls one at a time.

4. **Campaign summary report** — generate a human-readable markdown report from
   `results.tsv` and `findings/` after a campaign run.

5. **`crucible` agent** — benchmark agent quality on known-answer test cases to detect
   when an agent's output is confident-sounding but factually wrong.

6. **Verdict re-evaluation** — when a Q4/Q5/Q6 agent fixes something, automatically
   re-run the source Q1–Q3 question to confirm the original finding is cleared.

---

## Bugs Found in Recall (Logged by BrickLayer Agents)

- `bug_warm_injection_embeddings.md` — `logger.warning("write_guard_warm_failed",
  error=str(exc))` uses structlog-style kwargs on stdlib logger, raising TypeError in
  the except block. Fixed in commit `584e000`.
