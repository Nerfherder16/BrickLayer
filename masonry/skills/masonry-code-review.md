---
name: masonry-code-review
description: Comprehensive code review — logic, maintainability, security, API contracts. "review code", "review this PR", "code review".
---

## masonry-code-review — Code Review

Perform a comprehensive review of the code changes. Read the diff or specified files, then produce a structured review.

### What to Review

1. **Logic defects** — bugs, off-by-one errors, incorrect conditions, missing edge cases
2. **Maintainability** — naming, complexity, duplication, SOLID principles
3. **Security** — injection patterns, exposed secrets, auth bypass, XSS, unsafe deserialization
4. **Performance** — N+1 queries, blocking operations, unnecessary allocations
5. **API contracts** — breaking changes, missing validation, error handling
6. **Test coverage** — are the important paths tested?

### How to Get the Diff

If reviewing uncommitted changes:
```bash
git diff HEAD
```

If reviewing a specific commit:
```bash
git show {commit}
```

If reviewing specific files: read them directly.

### Review Report Format

```markdown
# Code Review — {files/commit/PR}

## Summary
{2-3 sentences on the overall quality and purpose of the changes}

## Findings

### 🔴 Critical (must fix before merge)
- **[File:Line]** {issue} — {why it's a problem} — {how to fix}

### 🟡 Warning (should fix)
- **[File:Line]** {issue}

### 🔵 Suggestion (consider)
- **[File:Line]** {suggestion}

### ✅ Good Patterns
- {what was done well}

## Verdict
**APPROVE** — No critical issues.
**CHANGES REQUESTED** — {N} critical issues must be resolved.
```

### Rules

- Be specific — cite file names and line numbers
- Severity matters — distinguish blocking issues from suggestions
- Praise what's good — balanced reviews are more useful
- Do not refactor during review — only report findings
