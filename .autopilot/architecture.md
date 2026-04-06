# Architecture — BrickLayer 2.0 Partial JS Engine Migration

## Component Boundaries

```
masonry/mcp_server/server.py         ← Python FastMCP (stays Python)
  _call_js_engine(cli_script, args)  ← new helper, subprocess bridge
      ↓ subprocess.run(["node", ...])
masonry/src/engine/cli/              ← NEW: 4 CLI wrappers (Node.js)
  registry-list.js                   ← wraps registry-router.js
  route.js                           ← wraps session/registry-router.js detectIntentAsync
  status.js                          ← reads questions.md + findings/ count
  healloop.js                        ← wraps healloop.js state machine
      ↓ require()
masonry/src/engine/*.js              ← existing JS engine (complete, tested)
  registry-router.js  (listAgents, getAgent, searchAgents, checkDrift)
  healloop.js         (heal loop state machine)
  routing.js          (routePrompt)
      ↓ reads
masonry/agent_registry.yml           ← agent registry YAML
{project}/questions.md               ← campaign question bank
{project}/findings/                  ← finding files
```

## Interface Contracts

### CLI Wrapper: registry-list.js
```
Input:  node registry-list.js [--tier <t>] [--mode <m>] [--project-dir <p>]
Stdout: JSON array of agent objects  |  {"error":"..."} on failure
Exit:   0 = success, 1 = failure
```

### CLI Wrapper: route.js
```
Input:  node route.js --prompt "<text>" [--project-dir <p>]
Stdout: {"agent":"<name>","confidence":<float>,"layer":"L1a|L1b|L2|null","note":"<string>"}
        OR {"agent":null,"confidence":0,"layer":null,"note":"no match"}  (not an error)
Exit:   0 = success (including no-match), 1 = unexpected error
```

### CLI Wrapper: status.js
```
Input:  node status.js --project-dir <p>
Stdout: {"state":"<mode|no_project>","questions":{"total":N,"answered":N,"pending":N},"wave":N,"findings":N}
Exit:   0 always (missing project = {"state":"no_project"}), 1 only on crash
```

### CLI Wrapper: healloop.js
```
Input:  node healloop.js --project-dir <p> --question-id <id> --verdict <V> [--max-cycles <N>]
Stdout: {"ran":false,"reason":"env_not_set"}        — BRICKLAYER_HEAL_LOOP != 1
        {"ran":false,"reason":"verdict_not_applicable"}  — verdict not FAILURE/DIAGNOSIS_COMPLETE
        {"ran":true,"cycles":N,"final_verdict":"FIXED|HEAL_EXHAUSTED"}
Exit:   0 always (including skipped), 1 only on crash
```

## Python Subprocess Helper

`_call_js_engine(cli_script: str, args: list[str], timeout: int) -> dict | None`

```
MASONRY_CLI_DIR = MASONRY_DIR / "src" / "engine" / "cli"
path = MASONRY_CLI_DIR / cli_script
result = subprocess.run(["node", str(path)] + args, capture_output=True, text=True, timeout=timeout)
if result.returncode == 0:
    return json.loads(result.stdout)   # parsed dict
else:
    logger.warning(f"JS engine CLI failed: {result.stderr[:200]}")
    return None  # → Python fallback fires
```

Falls back to Python on: non-zero exit, TimeoutExpired, FileNotFoundError, JSONDecodeError.

## MCP Tool Wiring

| MCP Tool               | CLI Wrapper         | Timeout | Fallback               |
|------------------------|---------------------|---------|------------------------|
| masonry_registry_list  | registry-list.js    | 10s     | YAML-reading Python loop |
| masonry_route          | route.js            | 15s     | Python slash-cmd + keyword routing |
| masonry_status         | status.js           | 10s     | Python questions.md reader |
| masonry_run_question   | healloop.js (post)  | 300s    | non-fatal, appends to response |

`masonry_run_question` only calls healloop.js AFTER verdict is determined, for FAILURE or DIAGNOSIS_COMPLETE only.

## Hook Extension

`masonry-hook-watch.js` (PostToolUse hook, existing):
- Current: detects edits to hooks/ files — lint stub (TODO)
- New behavior: if `tool_name === "Write"` AND file path is inside `masonry/src/hooks/` OR `masonry/src/engine/`: emit language-choice reminder to stderr before running smoke test
- Rationale: Write = new file creation; Edit = modifying existing

Language reminder format:
```
[hook-watch] NEW HOOK/ENGINE FILE DETECTED: <filename>
─────────────────────────────────────────────────────
Language choice guide: docs/hook-creation-guide.md
Quick rule:
  Node.js  → hot path (fires every tool use), MCP tool integration, I/O-bound
  Python   → DSPy/ML, tmux agent spawn, campaign state mutation
─────────────────────────────────────────────────────
```

## Out-of-Scope (DO NOT MODIFY)

- `bl/` — campaign runner, tmux, crucible, DSPy pipeline
- `masonry/mcp_server/server.py` tool schemas (input/output types)
- `masonry/src/engine/healloop.js` internals
- All existing 71 hook benchmark test expectations

## Test Locations

- New CLI tests: `masonry/tests/cli-registry-list.test.js`, `cli-route.test.js`, `cli-status.test.js`, `cli-healloop.test.js`
- Hook benchmark: `masonry/tests/hook-benchmark.js` (must stay 71/71)
- Engine tests: `masonry/tests/engine-*.test.js`
