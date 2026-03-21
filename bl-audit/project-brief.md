# Project Brief — BrickLayer 2.0 Code Health Audit

**Authority tier: Tier 1 — Ground Truth. Human eyes only. Do not modify during campaigns.**

---

## What This Campaign Is

A full codebase audit of the BrickLayer 2.0 platform at `C:/Users/trg16/Dev/Bricklayer2.0/`.
The goal is to find bugs, dead code, unwired items, config drift, stale references, and
structural problems — then produce actionable findings for each.

This is NOT a simulation campaign. There is no `simulate.py` to run. The research method
is static analysis + dynamic tracing through the codebase itself.

---

## The System Under Audit

BrickLayer 2.0 is a three-layer AI development platform:

```
Claude Code  (user-facing)
     ↕
  Masonry    (bridge: MCP server, hooks, routing, DSPy, agent registry)
     ↕
BrickLayer   (research loop, campaigns, simulations, agent fleet, findings)
     +
  Mortar     (executive router — all requests dispatched through here)
  Kiln       (Electron desktop app — monitors campaigns, findings, queue)
```

### Key Directories

```
masonry/src/hooks/          — 22 Claude Code hooks (JS)
masonry/src/routing/        — four-layer router (deterministic→semantic→LLM→fallback)
masonry/src/dspy_pipeline/  — DSPy MIPROv2 optimization pipeline
masonry/src/schemas/        — Pydantic v2 payload models
masonry/mcp_server/         — FastAPI MCP server
masonry/agent_registry.yml  — declarative agent registry
~/.claude/agents/           — global agent .md files (mortar, trowel, karen, etc.)
~/.claude/settings.json     — global hook configuration
.claude/agents/             — project-level agent overrides
template/                   — canonical project template
```

---

## Research Domains

### Domain 1 — Dead Code
Functions, classes, routes, hooks, or agents that are defined but never called/invoked.
Look in: hooks, routing/, dspy_pipeline/, mcp_server/, bl/ package, analyze.py.

### Domain 2 — Unwired Items
Things that exist in one layer but not connected to another:
- Hooks in `masonry/src/hooks/` not registered in `~/.claude/settings.json`
- Agents in `agent_registry.yml` with no corresponding `.md` file (or vice versa)
- MCP tools defined in the server but not listed in `tools-manifest.md`
- DSPy signatures generated but no optimizer configured for them
- `program.md` referencing agents that don't exist in `~/.claude/agents/`

### Domain 3 — Bugs & Logic Errors
- Race conditions in async hooks
- Incorrect exit codes (blocking when should warn, or vice versa)
- Path normalization bugs (Windows `/c/Users/...` vs `C:\Users\...`)
- Incorrect Pydantic schema field types
- Router returning wrong agent for known patterns

### Domain 4 — Config Drift
- `~/.claude/settings.json` hook list vs actual files in `masonry/src/hooks/`
- `agent_registry.yml` entries vs actual `.md` files
- `tools-manifest.md` vs actual MCP server tools
- `constants.py` thresholds that have drifted from documented values

### Domain 5 — Stale References
- Remaining `oh-my-claudecode` references anywhere in the codebase
- References to the old web dashboard (port 3100/8100)
- `DISABLE_OMC` references outside of git history
- Hardcoded paths that no longer exist
- Deprecated API patterns (Pydantic v1 syntax in a v2 codebase)

### Domain 6 — Structural Problems
- Hook files that duplicate logic already handled by another hook
- Agents in the fleet with overlapping responsibilities and no clear boundary
- Missing `.gitignore` entries for known runtime artifacts
- Template files out of sync with the live masonry/ implementation

---

## Key Invariants (Never Violate)

1. `program.md` and `constants.py` are Tier 1 — never edited by agents
2. Hooks must exit 0 (allow/warn) or 2 (block) — never 1 or other codes
3. `isResearchProject()` detection must use BOTH `program.md` AND `questions.md`
4. `masonry-activity-{sessionId}.ndjson` is the authoritative session write log
5. Async hooks (`async: true`) cannot block tool calls regardless of exit code
6. The stop guard must never flag files from sibling sessions
7. BL research campaigns are the only context where Bash is fully auto-approved

---

## Past Misunderstandings (Do Not Repeat)

- **OMC is gone.** `DISABLE_OMC=1` was a dead kill switch until March 2026 when hooks
  were updated to use `isResearchProject()` auto-detection instead.
- **The web dashboard is retired.** All monitoring goes through Kiln (Electron app).
- **`masonry-tdd-enforcer.js` is `async: true`** — it cannot actually block writes,
  it only surfaces warnings.
- **The approver hook does NOT auto-approve Bash** in build/fix mode — only in research
  project context. Intentional to prevent unsafe command approval in interactive sessions.

---

## What a Good Finding Looks Like

Each finding must:
- Identify the EXACT file(s) and line numbers involved
- Reproduce or demonstrate the problem
- Assess severity: Critical / High / Medium / Low / Info
- Propose a specific fix
- Verdict: CONFIRMED / FALSE_POSITIVE / INCONCLUSIVE
