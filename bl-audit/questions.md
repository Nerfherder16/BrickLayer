# Question Bank — BrickLayer 2.0 Code Health Audit

**Campaign type**: BrickLayer 2.0
**Generated**: 2026-03-21
**Modes selected**: audit, research, diagnose

Rationale: This is a static code audit campaign — no simulate.py. Three modes in use:
- `audit` — compliance checks against known invariants (dead code, config drift, wiring gaps)
- `research` — open investigation questions requiring exploration and synthesis
- `diagnose` — targeted bug hunting where a specific defect is suspected

Domains: D1 Dead Code · D2 Unwired Items · D3 Bugs & Logic Errors · D4 Config Drift · D5 Stale References · D6 Structural Problems

> Block format required — one `## {ID} [{tag}] {title}` header per question,
> followed by `**Field**: value` lines.
> Trowel will abort and auto-invoke question-designer-bl2 if it detects placeholder text.

---

## Wave 1

---

## D1.1 [audit] Are masonry-agent-onboard.js and masonry-recall-check.js dead code?

**Status**: PENDING
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: Both `masonry/src/hooks/masonry-agent-onboard.js` and `masonry/src/hooks/masonry-recall-check.js` exist on disk but are absent from every hook event in `~/.claude/settings.json`. They are never invoked by Claude Code and constitute dead code unless called from another hook.
**Agent**: compliance-auditor
**Success criterion**: Confirm neither file is referenced in `settings.json` or `require()`-d by any other hook; determine whether each was intentionally de-registered (feature retired) or accidentally omitted (regression); produce a verdict of DEAD or UNWIRED for each.

---

## D1.2 [audit] Are the 46 DSPy signature stubs in masonry/src/dspy_pipeline/generated/ dead outputs?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `masonry/src/dspy_pipeline/generated/` contains 46 auto-generated `.py` stub files but `masonry/optimized_prompts/` is empty — no optimization run has ever consumed these stubs. They may be unreferenced dead outputs of the agent-onboard pipeline.
**Agent**: compliance-auditor
**Success criterion**: Confirm whether `optimizer.py` or any runtime path imports from `generated/`; confirm `masonry/optimized_prompts/` is empty; determine if all 46 stubs are dead or legitimately awaiting future optimization runs.

---

## D1.3 [diagnose] Does the ~/.claude/hud/masonry-statusline.js shadow a newer copy in masonry/src/hooks/?

**Status**: PENDING
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `settings.json` `statusLine` points to `C:/Users/trg16/.claude/hud/masonry-statusline.js`, but a copy also exists at `masonry/src/hooks/masonry-statusline.js`. If the hud copy is older or diverged, one is stale dead code running silently.
**Agent**: diagnose-analyst
**Success criterion**: Diff both files; identify which is authoritative; confirm whether `masonry/src/hooks/masonry-statusline.js` is called anywhere else or is entirely dead.

---

## D1.4 [audit] Is mcp_gateway.py at the repo root wired into anything?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `C:/Users/trg16/Dev/Bricklayer2.0/mcp_gateway.py` exists at the repo root outside `masonry/`. It may be an orphaned prototype never imported or invoked by any other file or config.
**Agent**: compliance-auditor
**Success criterion**: Search all `.py` files, `settings.json`, and any MCP server config for imports or subprocess calls to `mcp_gateway.py`; if none found, confirm it is dead code eligible for removal.

---

## D1.5 [audit] Is onboard.py at the repo root superseded by masonry-agent-onboard.js?

**Status**: PENDING
**Mode**: audit
**Priority**: LOW
**Hypothesis**: `C:/Users/trg16/Dev/Bricklayer2.0/onboard.py` predates the JS hook `masonry-agent-onboard.js` and performs the same agent-registration function. It is likely entirely superseded and no longer invoked.
**Agent**: compliance-auditor
**Success criterion**: Read both files; determine if `onboard.py` is called from any script, Makefile, or hook; compare functionality to the JS hook; declare supersession or active survival.

---

## D1.6 [audit] Are there unused functions inside masonry/src/routing/ sub-modules?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `masonry/src/routing/` contains `deterministic.py`, `semantic.py`, `llm_router.py`, and `router.py`. Some helper functions in sub-modules may be defined but never called from `router.py` or any external caller including `masonry/mcp_server/server.py`.
**Agent**: research-analyst
**Success criterion**: Enumerate all public functions/classes in the four routing files; identify any with zero callers inside `masonry/src/` or `masonry/mcp_server/`.

---

## D2.1 [audit] Which hook files in masonry/src/hooks/ are not registered in ~/.claude/settings.json?

**Status**: PENDING
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: Two hook files on disk (`masonry-agent-onboard.js`, `masonry-recall-check.js`) are absent from `~/.claude/settings.json`. Either they were removed intentionally (features retired) or accidentally de-registered (broken features silently not running).
**Agent**: compliance-auditor
**Success criterion**: Produce a definitive two-way matrix — every `settings.json` hook entry maps to an existing file, and every file in `masonry/src/hooks/` maps to a `settings.json` registration. Confirm the two unregistered files and classify each removal as intentional or regression.

---

## D2.2 [audit] Do all agents in agent_registry.yml with file: agents/* have corresponding .md files?

**Status**: PENDING
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: Entries in `masonry/agent_registry.yml` that reference `agents/` paths (e.g., `agents/diagnose-analyst.md`) resolve to `C:/Users/trg16/Dev/Bricklayer2.0/agents/` — a directory that does not exist. The actual files live in `.claude/agents/`. These 15 registry entries are broken pointers.
**Agent**: compliance-auditor
**Success criterion**: List all `file: agents/` entries (quantitative-analyst, peer-reviewer, agent-auditor, forge-check, retrospective, test-writer, diagnose-analyst, compliance-auditor, regulatory-researcher, competitive-analyst, research-analyst, benchmark-engineer, cascade-analyst, health-monitor, evolve-optimizer); verify which `.md` files actually exist and where; map the gap.

---

## D2.3 [audit] Are there agents in ~/.claude/agents/ with no corresponding agent_registry.yml entry?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `~/.claude/agents/` contains 16 agent files (AGENTS.md, architect.md, developer.md, devops.md, health-monitor.md, karen.md, mortar.md, prompt-engineer.md, refactorer.md, rust-analyst.md, rust-developer.md, security.md, self-host.md, spec-writer.md, spreadsheet-wizard.md, test-writer.md). Some may lack `agent_registry.yml` entries and be invisible to the routing engine.
**Agent**: compliance-auditor
**Success criterion**: Cross-reference all `~/.claude/agents/*.md` filenames against `agent_registry.yml`; list any present on disk but absent from the registry (not routable by Masonry).

---

## D2.4 [audit] Does tools-manifest.md accurately reflect the tools exposed by masonry/mcp_server/server.py?

**Status**: PENDING
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: `tools-manifest.md` at the repo root catalogs MCP tools available to agents. The actual tool definitions live in `masonry/mcp_server/server.py`. These two sources have likely drifted — tools added to the server but not documented, or docs referencing removed tools.
**Agent**: compliance-auditor
**Success criterion**: Extract all tool names from `server.py`; compare against tools documented in `tools-manifest.md`; produce a diff showing additions, removals, or parameter mismatches.

---

## D2.5 [audit] Does CLAUDE.md document hooks that settings.json no longer registers?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `~/.claude/CLAUDE.md` lists Masonry hooks with event mappings in a table. Some entries (e.g., `masonry-agent-onboard.js` under PostToolUse) may be documented as active but not present in `settings.json`.
**Agent**: compliance-auditor
**Success criterion**: Compare every hook mentioned in the CLAUDE.md "Masonry Hooks" table against actual `settings.json` entries; flag documented-but-unregistered and registered-but-undocumented entries.

---

## D2.6 [audit] Are there agents in CLAUDE.md routing tables that don't have corresponding .md files?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: CLAUDE.md references agents like `solana-specialist`, `uiux-master`, and `code-reviewer` in routing tables. Some may not have corresponding `.md` files in either `~/.claude/agents/` or `.claude/agents/`.
**Agent**: compliance-auditor
**Success criterion**: Extract all agent names from CLAUDE.md tables and inline references; check both agent directories; report any referenced agents without a file.

---

## D3.1 [diagnose] Can masonry-stop-guard.js incorrectly flag writes from sibling sessions?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: Key invariant #6: the stop guard must never flag files from sibling sessions. If `masonry-stop-guard.js` uses `git status` without filtering by the current session's `masonry-activity-{sessionId}.ndjson` write log, it flags uncommitted files from any concurrent session.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry-stop-guard.js` source; determine whether it cross-references `masonry-activity-{sessionId}.ndjson` to scope changes to the current session; confirm presence or absence of the sibling-session bug.

---

## D3.2 [diagnose] Does masonry-approver.js auto-approve Bash outside of research project context?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: Key invariant #7: Bash auto-approval is only valid inside a BL research campaign. If `masonry-approver.js` lacks correct dual-sentinel `isResearchProject()` detection (requiring BOTH `program.md` AND `questions.md`) for Bash tool inputs, it may over-approve in interactive or build/fix sessions.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry-approver.js`; trace all code paths that lead to approval when toolName is Bash; confirm every such path requires `isResearchProject()` returning true; identify any path that approves Bash without that check.

---

## D3.3 [diagnose] Does the semantic router hardcode its Ollama host instead of reading OLLAMA_HOST?

**Status**: PENDING
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `masonry/src/routing/semantic.py` should connect to Ollama at the `OLLAMA_HOST` env var (`http://192.168.50.62:11434`). If it hardcodes a different host or ignores the env var, it silently fails on every request and falls through to the LLM layer — defeating the zero-LLM-call semantic routing.
**Agent**: diagnose-analyst
**Success criterion**: Read `semantic.py`; confirm it reads `OLLAMA_HOST` from environment rather than a hardcode; trace the fallback path when Ollama is unreachable; confirm threshold (0.75) is applied correctly.

---

## D3.4 [diagnose] Does masonry-tdd-enforcer.js attempt to block writes despite being async: true?

**Status**: PENDING
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `masonry-tdd-enforcer.js` is registered with `async: true` in `settings.json` and cannot block writes regardless of exit code (key invariant #5). If the hook calls `process.exit(2)` or constructs a blocking JSON payload, this is a logic error — the hook believes it can block but it cannot.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry-tdd-enforcer.js`; check for any `process.exit(2)` calls or `{"decision": "block"}` responses; if present, document the logic error and confirm async constraint renders blocking impossible.

---

## D3.5 [diagnose] Do any hooks exit with codes other than 0 or 2, violating the exit-code invariant?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: Key invariant #2: hooks must exit 0 (allow/warn) or 2 (block) — never 1 or other codes. Some hooks may use `process.exit(1)` in error handlers, which could cause unexpected behavior in Claude Code's hook runner.
**Agent**: diagnose-analyst
**Success criterion**: Grep all `.js` files in `masonry/src/hooks/` for `process.exit(`; extract the exit code argument from each call; report any hook using an exit code other than 0 or 2; include `.catch()` fallback handlers.

---

## D3.6 [diagnose] Are there Windows path normalization bugs in hook file-path comparisons?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: Hooks run via Node.js on Windows and receive file paths in mixed formats (`C:\Users\...` from git, `/c/Users/...` from bash, `C:/Users/...` from hook config). Any hook comparing file paths using string equality without normalization produces false negatives — particularly `masonry-stop-guard.js` and `masonry-guard.js`.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry-stop-guard.js` and `masonry-guard.js`; identify all file path comparisons; confirm whether `path.normalize()` or equivalent is applied before comparison; document any raw string comparison that could receive paths in different formats.

---

## D3.7 [diagnose] Does masonry-lint-check.js exit with code 1 on tool-not-found errors?

**Status**: PENDING
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `masonry-lint-check.js` calls external tools (ruff, prettier, eslint). If any subprocess call throws an uncaught exception or the lint tool is missing from PATH, Node.js may exit with code 1, violating invariant #2.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry-lint-check.js`; trace all error handling paths including missing tool, subprocess crash, and timeout; confirm every exit path uses only code 0 or 2.

---

## D3.8 [diagnose] Does the four-layer router's fallback return a valid RoutingDecision or crash?

**Status**: PENDING
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `masonry/src/routing/router.py` is documented as returning `target_agent="user"` on layer-4 fallback. If the fallback path has an unhandled exception or returns a malformed `RoutingDecision`, Masonry crashes instead of gracefully asking for clarification.
**Agent**: diagnose-analyst
**Success criterion**: Read `router.py` fallback branch; confirm it constructs a valid `RoutingDecision` with `target_agent="user"`; check for any unguarded exception paths in `llm_router.py` that could propagate to the caller.

---

## D4.1 [audit] Does agent_registry.yml have entries pointing to non-existent files across all three path conventions?

**Status**: PENDING
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: `agent_registry.yml` references agents across three path conventions: `~/.claude/agents/` (global), `.claude/agents/` (project-level), and `agents/` (bare — resolves to nothing). The bare `agents/` prefix affects 15 agents and is categorically wrong.
**Agent**: compliance-auditor
**Success criterion**: For each registry entry resolve its `file` field (handling `~/` expansion and relative paths from the repo root); check filesystem existence; produce counts: entries with existing files, entries with missing files, grouped by path pattern. Confirm whether any loader tries fallback paths.

---

## D4.2 [audit] Does masonry/mcp_server/server.py expose tools that match what CLAUDE.md documents?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: CLAUDE.md lists 5 Masonry MCP tools (`masonry_route`, `masonry_optimization_status`, `masonry_onboard`, `masonry_drift_check`, `masonry_optimize_agent`). The actual `server.py` may expose more, fewer, or differently-named tools.
**Agent**: compliance-auditor
**Success criterion**: Extract all tool-decorated functions from `masonry/mcp_server/server.py`; compare against the 5 tools listed in CLAUDE.md; list additions and removals.

---

## D4.3 [audit] Do agents with empty modes[] in agent_registry.yml fall through routing silently?

**Status**: PENDING
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: Many agents onboarded via `masonry-agent-onboard.js` frontmatter detection have `modes: []` and `capabilities: []` in the registry (code-reviewer, fix-implementer, git-nerd, trowel, synthesizer-bl2, and others). Empty modes may make them unreachable via the deterministic routing layer.
**Agent**: compliance-auditor
**Success criterion**: Parse `agent_registry.yml`; list all agents with empty `modes` or `capabilities`; cross-reference with `masonry/src/routing/deterministic.py` to confirm whether empty modes means the agent is unroutable; assess operational impact.

---

## D4.4 [audit] Is the masonry_status MCP tool counting questions correctly for BL 2.0 format?

**Status**: PENDING
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: The `masonry_status` tool in `server.py` counts questions by looking for lines starting with `### Q`. BL 2.0 questions use prefixes like `## D1.1`, `## R1.1`, `## D3.2` — not `### Q`. This means the question counter returns 0 for all BL 2.0 projects.
**Agent**: diagnose-analyst
**Success criterion**: Read the question-counting logic in `masonry/mcp_server/server.py`; test the pattern against actual BL 2.0 `questions.md` files; confirm whether it undercounts; identify the correct pattern needed.

---

## D5.1 [audit] Are there remaining oh-my-claudecode references in live non-git-history files?

**Status**: PENDING
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: OMC was uninstalled. References to "oh-my-claudecode" may still exist in hook files, agent `.md` files, documentation, or scripts — dead references to a non-existent tool.
**Agent**: compliance-auditor
**Success criterion**: Search all files under `C:/Users/trg16/Dev/Bricklayer2.0/` and `~/.claude/` for "oh-my-claudecode"; list every file and line; classify each as documentation (acceptable historical note), functional code (must be removed), or config (must be removed).

---

## D5.2 [audit] Are there active references to the retired web dashboard (ports 3100/8100)?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: The web dashboard on ports 3100/8100 is retired. References may persist in hook files, agent instructions, README files, or scripts directing users to a service that no longer runs.
**Agent**: compliance-auditor
**Success criterion**: Search all files for `:3100`, `:8100`, `localhost:3100`, `localhost:8100`; enumerate each occurrence; classify as: documentation acknowledging retirement (ok), active code that attempts to connect (must be updated), or dead script (remove).

---

## D5.3 [audit] Are there DISABLE_OMC references in active code outside of historical documentation?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `DISABLE_OMC=1` was a kill switch for OMC. Post-March 2026, hooks use `isResearchProject()` auto-detection instead. Active code that checks `DISABLE_OMC` is dead conditional logic referencing a removed system.
**Agent**: compliance-auditor
**Success criterion**: Search all `.js`, `.py`, `.md`, `.sh` files for "DISABLE_OMC"; classify each hit as: historical documentation (acceptable), active code checking the env var at runtime (dead — remove), or launch script setting the variable (unnecessary — remove).

---

## D5.4 [audit] Are there Pydantic v1 syntax patterns in the masonry/src/schemas/ v2 codebase?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `masonry/src/schemas/payloads.py` uses Pydantic v2. Code may still contain v1 patterns (`@validator`, `class Config:`, `.dict()`, `.schema()`) that generate deprecation warnings and will break in future Pydantic versions.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry/src/schemas/payloads.py` and any other Pydantic model files; list all v1 syntax instances; confirm correct v2 equivalents (`@field_validator`, `model_config`, `.model_dump()`, `.model_json_schema()`).

---

## D5.5 [audit] Do program.md files reference agents that no longer exist in ~/.claude/agents/?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `program.md` files in research project directories reference agents by name. If an agent was renamed or deleted, the `program.md` instruction points to a non-existent agent and the loop fails silently or routes incorrectly.
**Agent**: compliance-auditor
**Success criterion**: Extract all agent names referenced in every `program.md` across all project subdirectories; cross-reference against `~/.claude/agents/` filenames and `agent_registry.yml`; list stale or missing agent references.

---

## D5.6 [audit] Are there hardcoded Windows absolute paths in hook files that break portability?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: Hook files in `masonry/src/hooks/` may contain hardcoded `C:/Users/trg16/` paths rather than deriving them from `__dirname` or environment variables, breaking the hooks on any machine other than Tim's primary workstation.
**Agent**: research-analyst
**Success criterion**: Scan all `.js` files in `masonry/src/hooks/` for string literals matching `C:/Users/` or `C:\\Users\\`; evaluate whether each hardcode is necessary or should use `os.homedir()` / `__dirname` / env vars.

---

## D6.1 [research] Do masonry-observe.js and masonry-guard.js duplicate campaign-detection logic?

**Status**: PENDING
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: Both `masonry-observe.js` and `masonry-guard.js` fire on Write/Edit events and both likely implement `isResearchProject()` detection. If the logic is copy-pasted rather than shared via a common module, a fix to one will not propagate to the other.
**Agent**: research-analyst
**Success criterion**: Read both hooks; compare their campaign-detection implementations; determine if they share a library or duplicate logic; assess divergence risk between the two copies.

---

## D6.2 [research] Do masonry-session-start.js and masonry-session-end.js have symmetrical state management?

**Status**: PENDING
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: `masonry-session-start.js` writes session state for context restore. `masonry-session-end.js` should clean it up or persist it. If session-end does not clean up all state written by session-start, orphaned session files or stale context accumulates across restarts.
**Agent**: research-analyst
**Success criterion**: Trace all files and data written by `masonry-session-start.js`; confirm each is explicitly handled (read, cleaned, or persisted) by `masonry-session-end.js`; identify any asymmetry.

---

## D6.3 [audit] Is the template/ directory in sync with the live masonry/ implementation?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `C:/Users/trg16/Dev/Bricklayer2.0/template/` is copied to start new projects. If `masonry/` has evolved (new hook events, new schemas, new agent patterns) without updating `template/`, new projects start with outdated scaffolding.
**Agent**: compliance-auditor
**Success criterion**: Compare key files in `template/` against their live equivalents; specifically check `program.md`, `.claude/agents/` contents, and any config files; list divergences that would affect a new project's correctness.

---

## D6.4 [audit] Is masonry-state.json at the repo root tracked by git when it should be gitignored?

**Status**: PENDING
**Mode**: audit
**Priority**: LOW
**Hypothesis**: `C:/Users/trg16/Dev/Bricklayer2.0/masonry-state.json` is a runtime state file written by masonry hooks containing session-transient data. It may be tracked by git if not in `.gitignore`, polluting the commit history with runtime state.
**Agent**: compliance-auditor
**Success criterion**: Check `git status` and root `.gitignore` for `masonry-state.json`; confirm whether it is tracked; assess whether contents are session-transient or intentionally persisted; recommend gitignore action if needed.

---

## D6.5 [research] Do BL 1.x and BL 2.0 agent variants have unambiguous dispatch boundaries in Mortar?

**Status**: PENDING
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: Several agent pairs have overlapping descriptions: `hypothesis-generator` vs `hypothesis-generator-bl2`, `synthesizer` vs `synthesizer-bl2`, `question-designer` vs `question-designer-bl2`. Mortar's deterministic routing may send BL 2.0 campaigns to BL 1.x agents if trigger patterns are ambiguous.
**Agent**: research-analyst
**Success criterion**: Read `mortar.md` and `trowel.md` routing logic; confirm BL 1.x vs BL 2.0 agent dispatch is deterministic and unambiguous; identify any routing path where a BL 2.0 campaign could invoke a BL 1.x agent.

---

## D6.6 [audit] Are runtime artifacts (masonry-activity-*.ndjson, agent_db.json, .ui/, .autopilot/) missing from .gitignore?

**Status**: PENDING
**Mode**: audit
**Priority**: LOW
**Hypothesis**: Masonry generates runtime artifacts that should be gitignored. Some may be missing from `.gitignore` and accidentally committed, polluting version history with session-transient data.
**Agent**: compliance-auditor
**Success criterion**: Read the root `.gitignore` and any project-level `.gitignore` files; compare against known runtime artifact patterns (`masonry-activity-*.ndjson`, `masonry-state.json`, `agent_db.json`, `.ui/`, `.autopilot/`, `history.db`, `masonry/optimized_prompts/`); list any artifacts that are tracked but should be ignored.
