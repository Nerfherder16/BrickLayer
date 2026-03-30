# Phase 2 — Ruflo Medium-Term Gaps

## Tasks

- [ ] **Task 1** — Create senior-developer agent and wire escalation chain in hierarchical-coordinator.md
- [ ] **Task 2** — Add masonry_verify_7point tool to masonry-mcp.js and extend verification.md agent
- [ ] **Task 3** — Create pseudocode.md skill and extend developer.md to read pseudocode artifacts

---

## Task 1 Detail — Senior Agent Escalation Tier

Gap 7: DEV_ESCALATE goes straight to Tim with no intermediate capable agent.

Current: developer x3 → diagnose-analyst → human
Target:  developer x3 → senior-developer → diagnose-analyst → human

### 1a. Create C:/Users/trg16/Dev/Bricklayer2.0/.claude/agents/senior-developer.md

Study C:/Users/trg16/Dev/Bricklayer2.0/.claude/agents/developer.md for the frontmatter format.

The senior-developer agent:
- Receives tasks that DEV_ESCALATEd after 3 developer attempts
- Has broader context authority: reads ALL related files, not just the immediate target
- Can propose architectural changes (not just bug fixes)
- Decision tree:
  1. Read all failure logs and test output
  2. Read all files imported by / related to the failing code
  3. Determine: implementation bug OR design problem?
  4. Implementation bug: fix with full surrounding context
  5. Design problem: propose refactor, implement it, run tests
  6. Output: SENIOR_DONE (tests pass) or SENIOR_ESCALATE (still failing, needs diagnose-analyst)
- Frontmatter description: "Senior developer for escalated failures — wider context, architectural authority"

### 1b. Extend C:/Users/trg16/Dev/Bricklayer2.0/.claude/agents/hierarchical-coordinator.md

Read the full current file. Find the DEV_ESCALATE handling section.

Add senior-developer as an intermediate escalation step:
- After worker reports DEV_ESCALATE → spawn senior-developer with task context + all failure logs
- If SENIOR_DONE → mark task DONE
- If SENIOR_ESCALATE → proceed to diagnose-analyst (existing path)

---

## Task 2 Detail — 7-Point Verification Tool

Gap 6: Tests + lint is the full bar. Security and deployment never checked.

### 2a. Add masonry_verify_7point to C:/Users/trg16/Dev/Bricklayer2.0/masonry/bin/masonry-mcp.js

Read the full masonry-mcp.js to understand the tool registration pattern (look for toolHandlers and how other tools like masonry_status are registered).

Add tool: masonry_verify_7point
Parameters: { project_path: string, strategy?: "conservative"|"balanced"|"aggressive" }

Run checks in sequence (skip on first hard fail unless strategy=balanced):
1. Unit tests: detect pytest (pyproject.toml/setup.py) or vitest/jest (package.json); run; pass/fail
2. Coverage: rerun with coverage flag; parse for >=80%; warn if <80, fail if <50
3. Integration tests: look for tests/integration/ dir; run if found; skip if absent
4. E2E tests: look for playwright.config.* or cypress.config.*; run if found; skip if absent
5. Security: run `bandit -r src/ -ll -q` (Python) or `npm audit --audit-level=high` (Node); skip if neither
6. Perf baseline: if .autopilot/perf-baseline.json exists, time test run and compare; warn if >20% slower
7. Docker: if Dockerfile exists, run `docker build -q -t masonry-verify-tmp .` then `docker rmi masonry-verify-tmp`; skip if no Dockerfile

Return structure:
{
  "passed": true/false,
  "strategy": "balanced",
  "checks": [
    {"name": "unit_tests", "status": "pass|fail|skip", "detail": "..."},
    ...7 items...
  ],
  "blocking_failure": null
}

### 2b. Extend C:/Users/trg16/Dev/Bricklayer2.0/.claude/agents/verification.md

Read full file. In the verdict section, add: if masonry_verify_7point tool is available, call it and include its results. Any "fail" (not "skip") from the 7-point check = FAIL verdict regardless of other checks.

---

## Task 3 Detail — SPARC Pseudocode Phase

Gap 2: No pseudocode phase. Developer agents build the right code for the wrong design.

### 3a. Create C:/Users/trg16/Dev/Bricklayer2.0/.claude/skills/pseudocode.md

New skill: /pseudocode (run after /plan, before /build)

Behavior:
- Read .autopilot/spec.md — fail with clear message if not found
- Spawn a Plan subagent (subagent_type: "Plan") with the spec content
- The Plan agent generates per-task pseudocode:
  - Plain English only (no code syntax)
  - For each task: inputs, outputs, step-by-step logic, edge cases, what NOT to do
- Write result to .autopilot/pseudocode.md
- Print confirmation and tell user to review before /build

### 3b. Extend C:/Users/trg16/Dev/Bricklayer2.0/.claude/agents/developer.md

Read full current file. At the START of the task execution instructions, add:

"Before writing any code: check if .autopilot/pseudocode.md exists. If it does, find and read the pseudocode entry for this task ID. Treat it as the implementation blueprint — the agreed logic before any code was written. The pseudocode defines WHAT to build; you decide HOW to build it."
