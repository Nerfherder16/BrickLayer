---
name: masonry-security-review
description: Security vulnerability scan — OWASP Top 10, hardcoded secrets, injection, auth bypass. "security review", "security audit", "check for vulnerabilities".
---

## masonry-security-review — Security Review

Perform a focused security audit. Check for vulnerabilities, misconfigurations, and unsafe patterns.

### Checklist

**1. Injection (OWASP A03)**
- [ ] SQL queries use parameterized statements (never string concatenation)
- [ ] Shell commands use array form, not string interpolation
- [ ] Template rendering sanitizes user input

**2. Authentication & Authorization (OWASP A01, A07)**
- [ ] Auth checks on every protected endpoint
- [ ] No hardcoded credentials or API keys
- [ ] Tokens have appropriate expiry
- [ ] Rate limiting on auth endpoints

**3. Sensitive Data (OWASP A02)**
- [ ] No secrets in code or config files
- [ ] Passwords hashed with bcrypt (cost >= 12) or argon2
- [ ] PII not logged
- [ ] HTTPS enforced for external calls

**4. Input Validation (OWASP A03, A08)**
- [ ] All API inputs validated with Pydantic/Zod schema
- [ ] File uploads restricted by type and size
- [ ] Redirect targets validated against allowlist

**5. Dependencies (OWASP A06)**
- [ ] No known-vulnerable packages (check npm audit / pip audit)
- [ ] No abandoned packages with open CVEs

**6. XSS (OWASP A03)**
- [ ] No dangerouslySetInnerHTML with user content
- [ ] Content-Security-Policy headers set

**7. Error Handling (OWASP A09)**
- [ ] Error messages don't expose stack traces or internal paths to users
- [ ] Logging captures events without leaking sensitive data

### How to Scan

For each relevant file:
1. Read it
2. Check each applicable item in the checklist
3. Search for patterns: `grep -r "exec\|eval\|shell\|password\|secret\|token" .`

### Report Format

```markdown
# Security Review — {project}

## Summary
| Category | Status |
|----------|--------|
| Injection | PASS/FAIL |
| Auth | PASS/FAIL |
| Secrets | PASS/FAIL |
| Input Validation | PASS/FAIL |
| Dependencies | PASS/FAIL |

## Findings

### 🔴 Critical
- **[File:Line]** {vulnerability} — {exploitation scenario} — {remediation}

### 🟡 Warning
- **[File:Line]** {issue}

### ℹ️ Informational
- {note}

## Verdict
**PASS** — No critical vulnerabilities found.
**FAIL** — {N} critical issues. Fix before deployment.
```
