# Campaign Context — inline-execution-audit

**Generated**: 2026-03-29
**Wave**: 1
**Questions**: 14 PENDING

## Project Summary

Pure research campaign investigating why Claude Code defaults to inline execution instead of delegating to specialist agents despite explicit CLAUDE.md routing directives. The core finding from bl-audit (M1.4) confirmed that the Mortar directive is advisory, not enforced. This campaign investigates root causes and enforcement solutions.

## Top Findings (Wave 1 Start — None Yet)

No findings yet. Wave 1 beginning.

## High-Weight Pending Hypotheses

- **D1.1 (HIGH)**: The "trivial vs. substantive" escape hatch overrides the absolute "every request" Mortar directive
- **D2.1 (HIGH)**: Hook system can only gate (allow/deny), not force Agent tool invocation
- **A1.1 (HIGH)**: Enforcement authority is exactly zero — not weak, structurally absent

## Recall Status

✓ Recall reachable (100.70.195.84:8200)

## Campaign Notes

- No simulate.py — Wave 0 pre-flight check SKIPPED (pure research, no simulation)
- Domain mapping: D1=instruction-authority, D2=enforcement-gap, D3=routing-coverage, D4=fleet-gaps, D5=behavioral-triggers
- Key constraint: hooks cannot force Agent tool use — only block other tools
- Known landmines from bl-audit: M1.4, D2.6, D5.1, M1.6, E1.9 — do not re-confirm, use as evidence
