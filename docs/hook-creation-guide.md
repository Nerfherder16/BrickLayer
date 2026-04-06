# Hook & Engine Module Creation Guide

## Quick Rule

**Hooks → Node.js. Campaign runners → Python.**

If you are writing something that fires on every Claude Code tool use, it goes in `masonry/src/hooks/` as a `.js` file.
If you are writing something that mutates campaign state, runs an agent, or uses ML, it goes in `bl/` as a `.py` file.

---

## When to Use Node.js

Use Node.js when the code is:

- **Cold-start sensitive** — hook files fire on every PreToolUse, PostToolUse, UserPromptSubmit, or Stop event. Python subprocess cold-start adds 300-400ms per invocation; a busy session with 50 tool calls adds 15-20 seconds of pure overhead. JS hooks start in 50-100ms.
- **Integrated with the Claude Code hook system** — hooks read from stdin, write JSON to stdout, and exit 2 to block. This contract is native to Node.js and awkward to wrap in Python.
- **Doing file I/O on YAML, JSON, or Markdown** — reading agent registry, writing `.autopilot/` state files, appending to `.mas/` logs. Node.js `fs` is fast and the hook system already runs in Node.
- **A thin MCP CLI wrapper** — if you need to expose a new capability as an MCP tool and the logic is already in a JS engine module, add a CLI entry point rather than rewriting in Python.

---

## When to Use Python

Use Python when the code is:

- **Using DSPy or any ML/optimization library** — DSPy, scikit-learn, sentence-transformers, and similar have no JS equivalents. All optimization and scoring logic lives in `bl/`.
- **Performing GPU inference or calling Ollama with structured prompts** — the `bl/` modules have established patterns for async Ollama calls with timeout and retry handling.
- **Spawning tmux agents** — `bl/tmux/core.py:spawn_agent()` is the canonical entry point for agent dispatch. There is no JS equivalent; do not replicate this logic in hooks.
- **Mutating campaign state** — `bl/findings.py`, `bl/questions.py`, `bl/campaign_context.py` own campaign state. Writes that cross session boundaries belong in Python where the type system and tests are.
- **Part of the `bl/` ecosystem** — anything that imports from `bl/` must be Python.

---

## Migration Checklist: Adding a New JS Engine Module to Python MCP

When a capability starts in Python but needs to be callable from the hook system (or vice versa), follow this pattern — `masonry/src/engine/cli/` is the canonical wiring example.

1. **Create the JS module** in `masonry/src/engine/<module-name>.js`. Keep it pure: take input, return a result, no side effects on global hook state.

2. **Create a CLI wrapper** in `masonry/src/engine/cli/<module-name>-cli.js`. Accept arguments via `process.argv` or stdin JSON, print result to stdout as JSON, exit 0 on success, exit 1 on error.

3. **Add `_call_js_engine()` in `server.py`** — call the CLI wrapper via `subprocess.run`, parse stdout JSON, and include a Python fallback for when Node.js is unavailable.

4. **Add tests** in `masonry/tests/cli-<module-name>.test.js`. Cover the happy path, malformed input, and the error exit code.

---

## Latency Data

| Execution path | Cold-start overhead | Notes |
|----------------|--------------------|-----------------------------|
| Node.js hook | 50-100ms | V8 already warm in most sessions |
| Python subprocess | 300-400ms | CPython interpreter + import chain |
| Python via MCP server | ~0ms (already running) | MCP server stays resident |

**Why this matters:** Hooks that fire on PreToolUse or PostToolUse run on every single file read, edit, and bash call. A 300ms Python subprocess on a session with 100 tool calls adds 30 seconds of wall-clock latency the user feels directly. Use JS for hooks. Use the resident MCP server for Python capabilities that hooks need to call.

---

## Reference

See `masonry/src/engine/cli/` for the canonical CLI wrapper pattern. Any new engine module that needs to cross the JS/Python boundary should mirror that directory structure.
