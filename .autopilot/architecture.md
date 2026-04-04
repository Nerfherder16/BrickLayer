# Architecture: Phase 6 — Dev Execution Loop + Infrastructure + Agents + Skills + UI Quality

---

## Section 1: Component Map

**New:**
- `~/.claude/agents/spec-reviewer.md` — read-only pipeline gate between developer and code-reviewer; returns COMPLIANT/OVER_BUILT/UNDER_BUILT/SCOPE_DRIFT verdict (dual-write to template)
- `~/.claude/agents/verification-analyst.md` — 6-gate mandatory verifier for security/research findings with 13-item Devil's Advocate checklist (dual-write)
- `~/.claude/agents/mcp-developer.md` — MCP server specialist; scaffolds servers, adds tools, writes tests with MCP test client (dual-write)
- `~/.claude/agents/chaos-engineer.md` — controlled failure injection with blast radius analysis; read-only default, execution requires explicit approval (dual-write; also exists in global already — verify before overwrite)
- `~/.claude/agents/penetration-tester.md` — security testing with CVSS-scored findings; refuses without authorization context (dual-write)
- `~/.claude/agents/scientific-literature-researcher.md` — grounds findings in peer-reviewed literature; flags predatory journals, preprints, industry funding (dual-write)
- `masonry/src/hooks/masonry-config-protection.js` — PreToolUse Write|Edit: blocks writes to lint config sections unless `LINT_CONFIG_OVERRIDE` present
- `masonry/src/hooks/masonry-block-no-verify.js` — PreToolUse Bash: blocks `--no-verify`, `git push --force`, `git push -f`; allows `--force-with-lease`
- `~/.claude/skills/debug/SKILL.md` — 8-step diagnosis loop skill; escalates to DIAGNOSIS_FAILED.md on exhaustion
- `~/.claude/skills/aside/SKILL.md` — freezes active /build task, answers read-only, resumes; uses `.autopilot/aside-state.json`
- `~/.claude/skills/visual-diff/SKILL.md` — generates self-contained HTML before/after diff at `~/.agent/diagrams/visual-diff-{timestamp}.html`
- `~/.claude/skills/visual-plan/SKILL.md` — generates self-contained HTML task dependency graph from spec.md
- `~/.claude/skills/visual-recap/SKILL.md` — generates self-contained HTML session summary from git log + build.log
- `~/.claude/skills/spec-mine/SKILL.md` — inverse spec-writer; mines existing code into `.autopilot/spec.md`
- `~/.claude/skills/release-manager/SKILL.md` — semver automation; reads conventional commits, bumps version, generates CHANGELOG entry
- `~/.claude/skills/discover/SKILL.md` — JTBD + experiment design discovery; writes `.discover/{slug}/discovery.md`
- `~/.claude/skills/parse-prd/SKILL.md` — parses PRD into `.autopilot/spec.md` with SPARC mode annotations and complexity estimates

**Modified:**
- `~/.claude/agents/fix-implementer.md` — add commit-before-verify+revert pattern with `experiment:` prefix, Guard/Verify split, 3-attempt cap (also update `template/.claude/agents/fix-implementer.md`)
- `~/.claude/skills/build/SKILL.md` — add Guard/Verify split in validation step; add spec-reviewer gate between developer and code-reviewer with skip conditions
- `masonry/src/hooks/masonry-pre-compact.js` — extend with snapshot to `.autopilot/pre-compact-snapshot.json` on build mode; campaign snapshot to `masonry/pre-compact-campaign.json`; stdout output before compaction
- `masonry/src/hooks/masonry-context-monitor.js` — extend Stop hook with 4 semantic degradation patterns via Ollama nomic-embed-text; graceful Ollama failure handling
- `~/.claude/agents/uiux-master.md` — add 7-point slop gate (Task 19) then Phase 0 Domain Exploration forcing function (Task 20); always read-then-append, never overwrite (also update `template/.claude/agents/uiux-master.md`)
- `masonry/tests/test_wiring_completeness.py` — add assertions for 5 new agents (both paths + registry), 2 new hooks (file + settings.json), 7 new skills (SKILL.md exists)
- `masonry/agent_registry.yml` — add 6 new agent entries with `tier: draft` (spec-reviewer + 5 specialists)
- `~/.claude/settings.json` — wire masonry-config-protection.js in PreToolUse Write|Edit; wire masonry-block-no-verify.js in PreToolUse Bash BEFORE masonry-approver
- `ARCHITECTURE.md` — add Phase 6 agent fleet, hooks, skills, Guard/Verify pipeline notes
- `ROADMAP.md` — mark Phase 6 items complete
- `CHANGELOG.md` — add Phase 6 entry dated 2026-03-28

**Unchanged (referenced but not modified):**
- `masonry/src/schemas/payloads.py` — QuestionPayload / FindingPayload used by all new agents
- `masonry/agent_registry.yml` (structure) — YAML format with `version: 1 / agents:` list
- `~/.claude/settings.json` (structure) — hooks object with event keys; PreToolUse array with matcher groups
- `.autopilot/progress.json` — read by /aside and masonry-pre-compact extension; schema unchanged
- `.autopilot/build.log` — appended to by masonry-pre-compact extension; append-only, no schema change

---

## Section 2: Interface Contracts

### Agent: spec-reviewer
```
Input (via agent prompt):
  task_description: string   — the original spec task text
  files_changed: string[]    — list of files the developer modified

Output block (structured markdown):
  ## Spec Review
  **Verdict:** COMPLIANT | OVER_BUILT | UNDER_BUILT | SCOPE_DRIFT
  **Evidence:** <one paragraph citing specific diff vs spec>
  **Required action:** <what developer must correct, or "None">

  - No code changes. Read-only agent.
  - Raises: nothing — always returns one of the four verdicts
```

### Hook: masonry-config-protection.js
```
Event: PreToolUse Write|Edit
Reads: tool input (file_path, content/patch)
Checks: file_path matches protected patterns OR content modifies protected sections
  Protected files: .eslintrc*, .prettierrc*, prettier.config.*, ruff.toml
  Protected sections: [tool.ruff] or [tool.black] in pyproject.toml
Override: user message contains literal string LINT_CONFIG_OVERRIDE
On block: exit(2), stdout: "[masonry-config-protection] BLOCKED: ..."
On allow: exit(0), no output
Settings wiring: PreToolUse Write|Edit, timeout: 3, continueOnError: false
```

### Hook: masonry-block-no-verify.js
```
Event: PreToolUse Bash
Reads: tool input (command string)
Blocked patterns:
  --no-verify in any git command
  --force on git push  (git push ... --force or git push -f)
  -f shorthand on git push
Allowed: --force-with-lease (explicitly permit)
On block: exit(2), stdout: "[masonry-block-no-verify] BLOCKED: {pattern} bypasses safety checks."
On allow: exit(0), no output
Settings wiring: PreToolUse Bash, BEFORE masonry-approver entry, timeout: 3, continueOnError: false
```

### Hook: masonry-context-monitor.js (extension)
```
Event: Stop (existing hook, extended)
New behavior: after existing token-count check, attempt Ollama embedding call
  Endpoint: {OLLAMA_HOST}/api/embeddings, model: nomic-embed-text
  Failure mode: Ollama unreachable → skip silently, exit(0)
  Degradation patterns (all via cosine similarity):
    lost-in-middle:  cosine(recent_assistant, first_assistant) < 0.3
    poisoning:       consecutive cosine drop > 0.5 between adjacent assistant messages
    distraction:     cosine(recent_messages, progress.json task description) < 0.3
    clash:           cosine(assistant[n-1], assistant[n]) < 0.1
  On detection: stderr "[masonry-context-monitor] WARNING: Semantic degradation — {pattern}. Consider /compact."
  Does NOT block stop — warning only
```

### Hook: masonry-pre-compact.js (extension)
```
Event: PreCompact (existing hook, extended)
New state A — build mode (.autopilot/mode = "build"):
  Writes: .autopilot/pre-compact-snapshot.json
    { timestamp, project, task_id, task_description, status, done, total }
  Appends: .autopilot/build.log
    "[ISO-8601] PRE_COMPACT: Snapshot saved. Task N of M (STATUS). Resume with /build."
  Stdout: visible line before compaction
New state B — campaign active (questions.md has IN_PROGRESS questions):
  Writes: masonry/pre-compact-campaign.json
    { question_id, wave, timestamp }
  Stdout: visible line before compaction
Existing behavior: preserved unchanged
```

### Skill: /aside
```
Invoked as: /aside <question>
Reads: .autopilot/mode, .autopilot/progress.json
If mode = "build" and task IN_PROGRESS:
  Writes: .autopilot/aside-state.json
    { task_id, task_description, status, paused_at: ISO-8601 }
  Answers question read-only (no file writes)
  Prints: "Aside complete. Run /build to resume task N."
If no active build:
  Answers normally
On /build resume: clears .autopilot/aside-state.json
```

### Skill: /debug
```
Invoked as: /debug <error description or file>
Runs 8 techniques in order until root cause found:
  1. Binary search   2. Differential   3. Minimal repro   4. Forward trace
  5. Pattern search  6. Backward trace  7. Rubber duck     8. Hypothesis log
Each step: apply technique, assess result, continue or resolve
On resolution: print root cause + fix recommendation
On exhaustion: write DIAGNOSIS_FAILED.md, print escalation message
```

### API endpoints: none new in Phase 6

---

## Section 3: Data Flow

### /build pipeline — spec-reviewer gate (Tasks 2, 3, 4)

```
Orchestrator dispatches test-writer (writes failing tests)
  → Orchestrator dispatches developer (implements code to pass tests)
  → Developer returns: files changed list
  → Orchestrator dispatches spec-reviewer with (task_description, files_changed)
  → spec-reviewer returns COMPLIANT | OVER_BUILT | UNDER_BUILT | SCOPE_DRIFT
  → If COMPLIANT: proceed to code-reviewer
  → If verdict is drift/over/under: dispatch developer with correction feedback (1 cycle)
  → Orchestrator dispatches code-reviewer
  → Guard (full test suite -q --tb=short): pass → Verify (task-specific test file): pass → commit feat:
  → Guard pass, Verify fail → log warning, commit experiment:, continue
  → Guard fail → spawn fix-implementer
```

### fix-implementer — commit-before-verify+revert (Task 1)

```
Receives DIAGNOSIS_COMPLETE with root cause
  → Implement surgical fix (Karpathy rule)
  → git commit -m "experiment: fix attempt N"
  → Run Guard (full test suite)
  → Guard FAIL: git revert HEAD --no-edit, try next approach
  → Guard PASS: run Verify (task metric)
  → Verify FAIL: keep commit, log "metric not improved", escalate
  → Verify PASS: log success, exit
  → After 3 attempts all fail: set status BLOCKED
```

### masonry-block-no-verify.js in PreToolUse chain (Task 9)

```
Bash command submitted
  → masonry-block-no-verify.js fires FIRST (before masonry-approver)
  → Scans command string for blocked patterns
  → Blocked pattern found: exit(2), command rejected, user sees BLOCKED message
  → No blocked pattern: exit(0)
  → masonry-approver fires second (build mode auto-approval)
  → Command executes
```

### masonry-pre-compact.js — state preservation (Task 7)

```
PreCompact event fires
  → Existing: read .autopilot/mode, .ui/mode, progress.json, masonry-state.json
  → New: if mode = "build" → write pre-compact-snapshot.json + append build.log
  → New: if campaign active → write masonry/pre-compact-campaign.json
  → hookSpecificOutput written to stdout (survives compaction)
  → Recall checkpoint stored (existing behavior)
```

### /aside — freeze/answer/resume (Task 6)

```
User invokes /aside <question> mid-build
  → Skill reads .autopilot/mode and progress.json
  → Active build detected: write aside-state.json, enter read-only answer mode
  → Answer produced without any file writes
  → Print resume instruction
  → User runs /build → skill reads aside-state.json, clears it, resumes task
```

### Visual skills — HTML diagram generation (Tasks 12–14)

```
User invokes /visual-diff | /visual-plan | /visual-recap
  → Skill reads relevant data sources (git log, build.log, spec.md)
  → Generates self-contained HTML (no external CDN)
  → Writes to ~/.agent/diagrams/{skill}-{timestamp}.html
  → Prints file path to user
```

---

## Section 4: Dependencies

**Existing internal modules:**
- `masonry/src/schemas/payloads.py` — QuestionPayload / FindingPayload used as input/output schemas in all new agent frontmatter
- `.autopilot/progress.json` — read by /aside skill and masonry-pre-compact extension
- `.autopilot/build.log` — appended to by masonry-pre-compact extension
- `masonry/agent_registry.yml` — receives 6 new entries (spec-reviewer + 5 specialists)
- `~/.claude/settings.json` — receives 2 new hook wiring entries

**External packages (already installed):**
- `node` (v18+) — all hooks are Node.js scripts
- `pytest` + `pyyaml` — wiring completeness test suite runner
- `Ollama` at `http://100.70.195.84:11434` — semantic degradation detection in masonry-context-monitor.js; hook skips silently if unreachable

**External packages (must be added):**
- None — Phase 6 adds no new npm or pip dependencies

**Environment / services:**
- `OLLAMA_HOST` env var (default `http://100.70.195.84:11434`) — used by masonry-context-monitor.js extension for nomic-embed-text embeddings
- `RECALL_HOST` / `RECALL_API_KEY` — already set in settings.json env; used by existing pre-compact recall storage

---

## Section 5: Out of Scope

```
- promptfoo integration — requires Docker toolchain, deferred to Phase 7
- code-review-graph MCP server — requires Tree-sitter native module installation
- claude-task-master dependency graph — requires separate MCP server wiring
- worktrunk git worktree CLI — deferred to Phase 7
- HuggingFace skills integration — TBD, not scheduled
- Anthropic-Cybersecurity-Skills (734+ MITRE ATT&CK items) — separate audit project
- simulate.py / constants.py / any research campaign files — immutable in this phase
- Kiln (BrickLayerHub) electron app — no changes to kiln-engineer or Kiln source
- masonry-tdd-enforcer.js — existing hook, not modified in this phase
- masonry-lint-check.js — existing hook, not modified in this phase
- masonry-stop-guard.js — existing hook, not modified in this phase
- masonry-build-guard.js — existing hook, not modified in this phase
- Semantic routing engine (masonry/src/routing/) — unchanged
- DSPy optimization pipeline — unchanged
- Recall API or Recall hooks — unchanged
- Any database schemas (Qdrant, Neo4j, PostgreSQL) — no data model changes
- /plan skill — not modified; spec-reviewer is wired into /build only
- /verify and /fix skills — not modified in this phase
```

---

## Section 6: Rollback Plan

**Safe state:** commit before Task 1 begins (current HEAD on `bricklayer-v2/mar24-parallel`)

**Rollback procedure:**
1. `git revert HEAD~N..HEAD` for each task commit, or `git reset --hard <pre-phase-6-sha>`
2. Remove new hook files: `rm masonry/src/hooks/masonry-config-protection.js masonry/src/hooks/masonry-block-no-verify.js`
3. Remove new agent files from `~/.claude/agents/` and `template/.claude/agents/` (6 new .md files)
4. Remove new skill directories from `~/.claude/skills/` (7 new dirs)
5. Restore prior `~/.claude/settings.json` from git (2 new hook entries were added)
6. Restore `masonry/agent_registry.yml` (6 entries added)
7. No data migrations — all new files are additive, no schema changes

**Risk areas:**
- Task 9 — masonry-block-no-verify.js must be ordered BEFORE masonry-approver in settings.json PreToolUse Bash array; wrong order means block never fires
- Tasks 8 & 9 — both write to settings.json; must run sequentially; if run in parallel they will overwrite each other's changes
- Tasks 19 & 20 — both modify uiux-master.md; must run sequentially (Task 20 depends_on 19); Task 20 developer must re-read the file after Task 19 writes it
- Task 7 — masonry-pre-compact.js is production-critical (runs on every compaction); new code paths must not throw uncaught exceptions or they will block compaction
- Task 10 — masonry-context-monitor.js is a Stop hook; any synchronous Ollama call that hangs will delay stop; must use AbortSignal.timeout() for the fetch call
- Task 22 — wiring test run may fail if any earlier task missed a file or registry entry; fix-forward by creating the missing artefact
```
