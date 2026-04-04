# Autoresearch Program — BrickLayer 2.0 Code Health Audit

**Authority tier: Tier 1 — never modify during campaigns.**

This is a static code audit campaign. There is no `simulate.py`. The research method
is reading source files, tracing call graphs, comparing configs, and producing findings.

---

## Setup

1. **Read these files for context** (do not modify):
   - `project-brief.md` — what to audit, domains, invariants
   - `questions.md` — the question bank (32 questions, 6 domains)
2. **Confirm the target codebase is reachable**: `C:/Users/trg16/Dev/Bricklayer2.0/`
3. **Confirm findings/ directory exists** — write one .md file per question answered.
4. **Begin the loop.**

---

## What You CAN Do

- Read any file in `C:/Users/trg16/Dev/Bricklayer2.0/` — full codebase access
- Read any file in `C:/Users/trg16/.claude/` — settings, agents, hooks
- Run `git log`, `git grep`, `git diff` to trace history
- Run `grep`/`rg` to search for patterns
- Write findings to `findings/{question-id}-{slug}.md`
- Mark questions DONE in `questions.md` after writing a finding

## What You CANNOT Do

- Modify `project-brief.md` or `program.md` — Tier 1, human only
- Modify `questions.md` without first writing a finding
- Modify any file outside of `bl-audit/findings/` and `bl-audit/questions.md`
- Install packages or run arbitrary scripts on the host system

---

## The Research Loop

Work through questions in `questions.md` in priority order (HIGH first).

### For each question:

1. **Pick** the next PENDING question
2. **Investigate**: read relevant source files, grep for patterns, check configs
3. **Reproduce**: confirm the issue exists (or doesn't)
4. **Write a finding** in `findings/{id}-{slug}.md` using the format below
5. **Update** the question status in `questions.md` → DONE
6. **Commit**: `git add findings/ questions.md && git commit -m "finding: {id} — {one-line summary}"`
7. **Continue** to the next PENDING question

---

## Finding Format

```markdown
# Finding: {ID} — {Title}

**Agent**: {agent name}
**Date**: {ISO date}
**Severity**: Critical | High | Medium | Low | Info
**Verdict**: CONFIRMED | FALSE_POSITIVE | INCONCLUSIVE

## Summary

One-paragraph description of what was found.

## Evidence

Exact file paths and line numbers. Paste relevant code snippets.

## Reproduction

Steps or grep commands to verify independently.

## Proposed Fix

Specific, actionable change. Reference exact files and lines.

## References

Other findings or files this relates to.
```

---

## Self-Recovery (File Write Failures)

If a file write fails:
1. `git status` — check dirty state
2. Re-read the target file before retrying the write
3. If still failing, write to a temp file with a `.tmp` suffix and note in the finding

---

## Wave Completion

After all 32 questions in Wave 1 are DONE:
1. Invoke the `synthesizer-bl2` agent to write `synthesis.md`
2. Commit: `git add . && git commit -m "chore: wave 1 complete — synthesis written"`
3. Stop the loop and report to the user

**NEVER STOP before all PENDING questions are answered.**
