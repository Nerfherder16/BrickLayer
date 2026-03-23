# Wave 19 Synthesis — Masonry Self-Research

**Wave**: 19
**Status**: COMPLETE (4/4 questions DONE)
**Date**: 2026-03-21
**Questions**: 4 total -- 1 success (FIX_APPLIED), 1 diagnosis, 2 warnings

## Questions Answered

| ID | Verdict | Summary |
|----|---------|---------|
| D19.1 | DIAGNOSIS_COMPLETE | OVERCONFIDENT_PASS_RATE=0.95 produces false Thorn classifications -- root cause is confidence-based pass_rate (trivially 1.00) used instead of rubric-based scored_all percentages |
| F19.1 | FIX_APPLIED | Vigil: overlay scored_all rubric% onto findings-dir metrics, gate OVERCONFIDENT check on rubric_based flag. score_all_agents: populate agents_covered from dispatched_agent field |
| R19.1 | WARNING | 100pt routing records at 60% reliability (3/5 dispatches) -- session_id collision in scorer causes last-write-wins; fix-implementer/general-purpose missing from AGENT_CATEGORIES |
| R19.2 | WARNING | score_findings.py CAN be extended to masonry findings after 3 fixes (exclusion removal, regex fix for ### subsections, FIX_APPLIED in VALID_VERDICTS); domain contamination risk requires source-tagging |

## Key Milestones This Wave

### 1. Vigil Calibration Fixed (D19.1 + F19.1)

The most impactful fix this wave. Four self-research agents (diagnose-analyst, fix-implementer, design-reviewer, research-analyst) were falsely classified as Thorns because `run_vigil.py` used `confidence >= 0.70` pass_rate as a quality proxy -- a trivially low bar that every competent finding clears (pass_rate=1.00 for all agents). The fix overlays rubric-based percentages from `scored_all.jsonl` when available, and gates the OVERCONFIDENT check on a `rubric_based=True` flag so confidence-only agents are not penalized.

**Before**: Verdict CRITICAL, 5 Thorns (4 false), 5 Roses, 4 Buds
**After**: Verdict WARNING, 1 Thorn (genuine: `unknown`), 7 Roses, 6 Buds

This resolves Wave 18 open issue #1 (OVERCONFIDENT_PASS_RATE miscalibration) and #4 (score_routing agents_covered empty). The vigil now produces actionable fleet health assessments.

### 2. Routing Training Data at 60% Reliability (R19.1)

Agent tool dispatch does generate 100pt routing records, but structural flaws prevent reliable scaling:
- **Session_id collision**: All Wave 18+ agents share one session_id (315da739). `score_routing.py` maps start-to-finding via a flat dict keyed by session_id, so last-write-wins -- every agent in a wave gets matched to the same finding.
- **Missing AGENT_CATEGORIES**: `fix-implementer` and `general-purpose` are absent from the category lookup, producing no scored record or a zero-downstream-success record.
- **Orphaned findings**: 3 finding events have no corresponding start event (D18.1, F18.1, F19.1_fix), indicating SubagentStart hook coverage gaps.

Current rate: 3/5 completed dispatches produce 100pt records. The session_id matching design needs per-agent unique identifiers before this rate can reach 100%.

### 3. Masonry Findings Scorable With Three Changes (R19.2)

`score_findings.py` explicitly excludes `masonry/` from discovery (line 282 blocklist). Beyond the exclusion, two structural mismatches prevent meaningful scoring:
1. The `## Evidence` section regex stops at `###` subsection headers (71 of 137 findings affected -- evidence_quality=0)
2. `FIX_APPLIED` and `COMPLETE` are not in VALID_VERDICTS (38 fix-implementer findings penalized)

Three targeted changes would raise the pass rate from 14.6% (20/137) to an estimated 90%+ (105-115/137), producing training records for research-analyst (43), fix-implementer (38), diagnose-analyst (29), and design-reviewer (9). The primary risk is domain contamination if masonry self-research records are merged with ADBP campaign records without source tagging.

## Open Issues for Wave 20

1. **score_routing session_id collision** (R19.1) -- `_match_events` uses a flat dict keyed by session_id. All agents in a wave share one session, causing last-write-wins. Fix: use composite key `(session_id, agent_name)` or assign per-dispatch unique IDs.

2. **Missing AGENT_CATEGORIES entries** (R19.1) -- `fix-implementer` and `general-purpose` are absent from `score_routing.py` AGENT_CATEGORIES. These agents produce start events but no scored records.

3. **score_findings.py masonry extension** (R19.2) -- Three changes needed: (a) remove "masonry" from discovery blocklist, (b) fix `_extract_section` regex to not stop at `###` subsections, (c) add `FIX_APPLIED`/`COMPLETE` to VALID_VERDICTS. Requires source-tagging to avoid ADBP training data contamination.

4. **Vigil CWD path** (carried from Wave 18) -- Vigil writes proposals.json to `masonry/masonry/vigil/` instead of `masonry/vigil/` when run from masonry/ directory.

5. **DSPy trial blockers** (carried from Wave 18) -- ANTHROPIC_API_KEY not set; Ollama at 192.168.50.62:11434 is the viable alternative. All 36 QA training records score exactly 60 (floor value).

## Training Data Health (End of Wave 19)

- Total training records: ~254 (from score_all_agents)
- quantitative-analyst: 36 records (only agent with 10+)
- Routing records: 7 total (3 at 100pts, 1 at 70pts, 3 legacy)
- score_routing agents_covered: 6 (fixed from 0 in F19.1)
- Masonry findings scorable: 105-115 estimated after R19.2 changes (currently 20/137 pass)
- DSPy optimization: blocked (no API key), not urgent

## Recommendation

**CONTINUE**

The vigil calibration fix (D19.1/F19.1) was the highest-priority item and is now resolved. Two clear next-wave targets remain: (1) fix score_routing session_id collision to achieve reliable 100pt record generation, and (2) implement the three score_findings.py changes to unlock 100+ masonry training records. Both are well-scoped with concrete fix specifications from this wave's findings.
