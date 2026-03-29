# Wave 2 Synthesis -- inline-execution-audit

**Date**: 2026-03-29
**Questions**: 23 total (14 Wave 1 + 9 Wave 2) -- 12 success, 6 partial (WARNING), 3 failure, 1 frontier, 1 monitor

| Category | Count | IDs |
|----------|-------|-----|
| FIXED | 3 | F2.1, F2.2, F2.3 |
| DIAGNOSIS_COMPLETE | 8 | D1.1, D1.2, D1.3, D2.1, D2.2, D2.3, D2.4, D2.5 |
| CONFIRMED | 1 | A1.1 |
| WARNING | 6 | D4.1, D5.1, D5.2, V1.1, R2.1, R2.2 |
| FAILURE | 3 | D3.1, D3.2, D4.2 |
| FRONTIER_PARTIAL | 1 | FR1.1 |
| MONITOR_SET | 1 | M2.1 |

---

## Executive Summary

Wave 1 mapped a five-layer root cause chain explaining why Claude defaults to inline execution instead of routing through Mortar. Wave 2 **fixed the top three layers** and **fully specified fixes for two more**, shifting the campaign from diagnosis to implementation.

### What Wave 2 Changed

1. **Escape hatch closed (F2.1)**: CLAUDE.md line 68 "direct action when trivial" replaced with an operational definition -- "single-sentence factual lookups only, no tool use, no multi-step reasoning." Cross-reference added at line 37. The specificity-beats-general override identified in D1.1 is now structurally prevented.

2. **Routing hint channel and format fixed (F2.2)**: masonry-prompt-router.js switched from `hookSpecificOutput` (annotation format, may not enter model context) to `additionalContext` (imperative format with enforcement consequence framing). The two structural reasons D1.3 identified for hints carrying no authority are both corrected.

3. **Five-prerequisite enforcement bundle deployed (F2.3)**: All five V1.1 prerequisites deployed atomically behind `MASONRY_ENFORCE_ROUTING=1`:
   - Bash added to Mortar's tool list (gate-exempt write path)
   - Receipt write instruction added to mortar.md (Bash one-liner stamps `mortar_consulted: true`)
   - Per-turn receipt reset added to masonry-prompt-router.js (`mortar_consulted: false` on every UserPromptSubmit)
   - Gate hardened in masonry-approver.js (deny when receipt missing, behind env flag)
   - File split to satisfy 300-line guard (masonry-approver-helpers.js extracted)

4. **Receipt writer deadlock solved (D2.3)**: The D2.2 recommendation ("add receipt writer to Mortar instructions") was structurally impossible -- Mortar has no Write/Edit tools. D2.3 identified the correct architecture: add Bash to Mortar's tool list and use a `node -e` one-liner (Bash is unconditionally exempt from the PreToolUse gate at line 294). F2.3 implemented this.

5. **Dark fleet activation path specified (D2.4)**: 61 agents have rich descriptions but no `routing_keywords`. Three-strategy auto-extraction (quoted phrases, description noun-phrases, body section parsing) covers ~70-80% with estimated 5-10% false-match rate against the current 86% dark-fleet baseline.

6. **Multi-turn persistence schema specified (D2.5)**: `last_route` schema for masonry-state.json with 5 fields (agent, effort, prompt_summary, timestamp, turn_count). 14 follow-up regex patterns covering 30+ surface forms. TTL of 10 minutes, max 5 inherited turns. Question-word filter and 30-char minimum mitigate false positives to ~5-10%.

7. **Trivial threshold boundary stress-tested (R2.1)**: The F2.1 "single-sentence factual lookup" definition is semantically correct but structurally mismatched with effort:low classifier (syntactic question-word anchors). At MASONRY_ENFORCE_ROUTING=1, 8-15% of conversational queries would experience over-delegation. Key discriminating feature: whether the response requires tool use, not sentence form.

8. **Spec+build INTENT_RULES patterns designed (R2.2)**: Patterns A+B+C are collision-free at ~75% coverage. Pattern D (architect+spec) has a hard collision with the architecture rule -- omit. Maintenance verb expansion (fix/update/set/change/configure) safe, ~40-60% build silent zone reduction.

9. **Monitor targets set (M2.1)**: silent-zone-hit-rate (WARNING >50%, FAILURE >60%) and multi-turn-routing-signal-rate (WARNING <20%, FAILURE <5%) calibrated to Wave 1 baselines.

---

## Updated Root Cause Chain

Wave 2 fixes are annotated on the original chain:

```
D1.1  CLAUDE.md escape hatch       --> [FIXED by F2.1] operational definition deployed
  |
  +-- D1.2  Context dilution (4.8%)  --> [OPEN] UI rules still loaded unconditionally
  |
  +-- D1.3  Wrong output channel     --> [FIXED by F2.2] additionalContext + imperative format
        |
        +-- D5.1/D5.2  40-60% silent zone --> [OPEN] maintenance verbs specified (R2.2) but not deployed
              |
              +-- D3.1  70% routing surface dark --> [OPEN] spec+build patterns ready (R2.2) but not deployed
              |
              +-- D3.2  Multi-turn collapse     --> [OPEN] last_route schema specified (D2.5) but not deployed
                    |
                    +-- A1.1  Zero enforcement   --> [FIXED by F2.3] gate hardened behind MASONRY_ENFORCE_ROUTING=1
                          |
                          +-- D2.1/D2.2  Receipt absent --> [FIXED by F2.3] receipt writer via Bash, per-turn reset
```

**Status after Wave 2**: 3 of 7 chain nodes fixed. 4 nodes have complete fix specifications but await implementation (D1.2, D5.1/D5.2, D3.1, D3.2). The enforcement path (bottom of chain) is now complete end-to-end.

---

## Critical Findings (must act)

1. **D3.1** [FAILURE, Wave 1] -- 70% routing surface dark or degraded; Spec+build has zero INTENT_RULES coverage
   Fix: Deploy patterns A+B+C from R2.2 + maintenance verb expansion. ~75% spec+build coverage, ~40-60% silent zone reduction. Implementation: 3 new INTENT_RULES entries + 1 regex modification in masonry-prompt-router.js.

2. **D4.2** [FAILURE, Wave 1] -- 86% of 114 agents are dark fleet with no routing path
   Fix: Run D2.4 three-part plan -- (1) backfill sync of 20 agents with existing frontmatter keywords, (2) auto-extract keywords for 61 agents via backfill script, (3) enrich semantic corpus. Implementation: `onboard_agent.py --resync` + new `backfill_routing_keywords.py` script.

3. **D3.2** [FAILURE, Wave 1] -- Router stateless per-prompt; multi-turn workflows collapse by Turn 2
   Fix: Deploy D2.5 last_route persistence + 14 follow-up regex patterns. Implementation: 3 additions to masonry-prompt-router.js (FOLLOWUP_PATTERNS array, isFollowUp function, inheritance logic between detectIntent and hasSignal).

---

## Significant Findings (important but not blocking)

1. **R2.1** [WARNING, Wave 2] -- Trivial threshold over-delegates 8-15% of question-form queries at MASONRY_ENFORCE_ROUTING=1
   Fix: Augment effort:low classifier with tool-use intent check, OR add explicit Read tool exemption in gate alongside existing Bash exemption.

2. **R2.2** [WARNING, Wave 2] -- Spec+build patterns A+B+C collision-free (~75% coverage); Pattern D hard collision (omit); maintenance verbs safe
   Fix: Ready to deploy. 3 new INTENT_RULES entries + 1 in-place modification. No architectural changes.

3. **D1.2** [DIAGNOSIS_COMPLETE, Wave 1] -- Routing signal 4.8% of 23K context; UI rules 12.9x volume
   Fix: Move 6 UI rules files to conditional load group. Requires verification of Claude Code subdirectory behavior.

4. **D5.1/D5.2** [WARNING, Wave 1] -- 40-60% of prompts in silent zone; "medium" effort is structural default with zero regex
   Fix: Covered by R2.2 maintenance verb expansion + D2.5 follow-up detection. No separate fix needed.

5. **V1.1** [WARNING, Wave 1] -- 5 prerequisites for enforcement deployment
   Status: All 5 prerequisites deployed by F2.3. V1.1 is now resolved -- enforcement is available behind `MASONRY_ENFORCE_ROUTING=1`.

---

## Healthy / Verified

- **F2.1** [FIXED]: CLAUDE.md escape hatch replaced with operational "single-sentence factual lookup" definition. Specificity-beats-general override prevented.
- **F2.2** [FIXED]: Prompt router output channel corrected to additionalContext; hint format is imperative with enforcement consequence.
- **F2.3** [FIXED]: Five-prerequisite enforcement bundle deployed atomically. Gate hardened behind env flag. Bash receipt writer solves D2.3 deadlock.
- **D2.3** [DIAGNOSIS_COMPLETE]: Receipt writer architecture fully specified and implemented in F2.3.
- **D2.4** [DIAGNOSIS_COMPLETE]: Dark fleet activation via auto-extracted routing_keywords fully specified with three-strategy approach.
- **D2.5** [DIAGNOSIS_COMPLETE]: Multi-turn persistence schema, 14 follow-up regexes, expiry logic, false-positive mitigations all specified.
- **M2.1** [MONITOR_SET]: Two monitor targets calibrated to Wave 1 baselines for post-deployment tracking.
- **D4.1** [WARNING, structurally healthy]: All 20 Mortar routing table agents have resolvable .md files.
- **FR1.1** [FRONTIER_PARTIAL]: Write/Edit deny-gate architecture confirmed viable. Text-generation gap is permanent platform constraint.
- **A1.1** [CONFIRMED, now resolved by F2.3]: Enforcement infrastructure activated behind env flag.

---

## Recommendation

**STOP**

All 23 questions across two waves are answered. The root cause chain is fully mapped and 3 of 7 nodes are fixed. The remaining 4 nodes have complete fix specifications with specific regex patterns, schemas, and code paths. The enforcement path (F2.1 + F2.2 + F2.3) is deployed and available behind `MASONRY_ENFORCE_ROUTING=1`. The next phase is implementation of the remaining fix specifications (D2.4 dark fleet backfill, D2.5 multi-turn persistence, R2.2 INTENT_RULES expansion), not further investigation.

---

## Next Wave Hypotheses (for future campaigns)

1. **Post-enforcement behavioral validation**: After enabling MASONRY_ENFORCE_ROUTING=1 in production, what is the actual false-positive rate? Does the R2.1 8-15% over-delegation estimate hold, or is it higher/lower with real developer prompts?

2. **Dark fleet activation quality**: After running D2.4 backfill, what is the false-match rate for auto-extracted routing_keywords? Which agents receive the most mis-routed prompts?

3. **Multi-turn persistence effectiveness**: After deploying D2.5 last_route + follow-up patterns, does the Turn 2+ signal gap close from 40-60% to the <20% WARNING threshold set in M2.1?

4. **Context dilution reduction**: After moving 6 UI rules to conditional load (D1.2), does routing compliance measurably improve in non-UI sessions?

5. **End-to-end routing compliance rate**: With all fixes deployed (F2.1-F2.3 + D2.4 + D2.5 + R2.2), what percentage of developer prompts are correctly routed through Mortar vs. executed inline?

---

## Cross-Domain Conflicts

1. **Trivial threshold vs. enforcement gate (R2.1 + F2.3)**: The effort:low classifier uses syntactic form; the CLAUDE.md definition uses semantic intent. At MASONRY_ENFORCE_ROUTING=1, question-form prompts requiring file reads are incorrectly blocked. Must resolve before widespread enforcement enablement.

2. **Dark fleet activation vs. routing noise (D2.4 + D4.2)**: Auto-extracted keywords at 5-10% false-match rate could flood Mortar with incorrect dispatches. Stage activation: high-value specialists first, campaign agents second, stubs last. Manual review of top 20 keywords post-extraction recommended.

3. **Campaign mode blackout (D3.2/D5.1)**: Line 187 early exit suppresses all routing during campaigns. D2.5 last_route persistence is unaffected (TTL expiry prevents stale inheritance). Removing the exit for non-campaign routing requires careful Trowel interaction testing.
