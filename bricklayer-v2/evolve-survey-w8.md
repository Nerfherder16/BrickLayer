# Evolve Wave 8 Survey — 2026-03-24

## Current State (post Wave 7)

| Agent | Score | Status |
|-------|-------|--------|
| karen | 1.00 (20/20) | AT TARGET |
| quantitative-analyst | 0.90 (18/20) | AT TARGET |
| regulatory-researcher | 1.00 (10/10) | AT TARGET |
| competitive-analyst | ~0.92 avg | AT TARGET |
| synthesizer-bl2 | ~0.67 avg (5 records, unstable) | UNSTABLE — needs 10+ records |
| research-analyst | ~0.45 avg (10 records) | IN PROGRESS — reasoning Qs→0.97, code-inspect→0.00 |

## Key Discoveries from Wave 7

1. **Question type determines JSON compliance** for research-analyst. Code-inspection
   questions trigger agentic behavior (file reads → prose output → 0.00 score). Reasoning
   questions produce reliable JSON (0.97). The remaining 15 records MUST use reasoning style.

2. **2-stage eval** was identified as PROMISING (E7.2-pilot-5): Stage 1 scores evidence
   quality for prose responses; Stage 2 scores verdict match for clean JSON. Would eliminate
   the binary 0.00 penalty on code-inspection records.

3. **synthesizer-bl2** variance is structurally caused by 5-record sample + 1 stochastic
   failure. Adding 5+ records from diverse campaign sessions would stabilize the baseline.

4. **masonry-guard.js** has a confirmed FAILURE-class bug: `hasErrorSignal()` scans the
   entire `JSON.stringify(response)` payload including `oldString`, causing 37 false-positive
   warnings across 7 production sessions.

## Wave 8 Candidate Questions

### Candidate A: 2-Stage Eval Implementation
- **Impact**: HIGH — would convert current 0.00 code-inspection scores to 0.2-0.4 range
- **Effort**: LOW — eval_agent.py change, ~20 lines
- **Verdict potential**: IMPROVEMENT (if score gain materializes) or WARNING (if no gain)
- **Priority**: HIGH — unlocks all code-inspection records as usable training data

### Candidate B: 8 More Reasoning-Style Research-Analyst Records
- **Impact**: HIGH — moving from 10→18 records with better distribution
- **Effort**: MEDIUM — 8 records × agent calls, same pattern as E7.2
- **Verdict potential**: IMPROVEMENT (score increase toward 0.85 target)
- **Priority**: HIGH — direct path to research-analyst AT TARGET

### Candidate C: Synthesizer-BL2 Record Expansion (5+ records)
- **Impact**: MEDIUM — stabilizes unstable baseline
- **Effort**: MEDIUM — extract from diverse campaign session findings
- **Verdict potential**: IMPROVEMENT (stable 1.00 on 10+ records)
- **Priority**: MEDIUM — blocks optimization until stable

### Candidate D: Fix masonry-guard.js hasErrorSignal() Scope
- **Impact**: MEDIUM — eliminates production false-positive warnings
- **Effort**: LOW — targeted fix to JSON.stringify scope
- **Verdict potential**: IMPROVEMENT (false positive rate → 0)
- **Priority**: MEDIUM — production quality fix

## Wave 8 Question Plan

Four questions targeting the two highest-ROI candidates first:

| ID | Question |
|----|----------|
| E8.1 | Implement 2-stage eval: does it raise research-analyst score from ~0.45? |
| E8.2 | Generate 8 more reasoning-style research-analyst records (topics: program.md design, campaign yield, agent routing decisions, synthesis quality) |
| E8.3 | Add 5 synthesizer-bl2 records from recall/masonry/bricklayer-meta campaigns — does score stabilize at ≥0.90? |
| E8.4 | Fix masonry-guard.js hasErrorSignal() to scope signal detection to newString content only — does false-positive rate drop to 0? |
