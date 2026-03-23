# Wave 17 Synthesis — DSPy Pipeline Fixes + Vigil Health Baseline

**Wave**: 17
**Status**: COMPLETE (4/4 questions DONE)
**Generated**: 2026-03-21

## Questions Answered

| ID | Verdict | Summary |
|----|---------|---------|
| F17.1 | FIX_APPLIED | extractMarkdownField regex `[\w]+` → `[\w-]+`; hyphenated agents (fix-implementer, research-analyst) now extract correctly from routing_log.jsonl |
| R17.1 | WARNING | F17.1 confirmed via routing_log.jsonl event; session ID mismatch is sole remaining blocker for routing training records |
| F17.2 | FIX_APPLIED | `score_findings.run()` now returns `agents_covered` list; summary shows "Agents: 5" (was "Agents: 1"); discovered 3 routing records at 70pts via score_all_agents.py |
| R17.2 | WARNING | Vigil HEALTHY from masonry/ dir; false Thorn for diagnose-analyst eliminated; but 86% of findings lack `**Agent**:` field — low-quality signal |

## Key Discoveries

### 1. Routing Pipeline State (After F17.1 + F16.1 Fixes)

The routing pipeline now has **3 training records** at 70pts (correct_agent_dispatched=70, downstream_success=0):
- mortar → karen (karen dispatched from f68d4e9c BL-root session)
- mortar → planner
- mortar → question-designer-bl2

These 3 records exist only when score_routing.py is called via score_all_agents.py (which injects sys.path). Standalone `python masonry/scripts/score_routing.py` still returns 0 records due to import path failure (uses minimal fallback AGENT_CATEGORIES missing karen/planner/question-designer-bl2).

The `downstream_success=0` (30pts not awarded) because no session has a matching start+finding pair yet — the NEVER STOP loop writes findings directly without spawning subagents.

### 2. Score All Agents Summary (Post-Fixes)

```
Scorer                          Records     Agents   Agents w/10+
------------------------------------------------------------------
score_findings                       61          5              1
score_code_agents                     4          2              0
score_ops_agents                    181          2              0
score_routing                         3          0              0
------------------------------------------------------------------
TOTAL                               249         10              2
Total merged records: 243
```

quantitative-analyst: 36 findings (≥10 threshold, ready for DSPy training).
synthesizer-bl2: 9 findings (1 below threshold).

### 3. Vigil Low-Quality Signal (R17.2)

The vigil correctly avoids false Thorns when run from masonry/ dir (no BL1.x contamination). However, 109/127 masonry findings have no `**Agent**:` metadata field — they all pool into "unknown" (pass_rate=0.89 → Rose). Per-agent classification requires `**Agent**:` field to be present, which only exists in the 7 findings from this session (Wave 16-17).

## Open Issues Carried to Wave 18

1. **Session ID mismatch** (R17.1): NEVER STOP loop doesn't spawn subagents per session → no start+finding pairs in the same session → routing records stay at 70pts. Resolution requires spawning specialist agents (Agent tool calls) to write findings.
2. **score_routing.py standalone import failure**: Low priority — score_routing always called via score_all_agents.py in practice.
3. **Vigil `**Agent**:` field gap**: 109 pre-Wave 16 findings lack `**Agent**:` → vigil provides no per-agent signal for those waves. Fix: add `**Agent**:` to finding template going forward (already adopted in this session).
4. **scored_all.jsonl path mismatch in vigil**: When CWD=masonry/, `load_scored_all` resolves to wrong path. Low priority.

## Training Data Health

- Total training records: 243 merged
- quantitative-analyst: 36 records (only agent with ≥10 → DSPy training ready)
- DSPy Phase 16 roadmap: full-fleet training requires most agents to reach 10+ records
- Routing training at 70pts max until session ID structure is fixed

## Next Wave Priorities

1. Investigate whether running specialist agents via Agent tool (rather than direct investigation) would generate matching session ID pairs and push routing records to 100pts
2. Audit whether the `**Agent**:` field should be retrofitted to pre-Wave 16 findings (bulk update)
3. Examine whether vigil's `MIN_FINDINGS_FOR_METRICS=5` threshold is appropriate for self-research mode
4. Validate the DSPy pipeline end-to-end with quantitative-analyst's 36 training records
