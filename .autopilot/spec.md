# Spec: Masonry Ecosystem Expansion

## Goal

Bring Masonry to feature parity with OMC's richer capabilities while staying true to its
research-first identity. Seven deliverables: a richer HUD, file ownership in `/build`,
an `/ultrawork` parallel execution engine, a `/pipeline` skill, a `/masonry-team` skill,
a formalized plugin/pack architecture, and a fully operational `/masonry-fleet`.

All changes are to skill `.md` files, Node.js hooks/scripts, and config files.
No Python, no TypeScript, no frontend involved.

---

## Architecture

```
masonry/
  skills/
    masonry-build.md       ← add owned_by to progress.json schema
    masonry-fleet.md       ← reference new fleet CLI
    masonry-ultrawork.md   ← NEW parallel execution skill
    masonry-pipeline.md    ← NEW pipeline chaining skill
    masonry-team.md        ← NEW native teams wrapper
  src/hooks/
    masonry-statusline.js  ← enrich HUD (git, build task, UI mode)
  bin/
    masonry-fleet-cli.js   ← NEW fleet add/retire/status CLI
  packs/
    masonry-core/
      pack.json            ← NEW pack manifest
      agents/              ← symlink or copy of template agents
    masonry-frontier/
      pack.json            ← NEW pack manifest
  .claude-plugin/
    plugin.json            ← add packs reference

~/.claude/CLAUDE.md        ← update skill catalog table (new skills)
```

### Data Flow

- **HUD**: `masonry-statusline.js` reads `masonry-state.json`, `.autopilot/progress.json`,
  `.ui/mode`, and runs `git rev-parse`/`git status --short` synchronously (< 50ms).
- **Ownership**: `progress.json` tasks grow two fields — `owned_by` and `lock_files[]`.
  Orchestrator writes these before spawning, clears after DONE/BLOCKED.
- **Fleet CLI**: `bin/masonry-fleet-cli.js` is callable with
  `node {masonry_root}/bin/masonry-fleet-cli.js <cmd> [args]` from any project dir.
- **Packs**: `~/.masonry/config.json` gains an `"activePacks": []` array. The fleet CLI
  and skills read from this to know which agent packs are available.

---

## Tasks

### Task 1 — Rich HUD (`masonry-statusline.js`) · Parallel: YES

Enrich the statusline output with four new segments:

1. **Git segment**: current branch name + dirty indicator (`*` if uncommitted changes).
   Run `git rev-parse --abbrev-ref HEAD` and `git status --porcelain` synchronously
   with a 2s timeout; if git fails (not a repo) skip the segment silently.
2. **Build segment**: if `.autopilot/progress.json` exists, find the first IN_PROGRESS task
   and show `bld:#{id}` in amber. If no in-flight task, show nothing.
3. **UI mode segment**: if `.ui/mode` exists and is non-empty, show `ui:{mode}` in cyan.
4. **Active agents segment**: if `masonry-state.json` has `active_agents: []` array, show
   count `N agents` in purple; otherwise use existing `active_agent` string.

**Output format (campaign active):**
```
🧱  masonry  │  bl2  research · wave 3  │  Q12/49  mortar  │  main*  │  bld:#4  │  ui:compose  │  ████░░░░░░ 38%  ✓12 ⚠2  │  ● recall
```

**Rules:**
- Git ops must use `execSync` with `{ stdio: 'pipe', timeout: 2000 }` — never throw
- Never add > 20ms to statusline render time on a clean repo
- Keep all segments on one line; truncate git branch at 20 chars if needed

**Test:** Run `node masonry/src/hooks/masonry-statusline.js` with a mock JSON on stdin
containing `context_window`, `cwd`. Verify output contains branch name and no crash.
Output format is a single line ending in `\n`.

**File:** `masonry/src/hooks/masonry-statusline.js`

---

### Task 2 — File ownership in `/build` · Parallel: YES

Extend the `progress.json` task schema with two new optional fields:

```json
{
  "id": 1,
  "description": "Build auth module",
  "status": "PENDING|IN_PROGRESS|DONE|BLOCKED",
  "owned_by": "task-1",
  "lock_files": ["src/auth/login.py", "src/auth/models.py"]
}
```

**Orchestrator rules (update `masonry-build.md`):**
1. Before spawning a worker agent, set `owned_by: "task-{id}"` on that task in `progress.json`.
2. In the worker prompt, add: `"Owned files for this task: {lock_files}. Do NOT modify files
   owned by other IN_PROGRESS tasks: {list of other tasks' lock_files}."`
3. After marking a task DONE or BLOCKED, clear `owned_by` to `null`.
4. If two PENDING tasks share a file in `lock_files`, they are implicitly sequential — do
   not spawn them in the same parallel batch.

**Note:** `lock_files` is populated by the planning spec's task descriptions. If omitted,
ownership is inferred from files mentioned in the task description (best-effort).

**Test:** Verify the updated `masonry-build.md` skill doc contains the ownership fields
in the progress.json schema block and the worker prompt template.

**File:** `masonry/skills/masonry-build.md`

---

### Task 3 — Fleet CLI (`masonry-fleet-cli.js`) · Parallel: YES

Create `masonry/bin/masonry-fleet-cli.js` — a Node.js CLI that the fleet skill can call
to perform add/retire/status without relying on inline JS execution.

**Usage:**
```bash
node {masonry_root}/bin/masonry-fleet-cli.js status [project_dir]
node {masonry_root}/bin/masonry-fleet-cli.js add <name> [project_dir]
node {masonry_root}/bin/masonry-fleet-cli.js retire <name> [project_dir]
node {masonry_root}/bin/masonry-fleet-cli.js regen [project_dir]
```

`project_dir` defaults to `process.cwd()`.

**`status` output:**
```
MASONRY FLEET · {project} · {N} agents
────────────────────────────────────────────────────────────────────
Agent                  Model    Tier      Score  Runs  Last Activity
benchmark-engineer     sonnet   standard  0.82   12    2h ago
mortar                 sonnet   standard  —      —     active ←
...
Summary: N active, N elite tier, N below 0.40 threshold
agent_db.json: found | not found
```

**`add <name>`:**
1. Check `.claude/agents/{name}.md` doesn't exist (warn if it does)
2. Write scaffold file from the template defined in `masonry-fleet.md`
3. Run `generateRegistry(projectDir)` from `src/core/registry.js`
4. Print confirmation

**`retire <name>`:**
1. Move `.claude/agents/{name}.md` → `.claude/agents/.retired/{name}.md`
2. Create `.retired/` if needed
3. Run `generateRegistry(projectDir)`
4. Print confirmation

**`regen`:** Just runs `generateRegistry(projectDir)` and prints agent count.

**Dependencies:** Requires only `src/core/registry.js` — no external npm packages.

**Update `masonry-fleet.md`:** Change the `add` and `retire` step 2 from inline JS to:
```bash
node {masonry_bin}/masonry-fleet-cli.js regen {project_dir}
```

**Test:**
```bash
# Create a temp project dir with .claude/agents/ containing 2 agents
# Run: node masonry/bin/masonry-fleet-cli.js status {tmp_dir}
# Verify: outputs table with 2 rows, no crash
# Run: node masonry/bin/masonry-fleet-cli.js add test-agent {tmp_dir}
# Verify: .claude/agents/test-agent.md exists, registry.json updated
# Run: node masonry/bin/masonry-fleet-cli.js retire test-agent {tmp_dir}
# Verify: .claude/agents/.retired/test-agent.md exists, not in registry.json
```

**Files:** `masonry/bin/masonry-fleet-cli.js`, `masonry/skills/masonry-fleet.md` (update)

---

### Task 4 — `/ultrawork` skill · Parallel: YES (after task 2 schema is written)

Create `masonry/skills/masonry-ultrawork.md`.

**Difference from `/build`:** Ultrawork does not batch by dependency. Every PENDING task
that has no file ownership conflict with a currently IN_PROGRESS task is spawned immediately,
up to `max_concurrency` (default 6). This is appropriate for specs where tasks are largely
independent (e.g., building many separate modules, running multiple research questions).

**Skill structure:**

```markdown
---
name: masonry-ultrawork
description: High-throughput parallel build — spawns all independent tasks simultaneously with
  file ownership partitioning. Use when tasks are largely independent. Requires .autopilot/spec.md.
---
```

**Ultrawork Loop:**
1. Read `spec.md` and `progress.json` (create if missing)
2. Build ownership conflict map from `lock_files` across all IN_PROGRESS tasks
3. Find ALL PENDING tasks with no conflicts → spawn up to `max_concurrency` simultaneously
4. As each task completes (DONE/BLOCKED), immediately check for newly unblocked tasks
   and spawn them (refill the pool)
5. Validate and commit after each completed batch of 3 tasks (or when pool drains)
6. 3-strike rule same as `/build`
7. On completion: set status → COMPLETE, clear mode, run `/verify`

**`max_concurrency` setting:**
- Default 6
- Can be overridden by adding `max_concurrency: N` to the spec's Agent Hints section
- Hard cap: 10 (above this Claude's parallel agent rendering becomes unwieldy)

**Worker agent prompt:** identical to `/build` plus ownership constraints from task 2.

**Test:** Verify skill file exists, contains the refill-pool logic description, and references
the ownership conflict map. Verify the `max_concurrency` cap of 10 is documented.

**File:** `masonry/skills/masonry-ultrawork.md`

---

### Task 5 — `/pipeline` skill · Parallel: YES

Create `masonry/skills/masonry-pipeline.md`.

**Purpose:** Chain agents/skills in a DAG with data passing. Each step's output becomes
the next step's input. Supports sequential and branching topologies.

**Pipeline definition file** (`.pipeline/{name}.yml`):
```yaml
name: research-and-build
description: Research a topic, synthesize findings, then build the implementation

steps:
  - id: research
    agent: research-analyst
    input:
      topic: "{{pipeline.input.topic}}"
    output_key: research_findings

  - id: synthesize
    agent: synthesizer-bl2
    depends_on: [research]
    input:
      findings: "{{steps.research.output}}"
    output_key: synthesis

  - id: plan
    skill: plan
    depends_on: [synthesize]
    input:
      goal: "{{steps.synthesize.output}}"

  - id: build
    skill: build
    depends_on: [plan]
```

**Variable syntax:** `{{pipeline.input.KEY}}` for initial inputs, `{{steps.ID.output}}` for
step outputs. Substitution happens at step invocation time.

**Execution model:**
1. Read pipeline YAML from `.pipeline/{name}.yml` or path argument
2. Topological sort steps by `depends_on`
3. For each batch of steps with no unresolved dependencies, spawn agents in parallel
4. Capture each agent's final output (last markdown block or explicit `OUTPUT:` line)
5. Store outputs in `.pipeline/{name}-state.json`
6. On completion: print summary of outputs from each step

**Usage:**
```
/pipeline run {name}           — run a pipeline by name
/pipeline run {path/to/file}   — run a specific file
/pipeline status {name}        — show step statuses
/pipeline list                 — list .pipeline/*.yml files
```

**Test:** Verify skill file exists, contains the YAML schema definition, the variable syntax
spec, and the topological sort description. Verify all four sub-commands are documented.

**File:** `masonry/skills/masonry-pipeline.md`

---

### Task 6 — `/masonry-team` skill · Parallel: YES

Create `masonry/skills/masonry-team.md`.

**Purpose:** Partition a build spec across N coordinated Claude Code instances using the
native teams feature (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`).

**How it works:**
1. Read `.autopilot/spec.md`
2. Partition tasks into N roughly-equal groups (by estimated complexity: number of files
   in `lock_files` or word count of description)
3. For each partition, write `.autopilot/team-{n}-tasks.json` with the task subset
4. Launch N subagent instances, each running `/build` on their assigned partition
5. Coordinator polls `.autopilot/progress.json` for completion, merges results
6. Runs validation and commit after all partitions complete

**Team config** (optional, `.autopilot/team-config.json`):
```json
{
  "workers": 3,
  "partition_strategy": "tasks",
  "sync_interval_seconds": 30
}
```

**`workers` default:** 3 (balances parallelism vs. context overhead per instance)

**Conflict prevention:** Same ownership model as ultrawork — no two workers own the same file.
If two tasks in different partitions share a `lock_files` entry, merge them into the same partition.

**Usage:**
```
/masonry-team             — auto-detect worker count from spec size
/masonry-team 4           — explicitly 4 workers
/masonry-team status      — show per-worker progress
```

**Test:** Verify skill file exists, contains the partition algorithm description, the ownership
conflict merge rule, and the team-config.json schema.

**File:** `masonry/skills/masonry-team.md`

---

### Task 7 — Plugin pack architecture · Parallel: YES

Formalize `masonry/packs/` as the plugin extension point.

**Pack manifest** (`masonry/packs/{pack-name}/pack.json`):
```json
{
  "name": "masonry-frontier",
  "version": "0.1.0",
  "description": "Frontier research agents — blue-sky exploration, competitive analysis",
  "agents": "./agents/",
  "skills": "./skills/",
  "hooks": "./hooks.json"
}
```

**Pack activation** (`~/.masonry/config.json`):
```json
{
  "recallApiKey": "...",
  "activePacks": ["masonry-core", "masonry-frontier"]
}
```

**Pack resolution:** When a Masonry skill needs agents (e.g., `/masonry-fleet status`),
it looks in:
1. `.claude/agents/` (project-local — highest priority)
2. Each active pack's `agents/` directory (in order listed in `activePacks`)
3. `masonry/packs/masonry-core/agents/` (always last, lowest priority)

**Deliverables:**
1. Write `masonry/packs/masonry-core/pack.json`
2. Write `masonry/packs/masonry-frontier/pack.json`
3. Update `masonry/.claude-plugin/plugin.json` — add `"packs": "../packs/"` field
4. Update `masonry/skills/masonry-fleet.md` — document pack-aware agent resolution order
5. Update `~/.masonry/config.json` schema in README / `masonry-init.md`

**Test:** Verify both pack.json files parse as valid JSON, contain required fields (`name`,
`version`, `description`), and `plugin.json` references the packs directory.

**Files:** `masonry/packs/masonry-core/pack.json`, `masonry/packs/masonry-frontier/pack.json`,
`masonry/.claude-plugin/plugin.json`, `masonry/skills/masonry-fleet.md` (update notes),
`masonry/skills/masonry-init.md` (update config schema docs)

---

### Task 8 — Update `~/.claude/CLAUDE.md` skill catalog · Parallel: NO (after tasks 4-6)

Add the three new skills to the Masonry Skills table in `~/.claude/CLAUDE.md`:

```markdown
| `/ultrawork` | High-throughput parallel build — all independent tasks simultaneously |
| `/pipeline`  | Chain agents/skills in a DAG with data passing |
| `/masonry-team` | Partition build across N coordinated Claude instances |
```

Also update the Masonry Hooks section if any new hooks were added (none expected for this batch).

**File:** `C:/Users/trg16/.claude/CLAUDE.md`

---

### Task 9 — Tests · Parallel: NO (after tasks 1, 3)

Write `tests/test_masonry_hud.js` and `tests/test_masonry_fleet_cli.js`.

**`test_masonry_hud.js`** (Node.js, no test framework — just `assert` + process.exit):
- Pipe mock JSON to `masonry-statusline.js`, capture stdout
- Verify: output is single line, contains `masonry`, does not throw
- Verify: with `masonry-state.json` mock containing wave/Q data, output contains `wave` and `Q`
- Verify: with dirty git repo simulation, output contains branch-like string

**`test_masonry_fleet_cli.js`**:
- Create temp dir with 2 agent .md files with valid frontmatter
- Run `status` — verify table contains both agent names
- Run `add test-bot` — verify file created, registry updated
- Run `retire test-bot` — verify file moved to `.retired/`, removed from registry
- Run `regen` — verify registry count matches actual file count
- Cleanup temp dir

**Test runner:**
```bash
node tests/test_masonry_hud.js && node tests/test_masonry_fleet_cli.js
```

Both must exit 0 with descriptive pass output.

**Files:** `tests/test_masonry_hud.js`, `tests/test_masonry_fleet_cli.js`

---

## Tech Stack

- **Language**: Node.js (all existing hooks are Node.js)
- **No external dependencies**: Only `fs`, `path`, `os`, `child_process`, `assert` (stdlib)
- **Skill files**: CommonMark markdown with YAML frontmatter
- **Config format**: JSON
- **Test format**: Plain Node.js scripts using `assert` module

---

## Agent Hints

- **Masonry root**: `C:/Users/trg16/Dev/Bricklayer2.0/masonry/`
- **Skills directory**: `masonry/skills/`
- **Hooks directory**: `masonry/src/hooks/`
- **Bin directory**: `masonry/bin/`
- **Packs directory**: `masonry/packs/`
- **Registry module**: `masonry/src/core/registry.js` — exports `generateRegistry(projectDir)` and `readRegistry(projectDir)`
- **Existing statusline**: `masonry/src/hooks/masonry-statusline.js` — already reads `masonry-state.json`, parses `context_window` from stdin JSON
- **agent_db.json schema** (for fleet CLI):
  ```json
  {
    "agents": {
      "mortar": { "score": 0.82, "runs": 12, "last_run": "ISO-8601", "verdicts": { "HEALTHY": 8, "WARNING": 3, "FAILURE": 1 } }
    }
  }
  ```
- **Test command**: `node tests/test_masonry_hud.js && node tests/test_masonry_fleet_cli.js`
- **Global CLAUDE.md**: `C:/Users/trg16/.claude/CLAUDE.md`
- **Windows path note**: Use `path.join()` everywhere, never hardcoded slashes in fleet CLI

---

## Constraints

- No external npm packages — all stdlib only
- Skill files are prompts for Claude to follow, not code — they should be readable prose
- HUD must stay under 120 chars wide total; truncate aggressively if needed
- `/ultrawork` and `/masonry-team` are skills (markdown), not hooks — they don't need JS implementations
- Fleet CLI must work from any `cwd` — never assume it's run from masonry root
- Do NOT touch `masonry-state.json` format (Mortar writes this during campaigns)
- Do NOT modify any existing hook behavior — only extend `masonry-statusline.js`

---

## Parallelization Map

**Batch 1 (fully independent, run all simultaneously):**
- Task 1: Rich HUD
- Task 2: Ownership in /build
- Task 3: Fleet CLI
- Task 4: /ultrawork skill
- Task 5: /pipeline skill
- Task 6: /masonry-team skill
- Task 7: Plugin pack architecture

**Batch 2 (after batch 1 completes):**
- Task 8: Update CLAUDE.md skill catalog

**Batch 3 (after batch 2):**
- Task 9: Tests

---

## Definition of Done

- [ ] `masonry-statusline.js` shows git branch, build task, and UI mode in output
- [ ] `progress.json` schema in `masonry-build.md` includes `owned_by` and `lock_files`
- [ ] `masonry/bin/masonry-fleet-cli.js` passes all fleet CLI tests
- [ ] `masonry/skills/masonry-ultrawork.md` exists with complete loop description
- [ ] `masonry/skills/masonry-pipeline.md` exists with YAML schema and sub-commands
- [ ] `masonry/skills/masonry-team.md` exists with partition algorithm and team-config schema
- [ ] Both pack.json files valid, plugin.json references packs directory
- [ ] `~/.claude/CLAUDE.md` lists ultrawork, pipeline, masonry-team in skill table
- [ ] Both test files pass: `node tests/test_masonry_hud.js && node tests/test_masonry_fleet_cli.js`
- [ ] No regressions in existing hooks (lint check, stop guard, approver all still function)
