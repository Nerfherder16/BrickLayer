# Wave 14 Synthesis — Masonry Self-Research

**Wave**: 14
**Questions**: F14.1, F14.2, R14.1, R14.2, D14.1
**Completed**: 5/5
**Date**: 2026-03-21

---

## Summary

Wave 14 executes three fixes and two diagnostic investigations. Two structural gaps from Wave 13 are closed (nl_entry format drift, routing downstream_success gap). Two health checks confirm the rubrics pipeline is sound. One critical training data bug is diagnosed: ops agents (git-nerd, karen) produce hundreds of qualifying training records but only 1 each survives into `scored_all.jsonl` due to a dedup key collision. The BL root `findings/` directory creates a false Thorn signal for diagnose-analyst in vigil.

---

## Findings Table

| ID | Verdict | Severity | Title |
|----|---------|----------|-------|
| F14.1 | FIX_APPLIED | High | `_question_to_md()` fixed for BL 2.0 format |
| F14.2 | FIX_APPLIED | Medium | `masonry-observe.js` now emits "finding" events to routing_log.jsonl |
| R14.1 | WARNING | Low | Vigil diagnose-analyst Thorn is false signal from BL1.x findings at BL root |
| R14.2 | HEALTHY | Low | `rubrics.py` imports correctly; max_score()=100 for all categories |
| D14.1 | DIAGNOSIS_COMPLETE | Medium | 241→64 ops dedup collapse — commit_hash absent from dedup key |

---

## Fix Applied: F14.1 — `_question_to_md()` BL 2.0 Alignment

`bl/nl_entry.py` `_question_to_md()` was producing BL1.x-style question blocks. Three field names were wrong: `**Mode**:` (Trowel regex-compatible by accident), `**Test**:` (not `**Method**:`), `**Verdict threshold**:` (not `**Success criterion**:`), and the header used `## ID [PENDING] title` instead of `### ID: title`.

After fix, `masonry_nl_generate` produces fully BL 2.0-compatible question blocks. Trowel's `_MODE_FIELD_RE` accepts both old and new format, so no Trowel-side change needed.

---

## Fix Applied: F14.2 — Routing downstream_success Unlocked

`masonry-subagent-tracker.js` only wrote "start" events to `routing_log.jsonl` (Wave 13 finding R13.2). All mortar routing sessions scored ≤70/100, never earning the 30-pt `downstream_success` dimension.

`masonry-observe.js` now appends a `{"event":"finding","agent":"...","session_id":"...","verdict":"...","qid":"..."}` entry whenever a non-UNKNOWN finding is written. `score_routing.py` pairs "start" + "finding" events by session_id → `downstream_success=30`. Sessions with confirmed findings can now score 100/100 in routing, exceeding `min_training_score=65`.

---

## Structural Finding: Ops Dedup Collapse (D14.1)

**Severity: Medium — affects training quality for git-nerd and karen**

`score_ops_agents.py` scores ops agents via git log: every auto-commit is a git-nerd record, every CHANGELOG/ARCHITECTURE/ROADMAP commit is a karen record. The BL2.0 repo has accumulated 170 karen-attributed commits and 3 git-nerd commits, all scoring 100/100.

`_dedup_records()` in `score_all_agents.py` uses key `f"src:{source}:{branch}:{agent}:{score}"` for records without `question_id` or `session_id`. Since ops records have no `branch` field and all score 100, every karen commit maps to `"src:git_log::karen:100"`. Last-write-wins: 170 records collapse to 1.

**Impact**: Git-nerd and karen each have exactly 1 training record in `scored_all.jsonl` despite being the most active agents. MIPROv2 on these agents would train on 1 example each — insufficient for any meaningful optimization.

**Fix**: Include `commit_hash` in the else-branch of `_dedup_records()`:
```python
commit_hash = rec.get("commit_hash", "")
key = f"src:{source}:{commit_hash or branch}:{agent}:{rec.get('score', 0)}"
```
This would restore 170 karen records + 3 git-nerd records in scored_all.jsonl.

---

## Structural Finding: Vigil False Thorn for diagnose-analyst (R14.1)

`run_vigil.py` when invoked from the BL root reads `BLroot/findings/*.md` which contains 8 BL1.x-style diagnosis reports with `**Agent**: diagnose-analyst` but no `**Confidence**:` field. Vigil defaults missing confidence to 0.5 < CONFIDENCE_THRESHOLD (0.70) → 0% pass rate → Thorn classification.

These findings are pre-masonry diagnostic artifacts (D14.1-D16.1, etc.) in a different format from BL2.0 research findings. The vigil classification is meaningless for diagnose-analyst based on this data. The actual diagnose-analyst performance is not captured by vigil's confidence-threshold path from these findings.

**Options**: (1) Add `**Confidence**:` fields to BL root findings, or (2) vigil should skip/neutral-score findings without explicit confidence.

---

## Rubrics Pipeline Confirmed Healthy (R14.2)

`_HAS_RUBRICS=True` — masonry.src.scoring.rubrics imports correctly. `max_score()` returns 100 for all four categories (findings: 40+40+20, code: 50+20+30, ops: 60+40, routing: 70+30). The import guard fallback is a no-op in practice. Vigil's scored_all normalization is mathematically correct.

---

## Open Issues for Wave 15

1. **Ops dedup fix unimplemented**: D14.1 identifies the exact one-line fix. Wave 15 should apply it as F15.1 and verify karen/git-nerd training counts increase from 1 to 170/3 respectively.

2. **Vigil false Thorn**: R14.1 identifies two remediation options. The simpler path is adding `**Confidence**: 0.85` to the 8 BL root findings. Wave 15 could apply this.

3. **score_routing.py downstream_success still untested end-to-end**: F14.2 is syntax-verified but requires a live campaign session to confirm "finding" events appear in routing_log.jsonl and score_routing.py produces sessions scoring >70. Wave 15 could run a live verification.

4. **Masonry self-research agents absent from scored_all.jsonl**: Masonry's own research agents (fix-implementer, diagnose-analyst, research-analyst for masonry scope) are never in scored_all.jsonl due to the masonry/ exclusion in score_findings.py. These agents only train via `build_dataset()`. If the exclusion is ever lifted, the ops dedup fix and backfill_agent_fields.py F/V prefix gaps (R13.3) would also need addressing.
