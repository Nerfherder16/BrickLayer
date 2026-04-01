# repomix MCP — Codebase Context Packing

## What is repomix MCP

repomix MCP is an MCP server (`npx repomix-mcp`) that packs entire codebases into
single context-dense files. Instead of reading dozens of files individually, an agent
makes one call to pack an entire directory or remote GitHub repo, then searches or
summarizes the result. This dramatically reduces round-trips for repo analysis,
handoff compression, and pattern extraction.

repomix MCP is installed in `settings.json` and available in every Claude Code session
without any additional setup.

---

## Installation

Already configured in `settings.json`. Reference only:

```json
{
  "mcpServers": {
    "repomix": {
      "command": "npx",
      "args": ["repomix-mcp"]
    }
  }
}
```

---

## Tool Reference

| Tool | Purpose |
|------|---------|
| `pack_codebase` | Pack an entire local directory into a single context file |
| `pack_remote_repo` | Pack a GitHub repo URL into context (no clone needed) |
| `grep_repomix_output` | Search within a packed codebase by pattern |
| `generate_skill` | Generate a skill file from patterns found in packed code |
| `list_packed_files` | List all files included in a packed output |
| `get_file_summary` | Summarize a specific file from packed output |
| `extract_patterns` | Extract recurring patterns or idioms from a codebase |
| `compress_for_handoff` | Compress packed codebase to a ≤500-token handoff summary |

---

## Use Cases in BrickLayer

### 1. Repo Research (`repo-researcher` agent)

When analyzing external repos, use `pack_remote_repo` to get full context in one call
rather than cloning and reading files individually:

```
pack_remote_repo("https://github.com/owner/repo")
  → packed context (full codebase in one payload)

grep_repomix_output(packed_output, pattern="agent|prompt|tool")
  → find relevant sections without reading every file
```

This is the standard approach in the `repo-researcher` agent workflow. A single
`pack_remote_repo` call replaces 20–50 individual file reads.

### 2. Context Handoffs (`context-continuation`)

When context exceeds 120K tokens during a `/build` session, use repomix to compress
the working state before handoff:

```
pack_codebase(path=".", focus=[".autopilot/", "src/", "agents/"])
  → packed snapshot of changed work

compress_for_handoff(packed_output)
  → ≤500-token summary

Write summary to .autopilot/handoff-context.md
```

The compressed summary is injected into the next session via `HANDOFF_CONTEXT.md`
at session start. See [Context Compression Protocol](#context-compression-protocol)
below for the full flow.

### 3. Pattern Extraction for Skills

When a new codebase pattern should become a reusable skill:

```
pack_codebase(path="masonry/scripts/")
  → packed scripts directory

extract_patterns(packed_output, focus="optimization loops")
  → list of recurring patterns with examples

generate_skill(patterns=..., name="improve-agent")
  → skill.md ready for review
```

### 4. Cross-Repo Analysis

When comparing multiple repos (competitive analysis, analogues research):

```
pack_remote_repo("https://github.com/repo-1") → pack1
pack_remote_repo("https://github.com/repo-2") → pack2
```

Pass both packed outputs to the analysis agent as context. No manual cloning,
no file-by-file reads, no temp directory management.

---

## Context Compression Protocol

Active compression is triggered when the orchestrator context exceeds 120K tokens.

### Compression Steps

1. Call `pack_codebase` with focus on `.autopilot/`, changed source files, and `spec.md`
2. Call `compress_for_handoff` on the packed output → produces ≤500-token summary
3. Write summary to `.autopilot/handoff-context.md`
4. Reference the handoff file in the `build.log` HANDOFF entry:
   ```
   [ISO-8601] HANDOFF: Context compressed via repomix. Summary at .autopilot/handoff-context.md.
   Tasks 1-5 DONE, task 6 IN_PROGRESS. Next: Continue task 6.
   ```
5. Commit `.autopilot/handoff-context.md` with the other handoff files

### Resuming from Compressed Context

On session start when `handoff-context.md` is present:

1. Read `handoff-context.md` first (500 tokens vs thousands from raw files)
2. Read `progress.json` to confirm task state
3. Verify handoff summary is consistent with `progress.json`
4. Proceed — full context is restored from the compressed summary

---

## Token Savings

| Scenario | Without repomix | With repomix |
|----------|----------------|--------------|
| Analyze 50-file repo | 50 Read calls (~50K tokens) | 1 `pack_remote_repo` call |
| Handoff summary | 2000-token full build.log | ≤500-token compressed |
| Pattern search across codebase | 20+ Grep calls | 1 `grep_repomix_output` call |
| Cross-repo comparison | Clone + read both repos | 2 `pack_remote_repo` calls |

---

## Token Budget

| Context level | Action |
|---------------|--------|
| <80K tokens | No action needed |
| 80K–120K tokens | Warn user, suggest compact output + `/build` continuation |
| >120K tokens | Active compression via repomix before any new agent spawns |

---

## See Also

- `context-continuation.md` — full handoff protocol including repomix compression steps
- `repo-researcher` agent — uses `pack_remote_repo` as primary analysis tool
- `/ultrawork` skill — high-throughput parallel build (separate concern from context compression)
- `worktrunk.md` — parallel worker isolation for large builds
