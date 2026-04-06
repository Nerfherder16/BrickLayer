# Pseudocode — BrickLayer 2.0 Partial JS Engine Migration

## Task 1 — JS CLI wrapper: registry-list

Read `masonry/agent_registry.yml`. Parse YAML agents map.
If `--tier` arg present, filter to agents where tier matches.
If `--mode` arg present, filter to agents where modes array includes value.
If `--project-dir` provided, resolve registry path relative to it.
Output JSON array of agent objects to stdout. Exit 0.
If registry file missing or YAML parse fails: output `{"error":"..."}` to stdout, exit 1.

Tests: no-args returns array, --tier trusted filters, --mode build filters, missing registry exits 1.

## Task 2 — JS CLI wrapper: route

Parse `--prompt` (required). If missing, output error JSON, exit 1.
Import `detectIntentAsync` from `masonry/src/hooks/session/registry-router.js`.
Read `OLLAMA_HOST` env var (same as registry-router uses).
Call `detectIntentAsync(prompt)`.
If returns result: output `{"agent": name, "confidence": float, "layer": "L1a|L1b|L2", "note": string}` to stdout, exit 0.
If returns null (no route found): output `{"agent": null, "confidence": 0, "layer": null, "note": "no match"}`, exit 0.
If Ollama unreachable during L2 semantic: detectIntentAsync handles fallback internally; CLI just outputs whatever it returns.
If unhandled exception: output `{"error":"..."}`, exit 1.

Tests: /build prompt routes to rough-in L1b, registry keyword hits L1a, gibberish returns null, Ollama down doesn't crash.

## Task 3 — JS CLI wrapper: status

Parse `--project-dir` (required). Resolve to absolute path.
If directory doesn't exist: output `{"state":"no_project","questions":{"total":0,"answered":0,"pending":0},"wave":0,"findings":0}`, exit 0.
Read `questions.md` from project dir.
Parse question statuses: count total, count DONE (answered), compute pending = total - answered.
Detect wave number from questions.md header or highest wave seen in question IDs.
Count files in `findings/` directory (if exists).
Output status JSON to stdout, exit 0.
If unexpected crash: output `{"error":"..."}`, exit 1.

Tests: valid project dir returns counts, missing dir returns no_project state, wave number parsed correctly.

## Task 4 — JS CLI wrapper: healloop

Parse `--project-dir`, `--question-id`, `--verdict`, `--max-cycles` (optional, default 3).
Check env var `BRICKLAYER_HEAL_LOOP`. If not set to `"1"`: output `{"ran":false,"reason":"env_not_set"}`, exit 0.
Check verdict. If not FAILURE or DIAGNOSIS_COMPLETE: output `{"ran":false,"reason":"verdict_not_applicable"}`, exit 0.
Import healloop engine from `masonry/src/engine/healloop.js`.
Run heal loop state machine: up to max-cycles, each cycle calls diagnose-analyst then fix-implementer.
Track cycles run and final verdict (FIXED or HEAL_EXHAUSTED).
Output `{"ran":true,"cycles":N,"final_verdict":"FIXED|HEAL_EXHAUSTED"}`, exit 0.
On unexpected crash: output `{"error":"..."}`, exit 1.

Tests: without env returns env_not_set, HEALTHY verdict returns not_applicable, FAILURE with env triggers loop (mock agent calls).

## Task 5 — Wire masonry_registry_list into server.py

Add `_call_js_engine(cli_script, args, timeout)` helper at module level.
Helper: builds path as `MASONRY_DIR / "src" / "engine" / "cli" / cli_script`.
Calls `subprocess.run(["node", str(path)] + args, capture_output=True, text=True, timeout=timeout)`.
On returncode 0: parse stdout as JSON, return parsed object.
On any failure (non-zero exit, TimeoutExpired, FileNotFoundError, JSONDecodeError): log warning, return None.

In `masonry_registry_list`: call `_call_js_engine("registry-list.js", build_args(tier, mode, project_dir), timeout=10)`.
If result not None: return JSON of result.
If result is None: fall through to existing Python YAML-reading logic (fallback).
Tool input schema and output shape unchanged.

## Task 6 — Wire masonry_route into server.py

In `masonry_route`: build args `["--prompt", prompt]`. If context non-empty, add `["--context", context]`.
Call `_call_js_engine("route.js", args, timeout=15)`. Longer timeout — Ollama semantic layer may take time.
If result not None: return JSON of result.
If None: fall through to existing Python routing logic.

## Task 7 — Wire masonry_status into server.py

In `masonry_status`: call `_call_js_engine("status.js", ["--project-dir", project_dir], timeout=10)`.
If result not None and state is "no_project": return appropriate MCP response for missing project.
If result not None: return JSON of result.
If None: fall through to existing Python status reading logic.

## Task 8 — Wire healloop into masonry_run_question

After `masonry_run_question` determines its verdict:
If verdict in ("FAILURE", "DIAGNOSIS_COMPLETE"):
  Call `_call_js_engine("healloop.js", ["--project-dir", project_dir, "--question-id", qid, "--verdict", verdict], timeout=300)`.
  If heal_result not None: append `"heal_loop": heal_result` to the response dict before returning.
  If None: return response without heal_loop key (non-fatal).
HEALTHY/WARNING verdicts: do not call healloop at all.

## Task 9 — Extend masonry-hook-watch.js

In hook-watch, after path guard passes, add language-choice check BEFORE smoke test:
Check if tool_name is "Write" (new file creation signal).
Check if resolved path is inside hooks/ or engine/ directories.
If both true: emit reminder block to stderr with filename, quick rule for Node.js vs Python, and pointer to docs/hook-creation-guide.md.

After reminder (or if no reminder needed), run existing smoke test as before.
Existing behavior unchanged for Edit tool uses.
All hook-benchmark tests must still pass.

## Task 10 — ARCHITECTURE.md dual-engine section

Find insertion point after existing engine module table.
Add "## Dual-Engine Architecture" section (~80 lines):
- JS Engine (Hot Path): hooks, CLI wrappers, MCP fast-path tools, healloop dispatch
- Python Engine (Campaign Path): bl/runners/, bl/tmux/, crucible.py, DSPy — permanent
- Decision criteria table: latency-sensitive → JS, ML/GPU → Python, tmux spawn → Python, file I/O → JS
- ASCII wiring diagram: Python MCP → subprocess → Node CLI → JS engine module → disk

## Task 11 — Hook language-choice guide + README

docs/hook-creation-guide.md:
- When to use Node.js: cold-start sensitive (hook fires on every tool use), MCP integration, file I/O
- When to use Python: DSPy/ML, tmux agent spawn, campaign state mutation, GPU inference
- Default rule: hooks/ → JS, bl/runners/ → Python
- Migration checklist: create CLI wrapper → wire into server.py with fallback → add tests
- Reference masonry/src/engine/cli/ as canonical pattern

masonry/src/hooks/README.md:
- Decision table with 7 factors: cold-start latency, MCP integration, DSPy/ML, hook system, campaign runner, file I/O, GPU
- Each factor: Node.js column vs Python column

## Task 12 — Run full test suite (review-only)

Run `node masonry/tests/hook-benchmark.js` — expect 71/71 pass.
Run new CLI tests: `node --test masonry/tests/cli-*.test.js`
Run engine tests if they exist: `node --test masonry/tests/engine-*.test.js`
Report pass/fail counts. Zero failures required before proceeding to Task 13.

## Task 13 — Update docs/reviews/hook-map.md

Update masonry-hook-watch.js entry: add note that Write on new hook/engine files now emits language-choice reminder to stderr.
Add "JS Engine Integration" note to masonry_route, masonry_status, masonry_registry_list MCP tools section.
Note that masonry_run_question now triggers healloop CLI for FAILURE/DIAGNOSIS_COMPLETE verdicts.
Update "Last updated" date to 2026-04-06.
Update total hook/tool count if it changed.
