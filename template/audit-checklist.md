# Audit Checklist — [PROJECT NAME]

Audit mode reads this file to determine compliance checks.
Define the standard being audited against and the specific checks.

## Standard

[Name the standard: e.g., "Tim's frontend design philosophy", "OWASP Top 10", "ERISA compliance"]

## Checks

| ID | Check | Pass Condition | Fail Condition | Auto-checkable? |
|----|-------|---------------|----------------|-----------------|
| A1 | [description] | [pass] | [fail] | Yes (grep) / No (manual) |

## Verdict thresholds

- COMPLIANT: 0 fails
- PARTIAL: 1-3 fails, none are structural
- NON_COMPLIANT: Any structural violation OR 4+ total fails
