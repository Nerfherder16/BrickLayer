# Phase 3 Remediation Plan
**Date**: 2026-03-21
**Status**: Ready to execute (Phase 1+2 verified ✅)

---

## Phase 3: Active Runtime Fixes (core features)

These fix things that are silently broken in everyday use.

### P3.1 — Fix `/build` skill: replace dead subagent_type (D5.1) [High]

**File**: `~/.claude/agents/masonry-build.md`
**Problem**: Uses `subagent_type="oh-my-claudecode:executor"` — OMC is deleted. Every `/build` invocation fails to spawn the build worker.
**Fix**: Replace all `subagent_type="oh-my-claudecode:executor"` with `subagent_type="developer"`.
**Verify**: `grep -n "oh-my-claudecode" ~/.claude/agents/masonry-build.md` returns 0 lines.

---

### P3.2 — Create uiux-master.md + solana-specialist.md (D2.6) [High]

**Files**: `~/.claude/agents/uiux-master.md`, `~/.claude/agents/solana-specialist.md`
**Problem**: CLAUDE.md routing table references both agents; `/ui-*` skills invoke uiux-master. No .md files exist. Skills fail silently.
**Fix**: Create stub agent files with correct frontmatter (name, description, capabilities, modes) pointing to existing agents as their base. Min viable stubs that let routing succeed.
**Verify**: Both files exist and parse cleanly. Onboard hook adds them to registry.

---

### P3.3 — Fix onboard hook: skip non-agent files (D1.1 side-effect) [Medium]

**File**: `masonry/src/hooks/masonry-agent-onboard.js`
**Problem**: Hook fires on ANY Write/Edit to .md files — including `AUDIT_REPORT.md`, `synthesis.md`, etc. Generates phantom DSPy stubs for non-agent files (those without `name:` frontmatter).
**Fix**: At top of hook, read the file and check for YAML frontmatter `name:` field. If absent, exit 0 without onboarding.
**Verify**: Write a finding .md → no registry change. Write an agent .md with `name:` → registry updated.

---

### P3.4 — Remove DISABLE_OMC from all active files (D5.3) [Medium]

**Files**:
- `~/.claude/agents/karen.md`
- `masonry/src/hooks/masonry-session-start.js` (launch instruction comment)
- `bl/nl_entry.py`
- Any `program.md` files containing `DISABLE_OMC=1`

**Problem**: `DISABLE_OMC=1` is a no-op since OMC removal. Files teaching this as required create a false mental model. Future operators (and agents reading these files) will think it's required.
**Fix**: Remove all `DISABLE_OMC` references. Update launch instructions where present to remove the env var.
**Verify**: `grep -r "DISABLE_OMC" ~/.claude masonry/ bl/ --include="*.md" --include="*.js" --include="*.py"` returns 0 lines.

---

### P3.5 — Fix hardcoded blRoot path in session-start hook (D5.6) [Medium]

**File**: `masonry/src/hooks/masonry-session-start.js`
**Line**: ~123 — hardcodes `C:/Users/trg16/Dev/Bricklayer2.0`
**Problem**: Session-start context restoration silently skips on casaclaude/proxyclaude because the path doesn't exist there.
**Fix**: Replace hardcoded path with sentinel-file detection — walk up from `process.cwd()` looking for `masonry.json` OR both `program.md + questions.md`. Use the found directory as blRoot.
**Verify**: On a machine where the hardcoded path doesn't exist, hook still finds and restores context.

---

## Phase 4: Documentation Sync (accuracy)

These eliminate the false-confidence documentation surface.

### P4.1 — Sync CLAUDE.md MCP tools table (D4.2) [Medium]

**File**: `~/.claude/CLAUDE.md` (Masonry MCP Tools section)
**Problem**: Lists 5 of 14 tools. 9 tools undocumented including `masonry_status`, `masonry_questions`, `masonry_fleet`.
**Fix**: Update table to list all 14 tools from `server.py` with purpose column.
**Source of truth**: `masonry/mcp_server/server.py` — grep for `@mcp.tool()` decorators.

---

### P4.2 — Regenerate tools-manifest.md from server.py (D2.4) [Low]

**File**: `~/.claude/agents/tools-manifest.md`
**Problem**: Documents 4 phantom tools (don't exist in server.py), missing 7 real tools.
**Fix**: Script or manually regenerate by reading all `@mcp.tool()` definitions in server.py. Replace tools-manifest.md content.
**Verify**: Every tool in the manifest exists in server.py. Every `@mcp.tool()` in server.py appears in the manifest.

---

### P4.3 — Sync CLAUDE.md hook table with settings.json (D2.5) [Low]

**File**: `~/.claude/CLAUDE.md` (Masonry Hooks section)
**Problem**: Lists masonry-agent-onboard as inactive (it's now active per Phase 1). Missing masonry-tdd-enforcer entry.
**Fix**: Cross-reference every hook in settings.json against the CLAUDE.md table. Add missing, mark inactive ones correctly.

---

## Phase 5: Security + Dead Code Cleanup

### P5.1 — Delete mcp_gateway.py + rotate Exa API key (D1.4) [Critical — do first]

**File**: `masonry/mcp_server/mcp_gateway.py`
**Problem**: Contains hardcoded Exa API key `b4f32c4e-14af-43a5-8ae3-1c93f3fbe39b` committed to git history. File is dead (never imported, no entrypoint) but the key is in git history.
**Action**:
1. Delete `mcp_gateway.py`
2. Rotate the Exa API key at exa.ai (the committed key should be considered compromised)
3. Add key to `.gitignore` / `.env` pattern in repo
**Note**: Key is already in git history — rotation is the only real mitigation.

---

### P5.2 — Delete orphaned DSPy generated/ stubs (D1.2) [Low]

**Directory**: `masonry/src/dspy_pipeline/generated/`
**Problem**: 46 auto-generated stubs from phantom onboard runs. None imported, optimizer has never run. They're noise that grows with each broken onboard event.
**Fix**: Delete the directory. Once optimization pipeline is actually working end-to-end, let it regenerate from real data.
**Verify**: `ls masonry/src/dspy_pipeline/generated/` returns no .py stubs.

---

### P5.3 — Update .gitignore for runtime artifacts (D6.6) [Low]

**File**: `C:/Users/trg16/Dev/Bricklayer2.0/.gitignore`
**Add**:
```
masonry/agent_db.json
masonry/optimized_prompts/
masonry-activity-*.ndjson
masonry/routing_log.jsonl
masonry/training_data/
masonry/vigil/
```
**Problem**: These are runtime output files being committed alongside source. Makes git history noisy and can leak scoring data.

---

### P5.4 — Remove port 3100 dashboard references (D5.2) [Low]

**Files**: Any `bl/runners/` files and `QUICKSTART.md` referencing port 3100 or "dashboard frontend".
**Fix**: Replace with Kiln-only references. The web dashboard was retired.
**Verify**: `grep -r "3100\|dashboard frontend" bl/ QUICKSTART.md` returns 0 lines.

---

## Execution Order

```
P5.1 → (security, do first, needs key rotation)
P3.1 → P3.2 → P3.3 → P3.4 → P3.5  (runtime fixes, ordered by impact)
P4.1 → P4.2 → P4.3                  (doc sync, can run in parallel)
P5.2 → P5.3 → P5.4                  (cleanup, low risk)
```

## Remaining Verification Items (from Phase 2)

- **test-writer.md missing** (1 broken registry path): Either create `~/.claude/agents/test-writer.md` or remove the `test-writer` entry from `agent_registry.yml`.
- **1 agent with `modes: []`**: After P3.1-P3.2, run `python masonry/scripts/onboard_agent.py --agents-dir ~/.claude/agents/` to regenerate modes for any remaining empty entries.
