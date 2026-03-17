# Changelog — BrickLayer 2.0 Engine (Self-Audit)

Campaign targeting `bl/` engine source at `C:/Users/trg16/Dev/autosearch`.
Maintained by synthesizer-bl2 at each wave end.

---

## [Unreleased]

*(Next wave entries will be inserted here by synthesizer-bl2)*

---

## [Wave 4] — 2026-03-16

6 questions (D3.1, D3.2, D4.1–D4.3 + follow-ups). Critical regex fix + 5 secondary.

### Fixed
- `D3.1` — parse_questions() regex failed on multi-word operational modes (`bl/questions.py`)
- `D3.2` — secondary parse fix (related to D3.1 scope)
- `D4.1`–`D4.3` — three secondary fixes following D4 FAILURE investigation

### Found (open)
- `D4` [FAILURE] — `_reactivate_pending_external()` in `campaign.py`; spec says `questions.py` (informational)
- `D7` [WARNING] — `_STORE_VERDICTS` at module level but not in `constants.py`
- `M2.1` [WARNING] — `RECALL_STORE_VERDICTS` not in `constants.py` for enforcement

---

## [Wave 3] — 2026-03-16

Monitor/secondary wave. `_STORE_VERDICTS` extraction, print fix, end-to-end validation.

### Fixed
- `M2.x` — extracted `_STORE_VERDICTS` from inside `store_finding()` to module level (`bl/recall_bridge.py`)
- Minor print/stderr output cleanup

### Changed
- End-to-end heal loop validated — all 6 Wave 2 fixes confirmed working together

---

## [Wave 2] — 2026-03-16

Fix wave. 6 critical bugs fixed. The BL 2.0 engine fixed itself using BL 2.0.

### Fixed
- `F2.1` — `_verdict_from_agent_output()` now accepts all 30 BL 2.0 verdicts (`bl/runners/agent.py`)
- `F2.2` — DEGRADED, ALERT, UNKNOWN, BLOCKED added to `_NON_FAILURE_VERDICTS` (`bl/findings.py`)
- `F2.3` — `current_result = dict(fix_result)` copy not alias (`bl/healloop.py`)
- `F2.4` — identity check `healed_result is not result` for heal result propagation (`bl/campaign.py`)
- `F2.5` — `short_type` computed from agent_name, was hardcoded (`bl/healloop.py`)
- `F2.6` — `last_cycle` tracker for accurate EXHAUSTED cycle count (`bl/healloop.py`)

---

## [Wave 1] — 2026-03-16

Initial audit: 22 questions (D1–D10 diagnose, A1–A12 audit). 7 FAILUREs, 1 WARNING, 1 NON_COMPLIANT.

### Found (fixed in Wave 2)
- `D1` [FAILURE] — `_verdict_from_agent_output()` 4-verdict coverage gap
- `D2` [FAILURE] — `_NON_FAILURE_VERDICTS` missing DEGRADED/ALERT/UNKNOWN/BLOCKED
- `D3` [FAILURE] — heal ID mismatch (`_heal{n}_diagnose` vs `_heal{n}_diag`)
- `D5` [FAILURE] — EXHAUSTED note always reported `max_cycles` on early break
- `D6` [FAILURE] — `current_result = fix_result` alias mutation
- `D9` [FAILURE] — heal loop result discarded when verdict unchanged
- `A2` [NON_COMPLIANT] — `_NON_FAILURE_VERDICTS` missing 4 required verdicts

### Found (open)
- `D4` [FAILURE] — `_reactivate_pending_external()` location (spec vs implementation)
- `D7` [WARNING] — `_STORE_VERDICTS` not enforced via constants.py

### Healthy
- A1, A3–A12 all COMPLIANT. D8, D10 HEALTHY.
