# Wave 8 Synthesis — Masonry Self-Research

**Wave**: 8
**Questions**: F8.1, F8.2, D8.1, D8.2, R8.1, R8.2
**All questions**: DONE
**Date**: 2026-03-21

---

## Verdicts Summary

| ID | Question (short) | Verdict | Severity |
|---|---|---|---|
| F8.1 | `build_dataset()` question text extraction fix | FIX_APPLIED | High |
| F8.2 | `masonry_drift_check` `agent_db_path` default fix | FIX_APPLIED | Low |
| D8.1 | `masonry_optimize_agent` implemented (dspy 3.1.3 available) | FIX_APPLIED | High |
| D8.2 | `score_example()` gate — silent fail on missing agent_db.json | WARNING | Medium |
| R8.1 | `masonry-observe.js` Recall storage — correct, one silent gap | HEALTHY | Info |
| R8.2 | `project_context` gap — brief is sufficient but not injected | WARNING | Medium |

---

## Pattern Analysis

### Three fixes applied — P1 blockers resolved

Wave 8 resolved both Phase 16 P1 blockers identified in Wave 7:

**F8.1** closes R7.1: `_build_qid_to_agent_map()` now captures question text from `### QID: <text>` headers. `build_dataset()` uses `finding.get("question_text") or finding.get("question_id", "")`. `confidence` is extracted per-finding from `**Confidence**:` frontmatter instead of hardcoded `"0.75"`. Training examples now have meaningful primary inputs.

**D8.1** closes D6.2: `dspy` 3.1.3 is installed with compatible `MIPROv2` API. `_tool_masonry_optimize_agent()` was implemented in `mcp_server/server.py` using existing `build_dataset()` + `configure_dspy()` + `optimize_agent()` functions. The tool is registered in `TOOLS` and callable from Kiln and Claude Code.

**F8.2** closes V7.1: `masonry_drift_check` `agent_db_path` now has `str(_REPO_ROOT / "agent_db.json")` as default. `"required": ["agent_db_path"]` removed from schema. Kiln can invoke drift check without arguments.

### Two warnings remain — not blocking

**D8.2 (WARNING/Medium)**: `build_dataset()` silently returns `{}` when `agent_db.json` is missing — no log distinguishes file-not-found from zero findings. In the current environment this path doesn't fire (agent_db.json exists, all 30 agents score ≥ 0.5). Remediation: add a log line.

**R8.2 (WARNING/Medium)**: `project-brief.md` is sufficient context for DSPy training but is not injected. `build_dataset()` still passes `"project_context": ""`. The fix is read + inject up to 2000 chars from `project-brief.md`. This is the last non-trivial optimization quality gap.

### R8.1 — Recall storage verified healthy

`masonry-observe.js` correctly stores findings to Recall with accurate tags, severity-weighted importance, and project-scoped domains. Recall at `100.70.195.84:8200` is reachable (HTTP 200). The only gap is the silent 3-second timeout on network failure — findings are not stored but the research loop is unaffected.

---

## Phase 16 DSPy Training — Blockers Table

| Blocker | Finding | Status | Priority |
|---|---|---|---|
| `masonry_optimize_agent` MCP tool missing | D6.2 | **RESOLVED** (D8.1) | P1 → closed |
| `question_text` = question_id (degenerate input) | R7.1 | **RESOLVED** (F8.1) | P1 → closed |
| `project_context` empty despite brief available | R8.2 | UNFIXED | P2 |
| `agent_db.json` `verdicts` never populated | D7.1 | UNFIXED | P2 |
| `masonry_drift_check` missing default | V7.1 | **RESOLVED** (F8.2) | P3 → closed |
| `runBackground()` path-with-spaces on Windows | R6.1 | UNFIXED | P3 |
| `build_dataset()` silent fail on missing agent_db.json | D8.2 | UNFIXED | P3 |

Both P1 blockers are resolved. The optimizer can now be invoked from Kiln with meaningful training data. The remaining P2 gap (empty `project_context`) degrades optimization quality but does not prevent optimization from running.

---

## Cumulative Campaign State (Waves 1–8)

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
| `build_dataset()` degenerate question_text + hardcoded confidence | F8.1 | 8 |
| `masonry_drift_check` missing `agent_db_path` default | F8.2 | 8 |
| `masonry_optimize_agent` MCP tool missing | D8.1 | 8 |

### Open issues by priority

**P2 (optimization quality)**
- R8.2: `project_context` empty — brief not injected into `build_dataset()`
- D7.1: drift detector verdicts never populated (Phase 2 feature)

**P3 (low impact)**
- D8.2: `build_dataset()` silent `{}` return when `agent_db.json` missing
- R6.1: `runBackground()` path-with-spaces on Windows
- R8.1: `masonry-observe.js` silent timeout on Recall unavailability

---

## Wave 9 Focus Areas

1. **F9.x — Inject `project-brief.md` into `build_dataset()` `project_context`** (R8.2) — read brief up to 2000 chars, inject per example
2. **D9.x — Diagnose `run_drift_check()` verdict population pipeline** (D7.1) — design the findings→agent_db.json attribution script
3. **R9.x — Validate `masonry_optimize_agent` end-to-end** — does MIPROv2 complete successfully with current findings? How many training examples per agent?
4. **R9.x — Validate routing Layer 1 deterministic coverage** — R2.1 (WARNING, 0.70 threshold) still open; coverage claims unvalidated
5. **D9.x — Diagnose `masonry-subagent-tracker.js` post-F5.3** — verify the atomic write fix from Wave 5 is correctly applied in the deployed hook
