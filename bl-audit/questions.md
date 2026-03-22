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

**Status**: DONE
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: Both `masonry/src/hooks/masonry-agent-onboard.js` and `masonry/src/hooks/masonry-recall-check.js` exist on disk but are absent from every hook event in `~/.claude/settings.json`. They are never invoked by Claude Code and constitute dead code unless called from another hook.
**Agent**: compliance-auditor
**Success criterion**: Confirm neither file is referenced in `settings.json` or `require()`-d by any other hook; determine whether each was intentionally de-registered (feature retired) or accidentally omitted (regression); produce a verdict of DEAD or UNWIRED for each.

---

## D1.2 [audit] Are the 46 DSPy signature stubs in masonry/src/dspy_pipeline/generated/ dead outputs?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `masonry/src/dspy_pipeline/generated/` contains 46 auto-generated `.py` stub files but `masonry/optimized_prompts/` is empty — no optimization run has ever consumed these stubs. They may be unreferenced dead outputs of the agent-onboard pipeline.
**Agent**: compliance-auditor
**Success criterion**: Confirm whether `optimizer.py` or any runtime path imports from `generated/`; confirm `masonry/optimized_prompts/` is empty; determine if all 46 stubs are dead or legitimately awaiting future optimization runs.

---

## D1.3 [diagnose] Does the ~/.claude/hud/masonry-statusline.js shadow a newer copy in masonry/src/hooks/?

**Status**: DONE
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `settings.json` `statusLine` points to `C:/Users/trg16/.claude/hud/masonry-statusline.js`, but a copy also exists at `masonry/src/hooks/masonry-statusline.js`. If the hud copy is older or diverged, one is stale dead code running silently.
**Agent**: diagnose-analyst
**Success criterion**: Diff both files; identify which is authoritative; confirm whether `masonry/src/hooks/masonry-statusline.js` is called anywhere else or is entirely dead.

---

## D1.4 [audit] Is mcp_gateway.py at the repo root wired into anything?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `C:/Users/trg16/Dev/Bricklayer2.0/mcp_gateway.py` exists at the repo root outside `masonry/`. It may be an orphaned prototype never imported or invoked by any other file or config.
**Agent**: compliance-auditor
**Success criterion**: Search all `.py` files, `settings.json`, and any MCP server config for imports or subprocess calls to `mcp_gateway.py`; if none found, confirm it is dead code eligible for removal.

---

## D1.5 [audit] Is onboard.py at the repo root superseded by masonry-agent-onboard.js?

**Status**: DONE
**Mode**: audit
**Priority**: LOW
**Hypothesis**: `C:/Users/trg16/Dev/Bricklayer2.0/onboard.py` predates the JS hook `masonry-agent-onboard.js` and performs the same agent-registration function. It is likely entirely superseded and no longer invoked.
**Agent**: compliance-auditor
**Success criterion**: Read both files; determine if `onboard.py` is called from any script, Makefile, or hook; compare functionality to the JS hook; declare supersession or active survival.

---

## D1.6 [audit] Are there unused functions inside masonry/src/routing/ sub-modules?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `masonry/src/routing/` contains `deterministic.py`, `semantic.py`, `llm_router.py`, and `router.py`. Some helper functions in sub-modules may be defined but never called from `router.py` or any external caller including `masonry/mcp_server/server.py`.
**Agent**: research-analyst
**Success criterion**: Enumerate all public functions/classes in the four routing files; identify any with zero callers inside `masonry/src/` or `masonry/mcp_server/`.

---

## D2.1 [audit] Which hook files in masonry/src/hooks/ are not registered in ~/.claude/settings.json?

**Status**: DONE
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: Two hook files on disk (`masonry-agent-onboard.js`, `masonry-recall-check.js`) are absent from `~/.claude/settings.json`. Either they were removed intentionally (features retired) or accidentally de-registered (broken features silently not running).
**Agent**: compliance-auditor
**Success criterion**: Produce a definitive two-way matrix — every `settings.json` hook entry maps to an existing file, and every file in `masonry/src/hooks/` maps to a `settings.json` registration. Confirm the two unregistered files and classify each removal as intentional or regression.

---

## D2.2 [audit] Do all agents in agent_registry.yml with file: agents/* have corresponding .md files?

**Status**: DONE
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: Entries in `masonry/agent_registry.yml` that reference `agents/` paths (e.g., `agents/diagnose-analyst.md`) resolve to `C:/Users/trg16/Dev/Bricklayer2.0/agents/` — a directory that does not exist. The actual files live in `.claude/agents/`. These 15 registry entries are broken pointers.
**Agent**: compliance-auditor
**Success criterion**: List all `file: agents/` entries (quantitative-analyst, peer-reviewer, agent-auditor, forge-check, retrospective, test-writer, diagnose-analyst, compliance-auditor, regulatory-researcher, competitive-analyst, research-analyst, benchmark-engineer, cascade-analyst, health-monitor, evolve-optimizer); verify which `.md` files actually exist and where; map the gap.

---

## D2.3 [audit] Are there agents in ~/.claude/agents/ with no corresponding agent_registry.yml entry?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `~/.claude/agents/` contains 16 agent files (AGENTS.md, architect.md, developer.md, devops.md, health-monitor.md, karen.md, mortar.md, prompt-engineer.md, refactorer.md, rust-analyst.md, rust-developer.md, security.md, self-host.md, spec-writer.md, spreadsheet-wizard.md, test-writer.md). Some may lack `agent_registry.yml` entries and be invisible to the routing engine.
**Agent**: compliance-auditor
**Success criterion**: Cross-reference all `~/.claude/agents/*.md` filenames against `agent_registry.yml`; list any present on disk but absent from the registry (not routable by Masonry).

---

## D2.4 [audit] Does tools-manifest.md accurately reflect the tools exposed by masonry/mcp_server/server.py?

**Status**: DONE
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: `tools-manifest.md` at the repo root catalogs MCP tools available to agents. The actual tool definitions live in `masonry/mcp_server/server.py`. These two sources have likely drifted — tools added to the server but not documented, or docs referencing removed tools.
**Agent**: compliance-auditor
**Success criterion**: Extract all tool names from `server.py`; compare against tools documented in `tools-manifest.md`; produce a diff showing additions, removals, or parameter mismatches.

---

## D2.5 [audit] Does CLAUDE.md document hooks that settings.json no longer registers?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `~/.claude/CLAUDE.md` lists Masonry hooks with event mappings in a table. Some entries (e.g., `masonry-agent-onboard.js` under PostToolUse) may be documented as active but not present in `settings.json`.
**Agent**: compliance-auditor
**Success criterion**: Compare every hook mentioned in the CLAUDE.md "Masonry Hooks" table against actual `settings.json` entries; flag documented-but-unregistered and registered-but-undocumented entries.

---

## D2.6 [audit] Are there agents in CLAUDE.md routing tables that don't have corresponding .md files?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: CLAUDE.md references agents like `solana-specialist`, `uiux-master`, and `code-reviewer` in routing tables. Some may not have corresponding `.md` files in either `~/.claude/agents/` or `.claude/agents/`.
**Agent**: compliance-auditor
**Success criterion**: Extract all agent names from CLAUDE.md tables and inline references; check both agent directories; report any referenced agents without a file.

---

## D3.1 [diagnose] Can masonry-stop-guard.js incorrectly flag writes from sibling sessions?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: Key invariant #6: the stop guard must never flag files from sibling sessions. If `masonry-stop-guard.js` uses `git status` without filtering by the current session's `masonry-activity-{sessionId}.ndjson` write log, it flags uncommitted files from any concurrent session.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry-stop-guard.js` source; determine whether it cross-references `masonry-activity-{sessionId}.ndjson` to scope changes to the current session; confirm presence or absence of the sibling-session bug.

---

## D3.2 [diagnose] Does masonry-approver.js auto-approve Bash outside of research project context?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: Key invariant #7: Bash auto-approval is only valid inside a BL research campaign. If `masonry-approver.js` lacks correct dual-sentinel `isResearchProject()` detection (requiring BOTH `program.md` AND `questions.md`) for Bash tool inputs, it may over-approve in interactive or build/fix sessions.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry-approver.js`; trace all code paths that lead to approval when toolName is Bash; confirm every such path requires `isResearchProject()` returning true; identify any path that approves Bash without that check.

---

## D3.3 [diagnose] Does the semantic router hardcode its Ollama host instead of reading OLLAMA_HOST?

**Status**: DONE
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `masonry/src/routing/semantic.py` should connect to Ollama at the `OLLAMA_HOST` env var (`http://192.168.50.62:11434`). If it hardcodes a different host or ignores the env var, it silently fails on every request and falls through to the LLM layer — defeating the zero-LLM-call semantic routing.
**Agent**: diagnose-analyst
**Success criterion**: Read `semantic.py`; confirm it reads `OLLAMA_HOST` from environment rather than a hardcode; trace the fallback path when Ollama is unreachable; confirm threshold (0.75) is applied correctly.

---

## D3.4 [diagnose] Does masonry-tdd-enforcer.js attempt to block writes despite being async: true?

**Status**: DONE
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `masonry-tdd-enforcer.js` is registered with `async: true` in `settings.json` and cannot block writes regardless of exit code (key invariant #5). If the hook calls `process.exit(2)` or constructs a blocking JSON payload, this is a logic error — the hook believes it can block but it cannot.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry-tdd-enforcer.js`; check for any `process.exit(2)` calls or `{"decision": "block"}` responses; if present, document the logic error and confirm async constraint renders blocking impossible.

---

## D3.5 [diagnose] Do any hooks exit with codes other than 0 or 2, violating the exit-code invariant?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: Key invariant #2: hooks must exit 0 (allow/warn) or 2 (block) — never 1 or other codes. Some hooks may use `process.exit(1)` in error handlers, which could cause unexpected behavior in Claude Code's hook runner.
**Agent**: diagnose-analyst
**Success criterion**: Grep all `.js` files in `masonry/src/hooks/` for `process.exit(`; extract the exit code argument from each call; report any hook using an exit code other than 0 or 2; include `.catch()` fallback handlers.

---

## D3.6 [diagnose] Are there Windows path normalization bugs in hook file-path comparisons?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: Hooks run via Node.js on Windows and receive file paths in mixed formats (`C:\Users\...` from git, `/c/Users/...` from bash, `C:/Users/...` from hook config). Any hook comparing file paths using string equality without normalization produces false negatives — particularly `masonry-stop-guard.js` and `masonry-guard.js`.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry-stop-guard.js` and `masonry-guard.js`; identify all file path comparisons; confirm whether `path.normalize()` or equivalent is applied before comparison; document any raw string comparison that could receive paths in different formats.

---

## D3.7 [diagnose] Does masonry-lint-check.js exit with code 1 on tool-not-found errors?

**Status**: DONE
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `masonry-lint-check.js` calls external tools (ruff, prettier, eslint). If any subprocess call throws an uncaught exception or the lint tool is missing from PATH, Node.js may exit with code 1, violating invariant #2.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry-lint-check.js`; trace all error handling paths including missing tool, subprocess crash, and timeout; confirm every exit path uses only code 0 or 2.

---

## D3.8 [diagnose] Does the four-layer router's fallback return a valid RoutingDecision or crash?

**Status**: DONE
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `masonry/src/routing/router.py` is documented as returning `target_agent="user"` on layer-4 fallback. If the fallback path has an unhandled exception or returns a malformed `RoutingDecision`, Masonry crashes instead of gracefully asking for clarification.
**Agent**: diagnose-analyst
**Success criterion**: Read `router.py` fallback branch; confirm it constructs a valid `RoutingDecision` with `target_agent="user"`; check for any unguarded exception paths in `llm_router.py` that could propagate to the caller.

---

## D4.1 [audit] Does agent_registry.yml have entries pointing to non-existent files across all three path conventions?

**Status**: DONE
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: `agent_registry.yml` references agents across three path conventions: `~/.claude/agents/` (global), `.claude/agents/` (project-level), and `agents/` (bare — resolves to nothing). The bare `agents/` prefix affects 15 agents and is categorically wrong.
**Agent**: compliance-auditor
**Success criterion**: For each registry entry resolve its `file` field (handling `~/` expansion and relative paths from the repo root); check filesystem existence; produce counts: entries with existing files, entries with missing files, grouped by path pattern. Confirm whether any loader tries fallback paths.

---

## D4.2 [audit] Does masonry/mcp_server/server.py expose tools that match what CLAUDE.md documents?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: CLAUDE.md lists 5 Masonry MCP tools (`masonry_route`, `masonry_optimization_status`, `masonry_onboard`, `masonry_drift_check`, `masonry_optimize_agent`). The actual `server.py` may expose more, fewer, or differently-named tools.
**Agent**: compliance-auditor
**Success criterion**: Extract all tool-decorated functions from `masonry/mcp_server/server.py`; compare against the 5 tools listed in CLAUDE.md; list additions and removals.

---

## D4.3 [audit] Do agents with empty modes[] in agent_registry.yml fall through routing silently?

**Status**: DONE
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: Many agents onboarded via `masonry-agent-onboard.js` frontmatter detection have `modes: []` and `capabilities: []` in the registry (code-reviewer, fix-implementer, git-nerd, trowel, synthesizer-bl2, and others). Empty modes may make them unreachable via the deterministic routing layer.
**Agent**: compliance-auditor
**Success criterion**: Parse `agent_registry.yml`; list all agents with empty `modes` or `capabilities`; cross-reference with `masonry/src/routing/deterministic.py` to confirm whether empty modes means the agent is unroutable; assess operational impact.

---

## D4.4 [audit] Is the masonry_status MCP tool counting questions correctly for BL 2.0 format?

**Status**: DONE
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: The `masonry_status` tool in `server.py` counts questions by looking for lines starting with `### Q`. BL 2.0 questions use prefixes like `## D1.1`, `## R1.1`, `## D3.2` — not `### Q`. This means the question counter returns 0 for all BL 2.0 projects.
**Agent**: diagnose-analyst
**Success criterion**: Read the question-counting logic in `masonry/mcp_server/server.py`; test the pattern against actual BL 2.0 `questions.md` files; confirm whether it undercounts; identify the correct pattern needed.

---

## D5.1 [audit] Are there remaining oh-my-claudecode references in live non-git-history files?

**Status**: DONE
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: OMC was uninstalled. References to "oh-my-claudecode" may still exist in hook files, agent `.md` files, documentation, or scripts — dead references to a non-existent tool.
**Agent**: compliance-auditor
**Success criterion**: Search all files under `C:/Users/trg16/Dev/Bricklayer2.0/` and `~/.claude/` for "oh-my-claudecode"; list every file and line; classify each as documentation (acceptable historical note), functional code (must be removed), or config (must be removed).

---

## D5.2 [audit] Are there active references to the retired web dashboard (ports 3100/8100)?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: The web dashboard on ports 3100/8100 is retired. References may persist in hook files, agent instructions, README files, or scripts directing users to a service that no longer runs.
**Agent**: compliance-auditor
**Success criterion**: Search all files for `:3100`, `:8100`, `localhost:3100`, `localhost:8100`; enumerate each occurrence; classify as: documentation acknowledging retirement (ok), active code that attempts to connect (must be updated), or dead script (remove).

---

## D5.3 [audit] Are there DISABLE_OMC references in active code outside of historical documentation?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `DISABLE_OMC=1` was a kill switch for OMC. Post-March 2026, hooks use `isResearchProject()` auto-detection instead. Active code that checks `DISABLE_OMC` is dead conditional logic referencing a removed system.
**Agent**: compliance-auditor
**Success criterion**: Search all `.js`, `.py`, `.md`, `.sh` files for "DISABLE_OMC"; classify each hit as: historical documentation (acceptable), active code checking the env var at runtime (dead — remove), or launch script setting the variable (unnecessary — remove).

---

## D5.4 [audit] Are there Pydantic v1 syntax patterns in the masonry/src/schemas/ v2 codebase?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `masonry/src/schemas/payloads.py` uses Pydantic v2. Code may still contain v1 patterns (`@validator`, `class Config:`, `.dict()`, `.schema()`) that generate deprecation warnings and will break in future Pydantic versions.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry/src/schemas/payloads.py` and any other Pydantic model files; list all v1 syntax instances; confirm correct v2 equivalents (`@field_validator`, `model_config`, `.model_dump()`, `.model_json_schema()`).

---

## D5.5 [audit] Do program.md files reference agents that no longer exist in ~/.claude/agents/?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `program.md` files in research project directories reference agents by name. If an agent was renamed or deleted, the `program.md` instruction points to a non-existent agent and the loop fails silently or routes incorrectly.
**Agent**: compliance-auditor
**Success criterion**: Extract all agent names referenced in every `program.md` across all project subdirectories; cross-reference against `~/.claude/agents/` filenames and `agent_registry.yml`; list stale or missing agent references.

---

## D5.6 [audit] Are there hardcoded Windows absolute paths in hook files that break portability?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: Hook files in `masonry/src/hooks/` may contain hardcoded `C:/Users/trg16/` paths rather than deriving them from `__dirname` or environment variables, breaking the hooks on any machine other than Tim's primary workstation.
**Agent**: research-analyst
**Success criterion**: Scan all `.js` files in `masonry/src/hooks/` for string literals matching `C:/Users/` or `C:\\Users\\`; evaluate whether each hardcode is necessary or should use `os.homedir()` / `__dirname` / env vars.

---

## D6.1 [research] Do masonry-observe.js and masonry-guard.js duplicate campaign-detection logic?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: Both `masonry-observe.js` and `masonry-guard.js` fire on Write/Edit events and both likely implement `isResearchProject()` detection. If the logic is copy-pasted rather than shared via a common module, a fix to one will not propagate to the other.
**Agent**: research-analyst
**Success criterion**: Read both hooks; compare their campaign-detection implementations; determine if they share a library or duplicate logic; assess divergence risk between the two copies.

---

## D6.2 [research] Do masonry-session-start.js and masonry-session-end.js have symmetrical state management?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: `masonry-session-start.js` writes session state for context restore. `masonry-session-end.js` should clean it up or persist it. If session-end does not clean up all state written by session-start, orphaned session files or stale context accumulates across restarts.
**Agent**: research-analyst
**Success criterion**: Trace all files and data written by `masonry-session-start.js`; confirm each is explicitly handled (read, cleaned, or persisted) by `masonry-session-end.js`; identify any asymmetry.

---

## D6.3 [audit] Is the template/ directory in sync with the live masonry/ implementation?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `C:/Users/trg16/Dev/Bricklayer2.0/template/` is copied to start new projects. If `masonry/` has evolved (new hook events, new schemas, new agent patterns) without updating `template/`, new projects start with outdated scaffolding.
**Agent**: compliance-auditor
**Success criterion**: Compare key files in `template/` against their live equivalents; specifically check `program.md`, `.claude/agents/` contents, and any config files; list divergences that would affect a new project's correctness.

---

## D6.4 [audit] Is masonry-state.json at the repo root tracked by git when it should be gitignored?

**Status**: DONE
**Mode**: audit
**Priority**: LOW
**Hypothesis**: `C:/Users/trg16/Dev/Bricklayer2.0/masonry-state.json` is a runtime state file written by masonry hooks containing session-transient data. It may be tracked by git if not in `.gitignore`, polluting the commit history with runtime state.
**Agent**: compliance-auditor
**Success criterion**: Check `git status` and root `.gitignore` for `masonry-state.json`; confirm whether it is tracked; assess whether contents are session-transient or intentionally persisted; recommend gitignore action if needed.

---

## D6.5 [research] Do BL 1.x and BL 2.0 agent variants have unambiguous dispatch boundaries in Mortar?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: Several agent pairs have overlapping descriptions: `hypothesis-generator` vs `hypothesis-generator-bl2`, `synthesizer` vs `synthesizer-bl2`, `question-designer` vs `question-designer-bl2`. Mortar's deterministic routing may send BL 2.0 campaigns to BL 1.x agents if trigger patterns are ambiguous.
**Agent**: research-analyst
**Success criterion**: Read `mortar.md` and `trowel.md` routing logic; confirm BL 1.x vs BL 2.0 agent dispatch is deterministic and unambiguous; identify any routing path where a BL 2.0 campaign could invoke a BL 1.x agent.

---

## D6.6 [audit] Are runtime artifacts (masonry-activity-*.ndjson, agent_db.json, .ui/, .autopilot/) missing from .gitignore?

**Status**: DONE
**Mode**: audit
**Priority**: LOW
**Hypothesis**: Masonry generates runtime artifacts that should be gitignored. Some may be missing from `.gitignore` and accidentally committed, polluting version history with session-transient data.
**Agent**: compliance-auditor
**Success criterion**: Read the root `.gitignore` and any project-level `.gitignore` files; compare against known runtime artifact patterns (`masonry-activity-*.ndjson`, `masonry-state.json`, `agent_db.json`, `.ui/`, `.autopilot/`, `history.db`, `masonry/optimized_prompts/`); list any artifacts that are tracked but should be ignored.

---

## Wave 2

Domains: M (Mortar Adherence) · V (Post-fix Validation)

Focus: Does the Mortar routing system actually function as documented? Do the Phase 1/2 fixes hold under inspection?

---

## M1.1 [diagnose] Does masonry-register.js crash silently due to a duplicate `const cwd` declaration?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: `masonry-register.js` declares `const cwd` on line 88 (`const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd()`) and again on line 105 inside the same `main()` function scope. In strict mode (`'use strict'` is declared at line 1), a duplicate `const` declaration is a SyntaxError that crashes the process before any output is written — meaning the Mortar routing directive is never injected on any prompt.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry/src/hooks/masonry-register.js` fully; confirm or deny the duplicate `const cwd` declaration; determine whether Node.js would throw a SyntaxError or silently shadow; test by running the hook directly; confirm whether the Mortar directive has ever successfully been injected.

---

## M1.2 [diagnose] Does the routing_log.jsonl contain only empty `{}` objects, indicating the subagent-tracker write path is broken?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: `masonry/routing_log.jsonl` has 43 entries, all empty `{}`. The file is written by `masonry-subagent-tracker.js` (SubagentStart hook) and `masonry-observe.js` (PostToolUse). If both writers are appending empty objects, the DSPy routing training signal is entirely absent and `score_routing.py` has no data to score.
**Agent**: diagnose-analyst
**Success criterion**: Read both `masonry-subagent-tracker.js` and `masonry-observe.js` routing-log write paths; identify the condition under which they write `{}`; confirm whether any valid entry has ever been written; determine if the schema mismatch or missing fields causes serialization to produce empty objects.

---

## M1.3 [diagnose] Does masonry-register.js output conform to the Claude Code UserPromptSubmit hook spec for context injection?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: `masonry-register.js` writes plain text to stdout (e.g., `[MASONRY] Route this prompt through Mortar...`). The Claude Code UserPromptSubmit hook spec may require a structured JSON envelope (e.g., `{"type": "context", "text": "..."}`) for the output to be injected as system context. Plain-text stdout may be silently ignored, meaning the Mortar directive never reaches the model.
**Agent**: diagnose-analyst
**Success criterion**: Read the Claude Code hook documentation or any spec file in the repo describing UserPromptSubmit output format; confirm whether plain-text stdout is valid or whether a JSON envelope is required; compare against what `masonry-register.js` actually writes; cross-reference with how other UserPromptSubmit hooks (e.g., `recall-retrieve.js`) format their output.

---

## M1.4 [research] When the Mortar directive IS successfully injected, does Claude Code invoke mortar.md as an agent subagent or treat it as advisory context text?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: The `[MASONRY] Route this prompt through Mortar (.claude/agents/mortar.md)` directive is injected as a system message. Claude Code may interpret `.claude/agents/mortar.md` as an agent to invoke (spawning a subagent), as a file to read as context, or may ignore the instruction entirely and handle the request inline. The distinction determines whether Mortar's multi-agent dispatch actually fires.
**Agent**: research-analyst
**Success criterion**: Read `mortar.md` and `masonry-register.js`; determine the intended mechanism (subagent invocation vs context injection); check whether any session transcripts or logs show mortar.md being invoked as an agent vs. referenced as context; assess whether the "Every request → Mortar" policy is architecturally enforced or advisory-only.

---

## M1.5 [audit] Does masonry-register.js suppress Mortar injection in the bl-audit working directory, breaking routing during the audit itself?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `masonry-register.js` line 89: `if (isResearchProject(cwd)) return;` — `isResearchProject()` checks for both `program.md` AND `questions.md`. The `bl-audit/` directory has both files (it IS a research project). This means whenever Claude Code runs in `bl-audit/`, the Mortar directive is suppressed, and no routing occurs — the system running the audit is itself unrouted.
**Agent**: compliance-auditor
**Success criterion**: Confirm `bl-audit/` contains both `program.md` and `questions.md`; confirm `isResearchProject()` returns true for this path; determine the consequence — does masonry-register.js fully exit before writing the Mortar directive, meaning all audit-session prompts ran without Mortar routing?

---

## M1.6 [research] Does mortar.md contain routing trigger patterns that cover all task types, or are coding/git/docs tasks unrepresented?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: Mortar is supposed to route ALL request types (coding, research, git, docs, UI, campaigns). If `mortar.md` only contains campaign routing patterns and lacks deterministic triggers for `fix this bug`, `git commit`, `update the docs` type requests, those tasks fall through and are handled inline by Claude without specialist dispatch.
**Agent**: research-analyst
**Success criterion**: Read `mortar.md` fully; catalog all routing patterns and dispatch targets; identify which request types have explicit routing rules and which are handled by fallback or inline; assess whether the "Mortar dispatches ALL work" claim in CLAUDE.md is supported by the agent's actual instruction set.

---

## V1.1 [audit] After the D4.4 fix, does masonry_status correctly count questions for the bl-audit campaign?

**Status**: DONE
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: Phase 1 fixed `masonry_status` to recognize BL2.0 `## D1.1` format headers. The bl-audit campaign has 32 questions in this format. If the fix was applied correctly, `masonry_status` should now return `q_total=32` and accurate done/pending counts instead of the previous `q_total=0`.
**Agent**: compliance-auditor
**Success criterion**: Read the question-counting logic in `masonry/mcp_server/server.py`; verify the BL2.0 header pattern is now handled; count questions in `bl-audit/questions.md` against the pattern to confirm the fix produces the correct total; confirm no regression for BL1.x `### Q` format.

---

## V1.2 [diagnose] After the D3.3 OLLAMA_URL fix, does semantic.py now successfully read the OLLAMA_HOST env var?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: The D3.3 fix changed `semantic.py` to read both `OLLAMA_URL` and `OLLAMA_HOST` with fallback. The actual fix should have been applied during Phase 1. Confirm the fix is in place in the live file, that the env var `OLLAMA_HOST=http://192.168.50.62:11434` (set in settings.json) is correctly read, and that a connection attempt to Ollama succeeds.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry/src/routing/semantic.py`; confirm the OLLAMA_URL/OLLAMA_HOST fallback chain is present; verify Ollama is reachable at the configured host; confirm semantic routing can produce a similarity score for a test query.

---

## V1.3 [audit] After D4.3+D6.5, does deterministic routing successfully match Mode fields to the correct BL2.0 agents?

**Status**: DONE
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: Phase 2 added modes frontmatter to 16 agents and registered their mode values. The deterministic router's `get_agents_for_mode()` should now return `diagnose-analyst` for `**Mode**: diagnose`, `compliance-auditor` for `**Mode**: audit`, etc. Before the fix, all 16 agents returned nothing from this lookup.
**Agent**: compliance-auditor
**Success criterion**: Import `masonry/src/routing/deterministic.py` and `masonry/src/routing/registry_loader.py`; load the registry; call `get_agents_for_mode()` for each of the five BL2.0 modes (`audit`, `research`, `diagnose`, `simulate`, `campaign`); confirm each returns at least one agent; confirm BL1.x variants (`synthesis-bl1`, `hypothesis-bl1`) are NOT returned for BL2.0 mode labels.

---

## V1.4 [diagnose] Does masonry-agent-onboard.js (now registered in settings.json) successfully fire and update the registry when a new agent .md is written?

**Status**: DONE
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: Phase 1 registered `masonry-agent-onboard.js` in settings.json as an async PostToolUse hook for Write/Edit events. The hook calls `onboard_agent.py` to extract frontmatter and upsert the registry. If the hook has path assumptions or env var dependencies that prevent `onboard_agent.py` from running (e.g., the `PYTHONPATH` issue discovered during Phase 2), the registration is nominal but the pipeline is still broken.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry-agent-onboard.js` fully; trace the subprocess call to `onboard_agent.py`; confirm whether PYTHONPATH or working-directory is set correctly for the Python invocation; determine if the hook would succeed end-to-end or fail silently due to the same import error seen when running onboard_agent.py manually.

---

## Wave 3

Domains: E (Economizer — efficiency, dead weight, duplication, context overhead)

Focus: Whole-codebase efficiency audit targeting the economizer agent's six scan categories — dead code, duplication, over-engineering, dependency bloat, context overhead, and complexity hotspots.

---

## E1.1 [audit] Is `isResearchProject()` copy-pasted into 9 separate hook files instead of a shared utility?

**Status**: DONE
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: `isResearchProject()` is defined independently in at least 9 hook files (`masonry-approver.js`, `masonry-build-guard.js`, `masonry-context-safety.js`, `masonry-lint-check.js`, `masonry-register.js`, `masonry-session-start.js`, `masonry-stop-guard.js`, `masonry-tdd-enforcer.js`, and possibly others). Each copy may have drifted — `masonry-approver.js` additionally defines `isResearchProjectFresh()` as a variant. This is a textbook duplication problem: a fix to one copy never propagates to the others, as demonstrated by divergence already found in D3.2.
**Agent**: economizer
**Success criterion**: Read all 9+ `isResearchProject` definitions; count lines of duplicated logic; identify any behavioral divergence between copies; quantify total lines that could be replaced by a single shared `masonry-utils.js` module; estimate effort (Low) and impact (High — single source of truth for a security-critical gate).

---

## E1.2 [audit] Are masonry-observe.js and masonry-tdd-enforcer.js over 300 lines and decomposable?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `masonry-observe.js` (317 lines) and `masonry-tdd-enforcer.js` (311 lines) exceed the project's 300-line hard limit per `quality-standards.md`. `masonry-approver.js` (315 lines) also exceeds it. Files at this size typically contain multiple logical concerns that should be split into focused modules. Additionally, `masonry-session-summary.js` (288 lines) and `masonry-statusline.js` (273 lines) approach the limit and may benefit from decomposition.
**Agent**: economizer
**Success criterion**: For each file above 300 lines, identify the distinct logical concerns present; propose a decomposition into sub-modules with estimated line counts; confirm whether any sub-module would be shared across multiple hooks (reducing total lines further); score each split by effort/impact.

---

## E1.3 [audit] Does `deterministic.py` at 387 lines contain dead routing branches for retired agent patterns?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `masonry/src/routing/deterministic.py` is the largest Python file at 387 lines — 29% over the 300-line limit. It contains keyword-based routing tables and pattern matchers. Some entries may target agents that no longer exist (e.g., BL 1.x variants, retired agents), making those branches permanently dead. Additionally, helper functions `_read_file` and `_read_json` (lines 228-244) may duplicate functionality already in the standard library or in `registry_loader.py`.
**Agent**: economizer
**Success criterion**: Read `deterministic.py` fully; identify routing table entries that target agents not present in `agent_registry.yml` or either agents directory; identify any helper functions with zero callers outside this file that duplicate stdlib; quantify dead lines and propose either removal or extraction to a shared utils module.

---

## E1.4 [audit] Are there near-duplicate agents in the fleet whose descriptions overlap >60% and could be merged?

**Status**: PENDING
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: The combined agent fleet (~20 global agents in `~/.claude/agents/` plus ~33 project agents in `.claude/agents/`) contains multiple pairs with potentially overlapping responsibilities: `health-monitor` exists in both directories with different descriptions (fleet performance vs. live system health); `mortar.md` exists in both directories; `tools-manifest.md` exists in both directories (not an agent — likely misplaced); `hypothesis-generator` and `hypothesis-generator-bl2` coexist; `synthesizer` and `synthesizer-bl2` coexist. Each duplicate adds context overhead on every session start.
**Agent**: economizer
**Success criterion**: Read the `description:` and `capabilities:` frontmatter from all agents in both directories; identify pairs with overlapping responsibilities; flag agents that exist in both directories with diverged content (duplication risk) vs. intentional overrides; estimate total context tokens consumed by redundant agents per session; recommend merge or deprecation candidates.

---

## E1.5 [audit] Does `masonry/requirements.txt` pull in `dspy>=2.5` for a pipeline that has never run a successful optimization?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `masonry/requirements.txt` lists four dependencies: `pydantic>=2.10`, `pyyaml>=6.0`, `httpx>=0.27`, `dspy>=2.5`. DSPy is a large ML framework (pulls in PyTorch, transformers, and multiple ML transitive dependencies). The `masonry/optimized_prompts/` directory is empty — no optimization has ever completed. If DSPy is only used by `masonry/src/dspy_pipeline/optimizer.py` which itself is never invoked in production, the requirement may be a heavy optional dependency being carried as a hard dependency. Additionally, `httpx` may overlap with Python's native `urllib` for simple HTTP calls in `semantic.py`.
**Agent**: economizer
**Success criterion**: Audit which files import `dspy`, `httpx`, and `pyyaml`; determine if any import is in a production-critical path vs. an optimization-only path that could be behind a try/import guard; estimate the install footprint of `dspy>=2.5`; recommend whether DSPy should be an optional/extra dependency rather than a hard requirement.

---

## E1.6 [audit] Do CLAUDE.md and the rules files contain redundant content that is already enforced by active hooks?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `~/.claude/CLAUDE.md` documents hook behavior in detail (e.g., "masonry-lint-check.js runs ruff + prettier + eslint after every write"). The hooks themselves enforce this behavior — the documentation in CLAUDE.md is advisory context loaded into every session. If CLAUDE.md describes what hooks already do automatically, those sections add token overhead without adding routing signal. Additionally, several `.claude/rules/` files (tdd-enforcement.md, verification-checklist.md, spec-workflow.md) may overlap with each other and with hook behavior already enforced by `masonry-tdd-enforcer.js` and `masonry-build-guard.js`.
**Agent**: economizer
**Success criterion**: Read CLAUDE.md "Masonry Hooks" section and all files in `~/.claude/rules/`; identify content that describes behavior already enforced by a registered hook vs. content that provides genuine routing signal or override instructions; estimate total tokens consumed by redundant documentation per session; recommend which sections could be condensed or removed.

---

## E1.7 [audit] Does the masonry `package.json` declare zero dependencies while hooks use `require()` calls that assume global installs?

**Status**: PENDING
**Mode**: audit
**Priority**: MEDIUM
**Hypothesis**: `masonry/package.json` has `"dependencies": {}` — it declares no runtime dependencies. Yet hook files use `require('../core/recall')`, `require('../core/state')`, and potentially other internal modules. If any hook `require()`s a package that is not listed in `package.json` and not a Node.js built-in, the hook silently fails on a fresh install (no `node_modules/`). The `bin/` entry points may also have undeclared assumptions. This is a dependency-declaration gap, not a bloat issue, but falls within the economizer's "dead config keys" and "installed but undeclared" scope.
**Agent**: economizer
**Success criterion**: Enumerate all `require()` calls across all `.js` files in `masonry/src/hooks/` and `masonry/bin/`; classify each as: Node.js built-in (safe), internal relative path (safe if file exists), or third-party package (must be in `package.json`); list any third-party requires not declared in `package.json`; assess whether the empty `dependencies: {}` is intentional (self-contained) or an oversight.

---

## E1.8 [audit] Is `masonry/src/dspy_pipeline/signatures.py` dead weight — 112 lines of DSPy class definitions with no callers in the production path?

**Status**: PENDING
**Mode**: audit
**Priority**: LOW
**Hypothesis**: `masonry/src/dspy_pipeline/signatures.py` contains DSPy `Signature` class definitions (~112 lines). The DSPy pipeline was never successfully run (empty `optimized_prompts/`). If `signatures.py` is only imported by `optimizer.py` which is never invoked at runtime (only via `masonry_optimize_agent` MCP tool, manually), then the entire `dspy_pipeline/` subdirectory is effectively a draft that adds import overhead and maintenance surface without contributing to any production path. This connects to D1.2 (46 dead generated stubs) already confirmed DONE.
**Agent**: economizer
**Success criterion**: Map all callers of `signatures.py` classes across the codebase; determine if any production-critical path (MCP server startup, routing, hook execution) imports from `dspy_pipeline/`; confirm whether the entire subdirectory is exclusively triggered by the manual MCP tool call; estimate the token and import-time overhead of carrying dspy as a hard dependency; score removal vs. optional-extras approach by effort/impact.

---

## E1.9 [audit] Does the combined CLAUDE.md + rules + agent fleet load more than 50K tokens of context overhead per session?

**Status**: PENDING
**Mode**: audit
**Priority**: HIGH
**Hypothesis**: Each Claude Code session loads: `~/.claude/CLAUDE.md` (estimated ~600 lines), all `.claude/rules/*.md` files (10 files, ~1,400 lines total), and the project's `CLAUDE.md` (~120 lines). On top of this, `masonry-session-start.js` may inject additional campaign context. The economizer's context overhead analysis targets sessions where >30% of loaded context is boilerplate with no routing signal. The total may approach or exceed 50K tokens before any user message is processed — significant overhead for every session regardless of task type.
**Agent**: economizer
**Success criterion**: Count total lines across `~/.claude/CLAUDE.md`, all files in `~/.claude/rules/`, `C:/Users/trg16/Dev/Bricklayer2.0/.claude/CLAUDE.md`, and any context injected by `masonry-session-start.js`; convert to approximate token count (1 token ≈ 4 chars); identify sections with zero routing signal (pure documentation, historical notes, examples not referenced by hooks); estimate token savings from condensing; flag any rules files with >50% overlap with another rules file.

