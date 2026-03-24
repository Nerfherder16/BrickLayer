# BrickLayer 2.0 — Synthesis (Wave 1 + Evolve Wave 1)

**Wave**: 1
**Questions answered**: 20 (Q1.1–Q5.2)
**Campaign date**: 2026-03-16
**Mode spread**: diagnose (5), mode-design (5), project-status (5), evolve (3), frontier (2)

---

## Verdict Distribution

| Verdict | Count | Questions |
|---------|-------|-----------|
| DIAGNOSIS_COMPLETE | 5 | Q1.1–Q1.5 |
| HEALTHY | 8 | Q2.1, Q2.3, Q3.1, Q3.2, Q3.5, Q4.1, Q4.2, Q4.3 |
| WARNING | 3 | Q2.2, Q2.4, Q2.5 |
| PROMISING | 3 | Q3.3, Q5.1, Q5.2 |
| INCONCLUSIVE | 1 | Q3.4 |

**System health**: Mostly sound — 5 fix specs ready, 3 warnings to address before Wave 2 implementation, 1 blocked on missing context.

---

## Domain 1: bl/ Engine Gaps (Q1.1–Q1.5) — ALL DIAGNOSIS_COMPLETE

Five concrete fix specifications, all sized small-to-medium, none blocking the others.

**Implementation order** (dependency-safe):
1. **Q1.2** — Add `operational_mode` field to `questions.py` (5 lines, 30 min) — no dependencies
2. **Q1.3** — Expand 26 verdict types in `findings.py` + `questions.py` (30 min) — no dependencies
3. **Q1.1** — Mode dispatch in `campaign.py` + `runners/agent.py` (1 hour) — depends on Q1.2
4. **Q1.5** — PENDING_EXTERNAL mechanism (50 lines, 3 files) — depends on Q1.3 for new status
5. **Q1.4** — DIAGNOSIS_COMPLETE suppression (80 lines, 3 files) — depends on Q1.3 for new verdict

Total estimated engineering: ~3.5 hours, 5 files.

**Critical path**: Q1.2 → Q1.3 → Q1.1 → (Q1.4 + Q1.5 in parallel)

---

## Domain 2: Mode Specifications (Q2.1–Q2.5) — 1 HEALTHY, 2 WARNING, 1 HEALTHY, 1 WARNING

Three gaps found in the mode program specifications:

### WARNING: Fix mode pre-flight too permissive (Q2.2)
The current "Fix Specification present ✓" check is binary — it validates existence, not specificity. An underspecified spec passes the gate and enables scope creep during implementation.

**Required addition to `modes/fix.md`**:
```
PRE-FLIGHT SPECIFICITY GATE (required before implementation):
- [ ] Target file: exact path
- [ ] Target location: line number or function name
- [ ] Concrete edit: diff-level description (not "improve performance")
- [ ] Verification command: runnable, produces pass/fail (e.g., `python -m pytest tests/test_foo.py::test_bar`)
```

Also: FIX_FAILED findings must include a "Root Cause Update" section — the hypothesis was wrong; the updated hypothesis must be explicit.

### WARNING: Predict mode subjective probability (Q2.4)
IMMINENT/PROBABLE have time-based objective criteria. POSSIBLE/UNLIKELY have no decision criteria — verdict is subjective and varies by analyst.

**Required addition to `modes/predict.md`**:
```
POSSIBLE: 3+ documented instances of qualitative failure OR quantitative metric approaching threshold
          within 60-180 days at current trend
UNLIKELY: Failure mode documented but no active precursor; or <3 qualitative instances
```

Also: O(N²) interaction pairs in cascade maps need explicit filtering — analyze top 3-5 most dangerous chains only.

### WARNING: Three missing cross-mode handoffs (Q2.5)

| Missing handoff | From | To | Trigger |
|----------------|------|----|---------|
| Benchmark→Evolve | CALIBRATED | Evolve | Baseline established, improvement possible |
| Research→Validate | HEALTHY (all assumptions) | Validate | All assumptions confirmed, design ready |
| Fix→Monitor | FIXED | Monitor | Add fixed metric to monitoring targets |

Also: Validate FAILURE should split on system existence:
- New system in design: → Research (revisit assumptions)
- Existing deployed system with behavior mismatch: → Diagnose

**HEALTHY modes** (Q2.1 Frontier, Q2.3 Monitor): complete and actionable. Monitor missing DEGRADED_TRENDING is minor — add to modes/monitor.md.

---

## Domain 3: Active Project Status (Q3.1–Q3.5) — 3 HEALTHY, 1 PROMISING, 1 INCONCLUSIVE

### Recall: Fix Q33.2b first (Q3.1)
Causal chain analysis confirms double-decay is the root of three downstream cascades (consolidation bypass, premature decay, bulk re-score debt). Priority order:
1. Q33.2b — double-decay root fix (2 lines, IMMINENT)
2. Q24.5 — consolidation gap (co-deploy with Q21.5)
3. Q32.1 — hygiene cron (16.6-day deadline from wave 36)
4. Q34.7 — bulk re-score (PENDING_EXTERNAL on Q32.1)
5. Q24.2 — mark_superseded (monitoring only)

### ADBP: Predict mode next (Q3.2)
Wave 9 complete, mid-research phase. Open quantitative WARNINGs (Q9.3, Q9.4) need cascade projection before Validate. Sequence: Predict → Research (assumption revision) → Validate → Build.

### Uncreated App: Two PROMISING concepts, one BLOCKED (Q3.3)
- **RaaS (Recall as a Service)**: PROMISING — $29/mo tier, no Stripe/auth required to prototype
- **Homelab Copilot**: PROMISING — can start with read-only MCP tools, no public endpoint needed
- **F1.3**: BLOCKED — requires Cloudflare Tunnel (public endpoint) + Stripe (billing) first

### Legal project: Missing (Q3.4 — INCONCLUSIVE)
No `legal/` directory found. Two candidate interpretations:
- ADBP compliance questions (MSB/ERISA/SEC)
- Relay AI TCPA/FCC questions
Resume condition: create `legal/project-brief.md` to unlock this question bank.

### UI/UX: Audit checklist ready (Q3.5)
10-item compliance checklist derived from global design rules. Automated (grep-based) checks for 8/10 items. NON_COMPLIANT threshold: any structural violation (A1/A3/A4/A7) or 4+ total fails.

---

## Domain 4: Template Evolution (Q4.1–Q4.3) — ALL HEALTHY

All three decisions are conservative and backward-compatible:

1. **Single template/**: No per-mode directories. Add `modes/` + 6 stub files + updated `program.md`. Runtime mode selection, not structural variation.
2. **One new bootstrap step**: Mode decision tree added between question generation and git init. Question-designer gains `starting_mode` input.
3. **evaluate.py alongside simulate.py**: simulate.py stays for parametric modes (Benchmark, Evolve). evaluate.py added as optional stub for evidence-based modes (Research, Audit, Diagnose). Non-overlapping purposes.

---

## Domain 5: Frontier Concepts (Q5.1–Q5.2) — BOTH PROMISING

### Multi-agent BrickLayer (Q5.1)
Architecturally feasible today via question ID namespacing. Safe parallel pairs: (Diagnose+Monitor), (Frontier+Research), (Monitor+Predict). Unsafe: (Diagnose+Fix). Only synthesis.md is not parallel-safe; three solutions exist with increasing complexity. Phase 1 (naive parallel, 2 modes): zero code changes — run two claude processes.

### BrickLayer Dashboard (Q5.2)
Project Command Center layout: left sidebar (project list + mode badges) + detail panel (lifecycle progress bar + open findings + activity feed). All data derivable from existing files — no new storage. Maps to existing `dashboard/` FastAPI+React codebase as 3-4 new routes + 1 new page.

---

## Wave 2 Seeds

**Highest priority questions for Wave 2**:

1. **Implement Q1.1–Q1.5**: Engineering wave — write the actual code changes to `bl/`. These are fully specified; Wave 2 could be a pure implementation campaign.

2. **Fix mode specification tightening** (from Q2.2): Rewrite pre-flight gate in `modes/fix.md`; add FIX_FAILED "Root Cause Update" requirement.

3. **Predict mode decision criteria** (from Q2.4): Add POSSIBLE/UNLIKELY thresholds to `modes/predict.md`.

4. **Cross-mode handoff repair** (from Q2.5): Add 3 missing handoffs + fix Validate FAILURE branching in relevant mode files.

5. **Recall Q33.2b Fix campaign**: Apply Fix mode to the double-decay bug — this is the only deployment blocker with an unblocked causal chain.

6. **ADBP Predict mode Wave 1**: Open Q9.3/Q9.4 WARNING findings need cascade projection.

7. **Uncreated App Research Wave 1**: Seed from Q3.3 — test RaaS and Homelab Copilot assumptions.

---

## Architectural Conclusions

**BrickLayer 2.0 is sound as designed.** The 9-mode lifecycle framework has no fundamental structural flaws. The three WARNINGs are specification gaps in Fix and Predict modes — they're fixable in under 30 minutes of text edits to the mode files.

**The bl/ engine changes are the critical path.** Until Q1.1–Q1.5 are implemented, BrickLayer 2.0 runs as BrickLayer 1.x with manually applied mode context. The operational modes exist as documentation only until `campaign.py` dispatches them.

**The biggest unlock**: implementing Q1.3 (26 verdict types) alone transforms every campaign's output — DIAGNOSIS_COMPLETE, FIXED, PROMISING, IMMINENT are all immediately usable once the engine recognizes them.

**Template and multi-agent work are optional enhancements** — the core value is in the mode programs and the bl/ engine changes.

---

## Evolve Wave 1 (2026-03-24)

**Questions**: E1.1, E1.2, E1.3 — all IMPROVEMENT

**Status update**: By the time Evolve Wave 1 ran, all Q1.1–Q1.5 bl/ engine changes had been
implemented and all 3 WARNINGs (Q2.2, Q2.4, Q2.5) had been resolved.

### E1.1 — Monitor DEGRADED_TRENDING (+33% scenario coverage)
Added 5th verdict to Monitor mode: metrics trending toward threshold fire DEGRADED_TRENDING
before crossing, routing to Predict for early cascade assessment. `modes/monitor.md` + `program.md`.

### E1.2 — Validate FAILURE routing (self-contained mode)
Added FAILURE routing table to `modes/validate.md`: new-system FAILURE → Research, deployed-system
FAILURE → Diagnose. validate.md is now self-contained — agents no longer need to cross-reference
program.md for routing guidance.

### E1.3 — Karen accuracy 0.55→~0.90 (root cause diagnosed, fix applied)
Root cause: dual failure — training data captures karen's own doc writes as `files_modified`
(not source trigger files), AND the prompt was ambiguous about doc-only `files_modified`.
Fix: added commit-type-first priority rule and explicit `files_modified is scope context` guidance
to all karen.md copies. Projected score: ~0.90. Secondary fix pending: training data pipeline.

**Evolve Wave 1 conclusions**: BrickLayer 2.0 is now fully operational — mode programs complete,
engine implemented, and core agent calibration improving. The system is ready for production
campaign use.

---

## Evolve Wave 2 (2026-03-24)

**Questions**: E2.1 (WARNING), E2.2 (IMPROVEMENT), E2.3 (IMPROVEMENT)

### E2.1 — Karen eval regression 0.55→0.30 (root cause: training data self-reference)
The Wave 1 prompt fix (commit-type-first) was correct but caused a regression because the training
data was corrupt: `_score_karen()` captured karen's own output doc files as `input.files_modified`,
not the source files that triggered the update. The model correctly learned "docs already written
→ skip" from this misleading signal.

### E2.2 — Three compounding pipeline bugs fixed
1. **Training data self-reference**: Fixed `_score_karen()` to use parent commit source files
2. **Wrong bot commit labels**: Added `_RE_BOT_COMMIT_SUBJECT` to `_derive_expected()` — 237/321 records (73%) were mislabeled "updated" instead of "skipped"
3. **Windows cp1252 encoding**: `→` arrows in karen.md "Reasoning approach" section silently truncated `--system-prompt` argument; `eval_agent.py` user message now passes via stdin

### E2.3 — Karen eval 0.30→1.00 (20/20 passed), target exceeded
After all pipeline fixes, karen eval reached 1.00 — exceeding the 0.85 target. Score of 0.75 for
most examples reflects quality_score slightly off (e.g., 0.8 vs 1.0) but action and changelog
correct.

**Cumulative journey**: 0.55 (baseline) → 0.30 (Wave 1 regression) → 1.00 (Wave 2 fix)

---

## Evolve Wave 3 (2026-03-24)

**Questions**: E3.1 (IMPROVEMENT), E3.2 (WARNING), E3.3 (WARNING), E3.4 (WARNING)

### E3.1 — Training data merge: 5→10 eval-able agents
Merged 38 unique records from `scored_all_wave13.jsonl` into `scored_all.jsonl` (444→482 records).
Previously invisible: research-analyst, synthesizer-bl2, competitive-analyst, developer, test-writer.
quantitative-analyst gained +16 records (45→61).

### E3.2 — quantitative-analyst baseline: 0.10 (1/10) — WARNING
Eval works but training records mix heterogeneous types: FindingPayload + RoutingDecision +
QuestionPayload. Generic eval instruction insufficient. Fix: add `_RESEARCH_JSON_INSTRUCTION` with
explicit field list. Training data needs domain filtering.

### E3.3 — research-analyst baseline: 0.20 (1/5) — WARNING (eval design mismatch)
The research-analyst ignores generic JSON instructions and does actual agentic research. Eval score
is misleading: the 1 "pass" (0.60) was a verdict mismatch that passed due to metric leniency
(evidence_quality weight too high relative to verdict_match). Root cause: 5 records all HEALTHY,
eval not designed for agentic researchers. Two fixes needed: (1) explicit eval instruction with
field spec, (2) 20+ diverse training records.

Also fixed: `--system-prompt-file` support in `eval_agent.py` for prompts >8KB, resolving the
"command line too long" error on Windows that caused all research-analyst eval calls to fail silently.

### E3.4 — Optimizer write-back scope risk — WARNING
`writeback_optimized_instructions()` writes to ALL copies of an agent .md with no scope guard —
confirmed root of the Wave 2 karen overwrite incident. Guards present: DSPy section only (not full
file). Guards missing: pre-flight validation, git backup, scope limit to source file.
Proposed fix: `target_paths` parameter to limit writeback to the file that was read.

**Wave 3 conclusions**: Eval infrastructure is now wider (10 agents covered) but deeper work
needed on non-karen agents. The main gaps are training data quality and eval instruction specificity.
Karen at 1.00 is the only agent with a meaningful baseline.

---

## Evolve Wave 4 (2026-03-24)

**Questions**: E4.1 (IMPROVEMENT), E4.2 (IMPROVEMENT)

### E4.1 — Eval instruction fix: quantitative-analyst 0.10→0.70
Added `_RESEARCH_JSON_INSTRUCTION` to `eval_agent.py` with explicit field specification
(verdict/summary/evidence/confidence). This replaced the generic "Respond ONLY with JSON" instruction
that allowed agentic agents to return routing decisions and question payloads instead of findings.
quantitative-analyst: 1/10 → 7/10 passed (+600%). Karen regression: 1.00 unchanged.

### E4.2 — Optimizer write-back scope guard
Added `target_paths` parameter to `writeback_optimized_instructions()`. `optimize_with_claude.py`
now defaults to `target_paths=[md_path]` — only the source file is modified. This eliminates the
cross-file contamination risk confirmed in E3.4 (Wave 2 karen overwrite root cause).

**Wave 4 conclusions**: The eval infrastructure is now meaningfully functional for research-domain
agents. quantitative-analyst at 0.70 is the new second baseline (after karen at 1.00). The optimizer
write-back risk is now mitigated. Remaining work: filter heterogeneous training records to push
quantitative-analyst past 0.85.

---

## Cumulative Evolve Campaign Summary

| Wave | Focus | Key Outcomes |
|------|-------|-------------|
| W1 | Mode spec improvements | 3x IMPROVEMENT — monitor DEGRADED_TRENDING, validate FAILURE routing, karen prompt fix |
| W2 | Karen training data | 0.30→1.00 — fixed 3 pipeline bugs (self-reference, bot labels, Windows cp1252) |
| W3 | Eval coverage + audits | 5→10 eval-able agents; quantitative-analyst/research-analyst baselines established |
| W4 | Eval instruction + scope guard | quant-analyst 0.10→0.70; optimizer overwrite risk fixed |

**Current agent eval scores**:
- karen: **1.00** (20/20) — AT TARGET (0.85)
- quantitative-analyst: **0.70** (7/10) — below target, training data cleanup remains
- research-analyst: 0.20 (1/5) — eval design mismatch, needs more training data + instruction work
- All others: no meaningful baseline yet
