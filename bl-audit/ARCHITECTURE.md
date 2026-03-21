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
| **Total** | **36** | **24** | **12** | **COMPLETE** |

---

## Key Findings

- **D3.4** [CONFIRMED/High] Wave 1: TDD enforcer async:true defeats exit(2) -- enforcement entirely non-functional
- **D4.4** [CONFIRMED/High] Wave 1: masonry_status question parser BL1.x-only -- Kiln shows 0% for all BL2.0 campaigns
- **D3.3** [CONFIRMED/High] Wave 1: semantic.py reads OLLAMA_URL but env sets OLLAMA_HOST -- semantic routing always falls through

---

## Open Items

| ID | Verdict | Severity | Summary |
|----|---------|----------|---------|
| D3.4 | CONFIRMED | High | TDD enforcer non-functional (async:true + exit(2)) |
| D4.4 | CONFIRMED | High | masonry_status returns q_total=0 for BL2.0 |
| D3.3 | CONFIRMED | High | Semantic router reads wrong env var |
| D2.2/D4.1 | CONFIRMED | High | 9+ registry paths point to wrong location |
| D1.1/D2.1 | CONFIRMED | Medium | Agent onboard hook not registered |
| D2.6 | CONFIRMED | Medium | uiux-master and solana-specialist missing |
| D4.3 | CONFIRMED | Medium | 16 agents unreachable via Mode routing |
| D5.1 | CONFIRMED | Medium | masonry-build.md uses dead OMC executor |

---
