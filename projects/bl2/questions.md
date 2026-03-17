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
