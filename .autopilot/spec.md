# Spec: Learning Loop + Pattern Confidence Decay

## Goal
Close Ruflo gaps 1 and 3 by wiring build task outcomes back to pattern confidence scores,
implementing promote/demote functions, auto-running decay at session start, and injecting
top-confidence agents into session context so every build starts with relevant learned context.

## Success Criteria
- [ ] `toolPatternPromote` and `toolPatternDemote` are implemented in `impl-patterns.js` and registered in MCP dispatch
- [ ] When a build task transitions to DONE, the agent for that task gets its confidence promoted (+20% of headroom)
- [ ] When a build task transitions to FAILED, the agent for that task gets its confidence demoted (-15% of current)
- [ ] `toolPatternDecay` runs automatically at every session start (not just on manual MCP call)
- [ ] Top-5 agents by confidence are injected into session-start context as a hint
- [ ] All existing 264+ tests still pass
- [ ] New unit tests cover promote, demote, outcome hook, and session injection

## Tasks

- [ ] **Task 1** [mode:javascript] — Implement `toolPatternPromote` and `toolPatternDemote` in `impl-patterns.js` and register in MCP dispatch
  **Files:**
  - `masonry/src/tools/impl-patterns.js`
  - `masonry/bin/masonry-mcp.js`
  **What to build:**
  Add two functions to `impl-patterns.js`:
  - `toolPatternPromote({ agent_type, project_dir })`:
    - Reads `{project_dir}/.autopilot/pattern-confidence.json`
    - If agent not present, initializes with confidence 0.76
    - Applies: `confidence = conf + 0.2 * (1.0 - conf)` (ceiling-approached — prevents hitting 1.0)
    - Updates `last_used` to now, increments `uses`
    - Writes back, returns `{ agent_type, old_confidence, new_confidence, uses }`
  - `toolPatternDemote({ agent_type, project_dir })`:
    - Reads same file
    - Applies: `confidence = conf - 0.15 * conf` (proportional reduction)
    - Updates `last_used`, increments `uses`
    - Never goes below 0.1 (floor — don't fully retire via demote alone)
    - Writes back, returns `{ agent_type, old_confidence, new_confidence, uses }`
  In `masonry-mcp.js`, add dispatch cases:
  - `masonry_pattern_promote` → `patterns.toolPatternPromote(args)`
  - `masonry_pattern_demote` → `patterns.toolPatternDemote(args)`
  Also add tool definitions to the tool list (name, description, inputSchema) matching the existing pattern for `masonry_pattern_decay`.
  **Tests required:**
  - `toolPatternPromote` on new agent → initializes at 0.76 then promotes
  - `toolPatternPromote` at 0.9 → correct ceiling math (result ≈ 0.92)
  - `toolPatternDemote` at 0.9 → result is 0.765
  - `toolPatternDemote` at 0.1 → stays at 0.1 (floor)
  - Both functions handle missing `pattern-confidence.json` gracefully (create it)

- [ ] **Task 2** [mode:javascript] [depends:1] — Create `masonry-build-outcome.js` PostToolUse:Write hook
  **Files:**
  - `masonry/src/hooks/masonry-build-outcome.js` (new)
  - `/home/nerfherder/.claude/settings.json` (register hook)
  **What to build:**
  A PostToolUse:Write hook that fires when `.autopilot/progress.json` is written.
  Logic:
  1. Check `tool_input.file_path` — exit immediately if it doesn't end in `.autopilot/progress.json`
  2. Read the just-written `progress.json` to get current task states
  3. Read a state cache file `{os.tmpdir()}/masonry-outcome-prev-{sessionId}.json` to get previous states
  4. Diff: find tasks that just transitioned to `DONE` or `FAILED`
  5. For each transitioned task:
     - Infer agent type from task description's `[mode:X]` annotation. Default: `developer`
     - Mode→agent mapping: `python`→`python-specialist`, `typescript`→`typescript-specialist`, `database`→`database-specialist`, `tdd`→`tdd-london-swarm`, `devops`→`devops`, `security`→`security`, `architect`→`architect`
     - DONE → call `toolPatternPromote({ agent_type, project_dir: cwd })`
     - FAILED → call `toolPatternDemote({ agent_type, project_dir: cwd })`
  6. Write current states to the cache file for next comparison
  7. Runs async (non-blocking) — exit 0, no stdout (PostToolUse hooks are advisory)
  Import `toolPatternPromote` and `toolPatternDemote` directly from `../../tools/impl-patterns` (no HTTP round-trip).
  Fail silently on any error. Only fires when `.autopilot/mode` is `build` or `fix`.
  Register in `~/.claude/settings.json` under `PostToolUse` hooks, matcher `Write`, timeout 5s.
  **Tests required:**
  - DONE transition → promote called with correct agent_type
  - FAILED transition → demote called with correct agent_type
  - No transition (task already DONE from prev run) → neither called
  - Mode annotation parsing: `[mode:python]` → `python-specialist`, no annotation → `developer`
  - Non-progress.json write → exits immediately without reading anything

- [ ] **Task 3** [mode:javascript] [depends:1] — Auto-run decay at session start
  **Files:**
  - `masonry/src/hooks/session/context-data.js`
  **What to build:**
  At the start of `addContextData()`, before the Recall query block, call `toolPatternDecay({ project_dir: cwd })`.
  Import: `const { toolPatternDecay } = require('../../tools/impl-patterns')` (path relative to `masonry/src/hooks/session/`).
  Wrap in try/catch — never throw.
  If `result.pruned > 0`, push to lines:
  `[Masonry] Pattern decay: ${result.decayed} scores updated, ${result.pruned} stale patterns pruned`
  If `result.pruned === 0`, stay silent.
  **Tests required:**
  - Decay called with correct project_dir at session start
  - Pruned > 0 → line emitted; pruned === 0 → no line
  - Exception in decay does not propagate (session start must never fail due to this)

- [ ] **Task 4** [mode:javascript] [depends:3] — Inject top-confidence agents at session start
  **Files:**
  - `masonry/src/hooks/session/context-data.js`
  **What to build:**
  After decay runs (Task 3), read `{cwd}/.autopilot/pattern-confidence.json`.
  Filter to entries where the value is an object with `{ confidence, uses }` (exclude bare number entries like `"pattern-a": 0.999`).
  Filter to `uses >= 2` (skip cold-start agents with only one use).
  Sort by `confidence` descending. Take top 5.
  If at least 2 qualifying agents exist, push one line to `lines`:
  `[Masonry] Top agents by confidence: developer (99.9%, 94 uses), Explore (99.9%, 25 uses), ...`
  Format confidence as `(X.X%, N uses)`. Join with `, `.
  **Tests required:**
  - Correct top-5 sort and format
  - Bare-number entries excluded
  - Agents with uses < 2 excluded
  - Fewer than 2 qualifying agents → no line emitted
  - Missing pattern-confidence.json → no line, no throw

## Out of Scope
- Adaptive strategy selection per task type (Gap 4 — separate spec)
- PageRank pattern ranking (Gap 9)
- Persisting pattern confidence to Recall (stays local in `.autopilot/`)
- Changing the decay formula or thresholds (already calibrated)
- UI for viewing confidence history

## Notes
- `impl-patterns.js` is 114 lines — stays well under limit after additions (~170 lines)
- `context-data.js` import path from `masonry/src/hooks/session/`: `../../tools/impl-patterns`
- `masonry-build-outcome.js` import path: `../../tools/impl-patterns`
- Mixed entries in `pattern-confidence.json`: agent objects `{ confidence, last_used, uses }` vs bare numbers (`"pattern-a": 0.999`) — Task 4 must handle both shapes (filter by `typeof v === 'object'`)
- `masonry-build-outcome.js` imports impl-patterns directly — same process, no MCP HTTP hop
- The `[depends:X]` chain ensures Tasks 2/3/4 all use the finalized promote/demote API from Task 1
- Suggested strategy: `--strategy balanced`
