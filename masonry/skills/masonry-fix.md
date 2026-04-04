---
name: masonry-fix
description: Targeted fix mode — fix issues found by /masonry-verify using worker agents. "fix the issues", "fix build". Requires a verify report.
---

## masonry-fix — Targeted Fixes

You are an **ORCHESTRATOR** for targeted fixes. Read `.autopilot/verify-report.md` for the issue list.

### Prerequisites

1. Read `.autopilot/verify-report.md` — refuse if missing (tell user to run `/masonry-verify` first)
2. Set `.autopilot/mode` → "fix"

### Fix Loop

For each Critical issue in the verify report:

**1. Spawn a fix agent:**
```
Task: "Fix the following issue found by masonry-verify:
{issue description}
{relevant file paths}
{error output if available}
Apply the minimum change needed. Run tests after fixing. Report: what you changed, tests now passing (Y/N)."
```

**2. Validate:** Run tests after each fix

**3. Commit:** `git commit -m "fix: {issue description} [masonry-fix]"`

### Completion

After all Critical issues fixed:
1. Clear `.autopilot/mode`
2. Run `/masonry-verify` automatically
3. If PASS: done. If FAIL: loop again (max 3 cycles, then report to user)

### Rules

- Fix ONLY what the verify report flagged — no scope creep
- Never refactor unrelated code
- 3-cycle max: if still failing after 3 fix rounds, stop and ask user for input
