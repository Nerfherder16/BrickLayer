# BrickLayer Campaign Questions — BrickLayer 2.0 Engine

Questions are organized in waves. Each wave targets blindspots from the prior wave.
Status is tracked in results.tsv — do not edit manually.

---

## Wave 1 — Diagnose + Audit

---

## D1 [CORRECTNESS] _verdict_from_agent_output() ignores all BL 2.0 verdict types
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: `_verdict_from_agent_output()` in `bl/runners/agent.py` only recognizes `HEALTHY`, `WARNING`, `FAILURE`, `INCONCLUSIVE` as valid self-reported verdicts (line 78-82). When a heal-loop agent (diagnose-analyst, fix-implementer) or an audit/frontier/monitor agent self-reports `DIAGNOSIS_COMPLETE`, `FIXED`, `FIX_FAILED`, `COMPLIANT`, `NON_COMPLIANT`, `PROMISING`, `BLOCKED`, `CALIBRATED`, or any other BL 2.0 verdict, it falls through to `INCONCLUSIVE`. This means the heal loop can never receive `DIAGNOSIS_COMPLETE` or `FIXED` from its agents, making it structurally broken.
**Test**: `grep -n "self_verdict in" bl/runners/agent.py` — check if the tuple on that line includes BL 2.0 verdict types beyond the original 4.
**Verdict threshold**:
- HEALTHY: All 26 BL 2.0 verdict types are recognized in the self_verdict check
- FAILURE: Only the original 4 verdicts are recognized; BL 2.0 verdicts fall to INCONCLUSIVE

---

## D2 [CORRECTNESS] _NON_FAILURE_VERDICTS missing DEGRADED, ALERT, UNKNOWN, BLOCKED
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: `_NON_FAILURE_VERDICTS` in `bl/findings.py` is missing `DEGRADED`, `ALERT`, `UNKNOWN`, and `BLOCKED` — all four are listed in `constants.py` `NON_FAILURE_VERDICTS` but absent from the code's frozenset. This means Monitor-mode verdicts DEGRADED and ALERT, and Frontier verdict BLOCKED, will be incorrectly classified as failures by `classify_failure_type()`, triggering false failure_type assignments and incorrect severity in findings.
**Test**: `python -c "from bl.findings import _NON_FAILURE_VERDICTS; missing = set(['DEGRADED','ALERT','UNKNOWN','BLOCKED']) - _NON_FAILURE_VERDICTS; print('MISSING:', missing if missing else 'none')"` — or grep the frozenset definition and compare to constants.py NON_FAILURE_VERDICTS list.
**Verdict threshold**:
- HEALTHY: `_NON_FAILURE_VERDICTS` contains all 18 verdicts listed in constants.py
- FAILURE: Any verdict from constants.py NON_FAILURE_VERDICTS is absent from the frozenset

---

## D3 [CORRECTNESS] Heal loop synthetic question ID overwritten before agent sees it
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: In `bl/healloop.py`, `_synthetic_question()` generates an ID like `{qid}_heal{cycle}_diagnose` (line 75), which is passed to `_run_heal_agent()` → `run_agent()`. But after `run_agent()` returns, the ID is overwritten to `{qid}_heal{cycle}_diag` (line 218) before `write_finding()`. The agent itself sees the `_diagnose` ID in its prompt/context, but the finding is written with the `_diag` ID. If the agent references its own question ID in its output, the reference will be wrong.
**Test**: Read `bl/healloop.py` lines 74-76 and lines 217-219. Verify whether `_synthetic_question()` ID matches the ID used in `write_finding()`.
**Verdict threshold**:
- HEALTHY: The synthetic question ID used during agent execution matches the ID written to findings and results.tsv
- FAILURE: The IDs differ — agent sees one ID, finding is recorded under a different ID

---

## D4 [CORRECTNESS] _reactivate_pending_external() location mismatch with spec
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: The project-brief states `_reactivate_pending_external()` lives in `bl/questions.py`, but the actual implementation is in `bl/campaign.py` (lines 497-539). The function in campaign.py also does its own datetime parsing and results.tsv rewriting, duplicating logic that could conflict with `questions.py`'s `get_next_pending()` which also checks `resume_after`. If both are called, a question could be reactivated in results.tsv but still skipped by `get_next_pending()` if the resume_after gate hasn't passed (race between UTC wall clock evaluation).
**Test**: `grep -rn "_reactivate_pending_external" bl/` — verify which file(s) contain the function. Then check if `get_next_pending()` in questions.py also evaluates `resume_after` independently.
**Verdict threshold**:
- HEALTHY: The function lives where the spec says, or the spec is corrected, and there is no double-evaluation conflict
- FAILURE: Function location mismatches spec AND the two resume_after evaluations can produce different results

---

## D5 [CORRECTNESS] Heal loop EXHAUSTED note uses max_cycles instead of actual cycle count
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: In `bl/healloop.py` lines 323-329, the EXHAUSTED `_append_heal_note()` call always uses `max_cycles` as the cycle number, even when the loop exited early via `break` (e.g., missing agent on cycle 1, or diagnose returned non-DIAGNOSIS_COMPLETE on cycle 2). This means the EXHAUSTED note will say "Heal Cycle 3" even if the loop only ran 1 cycle, producing misleading audit trail.
**Test**: Read `bl/healloop.py` — trace all `break` paths and verify whether the EXHAUSTED note at lines 323-329 correctly reflects the actual cycle that exited.
**Verdict threshold**:
- HEALTHY: The EXHAUSTED note accurately reports the cycle number where the loop exited
- FAILURE: The EXHAUSTED note reports max_cycles regardless of actual exit cycle

---

## D6 [CORRECTNESS] Heal loop fix_result mutation via current_result alias
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: In `bl/healloop.py` line 309, `current_result = fix_result` creates an alias (not a copy). Then line 313, `current_result["verdict"] = "FAILURE"` mutates the original `fix_result` dict. While this doesn't affect results.tsv (already written), it means the `fix_result` dict returned by `_run_heal_agent()` is silently modified. If any downstream code (e.g., Recall bridge, regression detection) holds a reference to this dict, they will see `FAILURE` instead of `FIX_FAILED`.
**Test**: Read `bl/healloop.py` lines 309-313. Confirm whether `current_result = fix_result` is an alias or a copy. Check if any code after line 313 reads `fix_result` and would be affected by the mutation.
**Verdict threshold**:
- HEALTHY: The mutation is isolated — no downstream code reads the mutated dict
- FAILURE: Downstream code reads the mutated verdict, causing incorrect behavior

---

## D7 [CORRECTNESS] _STORE_VERDICTS in recall_bridge.py defined inside function body
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: In `bl/recall_bridge.py`, `_STORE_VERDICTS` is defined as a local set inside `store_finding()` (line 52-68) rather than as a module-level frozenset. This means a new set object is created on every call. While functionally correct, it also means the set is not importable for testing or validation against constants.py. More critically, the set contains 14 verdicts but there's no contract in constants.py defining which verdicts should be stored — so drift from the intended list is invisible.
**Test**: `grep -n "_STORE_VERDICTS" bl/recall_bridge.py` — check if it's module-level or function-local. Then verify there is a corresponding constant in constants.py.
**Verdict threshold**:
- HEALTHY: _STORE_VERDICTS is module-level and has a corresponding validation in constants.py
- WARNING: _STORE_VERDICTS is function-local but functionally correct
- FAILURE: _STORE_VERDICTS is missing verdicts that should be stored (e.g., REGRESSION, DEGRADED_TRENDING)

---

## D8 [CORRECTNESS] session_ctx_block injection happens before doctrine_prefix — spec says after
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: The project-brief specifies prompt order as `mode_ctx_block → session_ctx_block → doctrine_prefix → agent_prompt`. In `bl/runners/agent.py` line 290, the actual template is `{mode_ctx_block}{session_ctx_block}{doctrine_prefix}{agent_prompt}`. This matches the spec. However, the audit checklist A9 checks `mode_ctx_block then session_ctx_block then doctrine_prefix`. Need to verify the code actually follows this order — any refactoring could have broken it.
**Test**: `grep -n "full_prompt = " bl/runners/agent.py` — extract the f-string template and verify the order of the 4 blocks.
**Verdict threshold**:
- HEALTHY: Prompt order matches `mode_ctx_block → session_ctx_block → doctrine_prefix → agent_prompt`
- FAILURE: Blocks are in wrong order

---

## D9 [CORRECTNESS] campaign.py heal loop result replacement is conditional — may discard FIXED
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: In `bl/campaign.py` lines 129-138, the heal loop result replaces the original result only `if healed_result.get("verdict") != result.get("verdict")`. If the initial verdict is `FAILURE` and the heal loop returns `FIXED`, the condition is True and the result is replaced — correct. But if the initial verdict is `DIAGNOSIS_COMPLETE` and the heal loop returns `DIAGNOSIS_COMPLETE` (diagnose succeeded but fix-implementer was missing), the condition is False and the heal loop's updated context/summary is silently discarded.
**Test**: Read `bl/campaign.py` lines 129-138. Trace the case where initial verdict == healed verdict (both DIAGNOSIS_COMPLETE). Verify whether the heal loop's enriched summary and appended notes are preserved.
**Verdict threshold**:
- HEALTHY: All heal loop results (including same-verdict but enriched content) are correctly propagated
- FAILURE: Heal loop results are discarded when the verdict doesn't change, losing context

---

## D10 [CORRECTNESS] get_next_pending() double-gates on _PARKED_STATUSES and status != PENDING
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: In `bl/questions.py` `get_next_pending()` (lines 113-132), the function first checks `if q["status"] in _PARKED_STATUSES: continue` then checks `if q["status"] != "PENDING": continue`. Since `_PARKED_STATUSES` contains `DONE` but also `INCONCLUSIVE`, `FIXED`, etc., the second check is redundant for parked statuses but serves as a catch-all for non-PENDING, non-parked statuses (e.g., `HEALTHY`, `WARNING`, `FAILURE`). However, `get_question_status()` returns the raw verdict from results.tsv — including verdicts like `HEALTHY` which are NOT in `_PARKED_STATUSES`. The second check catches these. But `DONE` is in `_PARKED_STATUSES` while `_mark_question_done()` maps most verdicts to `DONE`. So a question marked `DONE` is caught by the first check, while `HEALTHY` (before `_mark_question_done` runs) is caught by the second. The real question: does `get_question_status()` read from results.tsv (raw verdict) or questions.md (mapped status)?
**Test**: Read `bl/questions.py` `get_question_status()` — verify what it reads. Then trace whether a question with verdict HEALTHY in results.tsv and Status: DONE in questions.md will be correctly skipped.
**Verdict threshold**:
- HEALTHY: Both checks correctly prevent re-running of completed questions regardless of status source
- FAILURE: There exists a verdict/status combination where a completed question could be re-run

---

## A1 [AUDIT] _PARKED_STATUSES completeness (checklist item A1)
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: `_PARKED_STATUSES` in `bl/questions.py` must contain all 10 terminal verdicts listed in `constants.py` `REQUIRED_PARKED`: DIAGNOSIS_COMPLETE, PENDING_EXTERNAL, DONE, INCONCLUSIVE, FIXED, FIX_FAILED, COMPLIANT, NON_COMPLIANT, CALIBRATED, BLOCKED.
**Test**: `python -c "from bl.questions import _PARKED_STATUSES; required = {'DIAGNOSIS_COMPLETE','PENDING_EXTERNAL','DONE','INCONCLUSIVE','FIXED','FIX_FAILED','COMPLIANT','NON_COMPLIANT','CALIBRATED','BLOCKED'}; missing = required - _PARKED_STATUSES; print('COMPLIANT' if not missing else f'NON_COMPLIANT: missing {missing}')"` — or grep the frozenset definition and compare element-by-element.
**Verdict threshold**:
- COMPLIANT: All 10 required verdicts present in _PARKED_STATUSES
- NON_COMPLIANT: Any required verdict absent

---

## A2 [AUDIT] _NON_FAILURE_VERDICTS completeness (checklist item A2)
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: `_NON_FAILURE_VERDICTS` in `bl/findings.py` must contain all 18 verdicts listed in `constants.py` `NON_FAILURE_VERDICTS`.
**Test**: Compare the frozenset in `bl/findings.py` against the list in `constants.py` `NON_FAILURE_VERDICTS`. Check for missing or extra entries.
**Verdict threshold**:
- COMPLIANT: All 18 required verdicts present
- NON_COMPLIANT: Any required verdict absent or extra verdicts that shouldn't be there

---

## A3 [AUDIT] Heal loop termination guarantee (checklist item A3)
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: `bl/healloop.py` must use a bounded `for` loop with explicit `break` paths and no `while True`. The loop must terminate within `HEAL_LOOP_MAX_CYCLES` iterations under all code paths.
**Test**: `grep -n "for\|while\|break" bl/healloop.py` — verify the loop is `for cycle in range(1, max_cycles + 1)` with no inner `while True`.
**Verdict threshold**:
- COMPLIANT: Bounded `for` loop with explicit `break` paths, no unbounded loop
- NON_COMPLIANT: Unbounded loop without guaranteed exit

---

## A4 [AUDIT] Recall bridge graceful-fail (checklist item A4)
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: Every httpx call in `bl/recall_bridge.py` must be wrapped in try/except. No bare httpx call should exist without exception handling.
**Test**: `grep -n "httpx\." bl/recall_bridge.py` — verify every httpx.get and httpx.post is inside a try/except block.
**Verdict threshold**:
- COMPLIANT: All httpx calls have exception handling
- NON_COMPLIANT: Any bare httpx call without exception handling

---

## A5 [AUDIT] Session context append-only (checklist item A5)
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: `session-context.md` must only be opened with `"a"` (append) mode in `bl/campaign.py`. Opening with `"w"` would destroy accumulated session context.
**Test**: `grep -n 'open.*session.context\|session_ctx_path.*open\|open(session' bl/campaign.py` — verify all open calls use mode `"a"`.
**Verdict threshold**:
- COMPLIANT: All opens use `"a"` mode
- NON_COMPLIANT: Any open uses `"w"` mode

---

## A6 [AUDIT] operational_mode defaults to "diagnose" (checklist item A6)
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: `bl/questions.py` `parse_questions()` must set `operational_mode` to `"diagnose"` as default when the field is absent from a question block.
**Test**: `grep -n "operational_mode.*diagnose\|operational_mode.*default" bl/questions.py` — verify the default value.
**Verdict threshold**:
- COMPLIANT: Default is `"diagnose"`
- NON_COMPLIANT: No default or wrong default

---

## A7 [AUDIT] Heal loop agent existence check (checklist item A7)
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: `bl/healloop.py` must call `_agent_exists()` before spawning each agent (both diagnose-analyst and fix-implementer). Agent should not be invoked without prior existence verification.
**Test**: Read `bl/healloop.py` — verify that `_agent_exists("diagnose-analyst")` is checked before `_run_heal_agent("diagnose-analyst", ...)` and `_agent_exists("fix-implementer")` before `_run_heal_agent("fix-implementer", ...)`.
**Verdict threshold**:
- COMPLIANT: Both agents have existence checks before spawning
- NON_COMPLIANT: Any agent spawned without prior existence check

---

## A8 [AUDIT] mode_context injection order in campaign.py (checklist item A8)
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: In `bl/campaign.py`, `mode_context` must be set on the question dict BEFORE `run_question()` is called. If injected after, the runner won't see it.
**Test**: Read `bl/campaign.py` `run_and_record()` — verify that `question["mode_context"] = mode_ctx` appears before the `result = run_question(question)` call.
**Verdict threshold**:
- COMPLIANT: mode_context set before run_question() call
- NON_COMPLIANT: mode_context set after run_question() or not set at all

---

## A9 [AUDIT] session_ctx_block prompt order in runners/agent.py (checklist item A9)
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: In `bl/runners/agent.py`, the full_prompt must follow the order: `mode_ctx_block` then `session_ctx_block` then `doctrine_prefix` then `agent_prompt`.
**Test**: `grep -n "full_prompt" bl/runners/agent.py` — extract the f-string and verify block order.
**Verdict threshold**:
- COMPLIANT: Order is mode_ctx_block → session_ctx_block → doctrine_prefix → agent_prompt
- NON_COMPLIANT: Blocks are in wrong order

---

## A10 [AUDIT] Heal intermediate finding IDs follow pattern (checklist item A10)
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: Synthetic heal finding IDs must follow `{qid}_heal{n}_{type}` pattern (where type is `diag` or `fix`). The pattern must not collide with real question IDs (which start with `Q` or `D` or `A` prefix).
**Test**: `grep -n "heal.*_diag\|heal.*_fix\|_heal{" bl/healloop.py` — verify the ID construction pattern.
**Verdict threshold**:
- COMPLIANT: IDs follow `{qid}_heal{n}_{type}` with no collision risk
- NON_COMPLIANT: ID pattern could collide with real question IDs

---

## A11 [AUDIT] Heal intermediates recorded in results.tsv (checklist item A11)
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: Both `_heal{n}_diag` and `_heal{n}_fix` intermediate findings must be recorded in results.tsv via `update_results_tsv()`.
**Test**: `grep -n "update_results_tsv" bl/healloop.py` — verify that both diag and fix intermediates call this function.
**Verdict threshold**:
- COMPLIANT: Both _heal{n}_diag and _heal{n}_fix verdicts written to results.tsv
- NON_COMPLIANT: Any intermediate finding not recorded

---

## A12 [AUDIT] BL 1.x backwards compatibility — FIX_LOOP vs HEAL_LOOP independence (checklist item A12)
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: `BRICKLAYER_FIX_LOOP` (BL 1.x) and `BRICKLAYER_HEAL_LOOP` (BL 2.0) must be independent environment variables. Enabling one must not disable or override the other. Both can theoretically be enabled simultaneously (though this would be unusual).
**Test**: `grep -n "BRICKLAYER_FIX_LOOP\|BRICKLAYER_HEAL_LOOP" bl/campaign.py` — verify the two env var checks are independent `if` blocks, not `elif`.
**Verdict threshold**:
- COMPLIANT: Independent env var checks; one does not override the other
- NON_COMPLIANT: One env var overrides or disables the other

---

## Wave 2 — Fix + Monitor

**Generated from findings**: D1, D2, D3, D5, D6, D7, D9, A2
**Mode transitions applied**: D1 FAILURE (root cause at code level) → F2.1 Fix; D2/A2 FAILURE/NON_COMPLIANT → F2.2 Fix; D6 FAILURE → F2.3 Fix; D9 FAILURE → F2.4 Fix; D3 FAILURE → F2.5 Fix; D5 FAILURE → F2.6 Fix; D7 WARNING → M2.1 Monitor

---

## F2.1 [FIX] Expand _verdict_from_agent_output() to accept all BL 2.0 verdicts
**Mode**: agent
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Priority**: HIGH
**Motivated by**: D1 — `_verdict_from_agent_output()` in `bl/runners/agent.py` lines 78-82 only recognizes 4 verdicts; all BL 2.0 verdicts fall to INCONCLUSIVE, structurally breaking the heal loop
**Hypothesis**: Adding all BL 2.0 verdicts to the acceptance check will allow diagnose-analyst to return DIAGNOSIS_COMPLETE and fix-implementer to return FIXED, enabling the heal loop to function as designed
**Method**: Edit `bl/runners/agent.py` lines 78-82. Define a module-level `_ALL_VERDICTS` frozenset containing all 30 BL 2.0 verdict types and replace the 4-item tuple check with `if self_verdict in _ALL_VERDICTS: return self_verdict`.
**Verification**: `python -c "from bl.runners.agent import _verdict_from_agent_output; import json; out = json.dumps({'verdict':'DIAGNOSIS_COMPLETE','summary':'test'}); print(_verdict_from_agent_output(out))"` — must print `DIAGNOSIS_COMPLETE` not `INCONCLUSIVE`
**Fix Spec**:
- File: `bl/runners/agent.py`
- Location: lines 78-82 (the `if self_verdict in (...)` block)
- Change: Replace 4-item tuple with module-level frozenset containing all BL 2.0 verdicts (HEALTHY, WARNING, FAILURE, INCONCLUSIVE, DIAGNOSIS_COMPLETE, FIXED, FIX_FAILED, COMPLIANT, NON_COMPLIANT, PARTIAL, NOT_APPLICABLE, CALIBRATED, UNCALIBRATED, NOT_MEASURABLE, IMPROVEMENT, REGRESSION, IMMINENT, PROBABLE, POSSIBLE, UNLIKELY, OK, DEGRADED, DEGRADED_TRENDING, ALERT, UNKNOWN, PROMISING, BLOCKED, WEAK, SUBJECTIVE, PENDING_EXTERNAL)
- Root cause: BL 1.x code never extended for BL 2.0 verdict vocabulary

---

## F2.2 [FIX] Add DEGRADED, ALERT, UNKNOWN, BLOCKED to _NON_FAILURE_VERDICTS in bl/findings.py
**Mode**: agent
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Priority**: HIGH
**Motivated by**: D2/A2 — `_NON_FAILURE_VERDICTS` frozenset in `bl/findings.py` is missing 4 verdicts required by `constants.py NON_FAILURE_VERDICTS`; Monitor-mode verdicts DEGRADED and ALERT, Frontier verdict BLOCKED, and UNKNOWN are misclassified as failures by `classify_failure_type()`
**Hypothesis**: Adding the 4 missing verdicts will bring the frozenset into compliance with constants.py and eliminate false failure_type assignments for Monitor and Frontier mode results
**Method**: Edit `bl/findings.py` `_NON_FAILURE_VERDICTS` frozenset to add `"DEGRADED"`, `"ALERT"`, `"UNKNOWN"`, `"BLOCKED"`. Cross-check the full frozenset against `constants.py NON_FAILURE_VERDICTS` to ensure all 18 are present.
**Verification**: `python -c "from bl.findings import _NON_FAILURE_VERDICTS; required = {'DEGRADED','ALERT','UNKNOWN','BLOCKED'}; missing = required - _NON_FAILURE_VERDICTS; print('FIXED' if not missing else f'STILL_MISSING: {missing}')"` — must print `FIXED`
**Fix Spec**:
- File: `bl/findings.py`
- Location: `_NON_FAILURE_VERDICTS` frozenset definition
- Change: Add `"DEGRADED"`, `"ALERT"`, `"UNKNOWN"`, `"BLOCKED"` to the frozenset
- Root cause: Frozenset was not updated when Monitor/Frontier modes were added to BL 2.0

---

## F2.3 [FIX] Use dict copy instead of alias in healloop.py fix_result assignment
**Mode**: agent
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Priority**: HIGH
**Motivated by**: D6 — `current_result = fix_result` at line 309 creates an alias; subsequent `current_result["verdict"] = "FAILURE"` mutates `fix_result` in place, causing `run_heal_loop()` to return `verdict="FAILURE"` instead of `"FIX_FAILED"`, which compounds with D9 to silently discard the heal loop's context in campaign.py
**Hypothesis**: Changing the alias to `dict(fix_result)` (shallow copy) will preserve `fix_result["verdict"] = "FIX_FAILED"` for the returned dict, allowing campaign.py to correctly detect the verdict change and update the result
**Method**: Edit `bl/healloop.py` line 309: change `current_result = fix_result` to `current_result = dict(fix_result)`. Verify no other aliases in healloop.py suffer the same pattern.
**Verification**: Read `bl/healloop.py` lines 305-320 after the fix. Confirm `fix_result["verdict"]` is not mutated, and `current_result["verdict"]` is set to `"FAILURE"` on the copy only.
**Fix Spec**:
- File: `bl/healloop.py`
- Location: line 309
- Change: `current_result = fix_result` → `current_result = dict(fix_result)`
- Root cause: Python dict assignment semantics — alias not copy

---

## F2.4 [FIX] Replace verdict-diff condition in campaign.py heal loop result replacement
**Mode**: agent
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Priority**: HIGH
**Motivated by**: D9 — `if healed_result.get("verdict") != result.get("verdict")` at lines 136-138 of `bl/campaign.py` silently discards heal loop results when the verdict is unchanged (e.g., FAILURE→FAILURE after D6 mutation, or DIAGNOSIS_COMPLETE→DIAGNOSIS_COMPLETE when fix-implementer missing), losing accumulated diagnostic context in session-context.md and final JSON output
**Hypothesis**: Replacing the verdict-diff check with an identity check (`if healed_result is not result`) will correctly propagate all heal loop results since `run_heal_loop()` returns the original `initial_result` object unchanged when no healing occurs
**Method**: Edit `bl/campaign.py` lines 136-138. Change `if healed_result.get("verdict") != result.get("verdict"):` to `if healed_result is not result:`. Verify that `run_heal_loop()` returns the same `initial_result` object (not a copy) when healing is skipped.
**Verification**: Read `bl/healloop.py` to confirm `initial_result` is returned by reference when no healing occurs. Then read `bl/campaign.py` after the fix to confirm the identity check.
**Fix Spec**:
- File: `bl/campaign.py`
- Location: lines 136-138
- Change: `if healed_result.get("verdict") != result.get("verdict"):` → `if healed_result is not result:`
- Root cause: Condition designed to detect useful changes but is too narrow; misses same-verdict enriched results

---

## F2.5 [FIX] Fix _synthetic_question() to use short form ID for diagnose-analyst
**Mode**: agent
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Priority**: MEDIUM
**Motivated by**: D3 — `_synthetic_question()` in `bl/healloop.py` line 75 generates `{qid}_heal{cycle}_diagnose` (via `agent_name.split('-')[0]`), but the finding is written under `{qid}_heal{cycle}_diag` at line 218; agent sees wrong ID in its context
**Hypothesis**: Changing `_synthetic_question()` to use the intended short form (`"diag"` for diagnose-analyst, `"fix"` for fix-implementer) will eliminate the post-facto ID overwrite at line 218 and ensure the agent's prompt context matches the recorded finding ID
**Method**: Edit `bl/healloop.py` line 75. Replace `agent_name.split('-')[0]` with an explicit mapping: `"diag" if "diagnose" in agent_name else "fix"`. Then remove the ID overwrite at line 218 (which becomes redundant).
**Verification**: After fix, `grep -n "diag_q\[.id.\]" bl/healloop.py` should show only one assignment (in `_synthetic_question()`), not two. `grep -n "fix_q\[.id.\]"` should also show only one.
**Fix Spec**:
- File: `bl/healloop.py`
- Location: line 75 in `_synthetic_question()`, and line 218 (remove redundant overwrite)
- Change: `agent_name.split('-')[0]` → `"diag" if "diagnose" in agent_name else "fix"`; remove line 218 `diag_q["id"] = f"{original_qid}_heal{cycle}_diag"`
- Root cause: `split('-')[0]` on "diagnose-analyst" yields "diagnose" not "diag"

---

## F2.6 [FIX] Track actual exit cycle in EXHAUSTED note
**Mode**: agent
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Priority**: MEDIUM
**Motivated by**: D5 — EXHAUSTED `_append_heal_note()` call at `bl/healloop.py` lines 323-329 uses `max_cycles` regardless of actual exit cycle; on early `break` (e.g., missing agent on cycle 1), the note falsely reports "Heal Cycle 3 — EXHAUSTED"
**Hypothesis**: Introducing a `last_cycle` variable that tracks the last executed cycle will produce an accurate EXHAUSTED note that reflects the actual number of cycles attempted
**Method**: Edit `bl/healloop.py` to add `last_cycle = 0` before the for loop, `last_cycle = cycle` as the first statement inside the loop, and change the `_append_heal_note` call at line 323 to use `last_cycle` instead of `max_cycles`.
**Verification**: Read `bl/healloop.py` after the fix. Confirm `last_cycle` is set inside the loop and used in `_append_heal_note`. Trace the case where the loop breaks on cycle 1 — `last_cycle` should be 1.
**Fix Spec**:
- File: `bl/healloop.py`
- Location: before the for loop (add `last_cycle = 0`), first line inside loop (add `last_cycle = cycle`), line 323 (change `max_cycles` → `last_cycle`)
- Change: Track `last_cycle` and use it in the EXHAUSTED note
- Root cause: `cycle` variable is in scope after a for loop exits via `break`, but the existing code ignored it and used the constant instead

---

## M2.1 [MONITOR] Watch _STORE_VERDICTS for drift from constants.py
**Mode**: agent
**Agent**: health-monitor
**Operational Mode**: monitor
**Status**: DONE
**Priority**: LOW
**Motivated by**: D7 WARNING — `_STORE_VERDICTS` in `bl/recall_bridge.py` is a function-local set not importable for validation; no contract in constants.py defines which verdicts should be stored; drift from the intended list is invisible
**Hypothesis**: Adding a `RECALL_STORE_VERDICTS` constant to `constants.py` and a validation assertion in `store_finding()` will make drift detectable via static analysis and test runs
**Method**: Check whether `constants.py` now has a `RECALL_STORE_VERDICTS` definition. If not, add a monitor-targets.md entry to alert when `_STORE_VERDICTS` (read via AST parse of `recall_bridge.py`) diverges from the set of verdicts that should be stored per the BL 2.0 spec.
**Verification**: `grep -n "RECALL_STORE_VERDICTS\|_STORE_VERDICTS" bl/constants.py bl/recall_bridge.py` — check if a shared constant exists. If absent, this question remains PENDING.
**Success criterion**: Either a `RECALL_STORE_VERDICTS` constant exists in `constants.py` that `recall_bridge.py` imports, or a monitor entry exists that detects divergence automatically.

---

## Wave 3 — Fix + Validate + Diagnose

**Generated from findings**: F2.6, M2.1, D4, F2.3+F2.4 (combined)
**Mode transitions applied**: M2.1 WARNING → F3.1 Fix (add shared constant); F2.6 FIXED but print inconsistency → D3.1 Diagnose; D4 FAILURE (location mismatch) → D3.2 Diagnose (functional impact); F2.3+F2.4 FIXED → V3.1 Validate (end-to-end heal loop correctness)

---

## F3.1 [FIX] Add RECALL_STORE_VERDICTS constant to constants.py and import it in recall_bridge.py
**Mode**: agent
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Priority**: LOW
**Motivated by**: M2.1 WARNING — `_STORE_VERDICTS` in `bl/recall_bridge.py` is function-local with no corresponding contract in `constants.py`; adding a shared constant makes the "which verdicts get stored to Recall" contract explicit and testable
**Hypothesis**: Moving the set to `constants.py` as `RECALL_STORE_VERDICTS` and importing it in `recall_bridge.py` will eliminate the drift risk and make the contract importable for tests
**Method**: Add `RECALL_STORE_VERDICTS: frozenset[str] = frozenset({...})` to `bl/constants.py` (copying the 15 verdicts currently in recall_bridge.py). Then in `bl/recall_bridge.py`, replace the local `_STORE_VERDICTS` set with `from bl.constants import RECALL_STORE_VERDICTS` and use `RECALL_STORE_VERDICTS` in the `if verdict not in` check.
**Verification**: `python -c "from bl.constants import RECALL_STORE_VERDICTS; print('OK', len(RECALL_STORE_VERDICTS))"` must succeed. `grep -n "_STORE_VERDICTS" bl/recall_bridge.py` must show zero local definitions (only the imported name).
**Fix Spec**:
- File: `bl/constants.py` (add constant), `bl/recall_bridge.py` (import and use it)
- Change: Extract function-local set to module-level frozenset in constants.py
- Root cause: Constant was never extracted when recall_bridge.py was written

---

## D3.1 [DIAGNOSE] Print statement at healloop.py line 338 still uses max_cycles after F2.6 fix
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Priority**: LOW
**Motivated by**: F2.6 FIXED — F2.6 changed `_append_heal_note` to use `last_cycle`, but the companion `print()` at line 338 (`f"[heal-loop] {original_qid} exhausted {max_cycles} cycle(s)"`) was not updated; audit log and stderr output are inconsistent
**Hypothesis**: The print at line 338 still uses `max_cycles`, so on an early break (e.g., cycle 1), the EXHAUSTED note says "1 cycle(s)" but the stderr print says "3 cycle(s)" — creating confusing output
**Test**: `grep -n "max_cycles\|last_cycle" bl/healloop.py` — check if any references to `max_cycles` remain in the EXHAUSTED block after F2.6
**Verdict threshold**:
- HEALTHY: print statement uses `last_cycle` consistently with `_append_heal_note`
- FAILURE: print statement still uses `max_cycles` — inconsistency confirmed

---

## D3.2 [DIAGNOSE] _reactivate_pending_external() location mismatch — functional bug or doc gap?
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Priority**: MEDIUM
**Motivated by**: D4 FAILURE — `_reactivate_pending_external()` is in `bl/campaign.py` (lines 497-539), not `bl/questions.py` as the spec states. D4 confirmed the location mismatch but did not assess whether the dual `resume_after` evaluation (campaign.py's reactivation + questions.py's `get_next_pending()` gate) creates a functional race or incorrect behavior
**Hypothesis**: The function in campaign.py independently evaluates `resume_after` UTC comparisons; if `get_next_pending()` in questions.py also evaluates `resume_after`, there is a window where campaign.py reactivates a question in results.tsv (setting status back to PENDING) but `get_next_pending()` skips it because the same UTC check passes in one but not the other (clock skew between calls, or timezone interpretation difference)
**Test**: Read `bl/questions.py` `get_next_pending()` — does it also parse `resume_after` from results.tsv and compare to UTC now? If yes, are the two comparisons logically equivalent?
**Verdict threshold**:
- HEALTHY: Only one UTC evaluation occurs per question per campaign run; no race condition possible
- FAILURE: Both campaign.py and questions.py evaluate `resume_after` independently, and the evaluations can produce different results for the same question

---

## V3.1 [VALIDATE] End-to-end heal loop correctness after F2.1+F2.3+F2.4 fixes
**Mode**: agent
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: DONE
**Priority**: HIGH
**Motivated by**: F2.1 (verdict recognition), F2.3 (copy vs alias), F2.4 (identity check) — three interlocked fixes that together should make the heal loop functional; need to verify no new interaction bugs were introduced
**Hypothesis**: After all three fixes, the heal loop correctly: (1) receives DIAGNOSIS_COMPLETE from diagnose-analyst, (2) receives FIXED or FIX_FAILED from fix-implementer, (3) propagates enriched results to campaign.py, (4) terminates within max_cycles
**Method**: Trace the full FIX_FAILED-then-FIXED scenario through the fixed code: cycle 1: FAILURE → diag → DIAGNOSIS_COMPLETE → fix → FIX_FAILED → `current_result = dict(fix_result)` (verdict=FAILURE copy) → loop to cycle 2: FAILURE → diag → DIAGNOSIS_COMPLETE → fix → FIXED → return fix_result. At campaign.py: `healed_result is not result` → True → `result = healed_result` (verdict=FIXED). Verify this trace is correct.
**Verdict threshold**:
- COMPLIANT: Trace confirms correct verdict flow with no aliasing or propagation gaps
- NON_COMPLIANT: Any step in the trace produces wrong verdict or loses context

---

## Wave 4 — Diagnose + Fix (structural BL 2.0 parser bugs + doc fixes)

**Generated from findings**: V3.1 (residual cleanup), D3.2 (doc error), pre-flight code audit of bl/questions.py, bl/findings.py, bl/healloop.py
**Mode transitions applied**: V3.1 COMPLIANT (residual) → F4.1 Fix cleanup; D3.2 HEALTHY (doc gap) → F4.2 doc Fix; pre-flight static audit → D4.1/D4.2/D4.3 new Diagnose questions

---

## D4.1 [CORRECTNESS] parse_questions() Q-prefix regex excludes all BL 2.0 question IDs
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Hypothesis**: `parse_questions()` in `bl/questions.py` uses `block_pattern = re.compile(r"^## (Q[\w.-]+) \[(\w+)\] (.+?)$", re.MULTILINE)`. The `Q[\w.-]+` group requires question IDs to start with `Q` (BL 1.x convention: Q1, Q2, Q1.1). BL 2.0 question IDs use alphabetic mode prefixes (D1, F2.1, A4, M3.1, R2, V3.1, etc.). If this regex cannot match BL 2.0 IDs, `parse_questions()` returns an empty list for any BL 2.0 campaign, `get_next_pending()` returns None immediately, and the campaign loop exits with zero questions executed — making the entire BL 2.0 engine unable to run BL 2.0-format question banks.
**Test**: `python -c "import re; p=re.compile(r'^## (Q[\w.-]+)', re.M); print(bool(p.search('## D1 [CORRECTNESS]'))); print(bool(p.search('## F2.1 [FIX]')))"`  — expected: both False if bug confirmed. Also: `grep -n "Q\[\\\\w\|Q\[" bl/questions.py` to locate the pattern.
**Verdict threshold**:
- FAILURE: The regex requires Q-prefix and cannot match any BL 2.0 question ID (D/F/A/M/R/V/P/E/C/N prefixes)
- HEALTHY: The regex matches BL 2.0 IDs (would require the pattern to have been already updated)
**Fix Specification** (for DIAGNOSIS_COMPLETE transition):
- **File**: `bl/questions.py`, `parse_questions()`, `block_pattern` definition
- **Change**: Replace `Q[\w.-]+` with `[\w][\w.-]*` (or `[A-Z]\w[\w.-]*`) to match any uppercase-letter-prefixed ID
- **Verification**: `python -c "import re; p=re.compile(r'^## ([\w][\w.-]*) \[(\w+)\] (.+?)$', re.M); m=p.search('## D4.1 [CORRECTNESS] test'); print(m.group(1) if m else 'NO MATCH')"`  → should print `D4.1`
- **Side effects**: Also check `_mark_question_done()` in `bl/findings.py` which uses `text.find("\n## Q", ...)` for next-block detection — this is also Q-prefixed and may need updating

---

## D4.2 [CORRECTNESS] write_finding() uses question["mode"] for **Mode** header instead of operational_mode
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: `write_finding()` in `bl/findings.py` writes `**Mode**: {question["mode"]}` in the finding markdown header. For BL 2.0 questions parsed by `parse_questions()`, `question["mode"]` is the lowercase tag from `## {ID} [{TAG}] ...` (e.g., "correctness", "fix", "compliance"). For synthetic heal questions created by `_synthetic_question()`, `question["mode"]` is inherited from the original question (also a tag string). The operational mode (diagnose, fix, monitor, audit, etc.) is stored in `question["operational_mode"]`. If the finding header says `**Mode**: correctness` instead of `**Mode**: diagnose`, findings are mislabeled and the human-readable finding document is inaccurate.
**Test**: `grep -n '"mode"' bl/findings.py | head -10` — look for the line writing `**Mode**:`. Compare with `question.get("operational_mode", question["mode"])`.
**Verdict threshold**:
- FAILURE: `write_finding()` uses `question["mode"]` (tag string) not `operational_mode` for the **Mode** header
- HEALTHY: `write_finding()` already uses `question.get("operational_mode", question["mode"])`

---

## D4.3 [CORRECTNESS] _synthetic_question() inherits question_type from original, triggering C-30 on heal findings
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: `_synthetic_question()` in `bl/healloop.py` creates synthetic questions via `q = dict(original_question)` — a shallow copy that inherits ALL original question fields including `question_type`. If the original question has `question_type="code_audit"` (set by `parse_questions()` from the `[CORRECTNESS]`, `[FIX]`, etc. tags), then synthetic diag_q and fix_q also have `question_type="code_audit"`. `write_finding()` applies C-30 logic to code_audit questions: caps confidence at "medium" and downgrades HEALTHY→WARNING. A diagnose-analyst returning DIAGNOSIS_COMPLETE with `confidence="high"` would have its confidence silently capped at "medium" in the written finding — reducing finding accuracy. The synthetic question should reset `question_type` to the appropriate type for its operational role.
**Test**: `grep -n "question_type\|code_audit\|behavioral" bl/healloop.py` — check if _synthetic_question() overrides question_type. `grep -n "C-30\|code_audit\|confidence.*medium" bl/findings.py | head -15` — confirm the C-30 confidence cap applies.
**Verdict threshold**:
- FAILURE: `_synthetic_question()` does not reset `question_type`; synthetic heal questions inherit it from original
- HEALTHY: `_synthetic_question()` explicitly sets `question_type` appropriate to the synthetic question's role

---

## F4.1 [FIX] Update project-brief.md to correct _reactivate_pending_external() location
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Motivated by**: D3.2 — `_reactivate_pending_external()` is in `bl/campaign.py` but project-brief.md says it is in `bl/questions.py`. This is a doc-only error with no functional impact, but misleads future auditors.
**Hypothesis**: project-brief.md contains an incorrect claim about where `_reactivate_pending_external()` lives. Correcting it prevents future false-positive diagnose questions.
**Method**: Read the relevant section of project-brief.md, locate the incorrect reference, change "questions.py" to "campaign.py" for `_reactivate_pending_external()`.
**Verification**: `grep -n "_reactivate_pending_external" projects/bl2/project-brief.md` — confirms "campaign.py" appears, not "questions.py".
**Verdict threshold**:
- FIXED: project-brief.md correctly states campaign.py as the location
- FIX_FAILED: The reference was not found or not corrected

---

## F4.2 [FIX] Remove redundant fix_q["id"] overwrite at healloop.py line 280
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Motivated by**: V3.1 residual — `fix_q["id"] = f"{original_qid}_heal{cycle}_fix"` at line 280 overwrites an ID that `_synthetic_question()` already set correctly (F2.5 fix). Harmless but adds confusion.
**Hypothesis**: The line is dead code after F2.5 set the correct ID in `_synthetic_question()`. Removing it makes the intent clearer.
**Method**: Delete line 280: `fix_q["id"] = f"{original_qid}_heal{cycle}_fix"` from `bl/healloop.py`. Confirm the remaining code at line 281 (`write_finding(fix_q, fix_result)`) uses the ID already set by `_synthetic_question()`.
**Verification**: `grep -n 'fix_q\["id"\]' bl/healloop.py` — should return no results after the fix.
**Verdict threshold**:
- FIXED: The redundant line is removed and write_finding() still receives a correctly IDed fix_q
- FIX_FAILED: The line was not found or removal broke something

---

## F4.3 [FIX] Fix parse_questions() regex to accept BL 2.0 question IDs
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Motivated by**: D4.1 DIAGNOSIS_COMPLETE — `block_pattern` regex `Q[\w.-]+` matches only BL 1.x Q-prefix IDs; 0 of 38 BL 2.0 questions matched, campaign engine sees empty question bank
**Hypothesis**: Changing `Q[\w.-]+` to `[\w][\w.-]*` in `block_pattern` and `"\n## Q"` to `"\n## "` in `_mark_question_done()` restores parse_questions() to work with BL 2.0 IDs.
**Method**: Two-file fix: (1) bl/questions.py parse_questions(): change `r"^## (Q[\w.-]+) \[(\w+)\] (.+?)$"` to `r"^## ([\w][\w.-]*) \[(\w+)\] (.+?)$"`. (2) bl/findings.py _mark_question_done(): change `text.find("\n## Q", block_start + 1)` to `text.find("\n## ", block_start + 1)` for correct next-block detection.
**Verification**: `python -c "import re; p=re.compile(r'^## ([\w][\w.-]*) \[(\w+)\] (.+?)$', re.M); text=open('projects/bl2/questions.md').read(); matches=list(p.finditer(text)); print(len(matches))"` → 38 (or however many total questions exist).
**Verdict threshold**:
- FIXED: New regex matches all BL 2.0 question IDs; _mark_question_done() finds next block correctly
- FIX_FAILED: Regex still fails to match or introduces regressions

---

## F4.4 [FIX] Fix write_finding() and _synthetic_question() mode/type fields for BL 2.0 correctness
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE

---

## Wave 5 — Diagnose + Fix + Validate + Audit (runner dispatch bug cascade)

**Generated from findings**: D4.1 (DIAGNOSIS_COMPLETE, F4.3 fix), static pre-flight audit of bl/runners/__init__.py and bl/questions.py post-F4.3
**Mode transitions applied**: F4.3 FIXED (regex now parses BL 2.0 IDs) → new audit of runner dispatch reveals next systemic gap; D5.1 DIAGNOSIS_COMPLETE → F5.1 Fix; F5.1 FIXED → V5.1 Validate

---

## D5.1 [CORRECTNESS] parse_questions() uses bracket tag for runner dispatch, discarding **Mode** body field
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Hypothesis**: After F4.3 fixed the regex, `parse_questions()` now finds BL 2.0 questions. However, line 37-65 sets `question["mode"] = mode_raw` where `mode_raw = tag_raw.lower()` — the lowercase bracket tag. For `## D1 [CORRECTNESS]`, mode_raw = "correctness"; for `## F2.1 [FIX]`, mode_raw = "fix". `run_question()` dispatches on `question["mode"]`: registered runners are "agent", "correctness", "http", "performance", "quality", "static", "subprocess". "fix", "compliance", "monitor", "diagnose", "validate", "frontier", "predict", "research", "evolve" are NOT registered — all produce INCONCLUSIVE. The intended runner (from body `**Mode**: agent`) is captured into `fields["mode"]` by `field_pattern` but then discarded in the question dict (line 65 uses `mode_raw` not `fields.get("mode", mode_raw)`).
**Test**: `python -c "from bl.runners import registered_modes; print(registered_modes())"` — check if "fix", "compliance", "monitor", "diagnose" are listed. `grep -n 'mode_raw\|mode.*fields' bl/questions.py | head -10` — confirm fields["mode"] is not used.
**Verdict threshold**:
- FAILURE: question["mode"] uses bracket tag; body **Mode**: agent discarded; [FIX]/[COMPLIANCE]/[MONITOR] etc. produce INCONCLUSIVE
- HEALTHY: parse_questions() uses fields.get("mode", mode_raw) for runner dispatch
**Fix Specification** (for DIAGNOSIS_COMPLETE transition):
- **File**: `bl/questions.py`, `parse_questions()`, line 65
- **Change**: Replace `"mode": mode_raw` with `"mode": fields.get("mode", mode_raw)` — body **Mode** field takes priority; bracket tag is fallback for BL 1.x questions without a body **Mode** field
- **Verification**: For a question with `## D1 [CORRECTNESS]` and body `**Mode**: agent`, verify question["mode"] == "agent" after parse

---

## A5.1 [COMPLIANCE] _BEHAVIORAL_TAGS and _CODE_AUDIT_TAGS coverage for all BL 2.0 bracket tags
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: `_BEHAVIORAL_TAGS = frozenset(("performance", "correctness", "agent", "http", "benchmark"))` and `_CODE_AUDIT_TAGS = frozenset(("quality", "static", "code-audit"))`. BL 2.0 introduces bracket tags: CORRECTNESS, FIX, COMPLIANCE, MONITOR, DIAGNOSE, VALIDATE, FRONTIER, BENCHMARK, EVOLVE, PREDICT, RESEARCH. Tags not in either set default to "behavioral" question_type. If any BL 2.0 tag should map to "code_audit" but doesn't, C-30 logic won't apply to those questions (acceptable). If any BL 2.0 tag maps to wrong type, findings could be misclassified. Audit whether the tag coverage is correct for all BL 2.0 modes.
**Test**: `grep -n "_CODE_AUDIT_TAGS\|_BEHAVIORAL_TAGS" bl/questions.py | head -5` — list current tags. Cross-reference against all BL 2.0 bracket tags in use.
**Verdict threshold**:
- COMPLIANT: All BL 2.0 bracket tags either correctly classified or correctly defaulting to "behavioral"
- NON_COMPLIANT: A BL 2.0 tag is misclassified (maps to code_audit when it should be behavioral, or vice versa with functional impact)

---

## F5.1 [FIX] Fix parse_questions() to use body **Mode** field for runner dispatch
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Motivated by**: D5.1 DIAGNOSIS_COMPLETE — bracket tag used for runner dispatch; BL 2.0 questions with [FIX], [COMPLIANCE] etc. tags produce INCONCLUSIVE because no runner is registered for those tag strings
**Hypothesis**: Changing `"mode": mode_raw` to `"mode": fields.get("mode", mode_raw)` at line 65 of parse_questions() causes the body **Mode**: agent field to control runner dispatch. The bracket tag remains the fallback for BL 1.x compatibility.
**Method**: Edit `bl/questions.py` parse_questions(), line 65: `"mode": fields.get("mode", mode_raw)`. This gives body **Mode** field priority over bracket tag. BL 1.x questions that lack a **Mode** body field fall back to mode_raw (correct). BL 2.0 questions with **Mode**: agent correctly dispatch to run_agent.
**Verification**: `python -c "from bl.questions import parse_questions; from bl.config import cfg; cfg.project_root = __import__('pathlib').Path('projects/bl2'); cfg.questions_md = cfg.project_root / 'questions.md'; cfg.results_tsv = cfg.project_root / 'results.tsv'; qs = parse_questions(); print(qs[0]['id'], qs[0]['mode'])"` — verify first question has mode="correctness" (bracket tag fallback since questions in this campaign have **Mode**: code_audit not **Mode**: agent).
**Verdict threshold**:
- FIXED: parse_questions() uses fields.get("mode", mode_raw); BL 2.0 questions with **Mode**: agent use run_agent runner
- FIX_FAILED: Change not applied or introduces regression

---

## V5.1 [VALIDATE] Full BL 2.0 campaign lifecycle correctness after F4.3 + F5.1 fixes
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: DONE
**Motivated by**: F4.3 FIXED (regex), F5.1 FIXED (runner dispatch) — combined effect on a live BL 2.0 question needs end-to-end trace
**Hypothesis**: After F4.3 (regex) and F5.1 (runner dispatch), a typical BL 2.0 question bank (with `## D1 [CORRECTNESS]` format and `**Mode**: agent` body field) would execute correctly through the full campaign pipeline: parse → dispatch → run_agent → _verdict_from_agent_output → write_finding(operational_mode) → update_results_tsv → _mark_question_done.
**Method**: Trace the lifecycle: (1) parse_questions() now matches D1 (F4.3) and sets mode="agent" (F5.1); (2) get_next_pending() returns D1; (3) run_question() calls run_agent(); (4) _verdict_from_agent_output() recognizes all BL 2.0 verdicts (F2.1); (5) write_finding() uses operational_mode for **Mode** header (F4.4); (6) update_results_tsv() upserts correctly; (7) _mark_question_done() finds ## D1 [ and updates status. Verify each step is now correct.
**Verdict threshold**:
- COMPLIANT: All 7 pipeline stages work correctly for a BL 2.0 question after the 4 waves of fixes
- NON_COMPLIANT: Any stage fails or produces wrong output
**Motivated by**: D4.2 (FAILURE: Mode header shows tag string not operational_mode) and D4.3 (FAILURE: synthetic questions inherit code_audit question_type)
**Hypothesis**: Two targeted fixes: (1) write_finding() **Mode** line uses operational_mode, (2) _synthetic_question() resets question_type to "behavioral" for synthetic heal questions.
**Method**: (1) bl/findings.py write_finding(): change `**Mode**: {question["mode"]}` to `**Mode**: {question.get("operational_mode", question["mode"])}`. (2) bl/healloop.py _synthetic_question(): add `q["question_type"] = "behavioral"` after the `q = dict(original_question)` line.
**Verification**: (1) `grep -n "operational_mode" bl/findings.py` → shows updated **Mode** line. (2) `grep -n "question_type" bl/healloop.py` → shows `q["question_type"] = "behavioral"` in _synthetic_question().
**Verdict threshold**:
- FIXED: Both changes applied and verified
- FIX_FAILED: Either change not applied or broken

---

## Wave 6 — Regression Fix + Format Correction + Runner Coverage Audit

**Generated from findings**: D5.1 (DIAGNOSIS_COMPLETE, F5.1 fix) introduced regression — body **Mode**: code_audit dispatches to unregistered runner; V5.1 noted results.tsv format mismatch; A5.1 audit revealed runner registry gap for semantic mode aliases
**Mode transitions applied**: F5.1 FIXED (runner dispatch) → reveals code_audit unregistered; V5.1 COMPLIANT → flags TSV format discrepancy; A5.1 COMPLIANT → prompts runner coverage audit

---

## D6.1 [CORRECTNESS] F5.1 regression: "code_audit" body **Mode** field dispatches to unregistered runner
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Hypothesis**: F5.1 fixed runner dispatch to use `fields.get("mode", mode_raw)`. For Wave 4-5 questions with `**Mode**: code_audit` in their body (e.g., D5.1, A5.1, F5.1, V5.1), this means `question["mode"] = "code_audit"`. However "code_audit" is NOT registered in `bl/runners/__init__.py` — registered runners are: agent, correctness, http, performance, quality, static, subprocess. `run_question()` would return INCONCLUSIVE for all Wave 4-5 questions run through the BL engine. This is a regression introduced by F5.1 — before the fix, the bracket tag fallback (e.g., "correctness" for D5.1 [CORRECTNESS]) was at least sometimes registered.
**Test**: `grep -n "code_audit" bl/runners/__init__.py` — expect no match (code_audit not registered). `python -c "from bl.runners import registered_modes; print(registered_modes())"` — verify "code_audit" absent. `grep -n '"Mode": code_audit\|Mode.*code_audit' projects/bl2/questions.md | head -10` — count affected questions.
**Verdict threshold**:
- FAILURE: "code_audit" body Mode field dispatches to INCONCLUSIVE for Wave 4-5 questions
- HEALTHY: "code_audit" is registered as a runner (or questions use **Mode**: agent)
**Fix Specification** (for DIAGNOSIS_COMPLETE transition):
- **Option A**: Register "code_audit" as alias for "agent" runner in bl/runners/__init__.py — `register("code_audit", run_agent)` — enables future questions to use **Mode**: code_audit semantically
- **Option B**: Patch Wave 4-5 questions.md to replace `**Mode**: code_audit` with `**Mode**: agent` — keeps runners minimal but requires question edits
- **Recommended**: Option A — aligns **Mode** body field with semantic intent; "code_audit" questions run via LLM agent (diagnose-analyst), so aliasing to run_agent is correct

---

## D6.2 [CORRECTNESS] results.tsv format mismatch — get_question_status() cannot read campaign TSV rows
**Mode**: agent
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DONE
**Hypothesis**: `get_question_status(qid)` reads results.tsv and checks `parts[0] == qid` (question_id in column 0). `update_results_tsv()` writes rows as `qid\tverdict\tfailure_type\tsummary\ttimestamp` — qid IS column 0, correct. However, this self-audit campaign's results.tsv was manually initialized with the BL 1.x format: `commit\tquestion_id\tverdict\t...` (6 columns, commit is column 0). All data rows have `N/A` as column 0. `get_question_status()` matches `parts[0] == "D1"` — never matches `"N/A"` — returns PENDING for all 44 questions. Campaign status tracking is completely non-functional for manually-maintained rows.
**Test**: `python -c "from bl.questions import get_question_status; from bl.config import cfg; from pathlib import Path; cfg.project_root = Path('projects/bl2'); cfg.results_tsv = cfg.project_root / 'results.tsv'; print(get_question_status('D1'))"` — expect PENDING (demonstrating the bug). `head -2 projects/bl2/results.tsv` — confirm column 0 is "commit" not qid.
**Verdict threshold**:
- FAILURE: get_question_status("D1") returns PENDING despite D1 having a row in results.tsv
- HEALTHY: get_question_status("D1") returns the correct verdict from the TSV

---

## A6.1 [COMPLIANCE] Runner registry coverage — all BL 2.0 **Mode** body field values must be registered
**Mode**: agent
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: After F5.1, `question["mode"]` comes from the body `**Mode**: <value>` field. For BL 2.0 campaigns to execute without INCONCLUSIVE, every value used in `**Mode**:` body fields must map to a registered runner. Registered runners: agent, correctness, http, performance, quality, static, subprocess. BL 2.0 questions in this campaign use `**Mode**: agent` (Wave 1-3) and `**Mode**: code_audit` (Wave 4-5). The "code_audit" alias is missing. Additionally: diagnose, fix, monitor, validate, audit, frontier, predict, research, evolve — if any of these appear as **Mode** body field values, they would also be unregistered.
**Test**: `grep -n "^\*\*Mode\*\*:" projects/bl2/questions.md | sort | uniq -c | sort -rn | head -10` — enumerate all body **Mode** values in use. Cross-reference against registered_modes().
**Verdict threshold**:
- COMPLIANT: All **Mode** body field values in use are either registered runners or question authors consistently use "agent" for LLM-based questions
- NON_COMPLIANT: Any **Mode** body value resolves to INCONCLUSIVE via unregistered dispatch

---

## F6.1 [FIX] Register "code_audit" as agent runner alias in bl/runners/__init__.py
**Mode**: agent
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Motivated by**: D6.1 DIAGNOSIS_COMPLETE — "code_audit" body **Mode** field dispatches to unregistered runner; F5.1 regression for Wave 4-5 questions
**Hypothesis**: Adding `register("code_audit", run_agent)` to `_register_builtins()` in bl/runners/__init__.py resolves the F5.1 regression. Code audit questions use diagnose-analyst (an LLM agent) to read source code — run_agent is the correct runner. This also allows future question authors to use `**Mode**: code_audit` semantically without needing to know the runner alias.
**Method**: Edit `bl/runners/__init__.py` `_register_builtins()`: add `register("code_audit", run_agent)` after the existing register("agent", run_agent) line. Verify `registered_modes()` now includes "code_audit".
**Verdict threshold**:
- FIXED: "code_audit" registered; registered_modes() includes "code_audit"; D5.1/A5.1/F5.1/V5.1 questions would dispatch to run_agent
- FIX_FAILED: Change not applied or introduces regression

---

## F6.2 [FIX] Rewrite results.tsv to use BL 2.0 engine format (qid first)
**Mode**: agent
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Motivated by**: D6.2 — results.tsv manually populated with BL 1.x format; get_question_status() cannot read any rows; all questions show PENDING
**Hypothesis**: Rewriting the results.tsv header and data rows to use the engine format (`question_id\tverdict\tfailure_type\tsummary\ttimestamp`) causes get_question_status() to correctly parse all rows. Each existing row `N/A\tD1\tFAILURE\tN/A\t<finding>\t<scenario>` becomes `D1\tFAILURE\t\t<finding truncated to 120>\t<timestamp>`.
**Method**: Parse the existing results.tsv, transform each non-header row from BL 1.x format to BL 2.0 format, rewrite the file. Preserve all existing data; add approximate timestamps where none exist.
**Verdict threshold**:
- FIXED: get_question_status("D1") returns "FAILURE"; all 44 questions have non-PENDING status; parse_questions() returns correct statuses
- FIX_FAILED: Data loss or format still wrong after rewrite

---

## V6.1 [VALIDATE] Runner dispatch and status tracking correct after F6.1 + F6.2
**Mode**: agent
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: DONE
**Motivated by**: F6.1 (code_audit runner alias) + F6.2 (TSV format fix) — combined effect needs end-to-end verification
**Hypothesis**: After F6.1, questions with `**Mode**: code_audit` dispatch to run_agent. After F6.2, get_question_status() returns correct verdicts for all 44 questions. The campaign engine can correctly identify PENDING questions and skip already-answered ones. The combination of F4.3 (regex), F5.1 (runner dispatch), F6.1 (code_audit alias), and F6.2 (TSV format) produces a fully functional BL 2.0 campaign pipeline.
**Method**: (1) Verify registered_modes() includes "code_audit". (2) Verify get_question_status("D1") returns "FAILURE". (3) Verify parse_questions() returns correct statuses for a sample of questions. (4) Trace full pipeline for a Wave 4 code_audit question end-to-end.
**Verdict threshold**:
- COMPLIANT: All 4 fixes interact correctly; no PENDING questions that should be DONE; code_audit questions dispatch to run_agent
- NON_COMPLIANT: Any regression or remaining status/dispatch error

---

## Wave 7 — Verdict Priority Fix + C-04 Drill-down BL 2.0 Compatibility

**Generated from findings**: V6.1 COMPLIANT triggered deep audit of run_and_record; static analysis of _verdict_from_agent_output() else-branch and followup.py _is_leaf_id() revealed two systemic bugs affecting BL 2.0 agent verdict accuracy and adaptive drill-down
**Mode transitions applied**: D7.1 DIAGNOSIS_COMPLETE -> F7.1 Fix; D7.2 DIAGNOSIS_COMPLETE -> F7.2 Fix; A7.1 audit; F7.1+F7.2 FIXED -> V7.1 Validate

---

## D7.1 [CORRECTNESS] _verdict_from_agent_output() checks changes_committed before self_verdict in else-branch
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Hypothesis**: In bl/runners/agent.py _verdict_from_agent_output(), the else branch (for all agents not matching the 4 hardcoded names) checks output.get("changes_committed", 0) > 0 and returns HEALTHY before reaching the self_verdict check. For BL 2.0 agents like fix-implementer that both commit code AND return a structured verdict (FIXED, FIX_FAILED), HEALTHY fires first. A fix-implementer returning {"verdict": "FIXED", "changes_committed": 2} produces HEALTHY instead of FIXED.
**Test**: Read bl/runners/agent.py lines 80-130. Verify: (1) else-branch checks changes_committed > 0 before self_verdict in _ALL_VERDICTS. (2) diagnose-analyst returning {"verdict": "DIAGNOSIS_COMPLETE"} with no changes_committed works correctly. (3) fix-implementer returning {"verdict": "FIXED", "changes_committed": 2} traces to HEALTHY (wrong).
**Verdict threshold**:
- FAILURE: else-branch returns HEALTHY on changes_committed > 0 before checking self_verdict
- HEALTHY: self_verdict is checked before or instead of changes_committed heuristic
**Fix Specification** (for DIAGNOSIS_COMPLETE transition):
- **File**: bl/runners/agent.py, _verdict_from_agent_output(), else-branch
- **Change**: Move self_verdict check before changes_committed heuristic. If self_verdict in _ALL_VERDICTS, return immediately. Fall through to changes_committed heuristic only if self_verdict empty/unrecognized.
- **Verification**: _verdict_from_agent_output("fix-implementer", {"verdict": "FIXED", "changes_committed": 2}) -> FIXED not HEALTHY

---

## D7.2 [CORRECTNESS] _is_leaf_id() treats all BL 2.0 question IDs as leaf nodes
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: FAILURE
**Hypothesis**: In bl/followup.py _is_leaf_id(qid), for BL 2.0 IDs like "D5.1", "F4.3", "A6.1": not "QG" prefix, not "Q" prefix -> else: return True (leaf). Every BL 2.0 question ID is classified as a leaf — generate_followup() skips drill-down for all BL 2.0 FAILURE/WARNING questions. C-04 adaptive follow-up is completely non-functional for this entire BL 2.0 campaign.
**Test**: Read bl/followup.py _is_leaf_id(). Trace: "D5.1" -> not QG, not Q -> else -> True (WRONG — should be non-leaf). "D5.1.1" -> same -> True (CORRECT — sub-question is leaf). "Q2.4" -> Q prefix -> "2.4" -> 2 parts -> False (CORRECT for BL 1.x).
**Verdict threshold**:
- FAILURE: _is_leaf_id("D5.1") returns True (BL 2.0 IDs treated as leaf)
- HEALTHY: _is_leaf_id("D5.1") returns False; _is_leaf_id("D5.1.1") returns True

---

## F7.1 [FIX] Fix _verdict_from_agent_output() to check self_verdict before changes_committed heuristic
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Motivated by**: D7.1 DIAGNOSIS_COMPLETE
**Method**: In bl/runners/agent.py _verdict_from_agent_output() else-branch: move self_verdict check first. Return self_verdict if in _ALL_VERDICTS. Fall through to changes_committed heuristic only if self_verdict empty/unrecognized.
**Verdict threshold**:
- FIXED: _verdict_from_agent_output("fix-implementer", {"verdict": "FIXED", "changes_committed": 2}) -> FIXED; _verdict_from_agent_output("legacy", {"changes_committed": 1}) -> HEALTHY (heuristic still works)
- FIX_FAILED: Change not applied or breaks legacy heuristic

---

## F7.2 [FIX] Fix _is_leaf_id() to correctly classify BL 2.0 question IDs
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Motivated by**: D7.2 DIAGNOSIS_COMPLETE
**Method**: In bl/followup.py _is_leaf_id(), before else: return True, add BL 2.0 handling: split qid on ".", return len(parts) >= 3. D1 (1 part) -> False; D5.1 (2 parts) -> False; D5.1.1 (3 parts) -> True.
**Verdict threshold**:
- FIXED: _is_leaf_id("D5.1") -> False; _is_leaf_id("D5.1.1") -> True; _is_leaf_id("D1") -> False; _is_leaf_id("Q2.4.1") -> True (BL 1.x unbroken)
- FIX_FAILED: Wrong classification or BL 1.x regression

---

## A7.1 [COMPLIANCE] followup.py sub-question generation format compatibility with BL 2.0
**Mode**: code_audit
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: Even after F7.2 fixes _is_leaf_id(), the generated sub-question ID format and block injection may be wrong for BL 2.0 parents. _get_existing_sub_ids() searches for ## {parent_id}.N. For parent "D5.1", searches "## D5.1.N". Audit whether generated sub-question IDs, block format, and questions.md injection are compatible with BL 2.0 parse_questions() block_pattern regex ([\w][\w.-]*).
**Test**: Read bl/followup.py fully. Check: (1) generated sub-question ID format for parent "D5.1" -> should be "D5.1.1". (2) Injected block header -> must match "## D5.1.1 [TAG] title". (3) Whether _get_existing_sub_ids() pattern works for BL 2.0 IDs.
**Verdict threshold**:
- COMPLIANT: Generated sub-question IDs "D5.1.1" conform to block_pattern; injection format correct
- NON_COMPLIANT: Sub-question IDs or block format incompatible with BL 2.0 parse_questions()

---

## V7.1 [VALIDATE] Verdict accuracy and C-04 drill-down after F7.1 + F7.2 fixes
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: DONE
**Motivated by**: F7.1 + F7.2 + A7.1
**Hypothesis**: After F7.1, fix-implementer FIXED verdicts preserved; DIAGNOSIS_COMPLETE from diagnose-analyst (no changes_committed) already worked. After F7.2, C-04 drill-down generates correctly-formatted BL 2.0 sub-questions for FAILURE/WARNING parents.
**Verdict threshold**:
- COMPLIANT: All targeted functions produce correct output; no BL 1.x regression; BL 2.0 self-healing loop and drill-down fully functional
- NON_COMPLIANT: Any regression or remaining verdict/drill-down error

---

## D8.1 [CORRECTNESS] _inject_override_questions() glob("Q*.md") excludes all BL 2.0 findings
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: FAILURE
**Hypothesis**: In bl/campaign.py _inject_override_questions() (line 396): `for finding_file in sorted(cfg.findings_dir.glob("Q*.md"))`. BL 2.0 findings are named D5.1.md, F7.1.md, A7.1.md etc — none start with "Q". If a peer reviewer returns OVERRIDE on a BL 2.0 finding, _inject_override_questions() silently skips it. Re-exam questions are never injected. This makes the peer OVERRIDE mechanism non-functional for the entire BL 2.0 campaign.
**Test**: Read bl/campaign.py _inject_override_questions(). Confirm: glob pattern is "Q*.md". Verify BL 2.0 finding filenames (D5.1.md, F7.1.md) would not match. Assess whether any BL 2.0 peer review OVERRIDEs have been silently dropped.
**Verdict threshold**:
- FAILURE: glob("Q*.md") confirmed; BL 2.0 OVERRIDE peer reviews silently excluded; fix needed
- HEALTHY: glob includes non-Q files or BL 2.0 doesn't use peer review OVERRIDE
**Fix Specification** (for DIAGNOSIS_COMPLETE transition):
- **File**: bl/campaign.py, _inject_override_questions(), glob call
- **Change**: Replace glob("Q*.md") with glob("*.md") to include all finding files
- **Verification**: A finding named D5.1.md with OVERRIDE peer review section gets a re-exam question injected

---

## D8.2 [CORRECTNESS] _mark_question_done() _PRESERVE_AS_IS missing FAILURE and NON_COMPLIANT
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: FAILURE
**Hypothesis**: In bl/findings.py _mark_question_done(), `_PRESERVE_AS_IS = frozenset({"INCONCLUSIVE", "DIAGNOSIS_COMPLETE", "PENDING_EXTERNAL", "FIXED", "FIX_FAILED", "BLOCKED"})`. Verdicts NOT in this set get status "DONE". FAILURE → DONE, NON_COMPLIANT → DONE, WARNING → DONE in questions.md. A human inspecting questions.md cannot distinguish a question that PASSED from one that produced a critical FAILURE. The status field loses diagnostic signal for the most important verdicts.
**Test**: Read bl/findings.py _mark_question_done(). Verify _PRESERVE_AS_IS does not include FAILURE, NON_COMPLIANT, WARNING, FIX_FAILED (wait — FIX_FAILED IS listed), REGRESSION. Trace: verdict="FAILURE" → new_status = "DONE". Confirm the status written to questions.md is "DONE" not "FAILURE".
**Verdict threshold**:
- FAILURE: FAILURE and NON_COMPLIANT not in _PRESERVE_AS_IS; these verdicts → status "DONE" (visibility bug)
- HEALTHY: All important failure verdicts preserved as-is in questions.md status
**Fix Specification** (for DIAGNOSIS_COMPLETE transition):
- **File**: bl/findings.py, _mark_question_done(), _PRESERVE_AS_IS
- **Change**: Add "FAILURE", "NON_COMPLIANT", "WARNING", "REGRESSION", "ALERT" to _PRESERVE_AS_IS
- **Verification**: verdict="FAILURE" → questions.md shows **Status**: FAILURE (not DONE)

---

## F8.1 [FIX] Fix _inject_override_questions() to glob all finding files not just Q-prefixed
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Motivated by**: D8.1 DIAGNOSIS_COMPLETE
**Method**: In bl/campaign.py _inject_override_questions(): change `cfg.findings_dir.glob("Q*.md")` to `cfg.findings_dir.glob("*.md")`. Ensure the injected re-exam question ID uses the original question ID from the finding filename (stem), not a Q-prefix assumption.
**Verdict threshold**:
- FIXED: glob("*.md") applied; D5.1.md and other BL 2.0 findings scanned for OVERRIDE; injected question IDs correct
- FIX_FAILED: glob not changed or injected question ID format broken

---

## F8.2 [FIX] Fix _mark_question_done() to preserve FAILURE and NON_COMPLIANT status
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Motivated by**: D8.2 DIAGNOSIS_COMPLETE
**Method**: In bl/findings.py _mark_question_done(), add "FAILURE", "NON_COMPLIANT", "WARNING", "REGRESSION", "ALERT" to _PRESERVE_AS_IS frozenset. These verdicts should be written as-is to questions.md status for human visibility.
**Verdict threshold**:
- FIXED: verdict="FAILURE" → status "FAILURE" in questions.md; verdict="NON_COMPLIANT" → status "NON_COMPLIANT"; DONE still applies to HEALTHY/COMPLIANT/IMPROVEMENT/etc.
- FIX_FAILED: _PRESERVE_AS_IS unchanged or wrong verdicts added

---

## A8.1 [COMPLIANCE] _load_mode_context() mode file resolution for BL 2.0 operational modes
**Mode**: code_audit
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: campaign.py _load_mode_context() reads `{project_root}/modes/{operational_mode}.md`. For BL 2.0 questions with operational_mode values (diagnose, fix, monitor, audit, validate, frontier, predict, research, evolve), the mode files must exist in the project's modes/ directory. If they don't, _load_mode_context() silently returns "" and agents run without mode context. Audit whether: (1) the modes/ directory exists in the bl2 project; (2) all 9 BL 2.0 operational modes have corresponding .md files; (3) the empty fallback is acceptable or causes degraded agent behavior.
**Test**: Check whether C:/Users/trg16/Dev/autosearch/projects/bl2/modes/ exists. List its contents. Verify each BL 2.0 mode (diagnose, fix, audit, validate) has a .md file. Read _load_mode_context() in campaign.py to confirm silent fallback behavior.
**Verdict threshold**:
- COMPLIANT: modes/ exists with all 9 operational mode files; _load_mode_context() correctly injects context
- NON_COMPLIANT: modes/ missing or incomplete; agents running without mode context
- PARTIAL: Some mode files present but not all

---

## V8.1 [VALIDATE] Campaign BL 2.0 integration after F8.1+F8.2: override injection and status preservation
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: DONE
**Motivated by**: F8.1 + F8.2 + A8.1
**Hypothesis**: After F8.1, peer review OVERRIDE findings for BL 2.0 question IDs correctly trigger re-exam injection. After F8.2, FAILURE and NON_COMPLIANT verdicts are visible in questions.md status. _load_mode_context() either provides mode context or silently degrades — both are acceptable behaviors.
**Verdict threshold**:
- COMPLIANT: All campaign BL 2.0 integration points verified correct after fixes; no BL 1.x regressions
- NON_COMPLIANT: F8.1 or F8.2 not applied, or introduced new bugs in the override/status path

---

## D9.1 [CORRECTNESS] hypothesis.py _QUESTION_BLOCK_HEADER regex only matches Q-prefixed BL 1.x IDs
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: FAILURE
**Hypothesis**: In bl/hypothesis.py, `_QUESTION_BLOCK_HEADER = re.compile(r"^## (Q\d+\.\d+[\w.]*)\s+\[(\w+)\]\s+(.+)$", re.MULTILINE)`. This regex only matches IDs starting with "Q" followed by digits. BL 2.0 IDs (D8.1, F5.1, A7.1, V6.1, M2.1) never match. Consequences: (1) `_get_wave_number()` returns 1 for BL 2.0 questions.md (no matches → waves=[] → returns 1). (2) `_get_existing_ids()` returns empty set. (3) `generate_hypotheses()` would generate "Wave 2" Q2.1-format questions even if Wave 8 is current. (4) Generated questions would use BL 1.x ID format.
**Test**: Read bl/hypothesis.py _QUESTION_BLOCK_HEADER. Trace: "## D8.1 [CORRECTNESS] title" against the regex — does it match? Confirm _get_wave_number() behavior for a questions.md with only BL 2.0 headers. Confirm generated IDs would be Q2.1, Q2.2... not D9.1, D9.2...
**Verdict threshold**:
- FAILURE: Regex confirmed Q-only; _get_wave_number() returns 1 for BL 2.0 questions.md; generated IDs use wrong format
- HEALTHY: Regex handles BL 2.0 IDs; wave detection and ID extraction correct
**Fix Specification** (for DIAGNOSIS_COMPLETE transition):
- **File**: bl/hypothesis.py, _QUESTION_BLOCK_HEADER
- **Change**: Replace `Q\d+\.\d+[\w.]*` with `[\w][\w.-]*` to match all BL 2.0 question IDs (same as block_pattern in questions.py)
- **Verification**: "## D8.1 [CORRECTNESS] title" matches; _get_wave_number() correctly returns 8 for BL 2.0 questions.md

---

## D9.2 [CORRECTNESS] campaign.py agent_db recording skips code_audit mode — BL 2.0 agents not tracked
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: FAILURE
**Hypothesis**: In bl/campaign.py run_and_record() lines 156-169: `if question.get("mode") == "agent" and agent_name`. After F5.1, BL 2.0 questions with `**Mode**: code_audit` in body have `question["mode"] = "code_audit"`. So all diagnose-analyst, fix-implementer, compliance-auditor, design-reviewer runs (mode=code_audit) are excluded from agent_db tracking. The agent performance scoring system has zero data on all BL 2.0 agent runs. The overseer underperformer detection cannot fire for any BL 2.0 agent.
**Test**: Read bl/campaign.py run_and_record() lines 156-170. Confirm condition is `mode == "agent"`. Read questions.md and count questions with **Mode**: code_audit. Confirm those agents are never passed to agent_db.record_run(). Check if agent_db.json exists in projects/bl2/ and has any entries for BL 2.0 agents.
**Verdict threshold**:
- FAILURE: Condition is mode=="agent" only; code_audit runs not tracked; agent_db.json empty or missing BL 2.0 agents
- HEALTHY: Condition covers code_audit mode or equivalent tracking exists
**Fix Specification** (for DIAGNOSIS_COMPLETE transition):
- **File**: bl/campaign.py, run_and_record(), agent_db recording block
- **Change**: Change `if question.get("mode") == "agent"` to `if question.get("mode") in ("agent", "code_audit")`
- **Verification**: diagnose-analyst run with mode=code_audit recorded in agent_db.json

---

## F9.1 [FIX] Fix hypothesis.py _QUESTION_BLOCK_HEADER to match BL 2.0 question IDs
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Motivated by**: D9.1 DIAGNOSIS_COMPLETE
**Method**: In bl/hypothesis.py: change `_QUESTION_BLOCK_HEADER = re.compile(r"^## (Q\d+\.\d+[\w.]*)\s+\[(\w+)\]\s+(.+)$", re.MULTILINE)` to use `[\w][\w.-]*` as the ID pattern (same as block_pattern in questions.py F4.3). Update `_get_wave_number()` to handle BL 2.0 IDs (extract wave from first numeric segment or use max dot-count).
**Verdict threshold**:
- FIXED: "## D8.1 [CORRECTNESS] title" matches; _get_wave_number() returns correct wave from BL 2.0 questions.md; _get_existing_ids() includes all BL 2.0 IDs
- FIX_FAILED: Regex still Q-only or wave detection broken

---

## F9.2 [FIX] Fix campaign.py agent_db recording to include code_audit mode
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Motivated by**: D9.2 DIAGNOSIS_COMPLETE
**Method**: In bl/campaign.py run_and_record() agent_db block: change `if question.get("mode") == "agent" and agent_name` to `if question.get("mode") in ("agent", "code_audit") and agent_name`. Both modes use run_agent() internally, so tracking is appropriate for both.
**Verdict threshold**:
- FIXED: code_audit mode agent runs recorded in agent_db.json; overseer can detect underperformers across all BL 2.0 agents
- FIX_FAILED: Condition not updated or agent_name not available for code_audit questions

---

## A9.1 [COMPLIANCE] agent_db.py verdict classification — "DONE" in _SUCCESS_VERDICTS is unreachable
**Mode**: code_audit
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: DONE
**Hypothesis**: In bl/agent_db.py, `_SUCCESS_VERDICTS` includes "DONE". But "DONE" is a questions.md **Status** value, not a verdict. No agent should ever return verdict="DONE" from run_agent(). The "DONE" entry is dead code. Audit: (1) Can any runner or agent return verdict="DONE"? (2) Is "DONE" in _VERDICT_CLARITY in findings.py? (3) Does having dead code in _SUCCESS_VERDICTS cause any correctness issue?
**Test**: Read bl/agent_db.py _SUCCESS_VERDICTS. Read bl/findings.py _VERDICT_CLARITY. Check if "DONE" appears in any verdict set or can be returned by any runner. Determine if the dead entry causes incorrect scoring.
**Verdict threshold**:
- COMPLIANT: "DONE" is dead code — no runner returns it; no correctness impact; minor cleanup opportunity only
- NON_COMPLIANT: A runner can return "DONE" as verdict causing incorrect 1.0 credit scoring

---

## V9.1 [VALIDATE] Hypothesis generation and agent tracking correct after F9.1+F9.2
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: DONE
**Motivated by**: F9.1 + F9.2 + A9.1
**Hypothesis**: After F9.1, _QUESTION_BLOCK_HEADER matches BL 2.0 IDs; _get_wave_number() returns correct wave; _get_existing_ids() returns all current question IDs. After F9.2, code_audit agent runs are tracked in agent_db; overseer can detect underperforming BL 2.0 agents.
**Verdict threshold**:
- COMPLIANT: All targeted functions produce correct output; BL 1.x Q-pattern behavior preserved
- NON_COMPLIANT: Regex change broke BL 1.x detection or wave number extraction

---

## D10.1 [CORRECTNESS] hypothesis.py _parse_question_blocks() rejects all BL 2.0 LLM output
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: FAILURE
**Hypothesis**: Even after F9.1 fixed _QUESTION_BLOCK_HEADER for reading, `_parse_question_blocks()` in hypothesis.py line 167 still uses `rf"## Q{next_wave}\.\d+"` to validate LLM output. Any BL 2.0-format block (e.g., `## D10.1`) is silently rejected, making hypothesis generation return zero questions for BL 2.0 campaigns. The LLM prompt template also hardcodes `Q{wave}.N` IDs, instructing the LLM to produce BL-1.x-format output.
**Test**: Read bl/hypothesis.py lines 100-180. Confirm: (1) Line 167 uses rf"## Q{next_wave}" pattern. (2) Prompt template at line 115 uses `## Q{next_wave}.1`. (3) A block with `## D10.1 [CORRECTNESS] title` would be rejected by _parse_question_blocks() for wave 10.
**Verdict threshold**:
- FAILURE: _parse_question_blocks() line 167 uses Q-only regex and prompt template hardcodes Q-format IDs — hypothesis generation silently produces zero questions for any BL 2.0 campaign
- COMPLIANT: Both functions correctly accept BL 2.0 format IDs

---

## D10.2 [CORRECTNESS] synthesizer.py parse_recommendation() false-triggers STOP on Dead Ends prose
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: FAILURE
**Hypothesis**: `parse_recommendation()` in synthesizer.py scans ALL lines of synthesis text looking for "STOP" before "CONTINUE". The synthesis prompt template (line 166-168) instructs Claude to write "stop probing here" in the Dead Ends section. Any synthesis output with dead ends will cause parse_recommendation() to return "STOP" before reaching the actual "## Recommended Next Action" section, prematurely terminating campaigns.
**Test**: Read bl/synthesizer.py parse_recommendation() (lines 104-118) and the prompt template (lines 152-180). Construct a representative synthesis string with Dead Ends containing "stop probing here" and Recommended Next Action of CONTINUE. Verify parse_recommendation() returns "STOP" (incorrect).
**Verdict threshold**:
- FAILURE: parse_recommendation() returns "STOP" for a synthesis where "stop probing here" appears in Dead Ends but "CONTINUE" is the actual recommendation
- COMPLIANT: parse_recommendation() correctly extracts recommendation from the designated section

---

## F10.1 [FIX] Fix hypothesis.py _parse_question_blocks() and prompt template for BL 2.0 IDs
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Source finding**: D10.1 (FAILURE)
**Fix**: In bl/hypothesis.py: (1) Change line 167 filter from `rf"## Q{next_wave}\.\d+"` to `rf"## \w+{next_wave}\.\d+"` (or simpler: check for any `## ID [` header pattern matching the wave number). (2) Update the LLM prompt template (line 115) to show a BL 2.0-compatible example format with `## {mode_prefix}{wave}.N` — or make the format description mode-agnostic.
**Verdict threshold**:
- FIXED: _parse_question_blocks() accepts blocks with BL 2.0-format headers; prompt template does not hardcode Q-only format
- FIX_FAILED: Regex or prompt still excludes BL 2.0 format

---

## F10.2 [FIX] Fix synthesizer.py parse_recommendation() to scan only recommendation section
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Source finding**: D10.2 (FAILURE)
**Fix**: In bl/synthesizer.py parse_recommendation(): instead of scanning all lines, locate the "## Recommended Next Action" section header first, then scan only lines after that header for CONTINUE/STOP/PIVOT. Fallback to full-text scan only if section header is absent.
**Verdict threshold**:
- FIXED: parse_recommendation() correctly returns CONTINUE when "stop probing here" appears in Dead Ends but "CONTINUE" appears in Recommended Next Action section
- FIX_FAILED: Still returns STOP for the test case above

---

## A10.1 [COMPLIANCE] synthesizer.py _build_findings_corpus() truncation drops audit/diagnose findings
**Mode**: code_audit
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: NON_COMPLIANT
**Hypothesis**: `_build_findings_corpus()` drops from the front of the sorted findings list when over the 12000-char budget (pop(0) drops alphabetically earliest). In BL 2.0, alphabetical order is A*.md, D*.md, F*.md, R*.md, V*.md. Audit and diagnose findings are systematically excluded before fix/validate findings, giving the LLM a biased corpus that skews toward recent positive verdicts (FIXED/COMPLIANT) rather than root-cause failures.
**Test**: Read bl/synthesizer.py _build_findings_corpus() lines 18-56. Determine the truncation order: which finding types (by filename prefix) are dropped first under the 12000-char budget. Determine if this causes systematic omission of high-severity findings (FAILURE, NON_COMPLIANT) in favor of low-severity (FIXED, COMPLIANT).
**Verdict threshold**:
- NON_COMPLIANT: pop(0) drops A*.md and D*.md before F*.md and V*.md — audit/diagnose findings systematically omitted, synthesizer sees biased view
- COMPLIANT: Truncation strategy is acceptable or findings are small enough that budget is not hit in practice

---

## V10.1 [VALIDATE] _parse_question_blocks() and parse_recommendation() correct after F10.1+F10.2
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: DONE
**Motivated by**: F10.1 + F10.2 + A10.1
**Hypothesis**: After F10.1, hypothesis.py _parse_question_blocks() accepts BL 2.0 ID format blocks; LLM prompt no longer hardcodes Q-only IDs. After F10.2, parse_recommendation() correctly extracts CONTINUE from the Recommended Next Action section even when Dead Ends prose contains "stop".
**Verdict threshold**:
- COMPLIANT: Both fixes verified correct; no BL 1.x regression; corpus truncation behavior documented
- NON_COMPLIANT: Either fix broke BL 1.x behavior or failed to resolve the BL 2.0 issue

---

## D11.1 [CORRECTNESS] crucible.py scoring functions return 0.0 for all BL 2.0 campaigns
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: FAILURE
**Hypothesis**: `_score_hypothesis_generator()` and `_score_question_designer()` in crucible.py both rely on (1) "## Wave N" section headers that don't exist in BL 2.0 questions.md, and (2) Q-only regex patterns `## Q[2-9]\d*\.\d+` / `## Q\d+\.\d+` that don't match BL 2.0 IDs. Both scorers return AgentScore with score=0.0 and an error message for any BL 2.0 campaign, making crucible benchmarks meaningless.
**Test**: Read bl/crucible.py _score_hypothesis_generator() (lines 154-213) and _score_question_designer() (lines 216-282). Confirm: (1) wave_match regex requires "## Wave N" headers; (2) block-split regex is Q-prefix only; (3) For BL 2.0 questions.md (with no Wave headers and D/F/A/V IDs), both functions return score=0.0 before reaching any per-question scoring logic.
**Verdict threshold**:
- FAILURE: Both scorers return 0.0 for BL 2.0 campaigns due to missing Wave headers and Q-only block detection
- COMPLIANT: Scorers correctly handle BL 2.0 question ID format

---

## D11.2 [CORRECTNESS] questions.py sync_status_from_results() maps FAILURE/NON_COMPLIANT to DONE
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: FAILURE
**Hypothesis**: `sync_status_from_results()` in questions.py (lines 199-207) has its own verdict→status mapping that preserves only {INCONCLUSIVE, DIAGNOSIS_COMPLETE, PENDING_EXTERNAL, FIXED, FIX_FAILED, BLOCKED} and maps all other verdicts to "DONE". This means FAILURE, NON_COMPLIANT, WARNING, REGRESSION, ALERT are all mapped to "DONE" in the sync path — the same bug fixed by F8.2 in findings.py but left unfixed in this separate code path.
**Test**: Read bl/questions.py sync_status_from_results() lines 145-231. Identify the preserve list at lines 199-207. Confirm: verdict="FAILURE" maps to "DONE" (not "FAILURE"). Contrast with findings.py _PRESERVE_AS_IS (fixed by F8.2) which correctly preserves FAILURE.
**Verdict threshold**:
- FAILURE: sync_status_from_results() maps FAILURE/NON_COMPLIANT/WARNING → "DONE" in its preserve logic; diverges from findings.py F8.2 fix
- COMPLIANT: sync_status_from_results() correctly preserves all terminal failure verdicts

---

## F11.1 [FIX] Fix crucible.py scoring functions for BL 2.0 question ID format
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Source finding**: D11.1 (FAILURE)
**Fix**: In bl/crucible.py: (1) Replace "## Wave [2-9]" section header detection with wave number extraction from question IDs (same approach as hypothesis.py after F9.1). (2) Change block-split regex from Q-only to `## \w+\d+\.\d+` to match any letter-prefixed question ID. Apply to both _score_hypothesis_generator() and _score_question_designer().
**Verdict threshold**:
- FIXED: Both scorers correctly identify and score BL 2.0 question blocks; BL 1.x Q-format still works
- FIX_FAILED: Scorers still return 0.0 for BL 2.0 format question banks

---

## F11.2 [FIX] Fix questions.py sync_status_from_results() preserve list to match F8.2
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Source finding**: D11.2 (FAILURE)
**Fix**: In bl/questions.py sync_status_from_results() lines 199-207, extend the inner preserve set to include FAILURE, NON_COMPLIANT, WARNING, REGRESSION, ALERT — matching the F8.2 fix applied to findings.py _PRESERVE_AS_IS. These verdicts should appear verbatim in questions.md status, not be overwritten with "DONE".
**Verdict threshold**:
- FIXED: sync_status_from_results() maps FAILURE → "FAILURE", NON_COMPLIANT → "NON_COMPLIANT", etc. in questions.md
- FIX_FAILED: Still maps failure verdicts to "DONE"

---

## F11.3 [FIX] Fix synthesizer.py _build_findings_corpus() to preserve high-severity findings
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: DONE
**Source finding**: A10.1 (NON_COMPLIANT)
**Fix**: In bl/synthesizer.py _build_findings_corpus() lines 43-45, replace alphabetical pop(0) truncation with severity-aware truncation: findings containing COMPLIANT or FIXED verdicts are dropped before findings containing FAILURE or NON_COMPLIANT verdicts. Alternatively, sort findings by severity descending (FAILURE first) and truncate from the low-severity tail.
**Verdict threshold**:
- FIXED: Under budget pressure, FAILURE/NON_COMPLIANT findings are retained while COMPLIANT/FIXED findings are dropped first
- FIX_FAILED: Alphabetical truncation behavior unchanged

---

## V11.1 [VALIDATE] Crucible scoring, sync status, and corpus truncation correct after F11.1-F11.3
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: DONE
**Motivated by**: F11.1 + F11.2 + F11.3
**Hypothesis**: After F11.1, crucible scorers correctly identify BL 2.0 question blocks and produce meaningful scores. After F11.2, sync_status_from_results() maps FAILURE → "FAILURE" matching F8.2 behavior. After F11.3, corpus truncation preserves high-severity findings over COMPLIANT/FIXED findings.
**Verdict threshold**:
- COMPLIANT: All three fixes verified with test cases; BL 1.x behavior preserved for F11.1 and F11.2
- NON_COMPLIANT: Any fix regressed BL 1.x behavior or failed to address the BL 2.0 issue

---

## Wave 12 — Regression Detection + Failure Classification + Follow-up Coverage

**Generated from findings**: Waves 1-11 fixed verdict extraction, dispatch, parsing, scoring, and corpus truncation for BL 2.0. Wave 12 targets three remaining BL 1.x-only components: `_REGRESSIONS` in history.py (regression detection blind to BL 2.0 verdict pairs), `classify_failure_type_local()` in local_inference.py (skips NON_COMPLIANT/REGRESSION/ALERT), and C-04 adaptive follow-up in campaign.py (fires only on FAILURE/WARNING, skips NON_COMPLIANT).
**Mode transitions applied**: D11.1/D11.2 FAILURE → F11.1/F11.2 FIXED → V11.1 COMPLIANT → hypothesis: what other BL 1.x-only components remain?

---

## D12.1 [DIAGNOSE] _REGRESSIONS set in history.py contains only BL 1.x verdict pairs — BL 2.0 regressions invisible
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Hypothesis**: `_REGRESSIONS` in `bl/history.py` (lines 130-134) contains exactly three pairs: `("HEALTHY", "FAILURE")`, `("HEALTHY", "WARNING")`, `("WARNING", "FAILURE")`. These are BL 1.x-only verdict transitions. BL 2.0 introduces: COMPLIANT, NON_COMPLIANT, FIXED, FIX_FAILED, DIAGNOSIS_COMPLETE, BLOCKED, REGRESSION, ALERT, DEGRADED, UNKNOWN, PROMISING, CALIBRATED. Verdict transitions like `("COMPLIANT", "NON_COMPLIANT")`, `("FIXED", "FAILURE")`, `("FIXED", "NON_COMPLIANT")`, `("HEALTHY", "NON_COMPLIANT")`, and `("DIAGNOSIS_COMPLETE", "FAILURE")` are valid BL 2.0 regressions that `detect_regression()` and `get_regressions()` currently return `None`/`[]` for — making the regression ledger completely blind to BL 2.0 campaign regressions.
**Test**: `grep -n "_REGRESSIONS" bl/history.py` — verify set contains only 3 BL 1.x pairs. Trace `detect_regression("D1", "NON_COMPLIANT")` when previous verdict was "COMPLIANT" — confirm it returns None.
**Verdict threshold**:
- FAILURE: `_REGRESSIONS` contains only BL 1.x pairs; BL 2.0 regression transitions return None
- HEALTHY: `_REGRESSIONS` already includes BL 2.0 pairs

---

## D12.2 [DIAGNOSE] classify_failure_type_local() returns None for NON_COMPLIANT/REGRESSION/ALERT — BL 2.0 failure classification skipped
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: FAILURE
**Hypothesis**: `classify_failure_type_local()` in `bl/local_inference.py` line 55: `if verdict not in ("FAILURE", "INCONCLUSIVE"): return None`. BL 2.0 failure verdicts `NON_COMPLIANT`, `REGRESSION`, and `ALERT` are not in this tuple — the function returns `None` for them, so `failure_type` is never classified for compliance audit failures. Additionally, `_SYSTEM_PROMPT` (lines 15-22) only describes BL 1.x verdicts (HEALTHY/WARNING/FAILURE/INCONCLUSIVE), so even if the guard were fixed, the local model would have no context for BL 2.0 verdict semantics.
**Test**: `grep -n "FAILURE.*INCONCLUSIVE\|not in.*FAILURE" bl/local_inference.py` — verify line 55 excludes BL 2.0 verdicts. Trace `classify_failure_type_local({"verdict": "NON_COMPLIANT", "summary": "..."}, "code_audit")` — confirm returns None.
**Verdict threshold**:
- FAILURE: Line 55 guard excludes NON_COMPLIANT/REGRESSION/ALERT; classification skipped for these verdicts
- HEALTHY: Guard already includes BL 2.0 failure verdicts

---

## A12.1 [AUDIT] C-04 adaptive follow-up in campaign.py only fires for FAILURE/WARNING — NON_COMPLIANT excluded
**Mode**: code_audit
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: NON_COMPLIANT
**Hypothesis**: `campaign.py` line 106: `if result.get("verdict") in ("FAILURE", "WARNING"):` — the C-04 adaptive follow-up drill-down only generates sub-questions for FAILURE and WARNING verdicts. BL 2.0 audit questions return `NON_COMPLIANT` when violations are found. No follow-up is generated for NON_COMPLIANT results, making the drill-down mechanism non-functional for the entire compliance audit mode. DIAGNOSIS_COMPLETE (which triggers the heal loop) is also excluded — though the heal loop handles it separately.
**Test**: `grep -n "verdict.*FAILURE.*WARNING\|generate_followup" bl/campaign.py` — check line 106 guard. Verify NON_COMPLIANT is absent from the tuple.
**Verdict threshold**:
- NON_COMPLIANT: Line 106 guard excludes NON_COMPLIANT; follow-up dead for compliance audit failures
- COMPLIANT: NON_COMPLIANT is included in the follow-up trigger guard

---

## F12.1 [FIX] Add BL 2.0 regression pairs to _REGRESSIONS in history.py
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: FIXED
**Motivated by**: D12.1
**Fix**: Add BL 2.0 regression pairs to `_REGRESSIONS` in `bl/history.py`: `("COMPLIANT", "NON_COMPLIANT")`, `("COMPLIANT", "FAILURE")`, `("FIXED", "FAILURE")`, `("FIXED", "NON_COMPLIANT")`, `("HEALTHY", "NON_COMPLIANT")`, `("DIAGNOSIS_COMPLETE", "FAILURE")`. BL 1.x pairs remain unchanged.
**Verdict threshold**:
- FIXED: All 6 BL 2.0 pairs added; BL 1.x pairs preserved; detect_regression() now returns regression dict for COMPLIANT→NON_COMPLIANT
- FIX_FAILED: Pairs not added or BL 1.x pairs removed

---

## F12.2 [FIX] Extend classify_failure_type_local() guard to include BL 2.0 failure verdicts and update _SYSTEM_PROMPT
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: FIXED
**Motivated by**: D12.2
**Fix**: In `bl/local_inference.py` line 55, change guard to: `if verdict not in ("FAILURE", "INCONCLUSIVE", "NON_COMPLIANT", "REGRESSION", "ALERT"): return None`. Also update `_SYSTEM_PROMPT` to describe BL 2.0 verdicts so the local model can classify them correctly.
**Verdict threshold**:
- FIXED: Guard includes 3 BL 2.0 failure verdicts; _SYSTEM_PROMPT updated with BL 2.0 context
- FIX_FAILED: Guard unchanged or regresses BL 1.x behavior

---

## F12.3 [FIX] Add NON_COMPLIANT to C-04 follow-up trigger guard in campaign.py
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: FIXED
**Motivated by**: A12.1
**Fix**: In `bl/campaign.py` line 106, change `if result.get("verdict") in ("FAILURE", "WARNING"):` to `if result.get("verdict") in ("FAILURE", "WARNING", "NON_COMPLIANT"):`. This enables C-04 adaptive drill-down for compliance audit failures without affecting BL 1.x behavior.
**Verdict threshold**:
- FIXED: NON_COMPLIANT added to guard; follow-up generated for compliance audit failures
- FIX_FAILED: Guard unchanged or regressed

---

## V12.1 [VALIDATE] Regression detection, failure classification, and follow-up trigger correct after F12.1-F12.3
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: DONE
**Motivated by**: F12.1 + F12.2 + F12.3
**Hypothesis**: After F12.1, detect_regression() returns a regression dict for COMPLIANT→NON_COMPLIANT and FIXED→FAILURE transitions. After F12.2, classify_failure_type_local() processes NON_COMPLIANT verdicts. After F12.3, C-04 follow-up fires for NON_COMPLIANT results. All BL 1.x behaviors preserved.
**Verdict threshold**:
- COMPLIANT: All three fixes verified; no BL 1.x regressions
- NON_COMPLIANT: Any fix regressed or failed to address root cause

---

## Wave 13 — Follow-up Sub-question Quality for BL 2.0

**Generated from findings**: Wave 12 fixed regression detection, failure classification, and C-04 follow-up trigger. Wave 13 targets the sub-question *content* generated by followup.py: the prompt defaults wrong agent for BL 2.0 code_audit mode, sub-questions lack **Operational Mode** field, and bracket tag injection uses runner mode string instead of operational mode.
**Mode transitions applied**: F12.3 FIXED (C-04 now triggers for NON_COMPLIANT) → raises question: are the sub-questions it generates actually correct for BL 2.0?

---

## D13.1 [DIAGNOSE] followup.py sub-question prompt uses wrong default agent for BL 2.0 code_audit questions
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Hypothesis**: `_build_followup_prompt()` in `bl/followup.py` line 102: `agent = question.get("agent_name", "quantitative-analyst")`. BL 2.0 code_audit questions (mode="code_audit") have no `agent_name` field in questions.md — they use `**Agent**:` as a documentation field but it's not parsed into `agent_name` in `parse_questions()`. So all BL 2.0 follow-up sub-questions will be generated with `**Agent**: quantitative-analyst`, which is a BL 1.x simulation agent — not the correct agent for compliance audit drill-down (should be `compliance-auditor`, `diagnose-analyst`, or `design-reviewer`).
**Test**: `grep -n "agent_name\|\"agent\"" bl/questions.py` — verify whether `**Agent**:` body field is parsed into `agent_name`. Then trace `_build_followup_prompt({"mode": "code_audit", ...}, ...)` — confirm agent defaults to "quantitative-analyst".
**Verdict threshold**:
- FAILURE: `agent_name` not parsed from `**Agent**:` field; default falls to "quantitative-analyst" for BL 2.0 questions
- HEALTHY: `agent_name` correctly populated from `**Agent**:` body field

---

## D13.2 [DIAGNOSE] followup.py sub-question format missing **Operational Mode** field — all sub-questions default to diagnose
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: FAILURE
**Hypothesis**: The sub-question format template in `_build_followup_prompt()` (lines 126-138) does not include a `**Operational Mode**:` field. The prompt produces sub-questions with `**Mode**: {mode}` (runner mode) and `**Agent**: {agent}` but no `**Operational Mode**:` line. When `parse_questions()` parses these sub-questions, `operational_mode` defaults to "diagnose" regardless of the parent question's operational mode. A follow-up from a NON_COMPLIANT audit result would generate sub-questions with operational_mode="diagnose" instead of "audit" — wrong mode context injected into the sub-question agent.
**Test**: Read `bl/followup.py` lines 126-138 — verify `**Operational Mode**:` is absent from the prompt template. Then check `bl/questions.py` parse_questions() default for operational_mode — confirm it defaults to "diagnose".
**Verdict threshold**:
- FAILURE: `**Operational Mode**:` absent from sub-question prompt; sub-questions default to "diagnose"
- HEALTHY: Sub-question format includes correct operational_mode derived from parent

---

## A13.1 [AUDIT] followup.py bracket tag injection uses mode.upper() — produces [CODE_AUDIT] instead of operational mode bracket
**Mode**: code_audit
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: NON_COMPLIANT
**Hypothesis**: `_parse_followup_blocks()` in `bl/followup.py` lines 209-219: when a sub-question block lacks a `[TAG]` in its header, it injects one using `mode_tag = f"[{mode_match.group(1).upper()}]"` where `mode_match` extracts from `**Mode**: code_audit`. This produces `[CODE_AUDIT]` as the bracket tag. BL 2.0 bracket tags must be one of: `DIAGNOSE`, `FIX`, `AUDIT`, `VALIDATE`, `MONITOR`, `FRONTIER`, `PREDICT`, `RESEARCH`, `EVOLVE`. `CODE_AUDIT` is not a valid bracket tag — it's a runner mode string. Questions with `[CODE_AUDIT]` bracket tags would be misclassified during parse and may not dispatch correctly.
**Test**: Read `bl/followup.py` lines 206-219 — verify the mode_tag construction uses `mode.upper()`. Trace what tag would be injected for a `**Mode**: code_audit` sub-question. Check if `[CODE_AUDIT]` is a registered bracket tag in BL 2.0.
**Verdict threshold**:
- NON_COMPLIANT: `[CODE_AUDIT]` injected as bracket tag; not a valid BL 2.0 operational mode tag
- COMPLIANT: Bracket tag derives from operational_mode field, not runner mode

---

## F13.1 [FIX] Fix followup.py sub-question prompt to use correct agent and include Operational Mode field
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: FIXED
**Motivated by**: D13.1 + D13.2
**Fix**: In `bl/followup.py` `_build_followup_prompt()`: (1) Use `agent = question.get("agent_name") or question.get("agent", "diagnose-analyst")` — parse `**Agent**:` field from question dict. (2) Add `op_mode = question.get("operational_mode", "diagnose")` and include `**Operational Mode**: {op_mode}` in the sub-question format template. This ensures BL 2.0 follow-up sub-questions inherit the correct agent and operational mode from their parent.
**Verdict threshold**:
- FIXED: Sub-question prompt uses correct agent from parent; format includes **Operational Mode** field
- FIX_FAILED: Default remains quantitative-analyst or operational_mode still absent

---

## F13.2 [FIX] Fix followup.py bracket tag injection to use operational_mode not runner mode
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: FIXED
**Motivated by**: A13.1
**Fix**: In `bl/followup.py` `_parse_followup_blocks()` lines 209-219: change bracket tag injection to use `operational_mode` field extracted from the sub-question body instead of `mode`. Change: `op_mode_match = re.search(r"\*\*Operational Mode\*\*:\s*(\w+)", seg)`, derive tag from that. Mapping: audit→AUDIT, diagnose→DIAGNOSE, fix→FIX, validate→VALIDATE, monitor→MONITOR. If no operational_mode found, fall back to DIAGNOSE.
**Verdict threshold**:
- FIXED: Bracket tag uses operational_mode; [AUDIT] injected for audit sub-questions; [CODE_AUDIT] eliminated
- FIX_FAILED: [CODE_AUDIT] still produced or mode.upper() still used

---

## V13.1 [VALIDATE] Follow-up sub-question quality correct after F13.1-F13.2
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: COMPLIANT
**Motivated by**: F13.1 + F13.2
**Hypothesis**: After F13.1, BL 2.0 follow-up sub-questions include **Operational Mode** and use the parent question's agent. After F13.2, bracket tag injection derives from operational_mode not runner mode. Combined: NON_COMPLIANT follow-up sub-questions are now correctly structured for BL 2.0 audit drill-down.
**Verdict threshold**:
- COMPLIANT: Both fixes verified; sub-questions include operational_mode; bracket tag uses operational mode
- NON_COMPLIANT: Any issue remains or BL 1.x behavior regressed

<!-- Wave 14 -->

---

## Wave 14 — Unaudited modules: goal.py, synthesizer.py, skill_forge.py, quality.py

**Generated from findings**: Wave 13 complete (V13.1 COMPLIANT). Wave 14 targets four source modules not previously audited — goal.py, synthesizer.py, skill_forge.py, quality.py — plus a residual check of healloop.py post all Wave 1-13 fixes.
**Mode transitions applied**: Clean slate from Wave 13 -> new Diagnose questions against unaudited modules. Two bugs confirmed in goal.py (QG-only ID scope, BL 1.x domain focus strings), two confirmed in synthesizer.py (wrong output path, incomplete severity frozenset), one clean bill for healloop.py.

---

## D14.1 [DIAGNOSE] goal.py wave-index collision — QG-only scan misses BL 2.0 numeric wave IDs
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Hypothesis**: `_get_next_wave_index()` in `bl/goal.py` line 220 scans `questions.md` with the regex `r"## QG(\d+)\.\d+"` — it only finds existing QG-prefixed question headers. In a BL 2.0 campaign where all waves are numbered D1, F2, A3, V4, M5 (no QG headers present), `_get_next_wave_index()` returns 1 every time. Every goal-directed batch is therefore labelled `QG1.x`, colliding with any previous goal campaign. The `"## QG"` guard in `_parse_goal_questions()` lines 236 and 242 compounds this: the LLM cannot produce BL 2.0-style IDs because any block without `## QG` is silently dropped.
**Test**: Trace `_get_next_wave_index(text)` where `text` is a BL 2.0 `questions.md` containing only `## D1.1`, `## F2.1`, `## A3.1` headers (no `## QG` headers). Confirm it returns 1. Then read `_parse_goal_questions()` lines 236 and 242 — confirm both guards use the string literal `"## QG"` and would discard any block with a `## D14.1`-style header.
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: `_get_next_wave_index()` returns 1 on a BL 2.0 questions.md with no QG headers; `_parse_goal_questions()` drops non-QG blocks; fix requires expanding the wave-index regex to also count BL 2.0 numeric waves and relaxing the QG-only guard in the block filter
- HEALTHY: wave-index regex already covers BL 2.0 IDs and the block filter is prefix-agnostic

---

## D14.2 [DIAGNOSE] goal.py focus default uses BL 1.x domain codes D1-D6, forcing wrong bracket tags from LLM
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Hypothesis**: `_build_prompt()` in `bl/goal.py` line 128 sets `focus_str = "all domains (D1-D6)"` when no focus is specified in goal.md. The string "D1-D6" is the BL 1.x domain taxonomy (D1=volume, D2=regulatory, D3=competitive, D4=unit economics, D5=operational, D6=cohort). BL 2.0 has no domain taxonomy — it uses operational modes (DIAGNOSE, FIX, AUDIT, VALIDATE, MONITOR, FRONTIER). The LLM interprets the D1-D6 hint as an instruction to emit `[D1]` / `[D2]` bracket tags in generated question headers (the prompt template on lines 158 and 170 shows `[D1]` and `[D4]` as examples). When parsed by `parse_questions()`, a `[D1]` bracket tag does not map to any BL 2.0 operational mode, producing wrong question_type routing.
**Test**: Read `_build_prompt()` line 128 — confirm the focus default is `"all domains (D1-D6)"`. Read the prompt template lines 155-181 — confirm header examples show `[D1]` and `[D4]` bracket tags. Then check `bl/questions.py` `_CODE_AUDIT_TAGS` and `_BEHAVIORAL_TAGS` constants — confirm `d1` through `d6` do not map to any BL 2.0 code_audit or operational mode tag, and that `question_type` for a `[D1]` bracket defaults to "behavioral".
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: Default focus is "D1-D6"; prompt template uses `[D1]`/`[D4]` examples; LLM output uses BL 1.x bracket tags that misroute in BL 2.0; fix requires replacing focus default and prompt examples with BL 2.0 operational mode terminology (DIAGNOSE, FIX, AUDIT, VALIDATE, MONITOR)
- HEALTHY: Focus default and prompt template already use BL 2.0 operational modes

---

## D14.3 [DIAGNOSE] synthesizer.py writes synthesis.md to project root — callers expect findings/synthesis.md
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Hypothesis**: `synthesize()` in `bl/synthesizer.py` line 226 writes to `project_dir / "synthesis.md"` (project root). The campaign loop, the dashboard backend, and the CLAUDE.md documentation all reference `findings/synthesis.md`. The `_build_findings_corpus()` reads from `project_dir / "findings"` via `findings_dir.glob("*.md")` — so a `synthesis.md` at project root is never included in the next synthesis corpus. Any caller that opens `project_dir / "findings" / "synthesis.md"` gets a FileNotFoundError or silently uses a stale file while the real synthesis sits one level up.
**Test**: Read `bl/synthesizer.py` line 226 — confirm output path is `project_dir / "synthesis.md"`. Read CLAUDE.md and any runner or loop code that reads synthesis output — confirm they reference `findings/synthesis.md`. Confirm `_build_findings_corpus()` line 34 uses `findings_dir.glob("*.md")` which excludes a root-level file.
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: Output path is project root not findings/; callers reference findings/synthesis.md; fix is changing line 226 to `project_dir / "findings" / "synthesis.md"` and ensuring the directory exists before writing
- HEALTHY: Output path already writes to findings/synthesis.md, or all callers consistently use project root

---

## A14.1 [AUDIT] synthesizer.py severity frozenset excludes all BL 2.0 high-signal verdicts — DIAGNOSIS_COMPLETE dropped under budget pressure
**Mode**: code_audit
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: NON_COMPLIANT
**Hypothesis**: `_build_findings_corpus()` in `bl/synthesizer.py` lines 44-54 defines `_HIGH_SEVERITY = frozenset({"FAILURE", "NON_COMPLIANT", "WARNING", "REGRESSION", "ALERT"})` and uses it to prioritize findings when the corpus exceeds the 12000-char budget. BL 2.0 adds verdict strings absent from this set: `DIAGNOSIS_COMPLETE` (confirmed bug with fix spec — highest actionable signal), `FIX_FAILED` (failed fix attempt — high signal), `BLOCKED` (frontier blocked), `PROMISING` (frontier viable), `IMMINENT` and `PROBABLE` (cascade prediction). Under budget pressure, a `DIAGNOSIS_COMPLETE` finding is assigned priority=1 (low severity) and dropped before a `COMPLIANT` or `FIXED` finding — the opposite of correct behavior. The synthesizer corpus will systematically exclude the most actionable BL 2.0 findings in long campaigns.
**Test**: Read `_HIGH_SEVERITY` frozenset at lines 44-45 — list its members exactly. Confirm `DIAGNOSIS_COMPLETE`, `FIX_FAILED`, `BLOCKED`, `PROMISING`, `IMMINENT`, `PROBABLE` are absent. Trace `_finding_priority()` for a finding string containing `**Verdict**: DIAGNOSIS_COMPLETE` — confirm it returns 1 (low priority). Trace it for a finding containing `**Verdict**: COMPLIANT` — confirm it also returns 1. Confirm both are dropped in tail-first order under budget pressure, meaning late-wave DIAGNOSIS_COMPLETE findings are the first to be truncated.
**Verdict threshold**:
- NON_COMPLIANT: DIAGNOSIS_COMPLETE, FIX_FAILED, and other BL 2.0 verdicts are absent from `_HIGH_SEVERITY`; these findings are treated as droppable under corpus budget pressure; fix requires adding all BL 2.0 high-signal verdicts to the frozenset
- COMPLIANT: All BL 2.0 high-severity verdicts are present in `_HIGH_SEVERITY` or an equivalent priority mechanism covers them

---

## V14.1 [VALIDATE] skill_forge.py and quality.py are structurally clean — no BL 1.x verdict strings or ID patterns
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: COMPLIANT
**Motivated by**: Wave 14 pre-flight — these modules not yet audited
**Hypothesis**: `bl/skill_forge.py` and `bl/quality.py` contain no verdict string comparisons, no question ID regex patterns, and no mode dispatch logic. They are pure utility modules (skill file I/O and amnesty feasibility math respectively). Neither references BL 1.x-only verdict lists, Q-prefix ID patterns, or domain codes D1-D6. Both are structurally clean for BL 2.0 use.
**Test**: Read `bl/skill_forge.py` in full — verify: (1) no verdict string comparisons against hardcoded lists, (2) no regex patterns matching question IDs, (3) no mode string dispatch tables. Read `bl/quality.py` in full — verify: (1) `action_type` parameter is a free-form string with no hardcoded BL 1.x action type enumeration beyond "amnesty", (2) no references to Q-prefix IDs or D1-D6 domain codes. Note any unexpected imports or hidden BL-version-specific dependencies.
**Verdict threshold**:
- COMPLIANT: Both files contain no BL 1.x verdict strings, no Q-prefix ID regexes, no domain code references; structurally safe for BL 2.0 campaigns
- NON_COMPLIANT: Either file contains hardcoded BL 1.x verdict strings, Q-prefix ID patterns, or other BL-version-specific logic that would fail silently in BL 2.0 campaigns

<!-- Wave 14 Fixes -->

## F14.1 [FIX] Fix goal.py wave-index and prompt template for BL 2.0 compatibility
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: FIXED
**Motivated by**: D14.1 + D14.2
**Fix**: In `bl/goal.py`: (1) Line 220: expand `_get_next_wave_index()` to scan both `## QG(\d+)` and `## [DFAV](\d+)` headers, taking max across both sets. (2) Line 128: replace `"all domains (D1–D6)"` with `"all operational modes (DIAGNOSE, FIX, AUDIT, VALIDATE)"`. (3) Lines 158/170: replace `[D1]`/`[D4]` bracket tag examples with `[DIAGNOSE]`/`[AUDIT]` and add `**Operational Mode**: diagnose`/`audit` field to each example block.
**Verdict threshold**:
- FIXED: wave-index counts BL 2.0 headers; prompt uses BL 2.0 tags; [D1]/[D4] eliminated
- FIX_FAILED: any BL 1.x domain code remains in defaults or examples

---

## F14.2 [FIX] Fix synthesizer.py output path and _HIGH_SEVERITY frozenset
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: FIXED
**Motivated by**: D14.3 + A14.1
**Fix**: In `bl/synthesizer.py`: (1) Line 226: change `project_dir / "synthesis.md"` to `project_dir / "findings" / "synthesis.md"`. (2) Lines 45-47: add `DIAGNOSIS_COMPLETE` and `FIX_FAILED` to `_HIGH_SEVERITY` frozenset.
**Verdict threshold**:
- FIXED: synthesis written to findings/synthesis.md; DIAGNOSIS_COMPLETE and FIX_FAILED in _HIGH_SEVERITY
- FIX_FAILED: path still wrong or frozenset still missing BL 2.0 verdicts

---

## V14.2 [VALIDATE] goal.py and synthesizer.py fixes correct after F14.1-F14.2
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: COMPLIANT
**Motivated by**: F14.1 + F14.2
**Hypothesis**: After F14.1, goal.py correctly counts BL 2.0 wave indices and uses BL 2.0 bracket tags. After F14.2, synthesizer.py writes to findings/synthesis.md and retains DIAGNOSIS_COMPLETE/FIX_FAILED findings under budget pressure.
**Verdict threshold**:
- COMPLIANT: all fixes verified; no regressions
- NON_COMPLIANT: any check fails

