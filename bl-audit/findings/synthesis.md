# Wave 3 Synthesis -- bl-audit

**Date**: 2026-03-22
**Questions**: 9 total -- 5 CONFIRMED, 4 FALSE_POSITIVE
**Campaign**: Efficiency and overhead audit of BrickLayer 2.0 / Masonry framework (E1.x series)

---

## Executive Summary

Wave 3 shifted from defect discovery (Waves 1-2) to efficiency analysis: how much redundancy, dead weight, and unnecessary overhead exists in the Masonry codebase? The answer is encouraging -- the system is leaner than expected. Of 9 hypotheses about waste, only 5 confirmed real issues, and none are severe. The four false positives demonstrate that several design decisions that looked wasteful on the surface (zero npm dependencies, CLAUDE.md hooks table, deterministic routing table size, auto-loaded context volume) are intentional and well-justified.

The confirmed issues cluster around two themes:

1. **Hook-layer duplication** (E1.1/E1.2) -- `isResearchProject()` is copy-pasted into 8 files with behavioral drift, and 3 hook files exceed 300 lines with clear decomposition points. A single `masonry-utils.js` shared module would eliminate ~24 lines of duplicated logic and bring all files under the size limit.

2. **DSPy dead weight** (E1.5/E1.8) -- The DSPy pipeline has 3 dead signature classes (62% of signatures.py) and is listed as a hard dependency despite being entirely optional in the production path. The optimization pipeline has never produced output.

The fleet analysis (E1.4) found `tools-manifest` global copy is redundant (85% overlap with BL version) and `health-monitor` has confusing name collision (70% overlap, different purposes). Both are low-effort consolidation targets. 
## verify above 'health' 

---   

## Critical Findings (must act)

*(None -- Wave 3 found no critical or high-severity issues)*

---

## Significant Findings (important but not blocking)

1. **E1.1** [CONFIRMED/Medium] -- `isResearchProject()` duplicated across 8 hook files with 2 behavioral divergences: masonry-approver.js has a null guard the others lack, masonry-build-guard.js re-requires fs/path inside the function body.
   Fix: Create `masonry/src/hooks/masonry-utils.js` with the canonical definition (including the null guard). Replace 8 inline copies with `require('./masonry-utils')`.

2. **E1.4** [CONFIRMED/Medium] -- `tools-manifest` global copy (152 lines) is fully superseded by BL version (149 lines, strict superset). `health-monitor` exists in both directories with ~70% overlap and confusing name collision. Combined fleet is 55 agents / ~12,144 lines.
   Fix: Remove global `tools-manifest.md`. Rename one `health-monitor` copy to disambiguate.

3. **E1.2** [CONFIRMED/Low] -- 3 hook files exceed 300-line limit: masonry-observe.js (317), masonry-approver.js (315), masonry-tdd-enforcer.js (311). Each has clear extraction points: code-fact block (136 lines), tdd-helpers (135 lines), context-detection helpers (158 lines).
   Fix: Extract `masonry-code-facts.js` from observe, `masonry-tdd-helpers.js` from tdd-enforcer. Combined with E1.1 fix, all files drop below 300 lines.

4. **E1.5** [CONFIRMED/Low] -- `dspy>=2.5` is a hard requirement in requirements.txt but only needed for optimization endpoints that have never been invoked. MCP server already lazy-imports all DSPy modules.
   Fix: Convert to pyproject.toml with `[project.optional-dependencies] optimize = ["dspy>=2.5"]`.

5. **E1.8** [CONFIRMED/Low] -- 3 of 4 DSPy signature classes are dead: DiagnoseAgentSig, SynthesizerSig, QuestionDesignerSig have zero callers. Only ResearchAgentSig is used. Dead weight = 69 lines (62% of file).
   Fix: Delete the 3 dead classes. File shrinks from 112 to ~43 lines.

---

## Healthy / Verified (False Positives)

- **E1.3**: `deterministic.py` has no dead routing branches -- all 34 keyword patterns target agents that exist in agent_registry.yml. The 387-line size is structural (170 lines of routing table constants).
- **E1.6**: CLAUDE.md and rules files are complementary to hooks, not redundant. Hooks enforce outcomes; rules describe process. True overlap is only ~22 lines across all 12 rules files.
- **E1.7**: `package.json` correctly declares zero dependencies. All `require()` calls resolve to Node.js built-ins or internal relative paths. No npm packages needed.
- **E1.9**: Auto-loaded context is 22,587 tokens (45% of 50K threshold) -- threshold not breached. Agent definitions are NOT auto-loaded (per-invocation only). Main inefficiency is 12,423 tokens of UI-specific rules loaded in non-UI sessions.

---

## Cross-Wave Patterns

### Updated Root Cause Map

Waves 1-2 identified 5 root-cause patterns. Wave 3 adds a sixth:

**Pattern 6: Incremental Growth Without Refactoring**

The hook system grew from a few files to 15+ hooks without extracting shared utilities. Each new hook copied `isResearchProject()`, `readStdin()`, and `getAutopilotMode()` from existing hooks rather than importing from a shared module. This is a natural consequence of hooks being developed independently -- each is self-contained by design. The cost is now ~24 lines of duplicated logic with 2 behavioral divergences and 3 files exceeding the 300-line limit.

This pattern also applies to the DSPy pipeline: 4 signature classes were written speculatively, only 1 was ever connected to callers, and the dead 3 were never cleaned up.

### Relationship to Prior Waves

| Wave 3 Finding | Related Wave 1/2 Finding | Relationship |
|----------------|--------------------------|-------------|
| E1.1 (isResearchProject duplication) | D3.2 (approver bash block) | D3.2 found the divergence in approver; E1.1 maps the full scope |
| E1.2 (oversized hooks) | D3.4 (TDD enforcer async bug) | Same file -- extraction reduces cognitive load for fixing D3.4 |
| E1.4 (duplicate agents) | D2.6 (missing agents) | Fleet has both gaps (D2.6) and redundancies (E1.4) |
| E1.5 (DSPy hard dependency) | D1.2 (DSPy stubs dead) | Same pipeline -- stubs dead, dependency unnecessary |
| E1.8 (dead signature classes) | D1.2 (DSPy stubs dead) | Same pipeline -- optimization never completed |

---

## Cumulative Open Items (All Waves)

### Still Open

| ID | Wave | Severity | Summary |
|----|------|----------|---------|
| M1.3 | 2 | Critical | masonry-register.js plain text output -- needs JSON envelope |
| M1.4 | 2 | High | Mortar directive is advisory, not enforced -- design decision needed |
| V1.4 | 2 | High | onboard hook spawns Python without PYTHONPATH |
| D3.4 | 1 | High | TDD enforcer non-functional (async:true + exit(2)) |
| E1.1 | 3 | Medium | isResearchProject() duplicated in 8 hooks with drift |
| E1.4 | 3 | Medium | tools-manifest global redundant; health-monitor name collision |
| M1.6 | 2 | Medium | mortar.md missing git-nerd and infra routing entries |
| D2.6 | 1 | Medium | uiux-master and solana-specialist .md files missing |
| D5.1 | 1 | Medium | masonry-build.md uses dead OMC executor |
| E1.2 | 3 | Low | 3 hook files exceed 300-line limit |
| E1.5 | 3 | Low | DSPy hard dependency should be optional |
| E1.8 | 3 | Low | 3 dead DSPy signature classes |

### Verified Fixed (Waves 1-2)

| ID | Was | Fix Verified By |
|----|-----|-----------------|
| D4.4 | High | V1.1 -- q_total=46 returned correctly |
| D3.3 | High | V1.2 -- OLLAMA_HOST fallback working |
| D4.3+D6.5 | Medium | V1.3 -- all 5 BL2.0 modes routed |
| D2.2/D4.1 | High | V1.3 -- registry paths corrected |
| M1.1 | Critical | Fixed in commit a038099 |

---

## Recommendation

**STOP** -- Wave 3 is complete. All 9 E-series questions answered.

The efficiency audit found no critical waste. The confirmed issues are all low-effort, low-risk cleanups (shared utility extraction, dead code deletion, dependency restructuring). None block feature development. The high-severity items from Waves 1-2 (M1.3, V1.4, D3.4) remain the priority for remediation. The E-series findings should be addressed opportunistically -- E1.1 in particular is a good warm-up task that improves code quality across 8 files.

---

## Cumulative Metrics

| Domain                | Wave | Questions | CONFIRMED | FALSE_POSITIVE |
|--------|------|-----------|-----------|----------------|
| D1: Dead Code           | 1 |     6 | 5 | 1 |
| D2: Unwired Items       | 1 |     6 | 6 | 0 |
| D3: Bugs & Logic        | 1 |     8 | 2 | 6 |
| D4: Config Drift        | 1 |     4 | 4 | 0 |
| D5: Stale References    | 1 |     6 | 4 | 2 |
| D6: Structural          | 1 |     6 | 3 | 3 |
| M1: Mortar Routing      | 2 |     6 | 5 | 1 |
| V1: Fix Verification    | 2 |     5 | 2 | 3 |
| E1: Efficiency/Overhead | 3 |     9 | 5 | 4 |
| **Total** | **1-3** | **56** | **36** | **20** |

**Wave 3 signal quality**: The 44% false-positive rate (4 of 9) is appropriate for an efficiency audit -- hypotheses about waste are inherently speculative. The false positives confirmed that several design decisions (zero npm deps, complementary rules/hooks, reasonable context budget) are sound. The 56% confirmation rate still yielded 5 actionable cleanup items.

**Campaign totals**: 56 questions across 3 waves, 36 confirmed issues (64%), 20 false positives (36%). The false-positive rate has been stable across waves (33% W1, 40% W2, 44% W3), indicating consistent question calibration.

---

## Next Wave Hypotheses

If a Wave 4 is warranted, the following directions emerge from the cumulative findings:

1. **Fix verification for Waves 1-2 open items** -- M1.3, V1.4, D3.4 are still open. A fix-then-verify wave would close the highest-severity items.

2. **Hook refactoring verification** -- After applying E1.1/E1.2 fixes, verify that all 15 hooks still pass `node --check` and that isResearchProject() behavior is identical across all call sites.

3. **Mortar architecture decision validation** -- M1.4 identified that Mortar is advisory, not enforced. If a design decision is made (accept vs redesign), a validation wave could verify the chosen approach works end-to-end.

4. **Cross-machine portability audit** -- Wave 1 Pattern 4 identified environment-specific assumptions. A targeted audit on casaclaude/proxyclaude would verify the system works beyond the primary dev machine.

5. **Test coverage gap analysis** -- The hook suite has `"test": "echo \"No tests yet\""` in package.json. A test-debt audit could quantify the gap and prioritize which hooks need tests most urgently.
