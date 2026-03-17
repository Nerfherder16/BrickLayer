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
