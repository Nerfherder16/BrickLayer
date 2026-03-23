# Wave 11 Synthesis — Masonry Self-Research Campaign

**Wave**: 11
**Questions answered**: 7 (F11.1, F11.2, R11.1, F11.3, F11.4, R11.2)
**Verdicts**: 3 FIX_APPLIED, 2 WARNING, 2 HEALTHY

---

## Wave 11 Overview

Wave 11 closed all four P2/P3 issues surfaced by Wave 10 and validated the drift check end-to-end. Three fixes were applied: `AgentRegistryEntry` now uses `extra="ignore"` (F11.1), masonry-only verdict sync is documented and working (F11.2), `synthesizer-bl2.md` now auto-invokes verdict sync at wave end (F11.3), and `optimize_agent()` now reads `optimized.score` instead of the non-existent `optimizer.best_score` (F11.4). Two remaining WARNING issues were identified and scoped to Wave 12: stale verdict persistence when sync scope is narrowed, and the semantic mismatch between finding verdict and agent quality for research agents.

---

## Findings Summary

| QID | Verdict | Severity | Summary |
|-----|---------|----------|---------|
| F11.1 | FIX_APPLIED | High | `AgentRegistryEntry` extra="ignore" — all 46 agents load, no skipping errors |
| F11.2 | WARNING | Medium | Masonry-only sync works; deeper issue: verdict ≠ agent quality for research agents |
| R11.1 | WARNING | Medium | Registry fix verified; stale verdict persistence + verdict≠quality false positives remain |
| F11.3 | FIX_APPLIED | Medium | `sync_verdicts_to_agent_db.py` integrated into `synthesizer-bl2.md` wave-end workflow |
| F11.4 | FIX_APPLIED | Low | `best_score` fix: reads `optimized.score` from compiled program (not non-existent `optimizer.best_score`) |
| R11.2 | HEALTHY | Low | F10.2 `cmd.exe /c` fix verified — no regression for absolute ruff paths or npx resolution |

---

## Key Achievements This Wave

### 1. Registry Fully Operational (F11.1)
All 46 agents in `agent_registry.yml` now load correctly. The `AgentRegistryEntry` schema change from `extra="forbid"` to `extra="ignore"` absorbs the five monitoring fields added by `masonry-agent-onboard.js`. The registry count is now stable at 46 (was 30 due to silent skipping of 14 agents with onboarding-added fields).

### 2. Drift Check Now Accurate for fix-implementer (F11.2 + R11.1)
`fix-implementer` correctly shows `alert=ok` (99% FIX_APPLIED verdicts, drift=−16%). This is the primary validation that both the registry fix (F11.1) and the masonry-scoped sync (F11.2) are working together correctly.

### 3. Verdict Sync Automated (F11.3)
`synthesizer-bl2.md` now automatically invokes `sync_verdicts_to_agent_db.py` at wave end, non-blocking. Starting from Wave 12, every synthesis will refresh the drift detection data without manual intervention.

### 4. DSPy Optimization Score Fixed (F11.4)
The source-level fix: after `MIPROv2.compile()`, the best score is stored on the returned program as `optimized.score` (not on the optimizer as `optimizer.best_score`). When Kiln triggers a real optimization, the score displayed will now be meaningful (0.0–1.0) rather than always showing 0%.

### 5. F10.2 Regression Verified Absent (R11.2)
The `cmd.exe /c` pattern correctly handles absolute ruff paths with spaces. Node.js quotes space-containing arguments when building the `CreateProcess` command line. No regression for any linting path (absolute ruff, npx prettier, npx eslint).

---

## Residual Issues (Wave 12 Targets)

### P2 — Verdict-as-Quality Metric Semantic Mismatch (F11.2 deferred)
The drift detector scores FAILURE verdicts as 0.0 (bad agent performance). For research agents (`research-analyst`, `diagnose-analyst`), FAILURE verdicts represent correct findings — the system under investigation has a problem. This produces false `alert=critical` for both agents. The fix (deferred to Wave 12): use agent confidence scores as the quality metric instead of finding verdicts. All findings have a `**Confidence**:` field (float 0.0–1.0) that directly measures agent certainty.

### P2 — Stale Verdict Persistence in agent_db.json (R11.1 new issue)
`sync_verdicts_to_agent_db.py` is update-only: when sync scope is narrowed from all-projects to masonry-only, agents no longer in the current scope retain their old verdicts indefinitely (`compliance-auditor` retains 3 cross-project verdicts). The fix: when `--questions-md` is specified, zero-out `verdicts` for all agents before writing results, OR add a `--clear-out-of-scope` flag.

---

## Cumulative P1/P2/P3 Summary

| Priority | Issue | Status |
|----------|-------|--------|
| P1 | Phase 16 DSPy training data complete | ✅ RESOLVED (Waves 8-9) |
| P1 | D7.1 verdicts never populated | ✅ RESOLVED (Wave 9 D9.1) |
| P2 | R9.2 Rule 5 regex mismatch | ✅ RESOLVED (Wave 10 F10.1) |
| P2 | R6.1 Windows path-with-spaces | ✅ RESOLVED (Wave 10 F10.2) |
| P2 | AgentRegistryEntry extra_forbidden excludes 14 agents | ✅ RESOLVED (Wave 11 F11.1) |
| P2 | Cross-project verdict contamination in drift check | ✅ RESOLVED (Wave 11 F11.2) |
| P3 | best_score always 0.0 in optimize result | ✅ RESOLVED (Wave 11 F11.4) |
| P3 | sync_verdicts_to_agent_db.py manual-only | ✅ RESOLVED (Wave 11 F11.3) |
| P2 | Verdict≠quality metric semantic mismatch | 🔴 NEW — Wave 12 |
| P2 | Stale verdict persistence on scope narrowing | 🔴 NEW — Wave 12 |

---

## Next Wave Priorities

1. **Confidence-based drift metric** (P2 → F12.1): Replace `_score_verdict()` with a confidence-based metric in `drift_detector.py`. Extract `**Confidence**:` float from findings and use mean confidence as the quality signal. Research agents with high-confidence FAILURE findings should show "ok"; uncertain agents should show "warning/critical".

2. **Scope-clear sync behavior** (P2 → F12.2): Add `--clear-all-verdicts` behavior to `sync_verdicts_to_agent_db.py` when `--questions-md` is specified — zero out `verdicts` for all agents before the scoped write, ensuring stale data from prior broader scans is purged.

3. **Drift check with confidence-based metric** (R12.1): Re-run `masonry_drift_check` after F12.1 + F12.2. Verify that research-analyst, diagnose-analyst, and design-reviewer show sensible alert levels based on confidence (not verdict polarity).

4. **Validate MCP tool `masonry_drift_check` end-to-end** (R12.2): The `masonry_drift_check` MCP tool has never been tested end-to-end since the registry and drift metric fixes. Verify it reads the correct agent_db, runs the drift check, and returns structured results without error.

5. **DSPy signature field coverage** (R12.3): Verify `ResearchAgentSig` field names match the actual `findings/*.md` structure used by `build_dataset()`. R5.2 identified a field mismatch risk — confirm it's been resolved or document the gap.
