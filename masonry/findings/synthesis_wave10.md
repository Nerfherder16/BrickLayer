# Wave 10 Synthesis — Masonry Self-Research Campaign

**Wave**: 10
**Questions answered**: 6 (F10.1, R10.1, R10.2, R10.3, D10.1, F10.2)
**Verdicts**: 2 FIX_APPLIED, 2 WARNING, 2 HEALTHY

---

## Wave 10 Overview

Wave 10 closed the remaining open issues from Waves 6-9 and surfaced two new structural defects in the drift detection pipeline. Two fixes were applied: `_MODE_FIELD_RE` now matches `**Operational Mode**:` (F10.1), and `runBackground()` on Windows now uses the safe `cmd.exe /c` spawn pattern (F10.2). The drift check ran for the first time against real data and revealed a schema mismatch that excludes 14 agents from registry validation (R10.2), plus cross-project verdict contamination producing false "critical drift" alerts.

---

## Findings Summary

| QID | Verdict | Severity | Summary |
|-----|---------|----------|---------|
| F10.1 | FIX_APPLIED | High | `_MODE_FIELD_RE` extended to match `**Operational Mode**:` — Rule 5 now fires for BL 2.0 campaign questions |
| R10.1 | WARNING | Medium | `sync_verdicts_to_agent_db.py` not integrated into wave-end workflow — manual invocation required |
| R10.2 | WARNING | Medium | Drift check produces output but: 14 agents skipped by registry (extra_forbidden), cross-project FAILURE verdicts inflate drift scores |
| R10.3 | WARNING | Low | `masonry_optimize_agent` will make Anthropic API calls during compile; `_weight` noise in examples; `best_score` always 0.0 |
| D10.1 | HEALTHY | Info | `masonry_drift_check` reads `agent_db.json` fresh from disk — no stale cache |
| F10.2 | FIX_APPLIED | Low | `runBackground()` Windows fix applied — `cmd.exe /c` pattern eliminates path-with-spaces silent failures |

---

## Key Achievements This Wave

### 1. Deterministic Routing Rule 5 Restored (F10.1)
BL 2.0 campaign questions with `**Operational Mode**: research/diagnose/fix/validate` now route deterministically via Rule 5. Previously, all campaign questions fell through to Ollama semantic lookup (Layer 2). The one-line regex fix `(?:Operational\s+)?` is backward-compatible — `**Mode**:` also continues to work.

### 2. Windows Path-With-Spaces Bug Fixed (F10.2)
R6.1 (Wave 6) documented but deferred the path quoting issue. F10.2 applies the Option B fix from R6.1 — matching the F4.2 `llm_router.py` pattern exactly. Background formatters (ruff, prettier, eslint) will now work on Windows paths with spaces.

### 3. First Live Drift Check Run (R10.2)
`masonry_drift_check` is confirmed functional with real data. The output structure (DriftReport per agent, with alert_level and recommendation) is correct. The data quality issues (registry exclusions, cross-project contamination) are fixable.

---

## New Issues Surfaced This Wave

### P2 — `AgentRegistryEntry` Extra-Forbidden Rejects 14 Agents (R10.2)
`model_config = ConfigDict(extra="forbid")` in `AgentRegistryEntry` rejects any YAML entry with fields not in the schema. The `masonry-agent-onboard.js` hook adds `dspy_status`, `drift_status`, `last_score`, `runs_since_optimization`, `registrySource` fields during auto-onboarding. These 14 agents (including `fix-implementer` with 25 verdicts) are excluded from drift checking. Fix: change `extra="forbid"` to `extra="ignore"` in `AgentRegistryEntry`.

### P2 — Cross-Project Verdict Contamination in Drift Check (R10.2)
`sync_verdicts_to_agent_db.py` scans all BL2.0 projects, attributing FAILURE verdicts from unrelated campaigns to masonry specialist agents. For `research-analyst`, 11/19 verdicts are FAILURE (from other projects), producing current_score=0.34 vs. baseline=0.85 → "critical drift" false positive. Fix: pass explicit `--questions-md masonry/questions.md` when syncing masonry-specific verdicts.

### P3 — `best_score` Always 0.0 (R10.3)
`MIPROv2` does not expose a `best_score` attribute. The optimizer result dict always shows `"score": 0.0`. Kiln cannot display actual optimization quality. Fix: use `optimizer.valset_score` or compute the score from the metric on a held-out validation set after compile.

### P3 — `sync_verdicts_to_agent_db.py` Manual-Only (R10.1)
No wave-end automation calls the verdict sync script. Drift data becomes stale after each new wave unless manually run.

---

## Cumulative P1/P2/P3 Summary

| Priority | Issue | Status |
|----------|-------|--------|
| P1 | Phase 16 DSPy training data complete | ✅ RESOLVED (Waves 8-9) |
| P1 | D7.1 verdicts never populated | ✅ RESOLVED (Wave 9 D9.1) |
| P2 | R9.2 Rule 5 regex mismatch | ✅ RESOLVED (Wave 10 F10.1) |
| P2 | R6.1 Windows path-with-spaces | ✅ RESOLVED (Wave 10 F10.2) |
| P2 | AgentRegistryEntry extra_forbidden excludes 14 agents | 🔴 NEW — Wave 11 |
| P2 | Cross-project verdict contamination in drift check | 🔴 NEW — Wave 11 |
| P3 | best_score always 0.0 in optimize result | 🔴 NEW — Wave 11 |
| P3 | sync_verdicts_to_agent_db.py manual-only | 🔴 NEW — Wave 11 |

---

## Next Wave Priorities

1. **Fix `AgentRegistryEntry` extra_forbidden** (P2 → F11.1): Change `extra="forbid"` to `extra="ignore"` to allow onboarding-added fields
2. **Scope verdict sync to masonry project** (P2 → F11.2): Pass `--questions-md masonry/questions.md` in sync invocation, or refactor sync to support per-project mode
3. **Validate fixed drift check** (R11.1): After F11.1+F11.2, re-run drift check and verify all 44 agents are checked with masonry-only verdicts
4. **Integrate verdict sync into synthesizer-bl2** (R10.1 → F11.3): Add non-blocking `sync_verdicts_to_agent_db.py` invocation to wave-end workflow
5. **Fix best_score = 0.0** (R10.3 → F11.4): Find the correct attribute or compute score from post-compile metric evaluation
