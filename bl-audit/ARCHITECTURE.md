# Architecture -- bl-audit

**Target**: BrickLayer 2.0 / Masonry framework (`C:/Users/trg16/Dev/Bricklayer2.0/`)
**Stack**: Python (BL core, routing, DSPy) + Node.js (hooks, MCP server) + YAML (agent registry)
**BL version**: 2.0

Maintained by BrickLayer synthesizer. Updated at each wave end.

---

## What This Campaign Targets

Static code health audit of the BrickLayer 2.0 and Masonry orchestration framework itself. The audit examines six domains: dead code, unwired items, bugs and logic errors, configuration drift, stale references, and structural problems. The goal is to map integration-layer rot and produce a prioritized remediation roadmap.

Key invariants under test:
- All hooks registered in settings.json must correspond to files on disk, and vice versa
- agent_registry.yml file paths must resolve to actual agent .md files
- Documentation claims (CLAUDE.md, tools-manifest.md) must match runtime behavior
- BL1.x-to-BL2.0 migration must be complete across all consumers
- The system must function on machines other than the primary dev machine

---

## System Under Audit: Component Map

### Hook System (Node.js)
15 hooks registered in `~/.claude/settings.json`, firing on SessionStart, PreToolUse, PostToolUse, PostToolUseFailure, SubagentStart, and Stop events. One additional hook file (`masonry-agent-onboard.js`) exists but is NOT registered -- agent auto-onboarding is broken. The live statusline script runs from `~/.claude/hud/` (not the repo copy).

| Hook | Event | Status |
|------|-------|--------|
| masonry-session-start.js | SessionStart | Active (hardcoded path issue D5.6) |
| masonry-approver.js | PreToolUse | Active, correct |
| masonry-context-safety.js | PreToolUse | Active, correct |
| masonry-lint-check.js | PostToolUse | Active, advisory-only, correct |
| masonry-design-token-enforcer.js | PostToolUse | Active |
| masonry-observe.js | PostToolUse | Active, correct |
| masonry-guard.js | PostToolUse | Active, correct |
| masonry-tdd-enforcer.js | PostToolUse | BROKEN: async:true defeats exit(2) blocking (D3.4) |
| masonry-tool-failure.js | PostToolUseFailure | Active |
| masonry-subagent-tracker.js | SubagentStart | Active |
| masonry-stop-guard.js | Stop | Active, correctly session-scoped |
| masonry-build-guard.js | Stop | Active |
| masonry-ui-compose-guard.js | Stop | Active |
| masonry-context-monitor.js | Stop | Active (async) |
| masonry-statusline.js | statusLine | Active via ~/.claude/hud/ (repo copy stale D1.3) |
| masonry-agent-onboard.js | (none) | DEAD: not in settings.json (D1.1/D2.1) |
| masonry-recall-check.js | (none) | BY DESIGN: subprocess utility, not a hook |

### Mortar Directive Injection (Node.js)
`masonry-register.js` is a `UserPromptSubmit` hook intended to inject the Mortar routing directive into every prompt. Wave 2 found three independent failure points:

1. **M1.1** (FIXED): Duplicate `const cwd` caused SyntaxError -- hook never parsed
2. **M1.3** (OPEN): Hook writes plain text stdout; Claude Code requires `{additionalContext: "..."}` JSON
3. **M1.4** (ARCHITECTURAL): Even with correct output, `additionalContext` is advisory context -- Claude may ignore it

**Net status**: Mortar has never dispatched a request in production. The routing_log.jsonl confirms all 29 agent spawns were direct invocations, not Mortar-dispatched. BL research projects additionally suppress injection via `isResearchProject()` guard (M1.5, by design).

### Routing Pipeline (Python)
Four-layer routing: deterministic -> semantic -> LLM -> fallback.

- **Deterministic** (`deterministic.py`): Slash commands, autopilot state, Mode field. All functions referenced correctly (D1.6). But 16 agents have empty modes (D4.3), reducing deterministic coverage.
- **Semantic** (`semantic.py`): Ollama cosine similarity. Reads wrong env var OLLAMA_URL instead of OLLAMA_HOST (D3.3). Threshold 0.60 vs documented 0.75.
- **LLM** (`llm_router.py`): Single Haiku call for ambiguous requests. Functioning correctly.
- **Fallback** (`router.py`): Returns `target_agent="user"`. Correctly implemented (D3.8).

### MCP Server (Node.js + Python)
`masonry/mcp_server/server.py` exposes 14 tools. CLAUDE.md documents 5. tools-manifest.md documents 11 (with 4 phantom entries and 7 missing). The `masonry_status` tool has a BL1.x-only question parser (D4.4).

### Agent Registry (YAML)
`masonry/agent_registry.yml` contains 48+ entries across three path conventions (`agents/`, `~/.claude/agents/`, `.claude/agents/`). 11+ entries have wrong file paths. 16 entries have empty modes. The registry is not a reliable source of truth (D2.2/D4.1).

### DSPy Pipeline (Python)
`masonry/src/dspy_pipeline/` has training extractor, optimizer, drift detector. `generated/` contains 46 stubs never imported. `optimized_prompts/` is empty. The pipeline has never produced output (D1.2).

### Schema Layer (Python)
`masonry/src/schemas/payloads.py` uses clean Pydantic v2 throughout. No v1 patterns found (D5.4).

---

## Agent Fleet

| Agent | Location | Registry Status | Notes |
|-------|----------|-----------------|-------|
| trowel | .claude/agents/ | Registered, modes:[] | Correctly hardcodes BL2.0 agent names |
| mortar | .claude/agents/ | Registered, modes:[] | Delegates campaigns to Trowel |
| diagnose-analyst | .claude/agents/ | Wrong path (agents/) | D2.2 |
| compliance-auditor | .claude/agents/ | Wrong path (agents/) | D2.2 |
| research-analyst | .claude/agents/ | Wrong path (agents/) | D2.2 |
| fix-implementer | .claude/agents/ | Wrong path (agents/) | D2.2 |
| design-reviewer | .claude/agents/ | Wrong path (~/.claude/agents/) | D2.3 |
| frontier-analyst | .claude/agents/ | Wrong path (~/.claude/agents/) | D2.3 |
| uiux-master | MISSING | Not registered | D2.6 -- referenced in CLAUDE.md but no file |
| solana-specialist | MISSING | Not registered | D2.6 -- referenced in CLAUDE.md but no file |

---

## Question Bank Summary

| Domain | Count | CONFIRMED | FALSE_POSITIVE | Status |
|--------|-------|-----------|----------------|--------|
| D1: Dead Code | 6 | 5 | 1 | COMPLETE |
| D2: Unwired Items | 6 | 6 | 0 | COMPLETE |
| D3: Bugs & Logic | 8 | 2 | 6 | COMPLETE |
| D4: Config Drift | 4 | 4 | 0 | COMPLETE |
| D5: Stale References | 6 | 4 | 2 | COMPLETE |
| D6: Structural | 6 | 3 | 3 | COMPLETE |
| M1: Mortar Routing | 6 | 5 | 1 | COMPLETE |
| V1: Fix Verification | 5 | 2 | 3 | COMPLETE |
| E1: Efficiency/Overhead | 9 | 5 | 4 | COMPLETE |
| **Total** | **56** | **36** | **20** | **COMPLETE** |

---

## Key Findings

- **E1.1** [CONFIRMED/Medium] Wave 3: `isResearchProject()` duplicated in 8 hooks with 2 behavioral divergences -- null guard missing in 7 copies, inline requires in 1
- **E1.4** [CONFIRMED/Medium] Wave 3: Fleet has 3 name collisions across global/BL directories; `tools-manifest` global copy is fully redundant (85% overlap, BL is superset)
- **E1.9** [FALSE_POSITIVE] Wave 3: Auto-loaded context is 22.6K tokens (45% of 50K threshold) -- not breached, but 12.4K tokens of UI rules are irrelevant in non-UI sessions

---

## Open Items

| ID | Wave | Verdict | Severity | Summary |
|----|------|---------|----------|---------|
| M1.3 | 2 | CONFIRMED | Critical | masonry-register.js plain text output -- needs JSON envelope |
| M1.4 | 2 | CONFIRMED | High | Mortar directive is advisory, not enforced -- design decision needed |
| V1.4 | 2 | CONFIRMED | High | onboard hook spawns Python without PYTHONPATH -- silent failure |
| D3.4 | 1 | CONFIRMED | High | TDD enforcer non-functional (async:true + exit(2)) |
| E1.1 | 3 | CONFIRMED | Medium | isResearchProject() duplicated in 8 hooks with behavioral drift |
| E1.4 | 3 | CONFIRMED | Medium | tools-manifest global redundant; health-monitor name collision |
| M1.6 | 2 | CONFIRMED | Medium | mortar.md missing git-nerd and infra routing entries |
| D2.6 | 1 | CONFIRMED | Medium | uiux-master and solana-specialist .md files missing |
| D5.1 | 1 | CONFIRMED | Medium | masonry-build.md uses dead OMC executor |
| E1.2 | 3 | CONFIRMED | Low | 3 hook files exceed 300-line limit |
| E1.5 | 3 | CONFIRMED | Low | DSPy hard dependency should be optional extras |
| E1.8 | 3 | CONFIRMED | Low | 3 dead DSPy signature classes (62% of file) |

### Verified Fixed (Waves 1-2)

| ID | Was | Fix Verified By |
|----|-----|-----------------|
| D4.4 | High | V1.1 -- q_total=46 returned correctly |
| D3.3 | High | V1.2 -- OLLAMA_HOST fallback working |
| D4.3+D6.5 | Medium | V1.3 -- all 5 BL2.0 modes routed |
| D2.2/D4.1 | High | V1.3 -- registry paths corrected |
| M1.1 | Critical | Fixed in commit a038099 |

---
