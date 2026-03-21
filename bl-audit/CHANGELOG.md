# Changelog -- bl-audit

All notable campaign findings and fixes documented here.
Maintained by BrickLayer synthesizer at each wave end.

Format: wave entries newest-first. Each wave appended automatically.

---

## [Unreleased]

*(In-progress wave -- entries added here during the wave)*

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
