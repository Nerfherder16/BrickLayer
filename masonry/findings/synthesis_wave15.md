# Wave 15 Synthesis — Masonry Self-Research

**Wave**: 15
**Questions**: F15.1, R15.1, D15.1, R15.2
**Completed**: 4/4
**Date**: 2026-03-21

---

## Summary

Wave 15 closes a major training data gap (ops dedup fix), uncovers a critical routing instrumentation gap (CWD guard blocks all routing events in masonry self-research sessions), and diagnoses two summary anomalies (score_findings "1 agent" and kill-switch coverage). The CWD guard issue discovered in R15.1 is Wave 15's most significant finding: both masonry-observe.js and masonry-subagent-tracker.js will never write routing_log.jsonl events when Claude Code runs from the masonry/ directory, making downstream_success scoring impossible for self-research sessions.

---

## Findings Table

| ID | Verdict | Severity | Title |
|----|---------|----------|-------|
| F15.1 | FIX_APPLIED | Medium | Ops dedup fix: karen 1→171, git-nerd 1→3 in scored_all.jsonl |
| R15.1 | WARNING | Medium | CWD guard silently drops routing events in masonry-scoped sessions |
| D15.1 | DIAGNOSIS_COMPLETE | Low | "Agents: 1" anomaly: 5 agents contribute, summary shows only 10+ count |
| R15.2 | HEALTHY | Low | DISABLE_OMC correctly absent from subagent-tracker; format verified |

---

## Fix Applied: F15.1 — Ops Dedup Restored

One-line fix to `_dedup_records()` in `score_all_agents.py` adds `commit_hash` as the discriminator for ops records. Karen: 1→171 training examples. Git-nerd: 1→3. Total scored_all.jsonl: 64→236 records. Karen is now MIPROv2-ready (170+ examples). Git-nerd still insufficient (3 examples — needs more campaign cycles to accumulate auto-commits).

---

## Critical Finding: CWD Guard Blocks All Routing Events in Masonry Sessions (R15.1)

Both hooks check `if (fs.existsSync(path.join(cwd, 'masonry')))` before writing to routing_log.jsonl. When Claude Code runs from `C:\Users\trg16\Dev\Bricklayer2.0\masonry`, `path.join(cwd, 'masonry')` = `masonry/masonry/` which doesn't exist → guard fails → all routing events silently dropped.

**Impact**: Zero routing training signal can be generated during masonry self-research campaigns. The F14.2 fix (finding events) and the existing subagent-tracker (start events) are both suppressed. score_routing.py will always produce 0 records for masonry self-research sessions.

**Fix needed**: Both hooks must resolve the routing_log.jsonl path using CWD-agnostic logic. The simplest approach:
```javascript
// Resolve masonry/ dir — cwd might be the masonry dir itself, or its parent
const masonryDir = path.basename(cwd) === 'masonry' && fs.existsSync(cwd)
  ? cwd
  : path.join(cwd, 'masonry');
if (fs.existsSync(masonryDir)) { ... }
```

---

## Diagnostic: score_findings Summary Table Inconsistency (D15.1)

The "Agents" column in `score_all_agents.py` summary shows `agents_with_10_plus` for score_findings (1 = only quantitative-analyst), but shows `all agents covered` for score_code_agents and score_ops_agents. This is a design inconsistency — not a bug, but misleading. Five agents actually contribute 61 records. 675 total findings scanned (7 projects), 614 below threshold (mostly BL1.x-format findings from recall/recall-arch-frontier). Masonry findings confirmed excluded.

---

## Healthy: DISABLE_OMC Coverage Is Intentional (R15.2)

Commit 7b4472f targeted exactly the 7 hooks that actively interfere with BL subprocess operation (route injection, stop guards, lint/TDD checks). masonry-subagent-tracker.js was correctly excluded because its CWD guard already provides implicit subprocess suppression. The "start" event format matches score_routing.py's schema exactly. This is a clean, well-designed system — the CWD guard is the right architectural pattern, it just needs extension to handle the masonry-as-CWD case.

---

## Open Issues for Wave 16

1. **CWD guard fix unimplemented** (HIGH): Both masonry-observe.js and masonry-subagent-tracker.js need the routing_log.jsonl path to be resolved CWD-agnostically. Without this fix, no routing training data can be generated from masonry self-research sessions regardless of F14.2.

2. **score_findings summary table inconsistency** (LOW): The "Agents" column should be standardized across scorers — either all show `agents_with_10_plus` or all show `total_agents_covered`. Currently mixed.

3. **score_routing.py pairing tested in BL root sessions only**: The current routing_log.jsonl has 4 "start" events from a BL root session (session f68d4e9c) with 0 "finding" events. Once the CWD guard is fixed and F14.2 is active, a live session should produce pairing. Wave 16 should verify this end-to-end.

4. **quantitative-analyst dominance in scored_findings**: 36 of 61 training records (59%) come from quantitative-analyst. If ADBP simulation findings continue growing, this concentration will bias DSPy optimization toward quantitative/simulation-style evidence. Wave 16 could assess whether the training distribution is appropriate.
