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

<!-- Wave 15 -->

---

## Wave 15

**Generated from findings**: Wave 14 DIAGNOSIS_COMPLETE verdicts (D14.1, D14.2, D14.3, A14.1) resolved via F14.1, F14.2, V14.2; new audit of questions.py, crucible.py, agent_db.py
**Mode transitions applied**: fresh audit of three unaudited modules → 3 DIAGNOSIS_COMPLETE → D15.1, D15.2, D15.3 Diagnose; 1 DIAGNOSIS_COMPLETE → D15.4 Diagnose; 1 DIAGNOSIS_COMPLETE → A15.1 Audit

---

## D15.1 [DIAGNOSE] questions.py sync_status_from_results() uses "\n## Q" sentinel — truncates BL 2.0 block boundaries at end-of-file
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Hypothesis**: `sync_status_from_results()` in `bl/questions.py` line 225 locates the end of a question block with `text.find("\n## Q", block_start + 1)`. The sentinel string `"\n## Q"` only matches BL 1.x question headers (e.g., `## Q5.2`). In a BL 2.0 questions.md containing only headers like `## D1.1`, `## F2.1`, `## A14.1`, the sentinel will never match, so `next_block` is always -1 and `block_end` is always `len(text)`. This means the `block` variable spans from the current question header to the very end of the file. When `str.replace()` is called on this oversized block, it replaces only the first occurrence of `**Status**: PENDING` — which is correct for the current question — but the replacement target and the replacement text are then written back as `text[:block_start] + new_block + text[block_end:]`, where `text[block_end:]` is empty. Each call to `sync_status_from_results()` for a non-last question correctly patches only one status line, but any subsequent question whose update runs while the prior iteration's oversized `block` is still in scope will operate on stale string indices. The actual bug: if two questions have `**Status**: PENDING` in the same "block" (which now spans to EOF), the second replace call on the already-modified `text` string will use indices derived from the pre-modification string — producing a corrupted or double-patched questions.md.
**Test**: Read `bl/questions.py` lines 219-233. Confirm the sentinel on line 225 is the literal string `"\n## Q"`. Construct a two-question BL 2.0 questions.md with headers `## D15.1` and `## D15.2` both `PENDING`. Trace `sync_status_from_results()` with `done_ids = {"D15.1": "DONE", "D15.2": "DONE"}` — confirm that on the first iteration `block_end = len(text)` (spanning both blocks), and on the second iteration the string indices derived from the original `text` are now misaligned with the modified string, producing either a double-replace or a missing replace.
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: sentinel is `"\n## Q"` (confirmed BL 1.x-only); `next_block` resolves to -1 for all BL 2.0 headers; the index-based replacement is applied to a stale string reference when multiple questions are updated in one pass; fix requires replacing the sentinel with a generic next-header pattern such as `re.search(r"\n## \w", text[block_start+1:])` or iterating over pre-computed block boundaries
- HEALTHY: sentinel already covers BL 2.0 headers, or the string replacement is re-parsed after each update making indices non-stale

---

## D15.2 [DIAGNOSE] crucible.py _score_question_designer() domains_covered check is hardwired to BL 1.x D1-D6 domain codes — always scores 0 in BL 2.0 campaigns
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Hypothesis**: `_score_question_designer()` in `bl/crucible.py` lines 246-260 defines `domain_keywords` as a dict mapping `"D1"` through `"D6"` to lists of BL 1.x domain-specific keywords (`"performance"`, `"legal"`, `"regulatory"`, `"market"`, `"benchmark"`, `"security"`, etc.). It then scans `wave1_text` for any of these keywords and scores `domains_covered = len(domain_hits) / 6.0`. In a BL 2.0 campaign, there are no D1-D6 domain codes — the six BL 1.x domains do not exist. The question-designer in BL 2.0 uses operational modes (DIAGNOSE, FIX, AUDIT, VALIDATE, MONITOR, FRONTIER). None of the BL 1.x domain keywords are guaranteed to appear in BL 2.0 questions, so `domain_hits` will be empty or near-empty and `domains_covered` scores 0.0. Since `domains_covered` carries a 0.35 weight (line 270), the question-designer's overall Crucible score is structurally suppressed by at least 0.35 in every BL 2.0 campaign, regardless of actual output quality. This will flag the question-designer as underperforming and trigger unnecessary overseer intervention.
**Test**: Read `bl/crucible.py` lines 246-287. Confirm `domain_keywords` keys are `"D1"` through `"D6"`. Confirm the `domains_covered` weight in `weights` dict is 0.35. Then read a real BL 2.0 Wave 1 question block from `questions.md` — confirm it contains none of the BL 1.x domain keywords associated with D1-D6 (e.g., "regulatory", "benchmark", "cohort"), making `domain_hits` empty and `domains_covered = 0.0`. Calculate the maximum achievable score for question-designer in a BL 2.0 campaign (should be 0.65 if all other checks pass — below the 0.80 promote threshold and approaching the 0.50 flag threshold).
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: `domain_keywords` keys are `"D1"` through `"D6"`; `domains_covered` weight is 0.35; BL 2.0 questions produce near-zero domain coverage; maximum achievable question-designer score in BL 2.0 is ≤ 0.65; fix requires replacing the BL 1.x domain coverage check with a BL 2.0 operational mode coverage check (DIAGNOSE, FIX, AUDIT, VALIDATE, MONITOR, FRONTIER)
- HEALTHY: domain keywords already include BL 2.0 operational mode terms, or the domains_covered check has been replaced with a mode-coverage check

---

## D15.3 [DIAGNOSE] crucible.py _score_synthesizer() and _score_quantitative_analyst() use BL 1.x-only file globs and ID regexes — both score 0 in BL 2.0 campaigns
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Hypothesis**: Two rubric functions in `bl/crucible.py` contain BL 1.x-only patterns that produce structural zero scores in BL 2.0 campaigns. First, `_score_synthesizer()` at line 302 checks `has_finding_refs` with `re.search(r"Q\d+\.\d+", text)` — this only matches BL 1.x finding IDs (`Q5.2`, `Q12.1`). BL 2.0 synthesis files reference findings as `D14.1`, `F2.1`, `A10.1` — none matching `Q\d+\.\d+`. `has_finding_refs` carries weight 0.30, so every BL 2.0 synthesis loses 0.30 from its score structurally, independent of quality. Second, `_score_quantitative_analyst()` at line 328 globs `findings_dir.glob("Q*.md")` — only finding files whose names begin with `Q` are examined. In BL 2.0, all finding files are named by BL 2.0 IDs (`D1.md`, `A10.1.md`, `F14.1.md`, etc.). The glob returns an empty list, the function returns `AgentScore(..., 0.0, {}, "No performance/D1/D5 findings found")`, and quantitative-analyst's Crucible score is permanently 0.0 regardless of its actual performance.
**Test**: Read `bl/crucible.py` line 302 — confirm `has_finding_refs` regex is `r"Q\d+\.\d+"`. Confirm weight is 0.30 in `checks_raw`. Read line 328 — confirm glob pattern is `"Q*.md"`. List actual finding files in a BL 2.0 project's findings/ directory — confirm all are named with BL 2.0 prefixes (D, F, A, V, M) and none match `Q*.md`. Confirm the function returns score=0.0 with the "No performance/D1/D5 findings found" message.
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: `has_finding_refs` uses `Q\d+\.\d+` regex (BL 1.x only); `_score_quantitative_analyst()` globs `Q*.md` (returns empty in BL 2.0); both produce structural zero scores; fix requires: (1) expanding the synthesis finding-refs regex to `[A-Z]\d+\.\d+` or `[DFAVM]\d+`, (2) changing the quantitative-analyst glob to `"*.md"` with a filter for performance-relevant content
- HEALTHY: both patterns already cover BL 2.0 IDs

---

## A15.1 [AUDIT] crucible.py _KNOWN_AGENTS excludes all BL 2.0 operational agents — diagnose-analyst, fix-implementer, compliance-auditor, design-reviewer are never benchmarked
**Mode**: code_audit
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: NON_COMPLIANT
**Hypothesis**: `_KNOWN_AGENTS` in `bl/crucible.py` lines 31-36 is a fixed list: `["hypothesis-generator", "question-designer", "synthesizer", "quantitative-analyst"]`. These are the four BL 1.x specialist agents. BL 2.0 introduced four new operational agents: `diagnose-analyst`, `fix-implementer`, `compliance-auditor`, and `design-reviewer`. None of these appear in `_KNOWN_AGENTS`. The consequences: (1) `get_all_statuses()` at line 401 only returns statuses for the four BL 1.x agents — the BL 2.0 fleet is invisible to Crucible's status tracking; (2) `print_report()` only prints rows for the four listed agents — the campaign operator never sees Crucible benchmarks for the agents doing the majority of BL 2.0 work; (3) `run_all_benchmarks()` only runs the four BL 1.x scorers — even if a BL 2.0 scorer were added to `_SCORERS`, it would be unreachable via `get_all_statuses()` because `_KNOWN_AGENTS` controls which agents appear in the status table. The BL 2.0 operational agent fleet is permanently invisible to the Crucible benchmarking system.
**Test**: Read `bl/crucible.py` lines 31-36 — list the exact contents of `_KNOWN_AGENTS`. Confirm `diagnose-analyst`, `fix-implementer`, `compliance-auditor`, and `design-reviewer` are absent. Read `get_all_statuses()` at line 401 — confirm it iterates only `_KNOWN_AGENTS`. Read `print_report()` at line 416 — confirm it iterates only `_KNOWN_AGENTS`. Check whether any BL 2.0 agent scorer exists in `_SCORERS` — confirm it would be unreachable via the current status/reporting path even if added.
**Verdict threshold**:
- NON_COMPLIANT: `_KNOWN_AGENTS` contains only BL 1.x agents; `diagnose-analyst`, `fix-implementer`, `compliance-auditor`, `design-reviewer` are absent; status tracking and reporting are blind to the BL 2.0 agent fleet; fix requires adding BL 2.0 agents to `_KNOWN_AGENTS` and adding corresponding rubric scorers to `_SCORERS`
- COMPLIANT: `_KNOWN_AGENTS` already includes BL 2.0 operational agents

---

## D15.4 [DIAGNOSE] agent_db.py unclassified verdict silently counts as failure — no warning emitted and no escape hatch for future BL 2.0 verdicts
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: HEALTHY
**Hypothesis**: `_compute_score()` in `bl/agent_db.py` lines 113-121 calculates agent score by summing verdict counts from `_SUCCESS_VERDICTS` and `_PARTIAL_VERDICTS` frozensets. Any verdict string that is not a member of either frozenset contributes 0 to the numerator but 1 to the denominator (via `rec["runs"]`, which is incremented unconditionally in `record_run()` line 151). An unclassified verdict is therefore treated identically to a full failure (`_FAILURE_VERDICTS` member), but silently — no log line, no warning, and no way for an operator to distinguish "agent produced FAILURE" from "agent produced an unknown verdict string". As BL 2.0 gains new verdicts (e.g., `BLOCKED` is in `_PARTIAL_VERDICTS` but a future `STALLED` or `DEGRADED_PARTIAL` would not be), the silent zero-credit treatment will depress agent scores without any observable signal. The three frozensets together cover 29 verdict strings, but `constants.py` defines a larger set — any verdict present in `constants.py` but absent from all three frozensets in `agent_db.py` will be silently misclassified.
**Test**: Read `bl/agent_db.py` lines 27-73 — list all verdicts in `_SUCCESS_VERDICTS`, `_PARTIAL_VERDICTS`, and `_FAILURE_VERDICTS`. Read `bl/constants.py` (or equivalent) — list all defined verdict strings. Compute the set difference: verdicts in constants.py not present in any of the three agent_db frozensets. Confirm that `_compute_score()` assigns 0 credit to any verdict in that difference set without logging a warning. Confirm `record_run()` line 151 increments `runs` before any verdict classification check.
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: at least one verdict defined in constants.py is absent from all three agent_db frozensets; absent verdicts receive 0 credit silently; `record_run()` increments `runs` before classification; no warning is emitted for unclassified verdicts; fix requires either (1) an exhaustive check that logs a warning when an unclassified verdict is recorded, or (2) an "unknown → partial" fallback with a warning log
- HEALTHY: the union of the three frozensets exactly covers all verdict strings defined in constants.py, or an explicit unknown-verdict handler already exists with a warning log

<!-- Wave 15 Fixes -->

## F15.1 [FIX] Fix questions.py sync_status sentinel for BL 2.0 block boundaries
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: FIXED
**Motivated by**: D15.1
**Fix**: In `bl/questions.py` line 225: change `text.find("\n## Q", block_start + 1)` to `text.find("\n## ", block_start + 1)`.
**Verdict threshold**:
- FIXED: sentinel changed to generic `"\n## "`; BL 2.0 block boundaries found correctly
- FIX_FAILED: Q-prefix sentinel remains

---

## F15.2 [FIX] Fix crucible.py BL 1.x patterns — domains_covered, ID regexes, Q-glob, and _KNOWN_AGENTS
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: FIXED
**Motivated by**: D15.2 + D15.3 + A15.1
**Fix**: In `bl/crucible.py`:
(1) Lines 245-260: Replace `domain_keywords` D1-D6 dict with prefix-detection via `re.findall(r'^## ([A-Z])\d+\.\d+', wave1_text, re.MULTILINE)`; score = `len(unique_prefixes) / 5.0`
(2) Line 300: Change `r'Q\d+\.\d+'` to `r'\b[A-Z]\d+\.\d+'`
(3) Line 328: Change `findings_dir.glob('Q*.md')` to `(f for f in findings_dir.glob('*.md') if f.name != 'synthesis.md')`
(4) Lines 31-36: Add `"diagnose-analyst"`, `"fix-implementer"`, `"compliance-auditor"`, `"design-reviewer"` to `_KNOWN_AGENTS`
**Verdict threshold**:
- FIXED: all four changes applied; BL 2.0 agents visible to Crucible
- FIX_FAILED: any change missing

---

## V15.1 [VALIDATE] questions.py and crucible.py fixes correct after F15.1-F15.2
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: COMPLIANT
**Motivated by**: F15.1 + F15.2
**Hypothesis**: After F15.1, sync_status uses generic `"\n## "` sentinel. After F15.2, crucible.py uses BL 2.0-aware patterns and includes all operational agents.
**Verdict threshold**:
- COMPLIANT: all fixes verified; no regressions
- NON_COMPLIANT: any check fails

<!-- Wave 16 -->

---

## D16.1 [DIAGNOSE] healloop.py exhausted-loop leaves results.tsv with stale FAILURE verdict — final state is never written back when max cycles expire
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Motivated by**: healloop.py deep audit — Wave 16 hypothesis generation
**Hypothesis**: `run_heal_loop()` in `bl/healloop.py` updates `results.tsv` for intermediate heal findings (lines 228-233 and 284-286) and writes a FIXED row for the original question only on the FIXED path (lines 296-300). On the exhausted path — when the for-loop in `range(1, max_cycles + 1)` exits without returning — no `update_results_tsv()` call is made for the original `original_qid`. The original question row therefore permanently retains the pre-heal verdict (FAILURE or DIAGNOSIS_COMPLETE) in results.tsv, even though the heal loop appended an EXHAUSTED note to the finding file and ran multiple additional diagnose/fix sub-cycles. The synthesizer, crucible, and agent_db all treat results.tsv as the authoritative verdict store — they will read the original FAILURE and score the question as a clean failure, potentially triggering redundant followup questions and incorrect agent performance penalties.
**Test**: Read `bl/healloop.py` lines 288-343. Trace the code path when `fix_verdict != "FIXED"` and the loop exhausts all cycles. Confirm `update_results_tsv(original_qid, ...)` is never called after the for-loop ends. Read `bl/campaign.py` lines 129-140 — confirm the caller only propagates the `healed_result` dict but does not re-call `update_results_tsv` for the original `qid` after `run_heal_loop` returns with an exhausted result. Confirm that `findings.py`'s `update_results_tsv()` is the sole mechanism for writing verdict state to results.tsv.
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: the exhausted-loop path calls no `update_results_tsv` for `original_qid`; results.tsv retains the pre-heal FAILURE verdict; the campaign.py caller does not compensate; fix requires calling `update_results_tsv(original_qid, "HEAL_EXHAUSTED", ...)` after the loop exits without FIXED, and adding `"HEAL_EXHAUSTED"` to the appropriate frozenset in agent_db.py
- HEALTHY: `update_results_tsv` is called for `original_qid` on the exhausted path, or the campaign.py caller compensates

---

## D16.2 [DIAGNOSE] campaign.py peer-reviewer spawned unconditionally for code_audit questions — produces vacuous verdicts that inject spurious re-exam questions
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Motivated by**: campaign.py deep audit — Wave 16 hypothesis generation
**Hypothesis**: `run_campaign()` in `bl/campaign.py` calls `_spawn_agent_background("peer-reviewer", ...)` at lines 593-601 after every question with no guard on `question["mode"]`. The peer-reviewer prompt instructs it to "re-run the original test for {question['id']}" and append a Peer Review section with verdict CONFIRMED, CONCERNS, or OVERRIDE. For `code_audit` mode questions (all BL 2.0 diagnose, fix, audit, validate questions), there is no runnable test command — the "test" field contains prose instructions such as "Read bl/crucible.py lines 31-36 and confirm...". The peer-reviewer will be unable to find or execute a test and will likely emit CONCERNS or OVERRIDE as a safe default. Any OVERRIDE verdict causes `_inject_override_questions()` (lines 391-437) to append a `{qid}.R` re-exam block to questions.md with status PENDING. This means every code_audit question that the peer-reviewer cannot verify produces a spurious re-exam question, growing the question bank with items that cannot be resolved by re-running a non-existent test command.
**Test**: Read `bl/campaign.py` lines 579-601. Confirm `_spawn_agent_background("peer-reviewer", ...)` is inside the for-loop over `pending` with no `if question["mode"] != "code_audit"` guard. Read `_inject_override_questions()` lines 391-437 — confirm it scans ALL finding files for the OVERRIDE pattern regardless of mode. Inspect the peer-reviewer context string at lines 596-601 — confirm "re-run the original test" is present with no mode-conditional branch. Read the peer-reviewer agent file at `{agents_dir}/peer-reviewer.md` if it exists — confirm whether it contains any special handling for code_audit questions.
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: peer-reviewer is spawned for all modes without a guard; the peer-reviewer prompt lacks code_audit awareness; OVERRIDE verdicts from code_audit questions feed `_inject_override_questions()`; fix requires either (a) guarding `_spawn_agent_background("peer-reviewer", ...)` with `if question["mode"] not in ("code_audit",)` or (b) injecting `question_mode` into the peer-reviewer context so it skips the test re-run for non-executable question types
- HEALTHY: the peer-reviewer prompt already handles code_audit mode gracefully without emitting OVERRIDE, or the spawn call is already guarded by mode

---

## D16.3 [DIAGNOSE] runners/agent.py _parse_text_output() has no fallback for BL 2.0 agents — plain-text output from any agent not in the BL 1.x name list returns empty dict and forces INCONCLUSIVE
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Motivated by**: runners/agent.py audit — Wave 16 hypothesis generation
**Hypothesis**: `_parse_text_output()` in `bl/runners/agent.py` lines 138-198 dispatches on `agent_name` with `if/elif` branches for `security-hardener`, `test-writer`, `type-strictener`, and `perf-optimizer`. There is no `else` clause. For any agent name outside these four — including all BL 2.0 agents (`diagnose-analyst`, `fix-implementer`, `compliance-auditor`, `design-reviewer`) — the function returns an empty dict `{}`. This empty dict is passed to `_verdict_from_agent_output()`, which enters the `else` branch (line 122), reads `output.get("verdict", "")` from the empty dict, gets `""`, which is not in `_ALL_VERDICTS`, falls through the legacy heuristic check (`changes_committed` also missing), and returns `"INCONCLUSIVE"`. The consequence: any BL 2.0 agent that emits plain text instead of a JSON block — whether due to a prompt compliance failure, a claude CLI version difference, or a transient formatting issue — will always produce INCONCLUSIVE regardless of what verdict text appears in the plain-text output. A BL 1.x agent in the same situation would at least have its specific heuristic metrics extracted, giving a non-INCONCLUSIVE result.
**Test**: Read `bl/runners/agent.py` lines 138-198. Confirm `_parse_text_output()` has no `else` clause and returns `out` (which equals `{}`) for any unrecognized agent name. Trace `run_agent()` lines 398-401: confirm `_parse_text_output(agent_name, agent_text)` is called when `not agent_output and agent_text`, meaning the JSON block extraction at line 391-396 failed. Trace `_verdict_from_agent_output("diagnose-analyst", {})` through the `else` branch — confirm it returns `"INCONCLUSIVE"`. Confirm that a plain-text response containing the literal string `"verdict: DIAGNOSIS_COMPLETE"` from a diagnose-analyst would produce INCONCLUSIVE rather than DIAGNOSIS_COMPLETE via the text-output fallback path.
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: `_parse_text_output()` has no `else` clause; BL 2.0 agent plain-text output returns `{}`; `_verdict_from_agent_output` returns INCONCLUSIVE for all BL 2.0 agents on the text-fallback path; fix requires adding an `else` clause to `_parse_text_output()` that searches for `verdict:\s*(\w+)` and `summary:\s*(.+)` in the plain text as a universal BL 2.0 fallback
- HEALTHY: an `else` clause already extracts `verdict` and `summary` from plain text, or the text-fallback path is unreachable for BL 2.0 agents

---

## V16.1 [VALIDATE] Minimum viable scorer design for the four new BL 2.0 agents in crucible.py _SCORERS — validate architecture is correct before implementation
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: COMPLIANT
**Motivated by**: V15.1 informational gap — _SCORERS has no rubric functions for BL 2.0 agents
**Hypothesis**: After F15.2, `_KNOWN_AGENTS` includes the four BL 2.0 operational agents but `_SCORERS` (lines 378-383) maps only the four BL 1.x agents to scorer functions. A minimum viable scorer for each BL 2.0 agent should evaluate quality from existing finding files without subprocess calls: (1) `_score_diagnose_analyst` — DIAGNOSIS_COMPLETE rate from results.tsv, fix-specification completeness (4 required fields: target file, target location, concrete edit, verification command) detected via regex in finding markdown; (2) `_score_fix_implementer` — FIXED rate, FIX_FAILED rate, presence of a verification command output block in the finding; (3) `_score_compliance_auditor` — NON_COMPLIANT/COMPLIANT/PARTIAL distribution, whether NON_COMPLIANT findings include a Fix Specification section; (4) `_score_design_reviewer` — COMPLIANT/NON_COMPLIANT distribution, whether findings reference specific line numbers. All scorers must follow the static-file pattern of `_score_synthesizer()`: read files from `findings/`, extract text metrics, return `AgentScore(name, score, checks_raw, notes)`. Validate that this design is compatible with the existing `run_all_benchmarks()` loop and `AgentScore` dataclass with no structural changes required.
**Test**: Read `bl/crucible.py` lines 370-440. Confirm `_SCORERS` is a plain dict mapping agent name strings to scorer callables. Confirm `run_all_benchmarks()` iterates `_KNOWN_AGENTS`, looks up each in `_SCORERS`, and calls the scorer — no hardwired logic beyond the dict lookup. Confirm `AgentScore` has fields sufficient to express: a float score (0.0-1.0), a dict of named check results (checks_raw), and a notes string. Read `_score_synthesizer()` as the canonical static-file scorer pattern — confirm it makes no subprocess calls, reads only from `findings/` and the project root, and returns `AgentScore`. Confirm that adding `"diagnose-analyst": _score_diagnose_analyst` to `_SCORERS` is the only change required to make the new scorer callable from `run_all_benchmarks()`.
**Verdict threshold**:
- COMPLIANT: `_SCORERS` is a plain dict requiring only a new key-value entry; `AgentScore` fields cover rate, completeness, and notes; the `_score_synthesizer()` static-file pattern is directly reusable; `run_all_benchmarks()` requires no structural changes; a concrete scorer stub for `diagnose-analyst` reading DIAGNOSIS_COMPLETE verdicts from `findings/*.md` is architecturally sound
- NON_COMPLIANT: `run_all_benchmarks()` has hardwired logic beyond dict lookup that blocks new scorer addition, or `AgentScore` is missing a field needed for BL 2.0 scorer output; document exactly what structural change is required before implementation

---

## A16.1 [AUDIT] campaign.py run_campaign() pending-list refresh inside the loop is dead code for execution — injected questions are silently skipped in the current run
**Mode**: code_audit
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: NON_COMPLIANT
**Motivated by**: campaign.py deep audit — Wave 16 hypothesis generation
**Hypothesis**: `run_campaign()` in `bl/campaign.py` lines 563-601 iterates `for i, question in enumerate(pending, 1)` where `pending` is constructed before the loop. Inside the loop at lines 582-584, when `questions_done > 0`, the code re-parses questions.md and rebinds the local name `pending`: `pending = [q for q in refreshed if q["status"] == "PENDING"]`. This rebind does not affect the `enumerate` iterator already in progress — `question` continues to be drawn from the original pre-loop list. The refreshed `pending` is only used for `len(pending)` on line 587 (the progress display denominator). Consequently: (1) questions injected mid-run by `generate_followup()` or `_inject_override_questions()` are never executed in the current invocation; (2) the progress display `[{i}/{len(pending)}]` shows a stale or inflated denominator after any injection; (3) the refresh on lines 582-584 creates a false impression that the campaign dynamically picks up new questions, when in fact it does not. This is likely a BL 1.x artifact — the refresh was originally meaningful when the loop could receive external question additions — but in BL 2.0 it is misleading dead code for the execution path.
**Test**: Read `bl/campaign.py` lines 563-601. Confirm `enumerate(pending, 1)` creates an iterator over the pre-loop `pending` list reference. Confirm the rebind `pending = [...]` inside the loop does not alter this iterator. Confirm `question` in the loop body always comes from the original list. Determine whether any question injected by `generate_followup()` (line 109) or `_inject_override_questions()` (called in `check_sentinels()` line 580) during a run is ever visited by the for-loop iterator in the same invocation. Document whether the discrepancy between the displayed denominator and actual remaining work is visible to the operator.
**Verdict threshold**:
- NON_COMPLIANT: `enumerate` iterator is bound to original `pending` before the refresh; refreshed `pending` is used only for display; injected questions are not executed in the current run; the progress display denominator diverges after injection; the refresh is misleading dead code for the execution path — document the exact behavior and whether the non-execution of injected questions is intentional campaign design or an oversight
- COMPLIANT: the refresh is used correctly and injected questions are processed within the same run, or the non-execution is explicitly documented as intentional


<!-- Wave 16 follow-ups from D16.1 and D16.2 -->

---

## D16.1.F1 [DIAGNOSE] agent_db.py terminal-verdict frozensets missing HEAL_EXHAUSTED — exhausted heal loops re-trigger on next campaign run
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: HEALTHY
**Motivated by**: D16.1 follow-up — HEAL_EXHAUSTED verdict must be in terminal frozensets to prevent re-queueing
**Hypothesis**: `agent_db.py` contains frozensets of terminal verdicts that determine whether a question is re-queued (e.g., `_TERMINAL_VERDICTS` or similar). Because `HEAL_EXHAUSTED` is a new verdict not currently in any frozenset, a question with `HEAL_EXHAUSTED` status in results.tsv will be treated as non-terminal and re-added to the pending list on the next campaign run, re-triggering the heal loop indefinitely.
**Test**: Read `bl/agent_db.py` — identify all frozensets of terminal or parked verdicts. Confirm whether `HEAL_EXHAUSTED` is present or absent. Read `bl/questions.py _PARKED_STATUSES` — confirm whether `HEAL_EXHAUSTED` is present. Read `bl/findings.py _PRESERVE_AS_IS` — confirm presence/absence.
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: `HEAL_EXHAUSTED` is absent from at least one frozenset that would cause re-queueing; fix requires adding it to `_PARKED_STATUSES`, `_PRESERVE_AS_IS`, and the agent_db terminal frozenset
- HEALTHY: `HEAL_EXHAUSTED` is already present in all relevant frozensets, or the verdict string is already handled by a wildcard/prefix match

---

## D16.2.F1 [DIAGNOSE] _inject_override_questions() has no mode filter — re-exam questions injected for code_audit findings have prose-only test commands that cannot be resolved
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: DIAGNOSIS_COMPLETE
**Motivated by**: D16.2 follow-up — secondary injection path via _inject_override_questions also needs a mode filter
**Hypothesis**: Even after guarding the peer-reviewer spawn in `run_campaign()`, the `_inject_override_questions()` function at lines 398-437 has no mode filter on the findings it scans. If a code_audit finding somehow acquires an OVERRIDE Peer Review section (e.g., from a prior unguarded run), `_inject_override_questions()` will inject a `.R` re-exam question with `**Mode**: agent` and a prose test command. This re-exam question will be picked up by the campaign and routed to the agent runner, which will fail because the test command is not executable. A secondary fix is needed in `_inject_override_questions()` to skip findings from code_audit questions.
**Test**: Read `bl/campaign.py` `_inject_override_questions()` lines 385-437. Confirm no mode filter exists on `finding_file` before generating the `reexam_block`. Check whether the injected `reexam_block` hard-codes `**Mode**: agent` or inherits the original question's mode. Confirm that a `.R` re-exam question with `**Mode**: agent` and a prose test command would be routed to `run_agent()` and would fail silently.
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: `_inject_override_questions()` has no mode filter; injected re-exam questions hard-code `mode: agent`; a code_audit-derived re-exam would fail in the agent runner; fix requires reading the original question's mode from questions.md and either skipping code_audit OVERRIDE findings or injecting with the correct mode
- HEALTHY: `_inject_override_questions()` already reads the original question mode and handles code_audit correctly, or the function is unreachable for code_audit findings

---

## Wave-mid

**Generated from findings**: D16.1, D16.2, D16.3, A16.1
**Mode transitions applied**: D16.1 DIAGNOSIS_COMPLETE → F-mid.1 Fix; D16.2 DIAGNOSIS_COMPLETE → F-mid.2 Fix; D16.3 DIAGNOSIS_COMPLETE → F-mid.3 Fix + D-mid.4 narrowing Diagnose; A16.1 NON_COMPLIANT → F-mid.5 Fix

---

### F-mid.1: Implement the fix specified in D16.1 — write HEAL_EXHAUSTED to results.tsv on exhausted-loop exit in healloop.py, and add HEAL_EXHAUSTED to all downstream frozensets

**Status**: FIXED
**Operational Mode**: fix
**Mode**: code_audit
**Agent**: fix-implementer
**Priority**: HIGH
**Motivated by**: D16.1 DIAGNOSIS_COMPLETE — the exhausted-loop path in `run_heal_loop()` never calls `update_results_tsv(original_qid, ...)`, leaving the original question with a stale pre-heal verdict in results.tsv; synthesizer, crucible, and agent_db all misread this as a clean FAILURE; additionally D16.1.F1 (PENDING) already confirmed that `HEAL_EXHAUSTED` is absent from every downstream frozenset
**Hypothesis**: Adding `update_results_tsv(original_qid, "HEAL_EXHAUSTED", f"Self-healing exhausted {last_cycle} cycle(s) — human intervention required.", None)` after `_append_heal_note` on the exhausted path, and adding `"HEAL_EXHAUSTED"` to `_PARKED_STATUSES` in questions.py, `_PRESERVE_AS_IS` in findings.py, and the appropriate terminal-verdict frozenset(s) in agent_db.py, will close the stale-verdict loop and prevent indefinite re-queueing
**Method**: Three-file edit: (1) `bl/healloop.py` lines 332-343 — add `update_results_tsv(original_qid, "HEAL_EXHAUSTED", ...)` after `_append_heal_note`; (2) `bl/questions.py` `_PARKED_STATUSES` — add `"HEAL_EXHAUSTED"`; (3) `bl/findings.py` `_PRESERVE_AS_IS` — add `"HEAL_EXHAUSTED"`; (4) `bl/agent_db.py` terminal/parked frozenset — add `"HEAL_EXHAUSTED"` (location confirmed by D16.1.F1 diagnose)
**Success criterion**: `grep -n "HEAL_EXHAUSTED" bl/healloop.py bl/questions.py bl/findings.py bl/agent_db.py` — each file shows at least one reference; `update_results_tsv` call appears on the exhausted path in healloop.py before `return current_result`

---

### F-mid.2: Implement the fix specified in D16.2 — add mode guard to peer-reviewer spawn in campaign.py run_campaign() to skip code_audit questions

**Status**: FIXED
**Operational Mode**: fix
**Mode**: code_audit
**Agent**: fix-implementer
**Priority**: HIGH
**Motivated by**: D16.2 DIAGNOSIS_COMPLETE — `_spawn_agent_background("peer-reviewer", ...)` at campaign.py lines 593-601 fires unconditionally for all question modes including `code_audit`; peer-reviewer cannot execute prose test commands and emits CONCERNS/OVERRIDE, causing `_inject_override_questions()` to inject unresolvable `.R` re-exam questions that grow the question bank indefinitely
**Hypothesis**: Wrapping the `_spawn_agent_background("peer-reviewer", ...)` call with `if question.get("mode") not in ("code_audit",):` will prevent spurious OVERRIDE verdicts and stop the `.R` question injection cascade for all current and future code_audit questions
**Method**: Edit `bl/campaign.py` lines 593-601 — add `if question.get("mode") not in ("code_audit",):` guard before `_spawn_agent_background("peer-reviewer", ...)`. Verify the guard does not suppress peer-reviewer for `mode == "agent"` questions (BL 1.x behavioral/simulation questions), which do have executable test commands
**Success criterion**: `grep -n "peer-reviewer\|code_audit" bl/campaign.py` — confirms the spawn is inside `if question.get("mode") not in ("code_audit",)`; no existing `.R` re-exam questions in questions.md that reference code_audit-sourced prose test commands

---

### F-mid.3: Implement the fix specified in D16.3 — add else-clause to _parse_text_output() in runners/agent.py for universal BL 2.0 plain-text verdict extraction

**Status**: FIXED
**Operational Mode**: fix
**Mode**: code_audit
**Agent**: fix-implementer
**Priority**: HIGH
**Motivated by**: D16.3 DIAGNOSIS_COMPLETE — `_parse_text_output()` has no `else` clause; all BL 2.0 agents (diagnose-analyst, fix-implementer, compliance-auditor, design-reviewer) return `{}` on the text-fallback path, causing `_verdict_from_agent_output()` to always return INCONCLUSIVE regardless of what verdict text appears in the plain-text output; any transient JSON formatting failure silently discards a correct DIAGNOSIS_COMPLETE
**Hypothesis**: Adding an `else` clause after the `elif agent_name == "perf-optimizer":` block that extracts `verdict` and `summary` via `re.search(r"^verdict:\s*(\w+)", text, re.IGNORECASE | re.MULTILINE)` and `re.search(r"^summary:\s*(.+)", text, re.IGNORECASE | re.MULTILINE)` will recover correct verdicts from plain-text BL 2.0 agent output on the fallback path
**Method**: Edit `bl/runners/agent.py` lines 188-198 — insert the `else` clause as specified in D16.3 Fix Specification before `return out`
**Success criterion**: `grep -n "else:" bl/runners/agent.py | grep -A5 "perf-optimizer"` — confirms an `else` clause follows the `perf-optimizer` branch and contains `re.search(r"^verdict:"` extraction logic

---

### D-mid.4: Does _summary_from_agent_output() have the same BL 2.0 gap as _parse_text_output() — no else-clause for non-BL-1.x agents, producing generic fallback summaries for all BL 2.0 agents on the text-fallback path?

**Status**: FIXED
**Operational Mode**: diagnose
**Mode**: code_audit
**Agent**: diagnose-analyst
**Priority**: MEDIUM
**Motivated by**: D16.3 DIAGNOSIS_COMPLETE — the finding explicitly flags `_summary_from_agent_output()` as a likely companion gap: "Does `_summary_from_agent_output()` also have the same BL 2.0 gap — no `else` clause for non-BL-1.x agents — resulting in generic 'no structured output produced' summaries for all BL 2.0 agents on the text-fallback path?"
**Hypothesis**: `_summary_from_agent_output()` in `bl/runners/agent.py` dispatches on `agent_name` with `if/elif` branches for the same four BL 1.x agents; for any other agent name the function falls through to a generic summary string ("no structured output produced" or similar); all BL 2.0 agent summaries on the text-fallback path are therefore generic, making the session-context.md and findings corpus less informative than they should be
**Method**: Read `bl/runners/agent.py` — locate `_summary_from_agent_output()`. Verify: (1) does it dispatch on `agent_name` with `if/elif` branches? (2) is there an `else` clause that extracts `summary:` from plain text? (3) what string is returned for `"diagnose-analyst"` when output is `{}`?
**Success criterion**: Either HEALTHY (else-clause already extracts summary from plain text) or DIAGNOSIS_COMPLETE with a Fix Specification for adding the same `re.search(r"^summary:")` extraction as F-mid.3 adds to `_parse_text_output()`

---

### F-mid.5: Implement the fix specified in A16.1 — document the intentional non-execution of mid-run injected questions and remove or clearly annotate the misleading pending-list refresh in campaign.py

**Status**: FIXED
**Operational Mode**: fix
**Mode**: code_audit
**Agent**: fix-implementer
**Priority**: LOW
**Motivated by**: A16.1 NON_COMPLIANT — `run_campaign()` rebinds `pending` inside the `enumerate` loop (lines 582-584) but the rebind has no effect on the active iterator; injected questions are silently skipped in the current run; the progress display denominator diverges after injection; the refresh code creates a false impression of dynamic pickup that does not exist
**Hypothesis**: The non-execution of mid-run injected questions is either (a) intentional design — next-run pickup is acceptable — or (b) a latent bug. Either way, a code comment at lines 582-584 explaining "this rebind affects only the progress display denominator, not the active iterator; injected questions execute on the next campaign invocation" eliminates the misleading appearance. If the intent was dynamic pickup, a structural fix (rebuilding the iterator, or switching to a while-loop with a deque) is needed instead.
**Method**: (1) Determine intent by reading surrounding comments and git history for lines 582-584. (2) If intentional: add a comment `# NOTE: rebind affects len() display only — enumerate iterator is already bound to original pending list; injected questions run next invocation`. (3) If unintentional: replace `enumerate(pending, 1)` with a deque-based while loop that re-checks the question bank after each iteration.
**Success criterion**: `grep -n "rebind\|next invocation\|display only" bl/campaign.py` — confirms an explanatory comment exists at the refresh site, OR the loop structure is changed to actually process injected questions within the same run

---

## D16.2.F1.F1 [AUDIT] Existing .R re-exam questions in questions.md with prose-only test fields from code_audit parents — identify and remove or convert
**Mode**: code_audit
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: COMPLIANT
**Motivated by**: D16.2.F1 follow-up — unresolvable .R re-exam questions may already exist in questions.md
**Hypothesis**: If the peer-reviewer was spawned for code_audit questions before D16.2 is fixed, some `.R` re-exam questions may already have been injected into questions.md. These questions have `**Mode**: agent` and `**Test**: Re-run the original test command from {qid}` where the test command is prose. They cannot be resolved. Audit questions.md for any `.R` questions where the referenced original question has `**Mode**: code_audit`, and classify them for removal or conversion.
**Test**: Search questions.md for all `## \w+\.R ` sections. For each, look up the parent question ID (strip `.R`) in questions.md. Check if the parent has `**Mode**: code_audit`. If so, flag the `.R` question as unresolvable.
**Verdict threshold**:
- NON_COMPLIANT: at least one `.R` re-exam question exists with a code_audit parent — document which ones and recommend removal or conversion to code_audit mode
- COMPLIANT: no `.R` questions exist, or all existing `.R` questions have executable test commands from non-code_audit parents

<!-- Wave 17 -->

---

## Wave 17

**Generated from findings**: F-mid.1, F-mid.2, F-mid.3, D-mid.4, F-mid.5, D16.2.F1.fix, D16.2.F1.F1, D16.1.F1
**Mode transitions applied**: 5x FIXED (F-mid.1, F-mid.2, F-mid.3, D-mid.4, F-mid.5) → V17.1 consolidated validate; D16.2 DIAGNOSIS_COMPLETE follow-up → D17.1 diagnose (unconditional background-agent spawns); D16.3 DIAGNOSIS_COMPLETE → D17.2 diagnose (_ALL_VERDICTS completeness); V16.1 COMPLIANT (scorer design validated) → F17.1 fix (implement BL 2.0 Crucible scorers); D16.2.F1 FIXED → A17.1 audit (O(N) parse_questions inside per-finding loop)

---

## V17.1 [VALIDATE] Wave-mid fixes correct — HEAL_EXHAUSTED propagation, mode guards, and text-fallback extraction all verified with no regressions
**Mode**: code_audit
**Agent**: design-reviewer
**Operational Mode**: validate
**Status**: COMPLIANT
**Motivated by**: F-mid.1 (FIXED) + F-mid.2 (FIXED) + F-mid.3 (FIXED) + D-mid.4 (FIXED) + F-mid.5 (FIXED) — five fixes applied across bl/healloop.py, bl/questions.py, bl/findings.py, bl/agent_db.py, bl/runners/agent.py, and bl/campaign.py
**Hypothesis**: After F-mid.1: update_results_tsv(original_qid, "HEAL_EXHAUSTED", ...) is present in healloop.py exhausted path and "HEAL_EXHAUSTED" appears in all four downstream frozensets (_PARKED_STATUSES, _TERMINAL_VERDICTS, _PRESERVE_AS_IS, agent_db._PARTIAL_VERDICTS). After F-mid.2: peer-reviewer spawn is inside `if question.get("mode") not in ("code_audit",):`. After F-mid.3 and D-mid.4: _parse_text_output() has an else clause with re.search(r"^verdict:") extraction, and _summary_from_agent_output() has an early `if output.get("summary"): return str(output["summary"])` check. After F-mid.5: an explanatory comment at the pending-list refresh site in run_campaign(). No BL 1.x agent regressions introduced.
**Test**: (1) `grep -n "HEAL_EXHAUSTED" bl/healloop.py bl/questions.py bl/findings.py bl/agent_db.py` — confirm presence in all four files including update_results_tsv call in healloop.py before return current_result. (2) `grep -n "code_audit" bl/campaign.py` — confirm peer-reviewer guard uses `not in ("code_audit",)`. (3) `grep -n "else:" bl/runners/agent.py` — confirm else-clause after perf-optimizer branch contains re.search for verdict extraction. (4) `grep -n "output.get" bl/runners/agent.py` — confirm early summary check in _summary_from_agent_output(). (5) `grep -n "rebind\|next invocation\|display only\|pre-loop snapshot" bl/campaign.py` — confirm explanatory comment at refresh site.
**Verdict threshold**:
- COMPLIANT: all five checks pass; the four BL 1.x agent-name branches in _parse_text_output() are unmodified (no regressions for security-hardener, test-writer, type-strictener, perf-optimizer)
- NON_COMPLIANT: any check fails — document which fix is incomplete or introduced a regression

---

## D17.1 [DIAGNOSE] campaign.py background-agent spawns other than peer-reviewer are mode-unconditional — forge-check and other spawns may misfire for code_audit questions
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: HEALTHY
**Motivated by**: D16.2 (DIAGNOSIS_COMPLETE) — suggested follow-up: "Are there other background agent spawns in run_campaign() that are also mode-unconditional and should be guarded similarly (e.g., forge-check, hypothesis-generator)?"
**Hypothesis**: run_campaign() in bl/campaign.py contains multiple _spawn_agent_background(...) call sites. The D16.2 fix (F-mid.2) guarded only the peer-reviewer spawn. Other spawns — specifically forge-check and/or hypothesis-generator, if they exist inside the per-question loop — may also fire unconditionally for all question modes including code_audit. A forge-check agent attempting to re-run a prose code-read test command would fail silently or produce a spurious verdict. A hypothesis-generator spawned per-question rather than per-wave would produce redundant follow-up waves that collide on wave numbering.
**Test**: Read bl/campaign.py in full — locate all _spawn_agent_background(...) call sites inside run_campaign(). For each: (1) identify the agent name, (2) check whether a mode guard of the form `if question.get("mode") not in (...)` wraps the call, (3) determine whether the agent behaviour is mode-sensitive (would it fail or produce incorrect output for code_audit questions with prose-only test fields). List all unconditional spawns that are mode-sensitive.
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: at least one background-agent spawn other than peer-reviewer is unconditional AND mode-sensitive for code_audit questions; fix requires adding mode guards to those spawns using the same pattern as F-mid.2
- HEALTHY: all remaining background-agent spawns are either already guarded by mode or are mode-insensitive (their behavior is correct for both agent and code_audit question types regardless of mode)

---

## D17.2 [DIAGNOSE] _ALL_VERDICTS in runners/agent.py may be missing BL 2.0 verdict strings — F-mid.3 regex extraction succeeds but extracted verdict is discarded if not in _ALL_VERDICTS
**Mode**: code_audit
**Agent**: diagnose-analyst
**Operational Mode**: diagnose
**Status**: HEALTHY
**Motivated by**: D16.3 (DIAGNOSIS_COMPLETE) + F-mid.3 (FIXED) — F-mid.3 adds re.search(r"^verdict:\s*(\w+)") extraction to _parse_text_output(), storing the result in out["verdict"]. In _verdict_from_agent_output() the else-branch reads output.get("verdict", "").upper() and checks `if self_verdict_early in _ALL_VERDICTS`. If _ALL_VERDICTS does not contain DIAGNOSIS_COMPLETE or other BL 2.0 verdicts, the extracted verdict is silently discarded and the function returns INCONCLUSIVE — nullifying the F-mid.3 fix entirely for those verdicts.
**Hypothesis**: _ALL_VERDICTS in bl/runners/agent.py was defined in the BL 1.x era and may contain only the original four verdicts (HEALTHY, WARNING, FAILURE, INCONCLUSIVE) or a partial expansion. If BL 2.0 verdicts (DIAGNOSIS_COMPLETE, FIX_FAILED, FIXED, NON_COMPLIANT, COMPLIANT, BLOCKED, PROMISING, CALIBRATED, REGRESSION, ALERT, DEGRADED, IMMINENT, PROBABLE) are absent, the F-mid.3 text-fallback path is a no-op for those verdicts: regex extraction succeeds, but the _ALL_VERDICTS guard immediately discards the result.
**Test**: `grep -n "_ALL_VERDICTS" bl/runners/agent.py` — locate the definition and list all verdict strings it contains. Compare against the full verdict list in constants.py. Specifically confirm whether DIAGNOSIS_COMPLETE is present. Trace _verdict_from_agent_output("diagnose-analyst", {"verdict": "DIAGNOSIS_COMPLETE", "summary": "..."}) through the else-branch — confirm whether "DIAGNOSIS_COMPLETE" in _ALL_VERDICTS evaluates to True or False.
**Verdict threshold**:
- DIAGNOSIS_COMPLETE: _ALL_VERDICTS is missing one or more BL 2.0 verdict strings; DIAGNOSIS_COMPLETE (or any other BL 2.0 verdict) absent from _ALL_VERDICTS causes F-mid.3 extraction to be silently discarded; fix requires adding all BL 2.0 verdicts to _ALL_VERDICTS or replacing the guard with a reference to the canonical set in constants.py
- HEALTHY: _ALL_VERDICTS already contains all BL 2.0 verdict strings including DIAGNOSIS_COMPLETE; F-mid.3 extraction is fully functional end-to-end

---

## F17.1 [FIX] Implement BL 2.0 Crucible scorer stubs for diagnose-analyst, fix-implementer, compliance-auditor, and design-reviewer
**Mode**: code_audit
**Agent**: fix-implementer
**Operational Mode**: fix
**Status**: FIXED
**Motivated by**: V16.1 (COMPLIANT) — design validated: _SCORERS is a plain dict; AgentScore fields cover rate + completeness + notes; _score_synthesizer() static-file pattern is directly reusable; adding "diagnose-analyst": _score_diagnose_analyst to _SCORERS is the only structural change required. The four BL 2.0 agents were added to _KNOWN_AGENTS by F15.2 but have no scorer entries in _SCORERS — run_all_benchmarks() will KeyError or return 0.0 for them.
**Hypothesis**: Adding four scorer functions to bl/crucible.py and registering them in _SCORERS will make the BL 2.0 operational agents visible to Crucible benchmarking. Rubric design per V16.1: (1) _score_diagnose_analyst — DIAGNOSIS_COMPLETE rate from results.tsv for diagnose-analyst runs; fix-spec completeness fraction (findings containing all four fields: Target file, Target location, Concrete edit, Verification command). (2) _score_fix_implementer — FIXED rate, FIX_FAILED rate, presence of a Verification or Fix Applied section in each FIXED finding. (3) _score_compliance_auditor — NON_COMPLIANT + COMPLIANT rate (fraction answered definitively vs INCONCLUSIVE), NON_COMPLIANT findings that include a Fix Specification section. (4) _score_design_reviewer — COMPLIANT rate, presence of specific line-number references in findings. All four follow the _score_synthesizer() static-file pattern: read findings/*.md, extract text metrics, return AgentScore(name, score, checks_raw, notes).
**Test**: After fix: `python -c "from bl.crucible import run_all_benchmarks, CrucibleConfig; import pathlib; cfg = CrucibleConfig(pathlib.Path('.')); s = run_all_benchmarks(cfg); names = {a.name for a in s}; assert names >= {'diagnose-analyst','fix-implementer','compliance-auditor','design-reviewer','hypothesis-generator'}; print('PASS')"` — all four BL 2.0 agents return AgentScore without KeyError; BL 1.x scorers unaffected.
**Verdict threshold**:
- FIXED: all four scorer functions implemented; all four registered in _SCORERS; run_all_benchmarks() returns scores for all eight agents (4 BL 1.x + 4 BL 2.0) without raising KeyError; BL 1.x scorer outputs unchanged
- FIX_FAILED: any scorer raises an exception, returns wrong type, or _SCORERS registration is missing for any of the four agents

---

## A17.1 [AUDIT] D16.2.F1.fix calls parse_questions() inside per-finding loop — O(N) parse overhead per _inject_override_questions() invocation
**Mode**: code_audit
**Agent**: compliance-auditor
**Operational Mode**: audit
**Status**: NON_COMPLIANT
**Motivated by**: D16.2.F1 (DIAGNOSIS_COMPLETE) → D16.2.F1.fix (FIXED) — the fix calls get_question_by_id(parse_questions(), qid) inside the `for finding_file in sorted(cfg.findings_dir.glob("*.md")):` loop, re-parsing all of questions.md on every iteration
**Hypothesis**: The D16.2.F1 fix is functionally correct but introduces an O(N) parse overhead: parse_questions() reads and parses the entire questions.md file once per finding file in the loop. In a campaign with 50 finding files, _inject_override_questions() performs 50 full parses of questions.md per invocation. At BL 2.0 campaign scale (current: ~60 questions, ~50 findings, questions.md ~1800 lines), this is measurable. The fix is correct (question mode is set at creation and never modified, ruling out staleness risk), but parse_questions() should be hoisted above the loop and the cached result passed to get_question_by_id() inside it.
**Test**: Read bl/campaign.py _inject_override_questions() — confirm whether parse_questions() is called (a) once before the for-finding_file loop, or (b) inside the loop on each iteration. Count the number of parse_questions() calls that would occur for a campaign with 50 finding files under the current implementation. Confirm that question["mode"] is immutable (never modified after initial write) so hoisting introduces no staleness risk.
**Verdict threshold**:
- NON_COMPLIANT: parse_questions() is called inside the per-finding loop (once per finding, not hoisted); at 50 findings this performs 50 full parses of questions.md; fix requires hoisting `all_questions = parse_questions()` above the loop and passing it into get_question_by_id() on each iteration
- COMPLIANT: parse_questions() is already hoisted above the per-finding loop (called once per _inject_override_questions() invocation), or the per-call cost is negligible and the staleness risk is confirmed absent


<!-- Wave 18 -->

---

## Wave 18

**Generated from findings**: F17.1, A17.1, V17.1
**Mode transitions applied**: F17.1 FIXED -> V18.1 Validate (dc_rate scope correctness); F17.1 FIXED -> V18.2 Validate (fix_spec_completeness false-positive scan); A17.1 NON_COMPLIANT+in-session fix -> A18.1 Audit (hoist correctness confirmation); V17.1 COMPLIANT (HEAL_EXHAUSTED in frozensets) -> D18.1 Diagnose (HEAL_EXHAUSTED write-back to questions.md); F17.1 FIXED -> D18.2 Diagnose (FIX_FAILED scope — no agent-name filter)

---

### V18.1: Does _score_diagnose_analyst in crucible.py correctly scope dc_rate to diagnose-analyst rows, or does it count verdicts from all agents in results.tsv?

**Status**: NON_COMPLIANT → Fix applied (F19.1)
**Operational Mode**: validate
**Mode**: code_audit
**Agent**: design-reviewer
**Priority**: HIGH
**Motivated by**: F17.1 (FIXED) — dc_rate numerator counts rows where verdict is DIAGNOSIS_COMPLETE or HEALTHY; denominator counts rows where verdict is any of DIAGNOSIS_COMPLETE|HEALTHY|FAILURE|INCONCLUSIVE. results.tsv has no agent-name column (columns: question_id, verdict, failure_type, summary, timestamp), so both lists are unfiltered across all agents. HEALTHY verdicts from fix-implementer, compliance-auditor, and design-reviewer questions all enter the denominator and numerator, making dc_rate a campaign-wide health metric rather than a diagnose-analyst performance metric.
**Hypothesis**: _score_diagnose_analyst lines 385-393 in bl/crucible.py compute dc_rate without filtering results.tsv rows by question_id prefix or agent name. In the BL 2.0 campaign, diagnose-analyst ran on D-prefix questions; fix-implementer on F-prefix; compliance-auditor on A-prefix; design-reviewer on V-prefix. Any HEALTHY verdict on an F/A/V-prefix row contributes to both diag_rows and all_diag, skewing the score. The metric needs either a question_id prefix filter (keep only D-prefix rows) or an explicit acknowledgement in details that it measures campaign-wide health.
**Method**: Read bl/crucible.py lines 381-393. Confirm: (1) diag_rows and all_diag are built from all lines with no prefix filter. (2) Open projects/bl2/results.tsv — count rows with verdict HEALTHY split by question_id prefix (D vs F/A/V). (3) Recalculate dc_rate with and without prefix filtering to determine the magnitude of distortion.
**Success criterion**: DIAGNOSIS_COMPLETE with a Fix Specification adding a question_id prefix filter (e.g., keep only rows where question_id starts with D) if non-D-prefix rows materially distort dc_rate; COMPLIANT only if the details string is updated to explicitly state 'campaign-wide metric, not agent-specific' — the current label 'DIAGNOSIS_COMPLETE rate' is misleading if it counts other agents' verdicts.

---

### V18.2: Does _score_diagnose_analyst fix_spec_completeness include FIXED findings from fix-implementer that also contain 'Fix Specification' and all four spec_fields?

**Status**: NON_COMPLIANT → Fix applied (F19.2)
**Operational Mode**: validate
**Mode**: code_audit
**Agent**: design-reviewer
**Priority**: MEDIUM
**Motivated by**: F17.1 (FIXED) — the fix_spec_completeness scan at bl/crucible.py lines 402-414 includes any finding that contains 'DIAGNOSIS_COMPLETE' or 'Fix Specification' in its text. FIXED findings produced by fix-implementer (e.g., F17.1.md) contain a Fix Applied section with all four spec_fields ('Target file', 'Target location', 'Concrete edit', 'Verification command'), and the string 'Fix Specification' appears in A17.1.md (the source finding that motivated the fix). These findings will be scored as complete fix specs and included in spec_scores, crediting diagnose-analyst for fix-implementer work.
**Hypothesis**: F-prefix findings in projects/bl2/findings/ contain 'Fix Specification' (they describe the fix that was applied) and all four spec_fields. The inclusion guard 'DIAGNOSIS_COMPLETE' not in content AND 'Fix Specification' not in content is a substring match — it includes a finding if either string appears anywhere, including in headings like '## Fix Specification' inside a FIXED finding. Removing F-prefix findings from spec_scores would lower spec_completeness from its current value.
**Method**: Read bl/crucible.py lines 402-414. Then check: (1) Does F17.1.md contain the string 'Fix Specification'? Does it contain all four spec_fields? (2) Does A17.1.md (NON_COMPLIANT with a fix specification block) contain all four spec_fields? (3) Count how many non-D-prefix findings in projects/bl2/findings/ pass the inclusion guard and contribute to spec_scores. (4) Recalculate spec_completeness excluding those findings.
**Success criterion**: DIAGNOSIS_COMPLETE with a Fix Specification if non-D-prefix findings materially inflate spec_completeness; the correct guard is a match on '**Verdict**: DIAGNOSIS_COMPLETE' (exact status-line) rather than 'DIAGNOSIS_COMPLETE' anywhere in content. COMPLIANT if the guard already excludes F-prefix findings in practice.

---

### A18.1: Is the A17.1 parse_questions() hoist correctly applied — all_questions assigned before the loop and consumed by get_question_by_id() inside it, with no residual inner call?

**Status**: COMPLIANT
**Operational Mode**: audit
**Mode**: code_audit
**Agent**: compliance-auditor
**Priority**: HIGH
**Motivated by**: A17.1 (NON_COMPLIANT, fix applied in-session) — grep confirmed all_questions = (parse_questions()) at lines 396-398 above the loop and get_question_by_id(all_questions, qid) at line 414 inside it. However the parenthesized multi-line assignment form is unusual, and the fix was applied in-session without a standalone verification run. A residual parse_questions() call inside the loop body or an incorrect variable name would preserve the O(N) behavior.
**Hypothesis**: The hoist is syntactically correct (all_questions = (parse_questions()) is valid Python) but the audit must confirm: (1) parse_questions() is called exactly once in _inject_override_questions() — the hoisted call — and zero times inside the for-finding_file loop body. (2) The variable passed to get_question_by_id at line 414 is all_questions, not a new parse_questions() call. (3) No other call site within _inject_override_questions() re-invokes parse_questions() after the loop starts.
**Method**: Run: grep -n 'parse_questions' bl/campaign.py — list all call sites with line numbers. Identify which are inside _inject_override_questions() and which are in other functions. Confirm the only call inside _inject_override_questions() is at the pre-loop hoist site (lines 396-398). Then read lines 400-445 to confirm get_question_by_id uses all_questions.
**Success criterion**: COMPLIANT if parse_questions() appears exactly once in _inject_override_questions() (the pre-loop hoist) and all_questions is passed to get_question_by_id() inside the loop. NON_COMPLIANT if a second parse_questions() call remains inside the loop body, or if all_questions is assigned but not used.

---

### D18.1: Does update_question_status() write 'HEAL_EXHAUSTED' to questions.md, or does HEAL_EXHAUSTED fail the _TERMINAL_VERDICTS guard and leave the question at PENDING?

**Status**: HEALTHY
**Operational Mode**: diagnose
**Mode**: code_audit
**Agent**: diagnose-analyst
**Priority**: HIGH
**Motivated by**: V17.1 (COMPLIANT) — confirmed HEAL_EXHAUSTED is in _PARKED_STATUSES, _TERMINAL_VERDICTS inline tuple, _PRESERVE_AS_IS, and agent_db._PARTIAL_VERDICTS. However V17.1 verified frozenset membership only. The write-back path in update_question_status() populates done_ids[qid] only when verdict is in _TERMINAL_VERDICTS. questions.py has two distinct frozensets: _PARKED_STATUSES (lines 100-113) and the _TERMINAL_VERDICTS check at line 197. These are separate sets; membership in one does not guarantee membership in the other.
**Hypothesis**: F-mid.1 added HEAL_EXHAUSTED to the inner ternary tuple at line 214 (the preserve-raw-verdict list). If HEAL_EXHAUSTED is also present in the outer _TERMINAL_VERDICTS frozenset (lines 100-113), the full path produces done_ids[qid] = 'HEAL_EXHAUSTED' and update_question_status() writes '**Status**: HEAL_EXHAUSTED' to questions.md. If HEAL_EXHAUSTED is only in the inner ternary but absent from _TERMINAL_VERDICTS, the outer guard at line 197 blocks entry entirely — done_ids is never populated and the question stays PENDING indefinitely after heal exhaustion, causing the campaign loop to re-attempt it.
**Method**: Read bl/questions.py lines 95-240 in full. Confirm: (1) _TERMINAL_VERDICTS frozenset definition at lines 100-113 includes HEAL_EXHAUSTED. (2) Trace the path for verdict='HEAL_EXHAUSTED': outer guard at line 197 passes -> done_ids[qid] entered -> inner ternary at lines 209-216 assigns raw verdict -> update_question_status() writes '**Status**: HEAL_EXHAUSTED'. (3) If the path is broken, identify the exact guard that excludes HEAL_EXHAUSTED.
**Success criterion**: HEALTHY if HEAL_EXHAUSTED is in _TERMINAL_VERDICTS and the full write-back path produces '**Status**: HEAL_EXHAUSTED' in questions.md. DIAGNOSIS_COMPLETE if HEAL_EXHAUSTED is absent from _TERMINAL_VERDICTS — the question stays PENDING after heal exhaustion, making it invisible as exhausted and causing the campaign to re-attempt it.

---

### D18.2: Does _score_fix_implementer in crucible.py scope fix_rows to F-prefix questions only, or do verdicts from other agents inflate or deflate the FIXED/FIX_FAILED ratio?

**Status**: HEALTHY
**Operational Mode**: diagnose
**Mode**: code_audit
**Agent**: diagnose-analyst
**Priority**: MEDIUM
**Motivated by**: F17.1 (FIXED) — _score_fix_implementer computes fix_rows as all results.tsv rows matching verdict FIXED or FIX_FAILED, with no question_id prefix filter. This is the same root issue as V18.1 (no agent-name column in results.tsv) but applied to the fix-implementer scorer. If any non-F-prefix question produces a FIXED or FIX_FAILED verdict (e.g., via text-fallback extracting a stray string from a code block), that row enters fix_rows and skews the fixed_rate and fix_failed_rate metrics.
**Hypothesis**: In the current BL 2.0 campaign results.tsv, all FIXED and FIX_FAILED verdicts appear on F-prefix question IDs, so the scorer is functionally correct for this campaign. However the scorer has no structural guard — it is fragile to any campaign where FIXED appears on a non-fix question. The question is whether the distortion is active (affects the current 0.9573 score) or latent (zero distortion today, fragile tomorrow).
**Method**: Read bl/crucible.py lines 425-475. Confirm fix_rows filter is verdict-only. Open projects/bl2/results.tsv — list all rows where verdict is FIXED or FIX_FAILED and identify their question_id prefixes. Determine if any non-F-prefix row is present in fix_rows. If distortion is active, recalculate fixed_rate excluding non-F-prefix rows.
**Success criterion**: DIAGNOSIS_COMPLETE with a Fix Specification adding a question_id prefix filter if non-F-prefix rows exist in fix_rows; HEALTHY if all FIXED/FIX_FAILED rows are F-prefix and the current score is accurate — document the latent fragility in the finding regardless so a future campaign does not inherit a silent metric error.

---

## Wave 19 — Fix Implementation

**Generated from findings**: V18.1, V18.2
**Mode transitions applied**: V18.1 NON_COMPLIANT -> F19.1 Fix (dc_rate BL 2.0 scope); V18.2 NON_COMPLIANT -> F19.2 Fix (fix_spec_completeness exact-verdict guard)

---

### F19.1: Apply V18.1 fix — scope _score_diagnose_analyst dc_rate to BL 2.0 D-prefix rows only, excluding BL 1.x FAILURE rows from the denominator

**Status**: FIXED
**Operational Mode**: fix
**Mode**: code_audit
**Agent**: fix-implementer
**Priority**: HIGH
**Motivated by**: V18.1 (NON_COMPLIANT) — dc_rate denominator counts all FAILURE/INCONCLUSIVE rows including 22+ BL 1.x old-format rows. These inflate all_diag from ~23 to ~45, dragging dc_rate from ~0.85 to ~0.51. Fix: add _is_bl2_diag_row() helper filtering to new-format rows (col[0]=="N/A") with D-prefix question IDs.
**Fix Specification**:
- Target file: bl/crucible.py
- Target location: _score_diagnose_analyst() lines 381-403
- Concrete edit: Added nested _is_bl2_diag_row() that checks parts[0]=="N/A" and parts[1].startswith("D"); both diag_rows and all_diag filtered through it
- Verification command: run_all_benchmarks() — diagnose-analyst dc_rate should rise from ~0.51 to ~0.85+

---

### F19.2: Apply V18.2 fix — replace fix_spec_completeness guard with exact **Verdict**: DIAGNOSIS_COMPLETE match

**Status**: FIXED
**Operational Mode**: fix
**Mode**: code_audit
**Agent**: fix-implementer
**Priority**: MEDIUM
**Motivated by**: V18.2 (NON_COMPLIANT) — fix_spec_completeness guard passes FIXED findings that contain "Fix Specification" with all 4 spec fields, inflating the metric. Fix: replace two-condition substring guard with exact `"**Verdict**: DIAGNOSIS_COMPLETE" not in content` check.
**Fix Specification**:
- Target file: bl/crucible.py
- Target location: _score_diagnose_analyst() line 410 guard condition
- Concrete edit: Changed from `if "DIAGNOSIS_COMPLETE" not in content and "Fix Specification" not in content: continue` to `if "**Verdict**: DIAGNOSIS_COMPLETE" not in content: continue`
- Verification command: Check that only D-prefix DIAGNOSIS_COMPLETE findings enter spec_scores — F-prefix FIXED findings excluded

---

## Wave 20 — Post-Fix Validation and Dashboard Audit

**Generated from findings**: F19.1, F19.2, D18.1, D18.2
**Mode transitions applied**: F19.1 FIXED -> V20.1 Validate (_is_bl2_diag_row edge-case coverage); F19.2 FIXED -> V20.2 Validate (exact verdict line match — variant format gap); D18.1 HEALTHY (HEAL_EXHAUSTED write-back confirmed) -> A20.1 Audit (HEAL_EXHAUSTED display in dashboard QuestionQueue); D18.2 HEALTHY (D-prefix FIXED contamination latent) -> A20.2 Audit (fix_rows prefix guard — should it be hardened now); F19.1 FIXED -> D20.1 Diagnose (run_all_benchmarks() post-fix score verification)

---

### V20.1: Does _is_bl2_diag_row() in crucible.py correctly handle edge cases — empty lines, lines with fewer than 3 tab-separated columns, and rows where parts[2] contains a trailing newline or whitespace?

**Status**: COMPLIANT
**Operational Mode**: validate
**Mode**: code_audit
**Agent**: design-reviewer
**Priority**: HIGH
**Motivated by**: F19.1 (FIXED) — _is_bl2_diag_row() was added as a nested helper to scope dc_rate to BL 2.0 D-prefix rows. The implementation checks `parts[0] == "N/A"` and `parts[1].startswith("D")` and matches `parts[2]` against a regex. However results.tsv rows produced by update_results_tsv() may have trailing newlines (splitlines() strips them, but other read paths may not), and lines with only whitespace or with a BOM at the start of the file would cause parts[0] to be non-"N/A" silently. An empty string from a trailing newline after splitlines() would produce parts=[""] with len < 3, falling to return False — but this must be confirmed. If parts[2] contains a space or tab suffix (e.g., "DIAGNOSIS_COMPLETE\n"), the regex r"^(DIAGNOSIS_COMPLETE|...)$" would correctly reject it, but the failure mode is silent: valid BL 2.0 rows are excluded from all_diag, producing an understated dc_rate with no error.
**Hypothesis**: The splitlines() call at results_tsv.read_text().splitlines() strips newlines before the list comprehension, so parts[2] will not have trailing newline characters. Empty lines from splitlines() would produce a one-element list [""] with len(parts) < 3, so the `len(parts) >= 3` guard correctly returns False. The function is edge-case correct for the current read path. However, if a future call site passes lines without splitlines() (e.g., from a generator or line-by-line reader), the guard could fail silently on valid rows.
**Method**: Read bl/crucible.py lines 383-403 in full. Confirm: (1) The read path that feeds lines into _is_bl2_diag_row() uses splitlines() (stripping newlines). (2) The `len(parts) >= 3` guard at line 385 handles short rows. (3) The regex `r"^(DIAGNOSIS_COMPLETE|HEALTHY|FAILURE|INCONCLUSIVE)$"` is anchored with ^ and $ — confirm this correctly rejects rows where parts[2] has trailing whitespace or content after the verdict token. (4) Check whether any other call site in crucible.py reads results.tsv lines without splitlines().
**Success criterion**: COMPLIANT if splitlines() strips newlines before the helper runs and all three guards (len check, parts[0] equality, parts[1] prefix, parts[2] regex) are collectively sufficient to handle empty lines, short rows, and whitespace edge cases. NON_COMPLIANT with Fix Specification if any valid BL 2.0 D-prefix row can be silently excluded by an edge condition in the helper.

---

### V20.2: Does the exact `**Verdict**: DIAGNOSIS_COMPLETE` match in fix_spec_completeness miss any legitimate diagnosis findings that use variant verdict formats — such as bold-italic, different spacing, or verdict inside a code block?

**Status**: COMPLIANT
**Operational Mode**: validate
**Mode**: code_audit
**Agent**: design-reviewer
**Priority**: MEDIUM
**Motivated by**: F19.2 (FIXED) — fix_spec_completeness guard was tightened to `"**Verdict**: DIAGNOSIS_COMPLETE" not in content` (exact bold-markdown pattern). This correctly excludes FIXED findings. However, the agent prompt template for diagnose-analyst may produce variant verdict formats in edge cases: e.g., `**Verdict:** DIAGNOSIS_COMPLETE` (space before colon vs. colon-space), `***Verdict***: DIAGNOSIS_COMPLETE` (bold-italic), or a verdict rendered inside a markdown code block (backtick-quoted). Any such variant would cause a genuine DIAGNOSIS_COMPLETE finding to be excluded from spec_scores, producing an understated fix_spec_completeness metric.
**Hypothesis**: The diagnose-analyst agent prompt specifies the exact output format `**Verdict**: DIAGNOSIS_COMPLETE` (double-asterisk bold, colon, space, then verdict). All existing DIAGNOSIS_COMPLETE findings in projects/bl2/findings/ use this exact format consistently. There are no variant formats in the current campaign. The risk is low for the current campaign but becomes relevant when the agent prompt changes or new campaigns start.
**Method**: Run: `grep -rn "DIAGNOSIS_COMPLETE" projects/bl2/findings/*.md | grep -v "synthesis"` — list all occurrences of "DIAGNOSIS_COMPLETE" across all finding files. For each occurrence, check whether it uses the exact `**Verdict**: DIAGNOSIS_COMPLETE` pattern or a variant (colon-space vs. space-colon, bold-italic, code-block, etc.). Confirm that every finding with a DIAGNOSIS_COMPLETE verdict in the file appears with exactly the expected pattern. Count how many findings have the exact pattern vs. how many findings in results.tsv have verdict DIAGNOSIS_COMPLETE.
**Success criterion**: COMPLIANT if all DIAGNOSIS_COMPLETE findings use the exact `**Verdict**: DIAGNOSIS_COMPLETE` format with no variants. NON_COMPLIANT with Fix Specification if any legitimate DIAGNOSIS_COMPLETE finding uses a variant format that the exact match would miss — the fix would be to normalize the pattern (e.g., strip surrounding whitespace from the match string, or use a regex).

---

### A20.1: Does the dashboard QuestionQueue component display HEAL_EXHAUSTED questions with a distinct visual status — or does it render them with the default fallback styling, making exhausted questions visually indistinguishable from unknown statuses?

**Status**: NON_COMPLIANT
**Operational Mode**: audit
**Mode**: code_audit
**Agent**: compliance-auditor
**Priority**: HIGH
**Motivated by**: D18.1 (HEALTHY) — HEAL_EXHAUSTED write-back to questions.md is confirmed correct end-to-end. However, HEAL_EXHAUSTED questions requiring human intervention must be visually prominent in the dashboard so an operator can identify them without scanning raw questions.md. The QuestionQueue component in dashboard/frontend/src/components/QuestionQueue.tsx defines STATUS_COLORS with only four entries: PENDING, DONE, INCONCLUSIVE, IN_PROGRESS. HEAL_EXHAUSTED is not in the map, so questions.status === "HEAL_EXHAUSTED" renders with the default fallback `bg-[#374151] text-[#9ca3af]` (same as PENDING gray). Additionally, the status filter dropdown has options only for PENDING, DONE, INCONCLUSIVE, and IN_PROGRESS — there is no HEAL_EXHAUSTED option, so operators cannot filter to show only exhausted questions. Both omissions reduce the operational visibility of a status that represents a campaign stall requiring human action.
**Hypothesis**: STATUS_COLORS in QuestionQueue.tsx line 9-14 is missing HEAL_EXHAUSTED. The filter dropdown at lines 152-156 is missing a HEAL_EXHAUSTED option. Both omissions are present in the current source. The dashboard would currently show HEAL_EXHAUSTED questions in plain gray with no filter accessibility.
**Method**: Read dashboard/frontend/src/components/QuestionQueue.tsx lines 1-30 (STATUS_COLORS map) and lines 148-160 (filter dropdown options). Confirm: (1) HEAL_EXHAUSTED is absent from STATUS_COLORS. (2) No filter option for HEAL_EXHAUSTED exists in the dropdown. (3) Other BL 2.0 terminal statuses — NON_COMPLIANT, FIXED, FIX_FAILED, DIAGNOSIS_COMPLETE, COMPLIANT, PROMISING, BLOCKED — are also checked for coverage in STATUS_COLORS. Document any missing entries.
**Success criterion**: NON_COMPLIANT with Fix Specification (covering STATUS_COLORS entry + filter dropdown option for HEAL_EXHAUSTED at minimum) if HEAL_EXHAUSTED is absent from both maps. COMPLIANT only if HEAL_EXHAUSTED renders with a visually distinct amber/red color and is selectable via the filter dropdown.

---

### A20.2: Does _score_fix_implementer in crucible.py require a structural question_id prefix guard now that D-prefix FIXED rows are a confirmed historical edge case, or is the latent fragility acceptable given BL 2.0 campaign design constraints?

**Status**: NON_COMPLIANT
**Operational Mode**: audit
**Mode**: code_audit
**Agent**: compliance-auditor
**Priority**: LOW
**Motivated by**: D18.2 (HEALTHY) — fix_rows is de facto scoped to fix questions in the current campaign because only F-prefix questions produce FIXED/FIX_FAILED verdicts. However D18.2 documented a confirmed edge case: D-mid.4 had verdict FIXED written to results.tsv (a diagnose question that self-fixed). This edge case is already in the historical results.tsv and is therefore already being counted in fix_rows. The fragility is not purely theoretical — it has already occurred once. The question is whether the project-brief or campaign design rules explicitly prohibit D-prefix questions from producing FIXED verdicts going forward, or whether a structural guard should be added to _score_fix_implementer to exclude non-F-prefix rows from fix_rows.
**Hypothesis**: The project-brief specifies that FIXED is a fix-implementer verdict (F-prefix questions). A D-prefix question producing FIXED is a campaign design violation, not a supported pattern. Therefore _score_fix_implementer should add a question_id prefix guard (keep only rows where qid starts with "F" or campaign-specific fix-question prefixes) to prevent future D-prefix FIXED rows from silently contaminating the metric. The D-mid.4 edge case is a known historical artifact that should be excluded from fix_rows going forward.
**Method**: Read bl/crucible.py lines 425-475 (_score_fix_implementer). Confirm the fix_rows filter is verdict-only with no prefix guard. Read project-brief.md — check whether FIXED is listed as an exclusive fix-implementer verdict. Count how many rows in results.tsv have verdict FIXED with a non-F-prefix question ID (D-mid.4 confirmed; check for others). Determine whether adding a prefix guard would change the current fixed_rate score (if D-mid.4 is the only non-F FIXED row, the impact is one row out of ~40).
**Success criterion**: NON_COMPLIANT with Fix Specification (add F-prefix filter to fix_rows) if the project-brief designates FIXED as an exclusive fix-implementer verdict AND the D-mid.4 historical row is distorting the current fixed_rate. COMPLIANT if the project-brief permits diagnose questions to produce FIXED in dual-mode scenarios — document the exception explicitly in the finding so future campaigns do not treat it as a defect.

---

### D20.1: Does run_all_benchmarks() produce a materially higher diagnose-analyst dc_rate after the F19.1 _is_bl2_diag_row() fix — specifically, does dc_rate rise from ~0.51 to ~0.85 as predicted, confirming the filter is functioning correctly?

**Status**: HEALTHY
**Operational Mode**: diagnose
**Mode**: code_audit
**Agent**: diagnose-analyst
**Priority**: HIGH
**Motivated by**: F19.1 (FIXED) — the fix was applied and verified by code inspection (correct logic confirmed), but run_all_benchmarks() was not executed post-fix to produce an actual score delta. The F19.1 finding states "Expected Outcome: dc_rate should rise from ~0.51 to ~0.85+". Without an actual benchmark run, the fix is code-verified but not score-verified. If dc_rate does not rise as expected, it would indicate that the _is_bl2_diag_row() helper is silently excluding valid BL 2.0 D-prefix rows — either because the column format check (parts[0]=="N/A") is wrong for some rows, or because D-prefix questions in this campaign produced HEALTHY/DIAGNOSIS_COMPLETE verdicts in old-format rows that the filter now excludes.
**Hypothesis**: Running run_all_benchmarks() against projects/bl2/results.tsv after the F19.1 fix will show diagnose-analyst dc_rate rising from ~0.51 to ~0.85+. The BL 2.0 D-prefix questions in Wave 15-19 all used new-format TSV rows (col[0]="N/A"), so the filter includes them. The ~22 excluded BL 1.x rows are old-format (qid in col[0]), so they are correctly excluded. The predicted score increase is structurally sound.
**Method**: Run: `python -c "from bl.crucible import run_all_benchmarks; import json; r = run_all_benchmarks('projects/bl2'); print(json.dumps(r, indent=2))"` from the Bricklayer2.0 root directory. Record the diagnose-analyst dc_rate value in the output. Compare against the pre-fix baseline of ~0.51. If dc_rate is between 0.80 and 0.95, the fix is functioning as expected. If dc_rate is below 0.70, run a diagnostic count: `grep -c "^N/A.*\tD.*\tDIAGNOSIS_COMPLETE\t" projects/bl2/results.tsv` vs `grep -c "^N/A.*\tD.*\t" projects/bl2/results.tsv` to verify all_diag row count.
**Success criterion**: HEALTHY if dc_rate is >= 0.80 after the fix (consistent with ~85% BL 2.0 diagnose-analyst success rate). DIAGNOSIS_COMPLETE with root cause if dc_rate remains at or near the pre-fix ~0.51 baseline — this would indicate the filter is not working as intended and requires a follow-up Fix question.

---

## Wave 21 — Dashboard Status Coverage + crucible.py Fix Guard

**Generated from findings**: A20.1, A20.2, D20.1
**Mode transitions applied**: A20.1 NON_COMPLIANT → F21.1 Fix (add BL 2.0 statuses to STATUS_COLORS and filter dropdown in QuestionQueue.tsx); A20.2 NON_COMPLIANT → F21.2 Fix (add _is_fix_row() F-prefix guard to _score_fix_implementer in crucible.py); D20.1 HEALTHY (fix_spec_completeness=0.29 noted as separate quality gap) → D21.1 Diagnose (identify which DIAGNOSIS_COMPLETE findings are missing Fix Specification fields and why)

---

### F21.1: Implement the A20.1 fix — add HEAL_EXHAUSTED and all BL 2.0 terminal statuses to STATUS_COLORS and the filter dropdown in QuestionQueue.tsx

**Status**: FIXED
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: A20.1 (NON_COMPLIANT) — HEAL_EXHAUSTED renders with the same gray fallback as PENDING; BL 2.0 statuses FIXED, FIX_FAILED, DIAGNOSIS_COMPLETE, COMPLIANT, NON_COMPLIANT, BLOCKED are absent from STATUS_COLORS and the filter dropdown entirely
**Hypothesis**: Adding the entries from the A20.1 Fix Specification will make HEAL_EXHAUSTED visually distinct (amber-red) and filterable, and will give all BL 2.0 terminal statuses correct color treatment in the dashboard
**Method**: fix-implementer
**Fix Specification**:
- Target file: `dashboard/frontend/src/components/QuestionQueue.tsx`
- Target location: Lines 9-14 (STATUS_COLORS map) and lines 152-156 (filter dropdown `<option>` elements)
- Concrete edit: Extend STATUS_COLORS with the following entries (colors from A20.1 Fix Specification):
  - `HEAL_EXHAUSTED: "bg-[#7c2d12] text-[#f97316]"` (amber-red — requires human action)
  - `FIXED: "bg-[#064e3b] text-[#34d399]"` (green — success, same as DONE)
  - `FIX_FAILED: "bg-[#4c0519] text-[#f43f5e]"` (rose-red — active failure)
  - `DIAGNOSIS_COMPLETE: "bg-[#1e3a5f] text-[#38bdf8]"` (blue — ready for fix)
  - `COMPLIANT: "bg-[#064e3b] text-[#34d399]"` (green — pass)
  - `NON_COMPLIANT: "bg-[#451a03] text-[#f59e0b]"` (amber — needs fix)
  - `BLOCKED: "bg-[#4a1d96] text-[#c4b5fd]"` (purple — blocked)
  Add corresponding `<option>` elements for each status in the filter dropdown, with HEAL_EXHAUSTED placed first after the existing four options (highest-priority operator signal)
- Verification command: Open dashboard at http://localhost:3100 — confirm a HEAL_EXHAUSTED question renders in amber-red (not gray), and the filter dropdown lists all newly added statuses as selectable options
**Success criterion**: FIXED if STATUS_COLORS contains all seven new entries and the filter dropdown contains matching `<option>` elements for each, with no TypeScript compile errors

---

### F21.2: Implement the A20.2 fix — add _is_fix_row() F-prefix guard to _score_fix_implementer in crucible.py to exclude non-F-prefix FIXED/FIX_FAILED rows from fix_rows

**Status**: FIXED
**Operational Mode**: fix
**Priority**: LOW
**Motivated by**: A20.2 (NON_COMPLIANT) — fix_rows is currently a verdict-only filter with no question_id prefix check; D-mid.4 (a D-prefix question with FIXED verdict) is already in fix_rows and confirmed by A20.2; project-brief.md designates FIXED/FIX_FAILED as exclusive Fix-mode verdicts; structural guard is warranted to prevent future D-prefix contamination
**Hypothesis**: Adding _is_fix_row() as a nested helper mirroring _is_bl2_diag_row() will exclude the D-mid.4 row from fix_rows for new-format rows (col[0]="N/A") while preserving old-format BL 1.x rows via the fallback path — net effect is fix_rows shrinks by exactly 1 (the D-mid.4 row)
**Method**: fix-implementer
**Fix Specification**:
- Target file: `bl/crucible.py`
- Target location: `_score_fix_implementer()` — the `fix_rows` list comprehension at line 447 (verdict-only filter)
- Concrete edit: Replace the single-line list comprehension with a nested `_is_fix_row(ln)` helper, as specified in A20.2 Fix Specification:
  ```python
  def _is_fix_row(ln: str) -> bool:
      parts = ln.split("\t")
      if len(parts) >= 3 and parts[0] == "N/A":
          return parts[1].startswith("F") and bool(
              re.search(r"^(FIXED|FIX_FAILED)$", parts[2])
          )
      return bool(re.search(r"\t(FIXED|FIX_FAILED)\t", ln))
  fix_rows = [ln for ln in lines if _is_fix_row(ln)]
  ```
- Verification command: Run `python -c "from bl.crucible import run_all_benchmarks; import json; r = run_all_benchmarks('projects/bl2'); print(json.dumps(r, indent=2))"` — confirm fix-implementer fix_rows count drops by 1 (from ~40 to ~39 new-format rows) and fixed_rate is unchanged or marginally adjusted
**Success criterion**: FIXED if fix_rows excludes D-mid.4 for the BL 2.0 new-format path and the fix-implementer benchmark score remains within 0.01 of the pre-fix value (D-mid.4 was FIXED, so fixed_rate numerator and denominator both drop by 1 — net rate impact near zero)

---

### D21.1: Why is fix_spec_completeness=0.29 in run_all_benchmarks() — which DIAGNOSIS_COMPLETE findings are missing the four required Fix Specification fields, and is the gap caused by findings that omit the spec intentionally (e.g., "no fix needed" subtypes) or by diagnose-analyst agents failing to populate the template?

**Status**: DIAGNOSIS_COMPLETE
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Motivated by**: D20.1 (HEALTHY) — run_all_benchmarks() post-fix shows diagnose-analyst score=0.7158 with dc_rate=1.00 but fix_spec_completeness=0.29; at 1.00 dc_rate every DIAGNOSIS_COMPLETE finding should include all four Fix Specification fields (target file, target location, concrete edit, verification command), but only 29% do; this is a separate quality gap from the dc_rate measurement error fixed in F19.1 and represents either findings that predate the Fix Specification template requirement or agent failures to populate it
**Hypothesis**: The low fix_spec_completeness is primarily caused by early-wave DIAGNOSIS_COMPLETE findings (Waves 1-14) that were written before the BL 2.0 Fix Specification template was standardized; later waves (15-20) should have higher completeness. A secondary cause may be DIAGNOSIS_COMPLETE findings for "no code change needed" conclusions (e.g., design decisions, architecture confirmations) where a Fix Specification is not applicable — these inflate the denominator without being genuine agent failures.
**Method**: Run `grep -rn "Verdict.*DIAGNOSIS_COMPLETE" C:/Users/trg16/Dev/Bricklayer2.0/projects/bl2/findings/*.md | grep -v synthesis` to list all DIAGNOSIS_COMPLETE findings. For each, check whether the finding contains all four Fix Specification fields: "Target file", "Target location", "Concrete edit", "Verification command". Group findings by wave number. Calculate per-wave completeness to determine whether the gap is concentrated in early waves or distributed across all waves. For findings missing the spec, check whether the finding conclusion is "no fix needed" (intentional omission) or a genuine fix recommendation without the structured spec (agent failure).
**Success criterion**: DIAGNOSIS_COMPLETE with Fix Specification if the gap is caused by agent failures on fixable findings — fix is to add a validation step to the diagnose-analyst prompt requiring Fix Specification population for all DIAGNOSIS_COMPLETE findings that recommend a code change. HEALTHY if the gap is entirely explained by early-wave pre-template findings and "no fix needed" subtypes — document as a known historical artifact requiring no code change.

---

## Wave 22 — Fix D21.1 + Validate F21.1 + Validate F21.2

**Generated from findings**: F21.1, F21.2, D21.1
**Mode transitions applied**: F21.1 FIXED → V22.2 Validate (confirm HEAL_EXHAUSTED amber-red badge renders and is not using gray fallback); F21.2 FIXED → V22.1 Validate (confirm fix_rows count reduced by 1 and fixed_rate is net-zero); D21.1 DIAGNOSIS_COMPLETE → F22.1 Fix (apply frontmatter-position guard to fix_spec_completeness in _score_diagnose_analyst)

---

### F22.1: Apply the D21.1 fix — replace the F19.2 full-text guard in _score_diagnose_analyst() with a frontmatter-position check restricted to the first 6 lines of each finding file

**Status**: FIXED
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: D21.1 (DIAGNOSIS_COMPLETE) — the current guard `"**Verdict**: DIAGNOSIS_COMPLETE" not in content` still admits V16.1, V18.2, F19.2, and V20.2 as false positives because those non-diagnosis findings quote the pattern in their body text; the correct guard checks only the frontmatter header (first 6 lines) where genuine diagnosis findings exclusively place their verdict declaration
**Hypothesis**: Replacing the substring guard with a first-6-lines position check will exclude the four false-positive findings (V16.1, V18.2, F19.2, V20.2) from spec_scores, leaving only the 16 genuine DIAGNOSIS_COMPLETE findings; spec_completeness will drop from ~0.29 to ~0.25 (4 complete / 16 genuine = 0.25), which is the accurate metric
**Method**: fix-implementer
**Fix Specification**:
- Target file: `bl/crucible.py`
- Target location: `_score_diagnose_analyst()` — fix_spec_completeness guard (line 421 post-F19.2, the `if "**Verdict**: DIAGNOSIS_COMPLETE" not in content: continue` line)
- Concrete edit:
  ```python
  # Before (F19.2 guard — still too broad, admits body-quoted occurrences):
  if "**Verdict**: DIAGNOSIS_COMPLETE" not in content:
      continue

  # After (frontmatter-position guard — exact standalone line in first 6 lines only):
  first_lines = content.split("\n")[:6]
  if not any(line.strip() == "**Verdict**: DIAGNOSIS_COMPLETE" for line in first_lines):
      continue
  ```
- Verification command: `python -c "from bl.crucible import run_all_benchmarks; import json; r = run_all_benchmarks('projects/bl2'); import pprint; pprint.pprint(r)"` — confirm spec_completeness is approximately 0.25 (4 complete / 16 genuine findings) and that V16.1, V18.2, F19.2, V20.2 are no longer counted in the spec_scores denominator
**Success criterion**: FIXED if re-running run_all_benchmarks() shows spec_completeness between 0.20 and 0.30 with exactly 16 findings in the denominator (not 20), and the four false-positive findings are absent from the spec_scores scan

---

### V22.1: Post-F21.2 validate — does run_all_benchmarks() show fix-implementer score unchanged after the _is_fix_row() guard excludes D-mid.4 from fix_rows?

**Status**: COMPLIANT
**Operational Mode**: validate
**Priority**: LOW
**Motivated by**: F21.2 (FIXED) — _is_fix_row() was added and D-mid.4 (D-prefix, FIXED verdict, new-format row) is now structurally excluded from fix_rows; the F21.2 finding states the expected impact is "net-zero for fixed_rate" because D-mid.4 was a 1:1 entry in both FIXED count and total, but this has not been confirmed by an actual benchmark run
**Hypothesis**: Running run_all_benchmarks() against projects/bl2/results.tsv will show fix-implementer fixed_rate within 0.01 of the pre-fix baseline (~0.96); fix_rows count will be exactly 1 lower than the pre-F21.2 count; all old-format BL 1.x fix rows (F2.1-F2.6) will still be present via the fallback path and are unaffected by the guard
**Method**: Run `python -c "from bl.crucible import run_all_benchmarks; import json; r = run_all_benchmarks('projects/bl2'); print(json.dumps(r, indent=2))"` from the Bricklayer2.0 root directory. Record fix-implementer fixed_rate. Also run `grep -c "^N/A.*\tF.*\tFIXED\t" C:/Users/trg16/Dev/Bricklayer2.0/projects/bl2/results.tsv` to get the post-fix F-prefix FIXED row count and confirm it is exactly 1 fewer than the total FIXED row count (which previously included D-mid.4)
**Success criterion**: HEALTHY if fix-implementer fixed_rate is within 0.01 of ~0.96 and the F-prefix FIXED row count is exactly 1 fewer than total FIXED rows (confirming D-mid.4 exclusion). DIAGNOSIS_COMPLETE with root cause if fixed_rate changed by more than 0.01 — this would indicate either multiple D-prefix FIXED rows exist (wider contamination than detected) or the fallback path is incorrectly filtering old-format rows

---

### V22.2: Post-F21.1 validate — does STATUS_COLORS in QuestionQueue.tsx now include HEAL_EXHAUSTED with amber-red styling, and is the badge render fallback correctly bypassed for HEAL_EXHAUSTED questions?

**Status**: COMPLIANT
**Operational Mode**: validate
**Priority**: MEDIUM
**Motivated by**: F21.1 (FIXED) — STATUS_COLORS was updated with HEAL_EXHAUSTED and seven other BL 2.0 statuses via code inspection and agent report; the F21.1 finding confirms the edit but no runtime screenshot or compiled output was captured to verify the badge renders correctly rather than falling through to the gray fallback (which would happen if the TypeScript key lookup fails at compile time or if the status string passed at runtime uses a different casing)
**Hypothesis**: The STATUS_COLORS entry for HEAL_EXHAUSTED uses key `"HEAL_EXHAUSTED"` (uppercase, underscore) which matches the status string produced by the BL 2.0 heal loop; the badge render path does a direct map lookup, so the amber-red classes `bg-[#7c2d12] text-[#f97316]` will be applied rather than the gray fallback; no TypeScript compile errors were introduced because the key is a plain string constant
**Method**: Read `dashboard/frontend/src/components/QuestionQueue.tsx` and verify: (1) STATUS_COLORS contains `HEAL_EXHAUSTED: "bg-[#7c2d12] text-[#f97316]"` as a top-level key, (2) the badge render expression uses a lookup pattern that will resolve to this entry for status value `"HEAL_EXHAUSTED"`, (3) the filter dropdown `<option>` element for HEAL_EXHAUSTED uses the exact same string as the STATUS_COLORS key. If the dashboard is running, also open http://localhost:3100 and filter by HEAL_EXHAUSTED to confirm the badge renders amber-red
**Success criterion**: HEALTHY if STATUS_COLORS contains the HEAL_EXHAUSTED entry with correct amber-red Tailwind classes, the badge render path would resolve the key at runtime, and the filter dropdown option string matches exactly. DIAGNOSIS_COMPLETE with Fix Specification if the key is present but the render path uses a different lookup expression that would still fall through to the gray fallback for HEAL_EXHAUSTED questions

---

## Wave 23 — Scorer Accuracy + Field Name Alignment

**Generated from findings**: F22.1 (FIXED), V22.1 (COMPLIANT), V22.2 (COMPLIANT)
**Mode transitions applied**: Wave 22 all COMPLIANT/FIXED → adjacent gap questions. V22.1 COMPLIANT + synthesizer=0.0 → V23.1 Validate (is synthesis.md absent by design or oversight?); hypothesis-generator has_derived_from=0.00 → D23.1 Diagnose (field name mismatch between scorer expectation and BL 2.0 format); fix_spec_completeness=0.29 pre-template gap → D23.2 Diagnose (characterize the 12 pre-template findings); compliance-auditor fix_spec_rate full-text scan → A23.1 Audit (does it suffer the same frontmatter gap as the now-fixed _score_diagnose_analyst?)

---

### V23.1: Is synthesizer score=0.0 because findings/synthesis.md does not exist in this campaign, or because the synthesizer agent was never run — and is running the synthesizer expected at this stage of the campaign?

**Status**: COMPLIANT
**Operational Mode**: validate
**Priority**: MEDIUM
**Motivated by**: V22.1 (COMPLIANT) — run_all_benchmarks() shows synthesizer=0.0 with message "findings/synthesis.md not found"; _score_synthesizer in crucible.py returns 0.0 immediately if `project_dir / "findings" / "synthesis.md"` does not exist; the question is whether this is expected (the synthesizer is designed to be run manually at session end per CLAUDE.md, not automatically mid-campaign) or whether an operator oversight has left the file absent when it should exist
**Hypothesis**: findings/synthesis.md is absent because the synthesizer agent has not been run for this campaign yet — this is the expected state for an active mid-campaign. CLAUDE.md instructs: "Run the synthesizer at session end before analyze.py." The campaign is mid-wave (Wave 22 findings present, Wave 23 just generated), so the synthesizer has not been triggered. The synthesizer score=0.0 is a structural false negative in the benchmark, not an agent failure.
**Method**: Check whether `C:/Users/trg16/Dev/Bricklayer2.0/projects/bl2/findings/synthesis.md` exists: `ls C:/Users/trg16/Dev/Bricklayer2.0/projects/bl2/findings/synthesis.md`. If absent, confirm this is the expected mid-campaign state by reading CLAUDE.md section "Generating the End-of-Session Report" — verify the synthesizer is explicitly described as a session-end operation. If present but empty or malformed, that is a separate issue.
**Success criterion**: COMPLIANT if synthesis.md is absent and CLAUDE.md confirms the synthesizer is a session-end operation — score=0.0 is the correct mid-campaign benchmark reading and requires no remediation. DIAGNOSIS_COMPLETE with Fix Specification if synthesis.md should exist at this stage (e.g., per-wave synthesis is a BL 2.0 requirement) but the agent has not been run — fix is to add a synthesizer invocation step to the Wave N completion checklist.

---

### D23.1: Why is hypothesis-generator has_derived_from=0.00 — does _score_hypothesis_generator check for "Derived from" while BL 2.0 questions use "Motivated by" as the field name?

**Status**: DIAGNOSIS_COMPLETE
**Operational Mode**: diagnose
**Priority**: HIGH
**Motivated by**: V22.1 (COMPLIANT) — run_all_benchmarks() shows hypothesis-generator score=0.1511 with has_derived_from=0.00 across all scored Wave 2+ questions; the benchmark description context identifies this as a potential field-name mismatch between the scorer and the BL 2.0 question format
**Hypothesis**: `_score_hypothesis_generator` at line 191 of bl/crucible.py checks `"Derived from" in b` for the has_derived_from metric. BL 1.x questions used `**Derived from**: {finding_id}` as the lineage field. BL 2.0 questions (Waves 15+) use `**Motivated by**: {source finding ID}` instead. Since no Wave 2+ question in this campaign contains the string "Derived from" (they all use "Motivated by"), the has_derived_from rate is 0.00 for every scored question block, and this single metric (weight=0.35) suppresses the overall score from its true value of ~0.42 to 0.1511.
**Method**: Read `bl/crucible.py` lines 159-205 (_score_hypothesis_generator). Confirm line 191 checks for `"Derived from"`. Then check a sample of Wave 15-22 question blocks in `questions.md` — grep for the lineage field: `grep -n "Derived from\|Motivated by" C:/Users/trg16/Dev/Bricklayer2.0/projects/bl2/questions.md | head -20`. Count how many questions use each field name. If "Motivated by" is used exclusively from Wave 15 onward, the scorer is measuring a BL 1.x field that does not exist in BL 2.0 question format.
**Success criterion**: DIAGNOSIS_COMPLETE with Fix Specification if the scorer checks "Derived from" while all BL 2.0 questions use "Motivated by" — fix is to update the has_derived_from check in _score_hypothesis_generator to accept both field names (or "Motivated by" exclusively for BL 2.0 format, with the BL 1.x fallback). HEALTHY if "Derived from" is found in a material fraction of Wave 2+ questions — the 0.00 score would then indicate a genuine quality gap in question lineage documentation.

---

### D23.2: Are the 12 pre-template DIAGNOSIS_COMPLETE findings (Waves 1-14) missing Fix Specification fields because diagnose-analyst was not prompted with the spec template at that stage, or because those findings had non-fixable verdicts such as "no code change needed" or partial diagnosis conclusions?

**Status**: HEALTHY
**Operational Mode**: diagnose
**Priority**: LOW
**Motivated by**: D21.1 (DIAGNOSIS_COMPLETE) — D21.1 found fix_spec_completeness=0.29 and diagnosed that early-wave findings (pre-template) are the primary cause; the D21.1 finding states the gap is "primarily caused by early-wave DIAGNOSIS_COMPLETE findings written before the BL 2.0 Fix Specification template was standardized"; this question validates that characterization by examining the 12 pre-template findings individually
**Hypothesis**: The 12 pre-template DIAGNOSIS_COMPLETE findings (D4.1, D5.1, D6.1, D7.1, D12.1, D12.2, D13.1, D13.2, D14.1, D15.1, D15.2, D15.3) all predate the Fix Specification template introduction (F16.x wave). Each finding ends with a fix recommendation expressed as prose (not structured fields). The agent was not presented with the four-field template ("Target file", "Target location", "Concrete edit", "Verification command") at generation time. Retroactively adding the structured spec fields to these findings would improve fix_spec_completeness from 0.25 to 1.00, but this is a cosmetic change to historical findings — it does not improve any running code and may not be worth the effort.
**Method**: For each of the following findings, read the first 30 lines: D4.1.md, D5.1.md, D6.1.md, D7.1.md, D12.1.md, D12.2.md, D13.1.md, D13.2.md, D14.1.md, D15.1.md, D15.2.md, D15.3.md (in `C:/Users/trg16/Dev/Bricklayer2.0/projects/bl2/findings/`). For each: (1) confirm the verdict is DIAGNOSIS_COMPLETE, (2) check whether the finding contains any of: "Target file", "Target location", "Concrete edit", "Verification command", "Fix Specification", (3) classify the fix recommendation as: prose-only, partial-spec, no-fix-needed, or already-fixed-by-later-wave. Report the breakdown across all 12 findings.
**Success criterion**: DIAGNOSIS_COMPLETE with Fix Specification (retroactive spec addition is warranted) if the majority of the 12 findings have clear fixable code changes documented in prose with no structural barrier to adding the four template fields. HEALTHY (no action needed) if the majority are either already addressed by later Fix questions, are "no code change needed" conclusions, or have partial diagnoses that would require a new investigation to complete the spec.

---

### A23.1: Does _score_compliance_auditor in crucible.py use a full-text scan for "NON_COMPLIANT" when building the fix_spec_scores denominator — the same structural gap that caused false positives in _score_diagnose_analyst before F22.1?

**Status**: NON_COMPLIANT
**Operational Mode**: audit
**Priority**: MEDIUM
**Motivated by**: F22.1 (FIXED) — F22.1 replaced the full-text DIAGNOSIS_COMPLETE guard in _score_diagnose_analyst with a frontmatter-position check (first 6 lines only) to exclude findings that quote the verdict in their body text; the compliance-auditor scorer uses an analogous pattern at bl/crucible.py line 527: `if "NON_COMPLIANT" not in content: continue` — this full-text scan would include any finding that mentions "NON_COMPLIANT" anywhere in its text (e.g., in the question motivation field, a hypothesis describing expected outcomes, or a code block), inflating the fix_spec_scores denominator the same way
**Hypothesis**: Line 527 of bl/crucible.py scans the full file content for "NON_COMPLIANT" without restricting to the frontmatter verdict line. Finding files for questions that describe NON_COMPLIANT as an expected outcome (e.g., V-prefix or D-prefix findings whose success criterion says "NON_COMPLIANT if...") will be included in fix_spec_scores even though they are not genuine compliance-auditor findings. This inflates the denominator, suppressing fix_spec_rate below its true value. The same structural fix applied in F22.1 (restrict to first 6 lines) should be applied here.
**Method**: Read `bl/crucible.py` lines 519-533 (_score_compliance_auditor fix_spec_scores loop). Confirm line 527 uses a full-text `"NON_COMPLIANT" not in content` scan with no frontmatter position restriction. Then run: `grep -rln "NON_COMPLIANT" C:/Users/trg16/Dev/Bricklayer2.0/projects/bl2/findings/*.md | grep -v synthesis` to list all finding files containing the string. Subtract the count of A-prefix findings (genuine audit findings) from the total — the remainder are non-audit findings that are being incorrectly included in the denominator. If the remainder is greater than zero, the false-positive inflation is confirmed.
**Success criterion**: DIAGNOSIS_COMPLETE with Fix Specification (apply frontmatter-position guard parallel to F22.1) if any non-A-prefix finding files contain "NON_COMPLIANT" and would be incorrectly included in fix_spec_scores. HEALTHY if the string "NON_COMPLIANT" appears exclusively in A-prefix finding files — in that case the full-text scan is incidentally correct for this campaign even without a structural guard.

---

## Wave 24 — Fix D23.1 + Fix A23.1 + Validate + Audit Adjacent Scorers

**Generated from findings**: D23.1 (DIAGNOSIS_COMPLETE), A23.1 (NON_COMPLIANT), V23.1 (COMPLIANT), D23.2 (HEALTHY)
**Mode transitions applied**: D23.1 DIAGNOSIS_COMPLETE → F24.1 Fix; A23.1 NON_COMPLIANT → F24.2 Fix; V23.1 COMPLIANT → V24.1 Validate (confirm F24.1 effect on has_derived_from score); D23.2 HEALTHY → no follow-up; structural pattern of full-text verdict scans in crucible.py → A24.1 Audit (check remaining scorers for same gap)

---

### F24.1: Apply the D23.1 fix — update _score_hypothesis_generator check_block to accept both "Derived from" (BL 1.x) and "Motivated by" (BL 2.0) as valid lineage field names

**Status**: FIXED
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: D23.1 (DIAGNOSIS_COMPLETE) — `check_block()` in `_score_hypothesis_generator` at `bl/crucible.py` line 191 checks `"Derived from" in b` exclusively; all BL 2.0 Wave 2+ questions use `**Motivated by**` as the lineage field; has_derived_from rate is 0.00 across every scored BL 2.0 question block, and the 0.35 weight contributes nothing to the overall score, suppressing it from ~0.42 to ~0.15
**Hypothesis**: Changing the check to `("Derived from" in b or "Motivated by" in b)` will cause has_derived_from to return 1.00 for every BL 2.0 Wave 2+ question that contains the `**Motivated by**` field, raising the overall hypothesis-generator score from ~0.15 to ~0.45+
**Method**: Edit `bl/crucible.py`: in `_score_hypothesis_generator()` → `check_block()`, change line 191 from `"has_derived_from": 1.0 if "Derived from" in b else 0.0,` to `"has_derived_from": 1.0 if ("Derived from" in b or "Motivated by" in b) else 0.0,`. Then re-run benchmarks for the bl2 project and confirm has_derived_from rate and overall hypothesis-generator score.
**Success criterion**: FIXED if `has_derived_from` rate rises from 0.00 to near 1.00 for BL 2.0 campaigns and overall hypothesis-generator score rises above 0.40. FIX_FAILED if the rate remains 0.00 or the score does not improve.

---

### F24.2: Apply the A23.1 fix — replace bare "NON_COMPLIANT" full-text scan in _score_compliance_auditor with a frontmatter-position guard (first 6 lines only), mirroring the F22.1 fix pattern

**Status**: FIXED
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: A23.1 (NON_COMPLIANT) — `_score_compliance_auditor()` at `bl/crucible.py` line 527 uses `if "NON_COMPLIANT" not in content: continue`, a bare substring match with no restriction to the verdict frontmatter; this admits any finding that mentions "NON_COMPLIANT" in body text (e.g., Fix findings that describe what they fixed, Diagnose findings whose success criteria mention the verdict) into the fix_spec_scores denominator, inflating it and suppressing fix_spec_rate; the identical structural gap in `_score_diagnose_analyst` was fixed in F22.1 using a first-6-lines frontmatter check
**Hypothesis**: Replacing the full-text scan with a frontmatter-position check (`first_lines = content.split("\n")[:6]; if not any(line.strip() == "**Verdict**: NON_COMPLIANT" for line in first_lines): continue`) will exclude non-audit findings that mention "NON_COMPLIANT" in body text, giving fix_spec_scores a denominator of only genuine compliance-auditor findings
**Method**: Edit `bl/crucible.py` `_score_compliance_auditor()` NON_COMPLIANT guard (line 527): replace `if "NON_COMPLIANT" not in content: continue` with a first-6-lines check that matches `**Verdict**: NON_COMPLIANT` exactly. Re-run benchmarks; confirm F21.1.md (a FIXED finding that mentions NON_COMPLIANT in its body) is excluded from fix_spec_scores.
**Success criterion**: FIXED if F21.1.md and any other non-A-prefix finding files mentioning "NON_COMPLIANT" are excluded from fix_spec_scores after the change, and only genuine `**Verdict**: NON_COMPLIANT` findings remain in the denominator. FIX_FAILED if F21.1.md is still included or if genuine NON_COMPLIANT findings are erroneously excluded.

---

### V24.1: Confirm F24.1 took effect — verify has_derived_from rate and overall hypothesis-generator benchmark score improved from the pre-fix baseline of 0.1511

**Status**: COMPLIANT
**Operational Mode**: validate
**Priority**: MEDIUM
**Motivated by**: D23.1 (DIAGNOSIS_COMPLETE) — D23.1 established the pre-fix baseline: has_derived_from=0.00 across all BL 2.0 Wave 2+ questions, overall hypothesis-generator score=0.1511; F24.1 applies the fix; this question validates the fix had the predicted effect
**Hypothesis**: After F24.1 is applied and benchmarks are re-run, `has_derived_from` will be 1.00 for every question block containing `**Motivated by**` (all Wave 2+ questions in bl2), and the overall hypothesis-generator score will rise to approximately 0.45–0.50 (the 0.35 weight now contributing in full, offset by any blocks still missing other fields)
**Method**: Run `python -c "from bl.crucible import run_all_benchmarks; import json; r = run_all_benchmarks('C:/Users/trg16/Dev/Bricklayer2.0/projects/bl2'); print(json.dumps(r, indent=2))"` (or equivalent benchmark invocation). Read the hypothesis-generator section: check `has_derived_from` rate and overall score. Compare to the D23.1 baseline (score=0.1511, has_derived_from=0.00).
**Success criterion**: COMPLIANT if hypothesis-generator score is measurably above 0.40 and has_derived_from rate is above 0.90. DIAGNOSIS_COMPLETE with Fix Specification if the score did not improve (F24.1 may not have been applied, or the field name used in questions.md differs from what was assumed).

---

### A24.1: Do other crucible.py scorers (_score_monitor_agent, _score_predict_agent, _score_frontier_agent, _score_evolve_agent) use bare full-text verdict substring scans analogous to the pre-fix guards in _score_diagnose_analyst and _score_compliance_auditor?

**Status**: NON_COMPLIANT
**Operational Mode**: audit
**Priority**: LOW
**Motivated by**: A23.1 (NON_COMPLIANT) — A23.1 identified `_score_compliance_auditor` as having the same structural gap (full-text verdict scan) as `_score_diagnose_analyst` before F22.1; F22.1 and F24.2 fix two scorers; the pattern may be present in other scorer functions that filter findings by verdict string before computing fix_spec_rate or equivalent metrics; an audit of all remaining scorer functions will determine whether the fix needs to propagate further
**Hypothesis**: The pattern `if "{VERDICT_STRING}" not in content: continue` (or equivalent bare substring check) exists in at least one other scorer beyond `_score_diagnose_analyst` and `_score_compliance_auditor`. Scorers for Monitor (CALIBRATED), Predict (PROBABLE/IMMINENT), Frontier (PROMISING/BLOCKED), and Evolve (IMPROVEMENT) that compute fix_spec or quality rates over finding files are the most likely candidates.
**Method**: Read `bl/crucible.py` in full for all `_score_*` functions beyond `_score_diagnose_analyst` and `_score_compliance_auditor`. For each scorer, identify any line that checks for a verdict string in `content` without restricting to the first N lines. List: scorer name, line number, verdict string checked, whether a frontmatter-position guard is present. Report all bare full-text scans as NON_COMPLIANT; report frontmatter-guarded checks as COMPLIANT.
**Success criterion**: COMPLIANT if all remaining scorers either use frontmatter-position guards or do not perform verdict-based filtering at all. NON_COMPLIANT with Fix Specification (one fix per affected scorer) if any bare full-text verdict scan is found in a scorer not yet covered by F22.1 or F24.2.

