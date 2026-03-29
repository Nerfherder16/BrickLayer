# Monitor Targets — inline-execution-audit

Metrics to track as Wave 2 fixes are deployed. Baselines from Wave 1 findings.

---

## silent-zone-hit-rate

**Definition**: Percentage of session prompts that exit masonry-prompt-router.js via the medium+no-intent path (line 195 `!hasSignal`), producing zero routing signal.

**Measurement**: Count exits at `if (!hasSignal) process.exit(0)` vs. total prompts processed per session.

**Wave 1 baseline**: 40-60% of developer session prompts (D5.2 WARNING)

| Threshold | Level | Action |
|-----------|-------|--------|
| ≤ 30% | HEALTHY | Target state after F2.2 + R2.2 fixes |
| 31-50% | WARNING | Monitor — Wave 1 baseline upper bound |
| > 50% | FAILURE | Regression — router coverage degraded above Wave 1 baseline |

**Expected improvement triggers**:
- F2.2 (additionalContext channel): does not change hit rate, but increases compliance when signal IS emitted
- R2.2 (INTENT_RULES expansion): directly reduces hit rate by capturing spec+build and maintenance-verb prompts
- D2.3 → F2.3 (receipt system): indirectly reduces hit rate by making routing signal matter

**Source findings**: D5.1, D5.2

---

## multi-turn-routing-signal-rate

**Definition**: Percentage of conversation turns in multi-step sessions that receive a non-empty routing hint (vs. complete routing silence).

**Measurement**: Count turns with `additionalContext` output containing `[ROUTING]` vs. total turns in sessions where Turn 1 received a routing signal (i.e., sessions with at least one routed turn).

**Wave 1 baseline**: Turn 1 = signal present; Turn 2+ = complete silence on every session (D3.2 FAILURE). Approximate Turn 2+ signal rate: ~0-5%.

| Threshold | Level | Action |
|-----------|-------|--------|
| ≥ 40% | HEALTHY | Target state after D2.5 → last_route persistence fix |
| 20-39% | WARNING | Partial coverage — follow-up detection patterns incomplete |
| < 20% | FAILURE | Regression — multi-turn collapse persists, near Wave 1 baseline |

**Expected improvement triggers**:
- D2.5 (last_route persistence design) → implementation: directly improves Turn 2+ signal rate by inheriting prior turn's routing decision on continuation prompts
- R2.2 (maintenance verb INTENT_RULES): improves Turn 2+ rate for prompts with recognizable maintenance verbs, independently of last_route

**Source findings**: D3.2, D5.1, D5.2
