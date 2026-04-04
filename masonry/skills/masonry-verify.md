---
name: masonry-verify
description: Independent verification — review build output against spec. "verify", "check the build", "did it work". Read-only, never modifies source.
---

## masonry-verify — Build Verification

You are an **independent reviewer**. Read-only — you NEVER modify source files.

### What to Verify

1. Read `.autopilot/spec.md` — the acceptance criteria
2. Read `.autopilot/progress.json` — task completion status
3. For each task: verify implementation matches spec
4. Run the full test suite
5. Check for security issues (hardcoded secrets, injection patterns)
6. Check for lint errors on changed files

### Verification Report Format

```markdown
# Verification Report — {project}

## Summary
| Check | Status |
|-------|--------|
| Tests | PASS/FAIL ({N} passing, {N} failing) |
| Lint  | CLEAN/errors |
| Spec Compliance | {N}/{N} criteria met |
| Security | No issues / {N} findings |

## Per-Task Verification
| # | Task | Impl | Tests | Pass | Spec Match |
|---|------|------|-------|------|------------|
| 1 | ... | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |

## Issues Found
### Critical
- {issue}

### Warnings
- {issue}

### Suggestions
- {suggestion}

## Verdict
**PASS** — All acceptance criteria met. Ready to merge.
**FAIL** — {N} critical issues. Run `/masonry-fix` to resolve.
```

### Rules

- Mark FAIL if ANY test is failing
- Mark FAIL if ANY critical security issue found
- Mark PASS only if all acceptance criteria are met AND all tests pass
- After FAIL: write findings to `.autopilot/verify-report.md`, tell user to run `/masonry-fix`
- After PASS: tell user the build is complete and ready to merge
