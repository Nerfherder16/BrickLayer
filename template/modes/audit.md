# Audit Mode — Program

**Purpose**: Verify compliance against a known, explicit standard. Not finding unknown
failures (Diagnose) — checking a defined checklist. The standard exists before
the audit begins.

**Input**: A standard definition (OWASP Top 10, WCAG AA, your own style guide, a legal requirement)
**Verdict vocabulary**: COMPLIANT | NON_COMPLIANT | PARTIAL | NOT_APPLICABLE
**Evidence sources**: Source code, configuration, live system, design files

---

## Loop Instructions

### Pre-flight (required)

1. Read the standard being audited against — it must be explicit
   - If in `docs/` — read it
   - If a named standard (OWASP, WCAG, etc.) — retrieve current version via web/context7
2. Expand the standard into a checklist stored in `audit-checklist.md`
   Each item: `[ID] [requirement] [how to verify] [severity if violated]`
3. Map checklist items to questions.md — one question per checklist item or logical group

### Per-question

1. Each question maps to one or more checklist items
2. Gather evidence by checking the actual system against the requirement:
   - Read source code for the relevant code path
   - Run automated checks (lint, security scan, accessibility check)
   - Query live endpoints for runtime behavior
3. Assign verdict:
   - `COMPLIANT` — requirement is fully met with evidence
   - `NON_COMPLIANT` — requirement is violated; note severity and exact location
   - `PARTIAL` — partially met; describe what is missing
   - `NOT_APPLICABLE` — this requirement doesn't apply to this system; explain why
4. Every `NON_COMPLIANT` finding automatically generates a Diagnose question
   (the audit found the gap; Diagnose will find the root cause if needed)

### Wave structure

- Work through the checklist systematically — not hypothesis-driven
- No hypothesis generator — questions are derived from the checklist, not findings
- All checklist items must be answered (no saturation stop condition)
- Stop condition: all checklist items have a verdict

### Session end

Produce `audit-report.md`:
- Summary table: COMPLIANT / NON_COMPLIANT / PARTIAL / NOT_APPLICABLE counts
- All NON_COMPLIANT findings with severity and location
- Compliance score: (COMPLIANT + NOT_APPLICABLE) / total items
- **Pass/Fail verdict**: if any HIGH-severity item is NON_COMPLIANT → overall FAIL
