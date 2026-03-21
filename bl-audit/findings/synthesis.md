# Wave 1 Synthesis -- bl-audit

**Date**: 2026-03-21
**Questions**: 36 total -- 24 CONFIRMED, 12 FALSE_POSITIVE
**Campaign**: Static code health audit of BrickLayer 2.0 / Masonry framework

---

## Executive Summary

The BrickLayer 2.0 / Masonry framework is structurally sound in its core design -- the four-layer routing pipeline, the hook event system, the Pydantic v2 schema layer, and session state management all function correctly at the individual-component level. However, the system suffers from **integration-layer rot**: the wiring between components has drifted significantly from both documentation and intent. Of 36 questions investigated across 6 domains, 24 confirmed real issues. The most impactful findings cluster around three root causes:

1. **Dead onboarding hook** (D1.1/D2.1) -- the mechanism that keeps agent_registry.yml synchronized with the actual agent fleet has never executed, causing cascading path drift across the registry, routing, and DSPy pipeline.

2. **Format migration gap** (D4.4/D6.3/D6.5) -- the BL1.x-to-BL2.0 transition changed question format, agent locations, and campaign structure, but several consumers (masonry_status, template/, agent_registry.yml) still expect BL1.x formats.

3. **Documentation-as-code disconnect** (D2.4/D2.5/D2.6/D4.2/D5.1/D5.3) -- CLAUDE.md, tools-manifest.md, and agent instructions contain claims that do not match runtime behavior, creating a false-confidence surface for both human operators and AI agents.

No data-loss or security-critical bugs were found in the active runtime path. The hardcoded Exa API key in dead code (D1.4) is the only security finding and the file is never loaded.

---

## Critical Findings (must act)

### Tier 1: Broken Core Features

1. **D3.4** [CONFIRMED/High] -- TDD enforcer hook is entirely non-functional. Registered as `async:true` but calls `process.exit(2)` to block writes -- async hooks cannot block. TDD enforcement during `/build` has never worked.
   - Fix: Change settings.json registration to `async: false` (or remove async field).

2. **D4.4** [CONFIRMED/High] -- masonry_status MCP tool returns q_total=0 for all BL2.0 campaigns. Counts `### Q` headers (BL1.x) but BL2.0 uses `## D1.1` format. Kiln dashboard permanently shows 0% progress.
   - Fix: Update question-counting regex to handle both `### Q` and `## {letter}{digit}.{digit}` patterns.

3. **D3.3** [CONFIRMED/High] -- Semantic router reads `OLLAMA_URL` but settings.json injects `OLLAMA_HOST`. Semantic routing always falls through to LLM layer on non-primary machines. Threshold documented as 0.75, actual default is 0.60.
   - Fix: Read both env vars with fallback chain: `OLLAMA_URL || OLLAMA_HOST || hardcoded default`. Align threshold with documentation.

4. **D2.2/D4.1** [CONFIRMED/High] -- agent_registry.yml has 9+ entries with `agents/` prefix pointing to files that only exist at `.claude/agents/`. Any tool reading agent content from the registry `file:` field gets FileNotFoundError. Additionally, 2 entries use `~/.claude/agents/` prefix for repo-local agents.
   - Fix: Run `onboard_agent.py` with correct `--agents-dir` flags to regenerate paths. Register onboard hook to prevent recurrence.

### Tier 2: Silent Feature Failures

5. **D1.1/D2.1** [CONFIRMED/Medium] -- masonry-agent-onboard.js is not registered in settings.json. Agent auto-onboarding never fires. CLAUDE.md falsely claims "Zero Manual Steps" for agent onboarding.
   - Fix: Add PostToolUse registration for Write/Edit events targeting agent .md files. Or remove the hook and update documentation.

6. **D2.6** [CONFIRMED/Medium] -- uiux-master and solana-specialist referenced in CLAUDE.md routing table but no .md files exist anywhere. All `/ui-*` skills that invoke uiux-master will fail or fall back silently.
   - Fix: Create the agent .md files, or remove references from CLAUDE.md and UI skills.

7. **D4.3** [CONFIRMED/Medium] -- 16 agents have `modes: []` in agent_registry.yml. They are unreachable via zero-cost Mode field routing. Undermines the "60%+ deterministic routing" claim.
   - Fix: Add `modes:` frontmatter to each agent .md file; re-run onboard_agent.py.

8. **D5.1** [CONFIRMED/Medium] -- masonry-build.md uses `subagent_type="oh-my-claudecode:executor"` -- a non-existent subagent type. The `/build` skill is broken.
   - Fix: Replace with `subagent_type="developer"` or equivalent active type.

---

## Significant Findings (important but not blocking)

### Documentation Drift

9. **D4.2** [CONFIRMED/Medium] -- CLAUDE.md lists only 5 of 14 MCP tools. Nine tools including `masonry_status`, `masonry_questions`, and `masonry_fleet` are undocumented in the primary context document.
   - Fix: Update CLAUDE.md MCP tools table to list all 14 tools.

10. **D2.4** [CONFIRMED/Medium] -- tools-manifest.md documents 4 phantom tools that do not exist in server.py and is missing 7 tools that do exist.
    - Fix: Regenerate tools-manifest.md from server.py.

11. **D2.5** [CONFIRMED/Low] -- CLAUDE.md hook table has masonry-agent-onboard.js listed as active (it is not) and is missing masonry-tdd-enforcer.js entry.
    - Fix: Sync hook table with settings.json.

### Stale References

12. **D5.3** [CONFIRMED/Medium] -- DISABLE_OMC=1 appears in 4 active files (recall/program.md, masonry-session-start.js, bl/nl_entry.py, karen.md). The env var is a no-op since OMC removal but teaches incorrect mental model.
    - Fix: Remove DISABLE_OMC from all launch instructions in active files.

13. **D5.6** [CONFIRMED/Medium] -- masonry-session-start.js line 123 hardcodes `C:/Users/trg16/Dev/Bricklayer2.0`. Breaks session-start context restoration on casaclaude/proxyclaude.
    - Fix: Replace with sentinel-file detection (`masonry.json` or `program.md + questions.md`).

14. **D1.2** [CONFIRMED/Medium] -- 46 DSPy stubs in `generated/` are never imported. `optimized_prompts/` is empty. The entire optimization pipeline has never produced output.
    - Fix: Delete `generated/` directory. Get one end-to-end optimization working before scaling.

### Low Priority / Hygiene

15. **D2.3** [CONFIRMED/Medium] -- design-reviewer and frontier-analyst registered under `~/.claude/agents/` but actually at `.claude/agents/`. Root cause: onboard_agent.py path resolution ambiguity.

16. **D1.3** [CONFIRMED/Low] -- Repo copy of masonry-statusline.js is stale (missing execSync import). Live copy at `~/.claude/hud/` has diverged.

17. **D1.4** [CONFIRMED/Low] -- mcp_gateway.py is dead code with hardcoded Exa API key `d1383966-...`. Security concern: key committed in plaintext to git history.
    - Fix: Delete file. Rotate the Exa API key.

18. **D1.5** [CONFIRMED/Low] -- Root onboard.py is BL1.x dead code, superseded by masonry/scripts/onboard_agent.py.

19. **D5.2** [CONFIRMED/Low] -- Dashboard port 3100 references remain in bl/runners/__init__.py and QUICKSTART.md (dashboard retired, Kiln is current).

20. **D6.3** [CONFIRMED/Low] -- template/program.md is BL1.x format only. No BL2.0 static-campaign template exists.

21. **D6.5** [CONFIRMED/Medium] -- BL1.x and BL2.0 variant agents (hypothesis-generator vs hypothesis-generator-bl2) have identical empty modes. Latent cross-version routing risk when D4.3 is fixed.

22. **D6.6** [CONFIRMED/Low] -- agent_db.json, masonry/optimized_prompts/, and masonry-activity-*.ndjson missing from .gitignore.

---

## Healthy / Verified (False Positives)

The following areas were investigated and confirmed working correctly:

- **D1.6**: All routing sub-module functions are referenced -- no dead functions in the routing pipeline
- **D3.1**: Stop guard correctly scopes to current session via sessionId-namespaced activity files
- **D3.2**: Approver correctly blocks Bash in build/fix mode while allowing it in research mode
- **D3.5**: All hook exit codes are valid (0 for pass-through, 1 for approve, 2 for block)
- **D3.6**: Windows path normalization is correct in both stop-guard (WSL-to-Windows) and lint-check (backslash-to-forward)
- **D3.7**: Lint check is correctly advisory-only (PostToolUse, exit 0 always, warns via stdout)
- **D3.8**: Router fallback correctly returns `target_agent="user"` when all layers return None; server.py wraps in try/except
- **D5.4**: Pydantic v2 syntax is clean throughout schemas -- no v1 patterns found
- **D5.5**: program.md files do not hardcode agent names -- agent selection delegated to question-level fields
- **D6.1**: masonry-observe.js and masonry-guard.js serve entirely different concerns (observation vs error fingerprinting)
- **D6.2**: Session start/end state management is correctly symmetrical for transient state and correctly asymmetrical for context-relay state
- **D6.4**: masonry-state.json is correctly in .gitignore

---

## Cross-Domain Patterns and Root Causes

### Pattern 1: The Dead Onboarding Cascade

D1.1 (dead hook) caused D1.2 (orphaned stubs), D2.2/D4.1 (drifted registry paths), D4.3 (empty modes), and D2.3 (wrong path prefixes). When the onboarding hook stopped running, the registry froze. New agents were added manually but with inconsistent path conventions. The registry then drifted from reality, making the routing engine's file lookups unreliable and DSPy optimization impossible.

**Fix cascade**: Register onboard hook (D1.1) -> regenerate registry (D4.1) -> add modes (D4.3) -> clean stubs (D1.2).

### Pattern 2: BL1.x Migration Incomplete

D4.4 (question count parser), D6.3 (template format), D6.5 (agent version disambiguation), and D5.2 (dashboard references) all stem from the BL1.x-to-BL2.0 migration leaving consumers of the old format unremediated. The migration changed the shape of questions.md, the agent directory location, and the monitoring UI, but not all consumers were updated.

### Pattern 3: Documentation Claims Exceed Implementation

D2.4 (tool manifest mismatch), D2.5 (hook table errors), D2.6 (missing agents), D4.2 (incomplete MCP table), and D5.1 (OMC references) form a pattern where documentation asserts capabilities that do not exist at runtime. CLAUDE.md claims 15 active hooks (14 actually fire), 5 MCP tools (14 exist), zero-manual-step onboarding (hook is dead), and agents like uiux-master and solana-specialist (no files exist).

### Pattern 4: Environment-Specific Assumptions

D3.3 (env var name), D5.6 (hardcoded Windows path), and to a lesser extent D1.3 (live vs repo copy divergence) show the system was tuned to work on the primary dev machine but silently degrades on other environments. The hardcoded Ollama URL, hardcoded blRoot path, and live-copy-only hooks all function correctly on Tim's main machine but fail elsewhere.

---

## Critical Path: Dependency-Ordered Remediation

The following fixes should be applied in order because later fixes depend on earlier ones:

```
Phase 1 (unblocks everything else):
  1. Register masonry-agent-onboard.js in settings.json       [D1.1/D2.1]
  2. Fix semantic.py env var: OLLAMA_URL -> OLLAMA_HOST         [D3.3]
  3. Fix masonry_status question pattern for BL2.0              [D4.4]

Phase 2 (requires Phase 1):
  4. Re-run onboard_agent.py to regenerate registry paths       [D2.2/D4.1/D2.3]
  5. Add modes: frontmatter to all agent .md files              [D4.3]
     (use distinct modes for BL1.x vs BL2.0 variants)          [D6.5]
  6. Change TDD enforcer to async:false in settings.json        [D3.4]

Phase 3 (cleanup, independent):
  7. Replace OMC executor in masonry-build.md                   [D5.1]
  8. Create uiux-master.md and solana-specialist.md             [D2.6]
  9. Remove DISABLE_OMC from active files                       [D5.3]
  10. Replace hardcoded blRoot with sentinel detection           [D5.6]
  11. Sync CLAUDE.md hook/tool tables with settings.json         [D2.5/D4.2]
  12. Regenerate tools-manifest.md from server.py                [D2.4]

Phase 4 (housekeeping):
  13. Delete mcp_gateway.py, rotate Exa API key                 [D1.4]
  14. Delete onboard.py (BL1.x dead code)                       [D1.5]
  15. Delete generated/ DSPy stubs                              [D1.2]
  16. Sync repo statusline copy with live copy                  [D1.3]
  17. Update .gitignore with missing patterns                   [D6.6]
  18. Update QUICKSTART.md and runners example                  [D5.2]
  19. Add BL2.0 template for static campaigns                  [D6.3]
```

---

## Recommendation

**STOP** -- Wave 1 is complete. All 36 questions answered. The audit has mapped the full health state of the Masonry/BrickLayer framework.

The system is fundamentally well-designed but has accumulated significant integration drift. No emergency fixes are required (all critical paths have working fallbacks), but the 8 Tier 1/Tier 2 findings should be addressed before the next feature-development push. The Phase 1 fixes (3 changes) will unblock the majority of the remaining issues.

---

## Metrics

| Domain | Questions | CONFIRMED | FALSE_POSITIVE |
|--------|-----------|-----------|----------------|
| D1: Dead Code | 6 | 5 | 1 |
| D2: Unwired Items | 6 | 6 | 0 |
| D3: Bugs & Logic Errors | 8 | 2 | 6 |
| D4: Config Drift | 4 | 4 | 0 |
| D5: Stale References | 6 | 4 | 2 |
| D6: Structural Problems | 6 | 3 | 3 |
| **Total** | **36** | **24** | **12** |

**Signal quality**: The 33% false-positive rate indicates the question bank was well-calibrated -- it probed genuine risk areas (hook exit codes, path normalization, session state symmetry) and confirmed they were correctly implemented. The false positives in D3 (6 of 8) demonstrate that the hook system's core logic is sound even though the wiring and configuration around it has drifted.

---
---

# Wave 2 Synthesis -- bl-audit

**Date**: 2026-03-21
**Questions**: 10 total -- 6 CONFIRMED, 4 FALSE_POSITIVE
**Campaign**: Mortar routing integrity (M1.x) + Wave 1 fix verification (V1.x)

---

## Executive Summary

Wave 2 investigated two concerns: (1) whether the Mortar routing directive -- the "Every request goes through Mortar" invariant from CLAUDE.md -- actually functions, and (2) whether Phase 1/2 fixes from Wave 1 were correctly applied.

The Mortar investigation (M1.1-M1.6) revealed a **triple failure** in the directive injection pipeline: a SyntaxError that prevented the hook from running (M1.1, now fixed), a format mismatch that means the hook's output is ignored even after the SyntaxError fix (M1.3, unfixed), and an architectural reality that even perfect injection would only produce advisory context, not enforced routing (M1.4). The "Every request goes through Mortar" principle has never been technically enforced and cannot be with the current hook architecture.

The verification questions (V1.1-V1.4) confirmed that three of four Wave 1 Phase 1/2 fixes are working correctly: question counting (D4.4), semantic router env var (D3.3), and deterministic mode routing (D4.3+D6.5). However, the agent onboard hook (V1.4), while now registered and firing, fails silently because it spawns Python without PYTHONPATH.

---

## Critical Findings (must act)

1. **M1.3** [CONFIRMED/Critical] -- masonry-register.js writes plain text stdout, but Claude Code UserPromptSubmit hooks require a `{additionalContext: "..."}` JSON envelope. Even after M1.1 fix, the Mortar directive is silently discarded.
   Fix: Wrap directive output in `JSON.stringify({ additionalContext: directive })`.

2. **V1.4** [CONFIRMED/High] -- masonry-agent-onboard.js fires correctly on agent .md writes but spawns `onboard_agent.py` without PYTHONPATH. Python fails with `ModuleNotFoundError: No module named 'masonry'`, silenced by `stdio: "ignore"`. Auto-onboarding is still broken end-to-end.
   Fix: Add `env: { ...process.env, PYTHONPATH: cwd }` to the spawn options.

## Significant Findings (important but not blocking)

3. **M1.4** [CONFIRMED/High] -- The Mortar directive is advisory context text, not automatic agent invocation. Claude Code has no mechanism to force agent dispatch from a hook. The "Every request goes through Mortar" policy is a voluntary compliance model. This is an architectural limitation, not a bug.
   Action: Accept the advisory model and strengthen CLAUDE.md language, or redesign the routing architecture.

4. **M1.6** [CONFIRMED/Medium] -- mortar.md routing table is missing entries for git operations (git-nerd) and infrastructure tasks. Coverage is approximately 70% of typical task types. Git and infra tasks fall through to inline Claude handling.
   Fix: Add git-nerd and infrastructure routing entries to mortar.md.

5. **M1.5** [CONFIRMED/Medium] -- bl-audit directory (and all BL research projects) suppress Mortar injection by design via `isResearchProject()` guard. This is intentional (BL subprocess isolation) but means the audit itself was never Mortar-routed. No fix needed -- documenting the design boundary.

## Healthy / Verified

- **M1.1** [CONFIRMED/Critical, FIXED] -- Duplicate `const cwd` SyntaxError fixed in commit `a038099`. Hook now parses cleanly.
- **M1.2** [FALSE_POSITIVE] -- routing_log.jsonl has 57 valid entries (29 start + 28 finding). Prior empty-parse report was a script bug.
- **V1.1** [FALSE_POSITIVE] -- masonry_status question counting now returns q_total=46 for bl-audit. D4.4 fix verified working.
- **V1.2** [FALSE_POSITIVE] -- semantic.py OLLAMA_HOST fallback working. Ollama reachable at 192.168.50.62:11434. D3.3 fix verified.
- **V1.3** [FALSE_POSITIVE] -- All 5 BL2.0 modes (audit/research/diagnose/simulate/campaign) now map to agents. D4.3+D6.5 fix verified.

---

## Cross-Wave Pattern: The Mortar Enforcement Gap

Wave 2 adds a fifth root-cause pattern to the four identified in Wave 1:

### Pattern 5: Advisory Architecture Masquerades as Enforcement

The CLAUDE.md architecture section presents Mortar as an execution engine ("Every request goes through Mortar"). In reality, the system has three independent points of failure that all must work simultaneously for the directive to reach the model:

1. **Hook must parse** (M1.1 -- was broken, now fixed)
2. **Hook output must use correct format** (M1.3 -- still broken)
3. **Model must choose to comply** (M1.4 -- architectural limitation)

Additionally, BL research projects intentionally suppress the directive (M1.5), and mortar.md itself lacks routing entries for common task types (M1.6). The total picture: Mortar has never routed a single request in production. Every agent invocation in routing_log.jsonl was spawned directly by Claude, not dispatched by Mortar.

This is the most significant finding of the entire audit. The claimed central architectural invariant of the system -- Mortar as universal dispatcher -- is an aspiration documented as a fact.

---

## Updated Remediation Roadmap

Wave 1 Phase 1 items (D3.3, D4.4) are now verified fixed (V1.1, V1.2, V1.3). The updated priority list:

```
Still open from Wave 1 (not yet fixed):
  - D3.4 [High]   TDD enforcer async:true -- enforcement non-functional
  - D2.6 [Medium]  uiux-master and solana-specialist .md files missing
  - D5.1 [Medium]  masonry-build.md uses dead OMC executor type

New from Wave 2:
  - M1.3 [Critical] masonry-register.js output format -- JSON envelope needed
  - V1.4 [High]     onboard hook PYTHONPATH -- spawn env fix needed
  - M1.6 [Medium]   mortar.md routing table gaps (git, infra)
  - M1.4 [High]     Mortar advisory architecture -- decision needed on accept vs redesign

Verified fixed (close these):
  - D4.4 [was High] masonry_status question counting -- FIXED, verified V1.1
  - D3.3 [was High] semantic.py OLLAMA_HOST -- FIXED, verified V1.2
  - D4.3+D6.5 [was Medium] deterministic mode routing -- FIXED, verified V1.3
  - M1.1 [was Critical] masonry-register.js SyntaxError -- FIXED in a038099
  - D1.1/D2.1 [was Medium] onboard hook registration -- FIXED (but V1.4 found new issue)
```

---

## Recommendation

**STOP** -- Wave 2 is complete. All 10 questions answered (6 CONFIRMED, 4 FALSE_POSITIVE).

The Mortar routing investigation has revealed the most architecturally significant finding of the audit: the central routing invariant has never been enforced and the current hook architecture cannot enforce it. This requires a design decision (accept advisory model vs redesign) before further remediation. The three remaining Wave 1 critical items (D3.4, M1.3, V1.4) are straightforward code fixes. The Mortar architecture question (M1.4) is a design decision that should be made by a human before investing in further Mortar-related work.

---

## Cumulative Metrics

| Domain | Wave | Questions | CONFIRMED | FALSE_POSITIVE |
|--------|------|-----------|-----------|----------------|
| D1: Dead Code | 1 | 6 | 5 | 1 |
| D2: Unwired Items | 1 | 6 | 6 | 0 |
| D3: Bugs & Logic | 1 | 8 | 2 | 6 |
| D4: Config Drift | 1 | 4 | 4 | 0 |
| D5: Stale References | 1 | 6 | 4 | 2 |
| D6: Structural | 1 | 6 | 3 | 3 |
| M1: Mortar Routing | 2 | 6 | 5 | 1 |
| V1: Fix Verification | 2 | 4 | 1 | 3 |
| **Total** | **1-2** | **46** | **30** | **16** |

**Wave 2 signal quality**: The 40% false-positive rate in Wave 2 is by design -- the V1.x verification questions were expected to confirm fixes were working (FALSE_POSITIVE = fix succeeded). The M1.x questions had a 17% false-positive rate (1 of 6), indicating the Mortar routing concerns were well-founded.
