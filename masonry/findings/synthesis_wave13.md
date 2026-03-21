# Wave 13 Synthesis — Masonry Self-Research

**Wave**: 13
**Questions**: R13.1, R13.2, D13.1, R13.3, R13.4, R13.5
**Completed**: 6/6
**Date**: 2026-03-21

---

## Summary

Wave 13 fully audits the phase-16 full-fleet scoring pipeline (8c73818) and the masonry optimization data stack. Key finding: the two training pipelines (`scored_all.jsonl` and `build_dataset()`) are deliberately parallel with no overlap — masonry findings are excluded from the scoring pipeline by design. The `build_dataset()` path has 125 well-weighted examples across 5 agents, sufficient for MIPROv2 on 4/5 agents. The `masonry_nl_generate` tool produces Trowel-compatible questions (via regex compatibility) with minor format deviations.

---

## Findings Table

| ID | Verdict | Severity | Title |
|----|---------|----------|-------|
| R13.1 | WARNING | Medium | `score_all_agents.py` runs correctly; masonry findings excluded by design |
| R13.2 | WARNING | Medium | `score_routing.py` valid but `downstream_success` structurally blocked at 0 |
| D13.1 | DIAGNOSIS_COMPLETE | Low | score=60 = null confidence → 0 pts on calibration dimension |
| R13.3 | WARNING | Medium | `backfill_agent_fields.py` excludes masonry; F/V prefixes missing from map |
| R13.4 | HEALTHY | Low | 125 examples, 4/5 agents MIPROv2-ready; pipelines confirmed parallel |
| R13.5 | WARNING | Low | nl_generate Trowel-compatible; `**Test**:` vs `**Method**:` deviation |

---

## Architectural Discovery: Two Parallel Training Pipelines

The most significant finding of Wave 13:

```
scored_all.jsonl (cross-project fleet)           build_dataset() (masonry-scoped)
  ← score_findings.py                              ← training_extractor.py
  ← score_code_agents.py                           ← masonry/findings/*.md
  ← score_ops_agents.py                            ← question_id attribution
  ← score_routing.py                               ← conf-based quality gate
  [masonry/ EXCLUDED]                              [masonry ONLY]
```

Both are intentional. `scored_all.jsonl` trains the full 46-agent fleet across all BL projects. `build_dataset()` provides masonry-specific signal for Masonry's own research agents (fix-implementer, diagnose-analyst, etc.). They serve different optimization targets.

---

## Data Readiness for MIPROv2

| Agent | build_dataset() n | Ready? |
|---|---|---|
| fix-implementer | 45 | ✓ Strong |
| diagnose-analyst | 37 | ✓ Strong |
| research-analyst | 31 | ✓ Strong |
| design-reviewer | 10 | ✓ Marginal |
| benchmark-engineer | 2 | ✗ Insufficient |

First optimization run can proceed for fix-implementer, diagnose-analyst, research-analyst now.

---

## Open Issues for Wave 14

1. **`downstream_success` gap in routing scorer**: `masonry-subagent-tracker.js` only writes "start" events, never "finding" events. Mortar routing scores are capped at 70/100. A "finding" event emitter (in masonry-observe.js or a new hook) would unlock the remaining 30 points.

2. **Confidence ceiling in rubric**: The `confidence_calibration` dimension rewards confidence in 0.5–0.95 range. Masonry findings tend to 0.97–0.99 (overconfident per rubric). ADBP findings are null (uncalibrated). Neither profile hits the 100-point maximum. Wave 14 could explore whether the rubric ceiling is appropriate or whether masonry findings should target lower confidence values for better rubric scores.

3. **nl_entry format drift**: `masonry_nl_generate` uses `**Test**:` and `**Verdict threshold**:` instead of BL 2.0's `**Method**:` and `**Success criterion**:`. Agents receive degraded context. A one-line template update in `_question_to_md()` would align the format.

4. **F/V prefix gaps in backfill**: fix-implementer (F*) and validate (V*) findings are not covered by `DEFAULT_PREFIX_MAP`. If the masonry exclusion were ever lifted, these 52 findings would remain unattributed.
