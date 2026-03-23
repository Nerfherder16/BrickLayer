# Changelog -- bl-audit

All notable campaign findings and fixes documented here.
Maintained by BrickLayer synthesizer at each wave end.

Format: wave entries newest-first. Each wave appended automatically.

---

## [Unreleased]

*(In-progress wave -- entries added here during the wave)*

---

## [Wave 3] -- 2026-03-22

9 questions (E1.1-E1.9) — efficiency and overhead audit; 5 CONFIRMED, 4 FALSE_POSITIVE. No critical issues found. Hook duplication and DSPy dead weight are the main cleanup targets.

### Found (open)
- `E1.1` [CONFIRMED/Medium] -- `isResearchProject()` copy-pasted into 8 hook files with 2 behavioral divergences (null guard, inline requires)
- `E1.4` [CONFIRMED/Medium] -- `tools-manifest` global copy redundant (85% overlap); `health-monitor` name collision (70% overlap, different purposes)
- `E1.2` [CONFIRMED/Low] -- 3 hook files exceed 300-line limit: masonry-observe.js (317), masonry-approver.js (315), masonry-tdd-enforcer.js (311)
- `E1.5` [CONFIRMED/Low] -- `dspy>=2.5` hard dependency in requirements.txt; MCP server lazy-imports it; should be optional
- `E1.8` [CONFIRMED/Low] -- 3 of 4 DSPy signature classes dead (DiagnoseAgentSig, SynthesizerSig, QuestionDesignerSig); 69 lines / 62% of file

### Healthy
E1.3 (deterministic.py has no dead routing branches), E1.6 (CLAUDE.md rules complement hooks, only ~22 lines true overlap), E1.7 (package.json zero deps is intentional and correct), E1.9 (auto-loaded context 22.6K tokens, below 50K threshold) confirmed working/correct.

---

## [Wave 2] -- 2026-03-21

10 questions across 2 domains (Mortar routing integrity + fix verification); 6 CONFIRMED, 4 FALSE_POSITIVE. Key outcome: Mortar "Every request" invariant has never been enforced -- triple failure in injection pipeline.

### Fixed
- `M1.1` -- masonry-register.js duplicate `const cwd` SyntaxError removed (commit `a038099`)

### Found (open)
- `M1.3` [CONFIRMED/Critical] -- masonry-register.js outputs plain text, needs JSON `{additionalContext}` envelope for UserPromptSubmit
- `M1.4` [CONFIRMED/High] -- Mortar directive is advisory context, not enforced agent invocation; architectural limitation
- `V1.4` [CONFIRMED/High] -- masonry-agent-onboard.js spawns onboard_agent.py without PYTHONPATH; ModuleNotFoundError silenced
- `M1.6` [CONFIRMED/Medium] -- mortar.md routing table missing git-nerd and infrastructure task entries (~70% coverage)
- `M1.5` [CONFIRMED/Medium] -- BL research projects suppress Mortar injection by design (intentional)

### Healthy
V1.1 (masonry_status counting fixed), V1.2 (semantic.py OLLAMA_HOST working), V1.3 (deterministic mode routing working for all 5 BL2.0 modes), M1.2 (routing_log.jsonl valid with 57 entries) confirmed working.

---

## [Wave 1] -- 2026-03-21

36 questions across 6 domains; 24 CONFIRMED issues, 12 FALSE_POSITIVE (working correctly). Full static code health audit of BrickLayer 2.0 / Masonry framework complete.

### Found (open)

**Tier 1 -- Broken Core Features:**
- `D3.4` [CONFIRMED/High] -- TDD enforcer registered async:true but calls exit(2); enforcement is entirely non-functional
- `D4.4` [CONFIRMED/High] -- masonry_status counts `### Q` but BL2.0 uses `## D1.1`; Kiln shows 0% for all BL2.0 campaigns
- `D3.3` [CONFIRMED/High] -- semantic.py reads OLLAMA_URL but env var is OLLAMA_HOST; semantic routing always falls through
- `D2.2`/`D4.1` [CONFIRMED/High] -- 9+ registry entries have wrong `agents/` prefix; file lookups fail

**Tier 2 -- Silent Feature Failures:**
- `D1.1`/`D2.1` [CONFIRMED/Medium] -- masonry-agent-onboard.js not in settings.json; auto-onboarding never fires
- `D2.6` [CONFIRMED/Medium] -- uiux-master and solana-specialist referenced but no .md files exist
- `D4.3` [CONFIRMED/Medium] -- 16 agents have modes:[]; unreachable via deterministic routing
- `D5.1` [CONFIRMED/Medium] -- masonry-build.md uses dead oh-my-claudecode:executor subagent type

**Documentation / Stale References:**
- `D4.2` [CONFIRMED/Medium] -- CLAUDE.md lists 5 of 14 MCP tools
- `D2.4` [CONFIRMED/Medium] -- tools-manifest.md has 4 phantom tools, missing 7 real tools
- `D2.5` [CONFIRMED/Low] -- CLAUDE.md hook table out of sync with settings.json
- `D5.3` [CONFIRMED/Medium] -- DISABLE_OMC=1 in 4 active files (no-op since OMC removal)
- `D5.6` [CONFIRMED/Medium] -- hardcoded Windows path in masonry-session-start.js
- `D1.2` [CONFIRMED/Medium] -- 46 orphaned DSPy stubs; optimized_prompts/ empty
- `D2.3` [CONFIRMED/Medium] -- design-reviewer and frontier-analyst have wrong path prefix in registry
- `D1.4` [CONFIRMED/Low] -- mcp_gateway.py dead code with hardcoded Exa API key
- `D1.3` [CONFIRMED/Low] -- repo statusline copy stale vs live ~/.claude/hud/ copy
- `D1.5` [CONFIRMED/Low] -- root onboard.py is BL1.x dead code
- `D5.2` [CONFIRMED/Low] -- dashboard port 3100 references in active files
- `D6.3` [CONFIRMED/Low] -- template/program.md is BL1.x only, no BL2.0 static template
- `D6.5` [CONFIRMED/Medium] -- BL1.x/BL2.0 agent variants have identical empty modes (latent risk)
- `D6.6` [CONFIRMED/Low] -- agent_db.json, optimized_prompts/, activity logs missing from .gitignore

### Healthy
D1.6, D3.1, D3.2, D3.5, D3.6, D3.7, D3.8, D5.4, D5.5, D6.1, D6.2, D6.4 confirmed working correctly. Hook exit codes valid, path normalization correct, Pydantic v2 clean, session state symmetry correct, routing fallback robust.

---
