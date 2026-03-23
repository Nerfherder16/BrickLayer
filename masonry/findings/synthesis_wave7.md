# Wave 7 Synthesis — Masonry Self-Research

**Wave**: 7
**Questions**: F7.1, F7.2, R7.1, D7.1, V7.1, R7.2
**All questions**: DONE
**Date**: 2026-03-21

---

## Verdicts Summary

| ID | Question (short) | Verdict | Severity |
|---|---|---|---|
| F7.1 | `_tool_masonry_route` error fallback schema fix | FIX_APPLIED | Medium |
| F7.2 | `onboard_agent.py` atomic registry writes | FIX_APPLIED | Medium |
| R7.1 | `build_dataset()` degenerate training inputs | FAILURE | High |
| D7.1 | `run_drift_check()` verdicts never populated | FAILURE | Medium |
| V7.1 | `masonry_drift_check` missing `agent_db_path` default | FAILURE | Low |
| R7.2 | `extract_training_data()` agent attribution (Method: field) | HEALTHY | Info |

---

## Pattern Analysis

### Two fixes applied — cumulative atomic-write remediation complete

F7.1 closes the V6.1 schema mismatch: `_tool_masonry_route` now returns `"layer": "fallback"` (str), includes `reason` (required field), and matches `decision.model_dump()` shape exactly.

F7.2 completes the atomic-write remediation campaign that started in Wave 5. All three non-atomic write races are now fixed:
- `masonry-guard.js` strike counter (F5.1) — Wave 5
- `masonry-subagent-tracker.js` agents.json (F5.3) — Wave 5
- `onboard_agent.py` agent_registry.yml (F7.2) — Wave 7

### DSPy Phase 16 remains multiply blocked

Wave 7 identified two new blockers for DSPy training on top of the existing D6.2 (missing `masonry_optimize_agent` MCP tool):

**R7.1 (High)**: Training examples have degenerate inputs — `question_text` is the question ID string ("R5.1"), `project_context` is always "". MIPROv2 requires meaningful input distributions to generate useful prompt optimizations. Even if optimization runs successfully, the resulting prompts would capture zero input-conditional patterns.

**D7.1 (Medium)**: The drift detector is non-functional because `agent_db.json` `verdicts: []` for all agents — nothing writes to this field. `masonry_drift_check` always returns 0 reports. The pipeline to populate `verdicts` (reading findings → attributing to agents → writing back) was explicitly deferred as Phase 2 in `masonry-handoff.js:94`.

**V7.1 (Low)**: `masonry_drift_check` requires `agent_db_path` explicitly (no default), making Kiln invocation impossible. This compounds D7.1 — even the tool interface is broken before the data issue.

### R7.2 — attribution is healthy, data quality is the gap

R7.2 is the HEALTHY result this wave. The `_build_qid_to_agent_map()` function correctly handles `**Method**:` fields, `\n---\n` splits, and all BL2.0 QID formats. The agent attribution pipeline works correctly end-to-end. The gap identified in R7.1 (degenerate `question_text`) is a data content problem, not an attribution correctness problem — attribution is fine.

---

## Phase 16 DSPy Training — Blockers Table

| Blocker | Finding | Status | Priority |
|---|---|---|---|
| `masonry_optimize_agent` MCP tool missing | D6.2 | UNFIXED | P1 |
| `question_text` = question_id (degenerate input) | R7.1 | UNFIXED | P1 |
| `agent_db.json` `verdicts` never populated | D7.1 | UNFIXED | P2 |
| `masonry_drift_check` missing `agent_db_path` default | V7.1 | UNFIXED | P3 |
| `runBackground()` path-with-spaces on Windows | R6.1 | UNFIXED | P3 |

Four of five blockers are unaddressed. Even after implementing `masonry_optimize_agent` (D6.2), the optimizer would run on training data where all primary inputs are opaque IDs (R7.1). The Phase 16 roadmap needs R7.1 fixed before optimization produces meaningful results.

---

## Cumulative Campaign State (Waves 1–7)

### Fully remediated issues

| Issue | Fix | Wave |
|---|---|---|
| masonry-guard.js strike counter non-atomic | F5.1 | 5 |
| masonry-subagent-tracker.js agents.json non-atomic | F5.3 | 5 |
| route_llm() constructed RoutingDecision with unfiltered dict | F5.2 | 5 |
| `_load_registry()` silent empty return with no log | F6.1 | 6 |
| `optimize_all()` DiagnoseAgentSig field mismatch | F6.2 | 6 |
| `_tool_masonry_route` error fallback schema mismatch | F7.1 | 7 |
| `onboard_agent.py` registry writes non-atomic | F7.2 | 7 |

### Open issues by priority

**P1 (Phase 16 blocking)**
- D6.2: `masonry_optimize_agent` MCP tool missing
- R7.1: `build_dataset()` degenerate training inputs

**P2 (system quality)**
- D7.1: drift detector verdicts never populated

**P3 (low impact)**
- V7.1: `masonry_drift_check` missing `agent_db_path` default
- R6.1: `runBackground()` path-with-spaces on Windows

---

## Wave 8 Focus Areas

1. **F8.x — Fix `build_dataset()` question_text extraction** (R7.1) — extend `_build_qid_to_agent_map()` to extract question text alongside agent name
2. **F8.x — Fix `masonry_drift_check` missing default** (V7.1) — add `str(_REPO_ROOT / "agent_db.json")` as default
3. **D8.x — Diagnose `masonry_optimize_agent` implementation completeness** — can the D6.2 fix spec be implemented? Does `dspy` package exist in the environment?
4. **R8.x — Validate routing semantic layer threshold** — R2.1 (WARNING, 0.70 threshold) still open; is there calibration data to set a better threshold?
5. **D8.x — Investigate `masonry-observe.js` hook effectiveness** — what actually gets written to Recall vs. what gets lost, and does it affect the question loop?
