# Finding: F-mid.1 — HEAL_EXHAUSTED written on exhausted path; frozensets updated

**Question**: Does adding `update_results_tsv(original_qid, "HEAL_EXHAUSTED", ...)` after `_append_heal_note` on the exhausted path, and adding `"HEAL_EXHAUSTED"` to all downstream frozensets, close the stale-verdict loop diagnosed in D16.1?
**Verdict**: FIXED
**Severity**: Info

## Evidence

**Changes applied**:

1. **`bl/healloop.py`** — added `update_results_tsv(original_qid, "HEAL_EXHAUSTED", ...)` call after `_append_heal_note` on the exhausted-loop exit path, before `return current_result`. The `update_results_tsv` import was already present at line 24.

2. **`bl/questions.py _PARKED_STATUSES`** — added `"HEAL_EXHAUSTED"` so `get_next_pending()` skips exhausted questions.

3. **`bl/questions.py _TERMINAL_VERDICTS`** (inside `sync_status_from_results()`) — added `"HEAL_EXHAUSTED"` so the sync function recognizes and processes HEAL_EXHAUSTED rows from results.tsv.

4. **`bl/questions.py` preserve inline tuple** (inside `sync_status_from_results()`) — added `"HEAL_EXHAUSTED"` so the status is preserved as HEAL_EXHAUSTED in questions.md (not mapped to DONE).

5. **`bl/findings.py _PRESERVE_AS_IS`** — added `"HEAL_EXHAUSTED"` so `_mark_question_done()` preserves the status for human visibility instead of mapping to DONE.

6. **`bl/agent_db.py _PARTIAL_VERDICTS`** — added `"HEAL_EXHAUSTED"` as half-credit (agent ran correctly, heal system exhausted, human intervention needed).

## Verification

`grep -n "HEAL_EXHAUSTED" bl/healloop.py bl/questions.py bl/findings.py bl/agent_db.py` confirms references in all four files. The `update_results_tsv` call appears on the exhausted-loop exit path in `healloop.py` before `return current_result`.
