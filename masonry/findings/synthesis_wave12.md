# Wave 12 Synthesis — Masonry Self-Research

**Wave**: 12
**Questions**: D12.1, F12.1, F12.2, R12.1, R12.2, R12.3
**Completed**: 6/6
**Date**: 2026-03-21

---

## Summary

Wave 12 completes the multi-wave drift check investigation series and validates the full confidence-based monitoring pipeline end-to-end. All 6 questions resolved. Zero open issues from this wave.

---

## Findings Table

| ID | Verdict | Severity | Title |
|----|---------|----------|-------|
| D12.1 | DIAGNOSIS_COMPLETE | Info | masonry-subagent-tracker.js unstaged change — already committed (0bfc56a) |
| F12.1 | FIX_APPLIED | High | Confidence-based drift metric replaces verdict-based scoring |
| F12.2 | FIX_APPLIED | High | Scope-clear behavior added to sync_verdicts_to_agent_db.py |
| R12.1 | HEALTHY | Medium | Post-fix drift check: all 5 agents alert=ok |
| R12.2 | HEALTHY | Low | masonry_drift_check MCP tool end-to-end validation |
| R12.3 | HEALTHY | Low | ResearchAgentSig / build_dataset() field alignment |

---

## Key Accomplishments

### 1. Confidence-Based Drift Metric (F12.1)

The fundamental flaw in verdict-based scoring was resolved. Research agents correctly produce FAILURE verdicts when they find real problems — this is good agent behavior, not degradation. Verdict polarity was wrongly penalizing these agents:

- Before: research-analyst=critical (0.38 score from 11/28 FAILURE verdicts)
- Before: diagnose-analyst=critical (0.34 score from 20/34 FAILURE verdicts)
- After: All 5 agents alert=ok (mean confidence 0.88–1.00)

The fix threads through two files: `sync_verdicts_to_agent_db.py` (extracts and persists confidence floats) and `drift_detector.py` (prefers confidences when present, falls back to verdict scoring).

### 2. Idempotent Scoped Sync (F12.2)

A second flaw: `sync_verdicts_to_agent_db.py` was append-only for `verdicts`/`confidences`. When invoked with `--questions-md` (masonry scope), stale cross-project data persisted. Fix: zero all agents' verdicts and confidences before the scoped write. Now every scoped sync is authoritative and produces the same result regardless of prior state.

### 3. End-to-End Pipeline Validation (R12.1, R12.2, R12.3)

- **R12.1**: All 3 success criteria verified post-fix. Drift check pipeline is production-ready.
- **R12.2**: `masonry_drift_check` MCP tool invoked via Python; returns clean `{"reports": [...5 DriftReport...], "count": 5}`. All import paths resolve, Pydantic serialization works, failure modes handled gracefully.
- **R12.3**: `ResearchAgentSig` fields align exactly with `build_dataset()` output. `_weight` extra key is benign. Confidence stored as string matches OutputField type.

---

## Cross-Wave Drift Check Investigation Timeline

The 6-wave arc that produced a production-ready drift monitoring system:

| Wave | Finding | Discovery |
|------|---------|-----------|
| Wave 7 | D7.1 | Verdicts never populated — sync script didn't exist |
| Wave 9 | D9.1 | sync_verdicts_to_agent_db.py implemented |
| Wave 11 | F11.1 | Registry `extra="ignore"` — 46 agents load correctly |
| Wave 11 | F11.2 | Masonry-only sync now uses --questions-md scope |
| Wave 11 | R11.1 | Post-fix: fix-implementer ok, research/diagnose still critical |
| Wave 12 | F12.1 | Confidence metric replaces verdict scoring |
| Wave 12 | F12.2 | Scope-clear eliminates stale data |
| Wave 12 | R12.1 | All 5 agents alert=ok — pipeline complete |

---

## System State

| Component | Status |
|-----------|--------|
| Agent registry — 46 agents load | ✓ Verified (F11.1) |
| Wave-end verdict sync in synthesizer-bl2 | ✓ Verified (F11.3) |
| MIPROv2 best_score reads from compiled program | ✓ Fixed (F11.4) |
| Confidence extracted per agent | ✓ Verified (F12.1) |
| Confidence-based drift scoring | ✓ All 5 alert=ok |
| Scope-clear on --questions-md | ✓ Idempotent (F12.2) |
| masonry_drift_check MCP tool | ✓ End-to-end functional (R12.2) |
| ResearchAgentSig ↔ build_dataset alignment | ✓ Fully aligned (R12.3) |

---

## Open Issues for Wave 13

No critical or high-severity open issues from Wave 12. Wave 13 should investigate new domains. Candidate areas:

1. **DSPy optimization feedback loop** — With confidence extraction now working, does running MIPROv2 on existing training data produce measurably better agent output? Is there sufficient training data volume for useful optimization?
2. **Semantic routing calibration** — The 0.75 cosine similarity threshold and Ollama embedding model remain unvalidated against real request distributions (from Wave 1 research questions).
3. **Hook performance under load** — masonry-observe and masonry-guard run on every Write/Edit. What is the actual latency overhead per hook invocation? Does it compound during large builds?
4. **masonry_nl_generate quality** — The NL-to-question generation MCP tool was implemented but never quality-checked: does it produce BL 2.0-compatible questions with correct Mode fields?
5. **agent_onboard.py coverage** — New agents auto-onboard via the hook. Does the onboard script correctly handle all edge cases: agents with missing frontmatter, duplicate names, agents in ~/.claude/agents/ vs local?
