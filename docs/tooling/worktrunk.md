# Worktrunk — Parallel AI Workflow Tool

## What is Worktrunk

Worktrunk is a CLI tool for spawning multiple Claude Code instances simultaneously,
each operating on its own isolated git worktree. Rather than running tasks serially in
a single Claude session, worktrunk fans work out across N workers that operate in
parallel and commit independently, then merge back to the base branch.

This pairs directly with BrickLayer's `/ultrawork` skill, which partitions a spec's
task list and hands each partition to a dedicated worker.

---

## Installation

```bash
npm install -g worktrunk
```

Verify:

```bash
worktrunk --version
```

---

## Core Concepts

### Worktree Isolation

Each worker receives a fresh git worktree checked out from the base branch. Workers
share the same git history but operate on separate branches, so edits in one worker
never interfere with edits in another.

### Named Branches

Workers commit to persistent named branches (`autopilot/worker-1-YYYYMMDD`, etc.).
Branches survive the worktrunk session and are available for review, rebasing, or
manual merge resolution before the final integration step.

### Merge by Orchestrator

After all workers signal completion, the main orchestrator merges every worker branch
back to the base branch. Conflicts are surfaced as standard git merge conflicts and
must be resolved before the build is marked COMPLETE.

---

## Usage Patterns

### Basic Parallel Build

Spawn 4 workers, each reading the spec file to determine its task partition:

```bash
worktrunk spawn 4 --base main --task-file .autopilot/spec.md
```

Workers are numbered 1–N. Each worker receives its shard index and the total worker
count so it can compute which tasks belong to it.

### BrickLayer `/ultrawork` Integration

When `/ultrawork` is invoked, BrickLayer partitions the task list and hands each
partition to a separate Claude Code instance via worktrunk:

| Worker   | Tasks    | Branch                        |
|----------|----------|-------------------------------|
| Worker 1 | 1–8      | `autopilot/worker-1-YYYYMMDD` |
| Worker 2 | 9–16     | `autopilot/worker-2-YYYYMMDD` |
| Worker 3 | 17–24    | `autopilot/worker-3-YYYYMMDD` |
| Worker 4 | 25–32    | `autopilot/worker-4-YYYYMMDD` |

Each worker follows the standard TDD cycle (test-writer → developer → code-reviewer)
for its assigned tasks and commits after each task completes. The main orchestrator
polls worker status and merges all branches once every worker reports DONE.

### Manual Worker Invocation

To run a single worker by hand (useful for debugging a partition):

```bash
worktrunk worker 2 --base main --task-file .autopilot/spec.md --total-workers 4
```

---

## BrickLayer Configuration

Add to `.autopilot/config.json` to enable worktrunk as the parallelism engine for
`/ultrawork`:

```json
{
  "parallelism": {
    "engine": "worktrunk",
    "max_workers": 4,
    "worker_branch_prefix": "autopilot/worker"
  }
}
```

`max_workers` caps the number of simultaneous Claude instances. For most projects,
4 is a practical ceiling — beyond that, merge conflict probability increases
significantly if workers touch overlapping files.

---

## Contrast with Agent Tool Worktree Isolation

The Claude Code `Agent` tool supports `isolation: "worktree"` for subagent tasks.
This is a different mechanism:

| Feature              | Agent tool `isolation: "worktree"` | worktrunk                       |
|----------------------|------------------------------------|---------------------------------|
| Scope                | Session-scoped (auto-cleanup)      | Persistent until merge          |
| Branches             | Temporary, unnamed                 | Named, survives session         |
| Multi-instance       | Single agent subprocess            | Multiple Claude Code instances  |
| Parallelism ceiling  | Bound by single session context    | N independent sessions          |
| Merge responsibility | Orchestrator (in-process)          | Orchestrator (shell/git)        |
| Use case             | Safe exploration / sandboxed reads | Parallel build across many tasks|

Use Agent tool worktree isolation for short, exploratory subagent tasks inside a
single build session. Use worktrunk when task count or context pressure justifies
splitting across fully independent Claude instances.

---

## Limitations

- **No direct worker communication.** Workers cannot share state during execution.
  Design tasks to be independent — if task B depends on a type exported by task A,
  put them in the same partition.
- **Merge conflicts.** Workers that edit the same file will produce conflicts at merge
  time. Mitigate by grouping tightly coupled files into a single worker's partition.
- **Clean working tree required.** `worktrunk spawn` refuses to start if the base
  branch has uncommitted changes. Commit or stash first.
- **Branch proliferation.** Long-running campaigns can accumulate many worker branches.
  Delete merged branches periodically: `git branch --merged | grep autopilot/worker | xargs git branch -d`

---

## See Also

- `/ultrawork` skill — high-throughput parallel build orchestration
- `adaptive-coordinator` agent — selects parallelism topology (serial / agent / worktrunk)
  based on task count, dependency graph, and repo characteristics
- `.autopilot/spec.md` — task list consumed by worktrunk workers
