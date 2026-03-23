# Wave 16 Synthesis — Masonry Self-Research

**Wave**: 16
**Questions**: F16.1, R16.1, D16.1, R16.2
**Completed**: 4/4
**Date**: 2026-03-21

---

## Summary

Wave 16 closes the major CWD guard bug (F16.1), uncovers two additional routing pipeline blockers (R16.1), diagnoses the BL1.x format as the root cause of the 614-finding rejection rate (D16.1), and confirms the "Agents: 1" summary column inconsistency is accidental (R16.2). The CWD guard fix is confirmed live: routing_log.jsonl received its first "finding" event from a masonry-scoped session. However, score_routing.py still produces 0 training records due to session ID mismatch and agent name truncation bugs discovered in R16.1.

---

## Findings Table

| ID | Verdict | Severity | Title |
|----|---------|----------|-------|
| F16.1 | FIX_APPLIED | High | CWD guard fixed in both routing hooks; routing_log.jsonl writeable from masonry/ dir |
| R16.1 | WARNING | Medium | score_routing.py still produces 0 records: session ID mismatch + agent name truncation |
| D16.1 | DIAGNOSIS_COMPLETE | Low | 99.5% of below-threshold findings fail confidence_calibration: missing `**Confidence**:` field (BL1.x format) |
| R16.2 | WARNING | Low | "Agents: 1" inconsistency is accidental; fix is minimal (add agents_covered to score_findings.run()) |

---

## Fix Applied: F16.1 — CWD Guard Fixed in Both Routing Hooks

Both `masonry-observe.js` and `masonry-subagent-tracker.js` had two co-dependent bugs:
1. CWD guard: `fs.existsSync(path.join(cwd, 'masonry'))` → failed when CWD was the masonry/ dir
2. Path computation: `routingLogPath = path.join(cwd, 'masonry', 'routing_log.jsonl')` pre-computed before masonryDir resolved

Fix:
```javascript
// Resolve masonry/ dir — cwd might be the masonry dir itself (self-research sessions)
const masonryDir = path.basename(cwd) === 'masonry' && fs.existsSync(cwd)
  ? cwd
  : path.join(cwd, 'masonry');
if (fs.existsSync(masonryDir)) {
  const routingLogPath = path.join(masonryDir, 'routing_log.jsonl');
  fs.appendFileSync(routingLogPath, entry + '\n', 'utf8');
}
```

**Live verification**: Writing F16.1.md triggered masonry-observe.js → routing_log.jsonl received event `{"event":"finding","agent":"fix","session_id":"315da739-...","verdict":"FIX_APPLIED","qid":"F16.1"}`. Guard now passes for all three CWD scenarios (masonry-as-CWD, BL-root, subprocess suppression preserved).

---

## Warning: Two Additional Routing Pipeline Blockers (R16.1)

Despite F16.1 working, score_routing.py produces 0 training records due to:

### Blocker 1: Session ID Mismatch
The 4 existing "start" events are from session `f68d4e9c` (BL-root setup session). The 1 "finding" event is from session `315da739` (current masonry self-research session). `_match_events()` pairs by session_id → no matches.

**Will resolve** when: A masonry-scoped session spawns specialist subagents AND writes findings (typical Mortar/Trowel-dispatched campaign).

### Blocker 2: Agent Name Truncation Bug
`extractMarkdownField()` regex `[\w]+` stops at hyphens:
- `**Agent**: fix-implementer` → extracted `"fix"` (not in AGENT_CATEGORIES → 0 pts)
- `**Agent**: research-analyst` → extracted `"research"` (not in AGENT_CATEGORIES → 0 pts)
- `**Agent**: synthesizer-bl2` → extracted `"synthesizer"` (not in AGENT_CATEGORIES → 0 pts)

Even when sessions pair, most specialist agents would score 0 for `correct_agent_dispatched` → total ≤ 30 → below min_training_score(65) → 0 training records.

**Fix (one line)**: Change `[\w]+` → `[\w-]+` in `extractMarkdownField()` line 30 of `masonry-observe.js`.

### Note: "sessions_matched: 1" Metric Is Misleading
`min(start_count=4, finding_count=1) = 1` is not actual pairs. Should be `len(records)` (actual training records produced).

---

## Diagnosis: 614/675 Findings Fail on Missing Confidence Field (D16.1)

The BL1.x format (recall, recall-arch-frontier: 494 findings) lacks the `**Confidence**:` field standardized in BL2.0. This causes `confidence_calibration = 0` (of possible 40 pts) for 99.5% of below-threshold findings.

| Dimension = 0 | Count | Percentage |
|---------------|-------|------------|
| confidence_calibration | 624 | 99.5% |
| evidence_quality | 572 | 91.2% |
| verdict_clarity | 74 | 11.8% |

Score distribution: 342 findings (55%) score 20-29 (verdict only, no confidence, minimal evidence). 30 findings score 0-9 (missing verdict too). Only 43 reach 40-49 (evidence present, no confidence).

**This is expected behavior**: The scorer correctly gates on BL2.0 quality. BL1.x findings are not appropriate training examples for BL2.0 agents. No fix warranted.

---

## Warning: "Agents" Column Inconsistency Is Accidental (R16.2)

The "Agents" column shows different populations per row because `score_findings.run()` doesn't return `agents_covered` — only `agents_with_10_plus`. The minimal fix adds `agents_covered = list(agent_counts.keys())` to `score_findings.run()`.

Current display (misleading):
```
score_findings    61    1   ← agents_with_10_plus, not all agents
score_code_agents  4    2   ← total agents covered
score_ops_agents 171    2   ← total agents covered
```

Correct display would show `5` for score_findings (quantitative-analyst, synthesizer-bl2, competitive-analyst, regulatory-researcher, research-analyst).

---

## Open Issues for Wave 17

1. **Agent name truncation bug in masonry-observe.js** (HIGH): `extractMarkdownField` regex `[\w]+` → `[\w-]+`. One-line fix. Blocks all routing training records for hyphenated agent names.

2. **Generate matched start+finding event pairs** (HIGH): Need a Mortar/Trowel campaign running from masonry/ directory to populate routing training data. Current NEVER STOP self-research loop (main process writes findings directly, no subagent spawns) cannot generate "start" events in the current session.

3. **score_findings "agents_covered" fix** (LOW): Add `agents_covered` key to `score_findings.run()` return dict. Fixes misleading "Agents: 1" in summary table.

4. **score_routing.py "sessions_matched" metric** (LOW): Replace `min(start_count, finding_count)` with actual pair count. Misleading as-is.

5. **BL1.x findings enrichment** (OUT OF SCOPE): 614 findings fail threshold due to missing confidence fields. Retroactive enrichment is not warranted — these are from a different toolchain and the rejection is correct.
