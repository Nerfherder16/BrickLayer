# Campaign Retrospective — hook-audit

**Date**: 2026-03-29
**Campaign**: Masonry hook stack audit (hook-audit)
**Scope**: 35 questions across Wave 1 (16 original + 7 follow-up/wave-mid = 23 total), Wave 2 (8 fix verifications)
**Overall Score**: 0.77 (Good)

---

## Process Scores

| Dimension | Score | Notes |
|---|---|---|
| Tool Friction | 0.97 | No subprocess errors, no Unicode failures, no re-runs without root fix. One structural note: W2D1.4 discovered a Wave-2 fix was itself incomplete, but that is verification working correctly — not friction. |
| Sweep Efficiency | N/A | Pure code-audit campaign; no simulation sweeps. Agents used direct file reads with line-level citations throughout. Effective execution for the domain. |
| Finding Quality | 0.75 | No confidence scores in finding frontmatter (template field absent from all 35 findings). Compensated by: line-number evidence in every finding, peer review blocks on all 3 highest-severity FAILUREs (D1.3, A1.3, D1.3-FU1) with independent code trace confirmation, and explicit verdict rationale sections citing H0/H1 outcomes. Evidence quality is high; only the missing numeric confidence field reduces this score. |
| Question Coverage | 0.70 | 35/35 questions DONE (1.0 completion rate). No pre-flight.md present, so the +0.3 pre-flight bonus does not apply. Base score: (35/35) × 0.7 = 0.70. The absence of pre-flight was a real gap: four follow-up questions (D1.3-FU1, D1.3-FU2, A1.3-FU1, A1.3-FU2) were reactive discoveries that a pre-flight pass would have anticipated as sub-hypotheses. |

**Composite score**: 0.77 (sweep efficiency excluded as non-applicable; three-dimension average with modest penalty for missing pre-flight and absent confidence scoring).

---

## Content Integrity

### Verdict Distribution

| Verdict | Count | Percentage |
|---|---|---|
| HEALTHY | 19 | 54% |
| WARNING | 10 | 29% |
| FAILURE | 4 | 11% |
| INCONCLUSIVE | 0 | 0% |

**Status: PASS.** Distribution is healthy and well-spread. No single bucket dominates. Zero INCONCLUSIVE verdicts confirm agents could evaluate every question with the available source code.

**Minor discrepancy**: The synthesis header states "3 failure" but results.tsv contains 4 FAILURE rows (D1.3, D1.3-FU1, A1.3, WM1.1). D1.3-FU1 was rated FAILURE in results.tsv because hook-runner.exe having zero template injection capability is a definitive structural defect. The synthesis merged it with D1.3's root-cause narrative. Both treatments are defensible; the inconsistency between results.tsv and synthesis.md is visible and worth resolving in future campaigns.

### Finding Consistency

**Status: PASS.** No contradictions found across the 35 findings. Notably:

- R1.4 found "no duplicate retrieval" and correctly attributed this to the A1.3 domain bug. Post-A1.3 fix, both summaries now land in the correct domain. R1.4 explicitly documented the post-fix risk — not a contradiction, correct reasoning about state before and after the fix.
- V1.1 flagged the mtime fallback as a cross-session imprecision risk. FR1.1 later enumerated the full session-ID-absent cascade — complementary, not contradictory.
- WM1.2 (HEALTHY: stop_hook_active is a per-invocation stdin boolean) correctly rules out the cold-start pollution scenario. Consistent with how D1.1, D1.2, and A1.1 describe stop_hook_active throughout Wave 1.

### Question–Finding Alignment

| Finding | Question focus | Alignment |
|---|---|---|
| D1.3 | Was session_id ever passed via argv? | ALIGNED |
| D1.3-FU1 | Does hook-runner.exe support template injection? | ALIGNED |
| A1.3 | Do domain maps match between write/read hooks? | ALIGNED |
| WM1.1 | Can concurrent sessions corrupt masonry-state.json? | ALIGNED |
| W2D1.4 | Is the ppid fallback stable across session lifetime? | ALIGNED (revealed a gap in the fix, not a misalignment with the question) |
| R1.4 | Are there duplicate session summaries in Recall? | ALIGNED — includes post-fix analysis |
| A1.3-FU1 | Are wrong-domain orphans benign? | ALIGNED |
| All remaining | — | ALIGNED |

**Status: PASS.** All 35 findings address their stated question. No misaligned or substituted questions observed.

### Confidence Calibration

**Status: WARN.** Confidence scores are absent from finding frontmatter across all 35 findings. The standard BL2 finding template includes a `confidence` field, but the hook-audit finding template omits it. Qualitative calibration appears sound: FAILURE verdicts carry exhaustive evidence, HEALTHY verdicts are direct, WARNING verdicts include specific mitigations. The absence of a numeric confidence field is a template gap, not an agent reasoning failure.

**Recommendation**: Add `confidence: 0.0–1.0` to the hook-audit finding template for future audit campaigns.

---

## False Positive / False Negative Analysis

### False Positives

**None confirmed.** All four FAILURE findings were independently verified by peer review and fixed by code changes subsequently confirmed in Wave 2. The one borderline case: A1.4 (masonry-ui-compose-guard.js missing BL silence guard) was rated WARNING. Risk was real; WARNING was appropriate.

### False Negatives

**One confirmed**: W2D1.4 discovered that the D1.4 fix was incomplete — masonry-session-start.js added the `session-${process.ppid}` fallback, but masonry-stop-guard.js was not updated to match. The snap file written by session-start was therefore never found by stop-guard when session_id was absent. D1.4 correctly identified the risk and recommended a ppid-based fallback but did not verify that the fix needed to be applied consistently to both hooks. Wave 2 caught the gap; post-finding patch applied same-day.

**Potential false negative (unconfirmed)**: R1.4 found "no duplication concern" but noted the post-A1.3 fix scenario where both session summaries land in the correct domain could exceed the context budget. This risk was not verified against actual Recall retrieval token counts — a known unknown that should be checked after A1.3 deployment.

---

## Wave 2 Verification Accuracy

| W2 Finding | Wave 1 defect | Fix verified? | Any new issues? |
|---|---|---|---|
| W2D1.1 | D1.3 (handoff argv) | Yes | Residual 'unknown' fallback if stdin parse fails (acceptable) |
| W2A1.1 | A1.3 (domain mismatch) | Yes | 57 orphaned memories already remigrated |
| W2WM1.1 | WM1.1 (non-atomic writeState) | Yes | Minor: orphaned .tmp.{pid} files on crash (cosmetic) |
| W2R1.2 | R1.2 (spawnSync blocking) | Yes | None |
| W2R1.3 | R1.3 (analytics from subdir) | Yes | None |
| W2A1.4 | A1.4 (missing BL guard) | Yes | Style difference only (inline vs top-level requires) |
| W2D1.4 | D1.4 (mtime fallback) | Partial | Post-finding patch applied: stop-guard now uses session-${process.ppid||null} |
| W2R1.1 | R1.1 (dead guard flush) | Yes | Dead file reference confirmed absent |

Wave 2 accuracy: 7/8 fixes fully confirmed, 1/8 flagged an incomplete fix. The W2D1.4 catch is a verification success — catching a partial fix is exactly what Wave 2 is for.

**Structural lesson**: When a fix spans two hooks, Wave 2 must verify both hooks. Future fix recommendations should include an explicit "files to change" list enumerating every file requiring a change and why.

---

## Agent Tooling Gaps

### What Was Unavailable

1. **No confidence field in finding template.** All 35 findings omit a numeric confidence score. Project-local template gap — not a framework defect.

2. **No pre-flight.md.** Question bank generated without a formal pre-flight pass. Consequence: four reactive follow-up questions generated mid-campaign. A pre-flight pass would have predicted most of them as sub-hypotheses.

3. **No cross-file diff tool.** Several findings required side-by-side comparison of domain tables across three or four files (A1.3, A1.3-FU2, WD1.2). Agents read each file separately and mentally compared. A diff-table utility would reduce the chance of missed entries.

### Where Agents Improvised

1. **Peer review blocks**: Three highest-severity FAILURE findings include a `## Peer Review` block that was not part of the standard finding template. Improvised but effective.

2. **W2D1.4 post-finding patch**: The finding identified an incomplete fix and a code patch was applied within the same session — outside the standard retro-actions → /retro-apply pipeline. The patch is correct, but it bypassed the normal review cycle.

3. **D1.3-FU1 FAILURE classification**: Classified as FAILURE in results.tsv but merged into D1.3 in synthesis. Both treatments are defensible; the inconsistency is visible.

### What Worked Well

- Hypothesis-driven question structure (H0/H1/prediction/success criterion) produced unambiguous verdicts on all 35 questions. Zero INCONCLUSIVE results.
- Wave 2 adversarial verification caught one incomplete fix that would have left a residual gap.
- Follow-up question generation from findings' "Suggested Follow-ups" sections closed the loop cleanly — every suggested follow-up was actually pursued.
- A1.3-FU1 surfaced a past incident (v3.0.1 timestamp in remigrate source) invisible before the campaign, confirming the defect class had occurred before.
- D1.3-FU1 clarified why the argv-based session_id was architecturally impossible to fix via configuration, eliminating a class of proposed quick fixes.

---

## Issues by Severity

### HIGH

**[RETRO-H1] Confidence field absent from all audit-mode findings**
- Severity: HIGH · Universality: PROJECT
- Fix: Add `confidence: 0.0–1.0` to the hook-audit finding template.

**[RETRO-H2] Pre-flight.md not produced before Wave 1 question bank**
- Severity: HIGH · Universality: PROJECT
- Fix: For future audit campaigns, produce a pre-flight.md after the question designer runs, explicitly testing whether each question's H0/H1 prediction is plausible given a quick read of the relevant source.

**[RETRO-H3] Fix recommendations must enumerate all affected files**
- Severity: HIGH · Universality: UNIVERSAL
- Surface symptom: D1.4's mitigation described adding a ppid fallback but did not list both hooks requiring the change. Fix applied to session-start only. Wave 2 caught the gap.
- Proposed action: Add a "Files to change" subsection to the mitigation recommendation template. Each entry: filename + specific change + why it is required.

### MEDIUM

**[RETRO-M1] results.tsv FAILURE count inconsistent with synthesis FAILURE count**
- Severity: MEDIUM · Universality: HYBRID
- Fix: Add a classification rule to program.md: "Follow-up questions that share the same root cause and the same fix as a parent finding should be recorded as CONFIRM rather than FAILURE in results.tsv."

**[RETRO-M2] R1.4 post-A1.3 context budget risk not closed**
- Severity: MEDIUM · Universality: PROJECT
- Fix: After A1.3 deployment, run a verification query against the Recall API to confirm both session summaries are retrievable and within token budget.

**[RETRO-M3] Peer review blocks improvised rather than templated**
- Severity: MEDIUM · Universality: HYBRID
- Fix: Add a peer review requirement to the finding template for FAILURE findings. Enforce by agent instructions.

---

## Recommended Workflow Tools

- **Pre-flight scan agent step**: Before Wave 1, run a lightweight pre-flight agent that reads each question's target files and assesses whether the H1 hypothesis is likely. Produces a pre-flight.md with null-gate candidates (deprioritize) and high-risk candidates (prioritize). Pays off for any audit campaign with more than 12 questions.
- **Cross-file comparison table utility**: For questions requiring side-by-side comparison of domain maps or config tables across multiple files, a utility producing a diff table would reduce manual comparison errors.
- **Post-campaign Recall rehydration check**: After a fix that changes what memories are retrievable (like A1.3), run a verification query to confirm previously invisible memories are now accessible.

---

*Retrospective generated by retrospective agent — 2026-03-29*
*Campaign branch: hook-audit/mar29*
