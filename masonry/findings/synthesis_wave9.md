# Wave 9 Synthesis — Masonry Self-Research Campaign

**Wave**: 9
**Questions answered**: 6 (F9.1, R9.1, D9.1, R9.2, V9.1, D9.2)
**Verdicts**: 3 HEALTHY/FIX_APPLIED, 2 WARNING, 1 HEALTHY

---

## Wave 9 Overview

Wave 9 completed the Phase 16 DSPy training data quality remediation chain and resolved the D7.1 drift-detection gap. Three infrastructure fixes across Waves 7-9 are now fully validated: `question_text` from actual questions (F8.1), per-finding `confidence` extraction (F8.1), and `project_context` from `project-brief.md` (F9.1). The `sync_verdicts_to_agent_db.py` script now populates verdict history for drift detection (D9.1). Two secondary structural issues were found: deterministic routing Rule 5 is broken for campaign questions (R9.2), and the `masonry-subagent-tracker.js` atomic write is intact (D9.2).

---

## Findings Summary

| QID | Verdict | Severity | Summary |
|-----|---------|----------|---------|
| F9.1 | FIX_APPLIED | High | `project-brief.md` injection complete — all 89 training examples have `project_context len: 2000` |
| R9.1 | HEALTHY | Info | `build_dataset()` produces 89 examples across 5 agents; 4 of 5 exceed 5-example minimum |
| D9.1 | FIX_APPLIED | High | `sync_verdicts_to_agent_db.py` writes 81 verdicts across 6 agents; garbage name filter works |
| R9.2 | WARNING | Medium | Deterministic Rule 5 (`**Mode**:`) never fires — regex mismatch with `**Operational Mode**:` format |
| V9.1 | HEALTHY | Info | `ResearchAgentSig.input_fields` is a plain dict in dspy 3.1.3; optimizer.py line 112 is correct |
| D9.2 | HEALTHY | Info | F5.3 atomic write confirmed in `masonry-subagent-tracker.js`; no reversion |

---

## Key Achievements This Wave

### 1. Phase 16 Training Pipeline Complete (F9.1 + R9.1)
All three DSPy `ResearchAgentSig` input fields are now populated with meaningful data:
- `question_text`: actual question text from `### QID: <text>` headers (F8.1)
- `confidence`: per-finding float from `**Confidence**:` field (F8.1)
- `project_context`: `project-brief.md` content (2000 chars) via `_load_project_brief()` (F9.1)

R9.1 confirmed the end-to-end pipeline produces 89 examples, 4/5 agents eligible for MIPROv2 optimization. DSPy training can now proceed.

### 2. Drift Detection Unblocked (D9.1)
`sync_verdicts_to_agent_db.py` resolves the D7.1 gap where `agent_db.json["verdicts"]` was always empty. The script:
- Runs against the full BL2.0 directory (multi-project scan)
- Filters garbage agent names via `^[a-z][a-z0-9-]*$` regex
- Writes atomically via `tmp.{pid} + Path.replace()`
- Currently writes 81 verdicts across 6 agents: benchmark-engineer, compliance-auditor, design-reviewer, diagnose-analyst, fix-implementer, research-analyst

### 3. Optimizer Infrastructure Confirmed Sound (V9.1)
dspy 3.1.3 exposes `Signature.input_fields` as a plain dict. The `type: ignore[attr-defined]` comment in optimizer.py line 112 is defensive but correct — the attribute exists at runtime. No silent fallback to unoptimized module will occur from this path.

---

## Open Issues Surfaced This Wave

### P2 — Deterministic Routing Rule 5 Broken (R9.2)
`_MODE_FIELD_RE = re.compile(r"\*\*Mode\*\*:\s*(\w+)")` does not match `**Operational Mode**:` (the actual format in questions.md). Rule 5 contributes ~0% coverage for campaign questions. Fix: extend regex to `r"\*\*(?:Operational\s+)?Mode\*\*:\s*(\w+)"`. The 60%+ coverage claim remains valid only for active campaign/build sessions (via Rules 2-3).

### P3 — `masonry-state.json` Write Still Non-Atomic (D9.2 → noted)
F5.3 intentionally left `masonry-state.json` with non-atomic `safeWrite`. This is acceptable for monitoring data, but if Rule 3 of the deterministic router ever relies on this file's `active_agent` field for correctness, a race condition could produce stale routing decisions. Low priority while Rule 3 is treated as best-effort.

---

## Cumulative Findings Across All Waves

| Domain | HEALTHY/FIX | WARNING | FAILURE | INCONCLUSIVE |
|--------|------------|---------|---------|--------------|
| Routing | 4 | 2 | 0 | 0 |
| Hooks | 5 | 1 | 0 | 0 |
| DSPy/Training | 6 | 1 | 0 | 0 |
| Drift Detection | 2 | 0 | 1→resolved | 0 |
| Concurrency | 2 | 2 | 0 | 0 |
| Schemas | 3 | 0 | 0 | 0 |

### Still-Open P1 Blockers
None. All P1 blockers resolved across Waves 6-9.

### Still-Open P2 Issues
- R9.2: Deterministic Rule 5 broken (`**Mode**:` vs `**Operational Mode**:`)
- D2.2: `masonry-state.json` non-atomic write (last-write-wins, monitoring only)

### Still-Open P3 Issues
- R6.1: `runBackground()` path-with-spaces on Windows (async process spawning)
- Observation: `sync_verdicts_to_agent_db.py` should be wired into the campaign loop (post-synthesis invocation) — not yet automated

---

## Next Wave Priorities

1. **Fix Rule 5 regex** (R9.2 → F10.1): Extend `_MODE_FIELD_RE` to match `**Operational Mode**:` — zero-LLM routing for campaign questions currently falls through to Layer 2/3
2. **Automate verdict sync** (D9.1 follow-up → R10.1): Wire `sync_verdicts_to_agent_db.py` into the synthesizer-bl2 or trowel wave-end workflow
3. **Live drift check validation** (D7.1 → R10.2): Now that verdicts are populated, run `masonry_drift_check` end-to-end and verify the output format is actionable
4. **End-to-end optimize run** (D8.1 → R10.3): Run `masonry_optimize_agent` for `diagnose-analyst` (28 examples) — the most data-rich agent — and verify the output `.json` is loadable by Kiln
5. **`runBackground()` Windows fix** (R6.1 → F10.2): Investigate path-with-spaces issue in async hook subprocess spawning on Windows
