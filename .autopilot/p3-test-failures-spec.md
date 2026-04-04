# P3 — Pre-existing Test Failure Fixes

## Context
All tests target masonry/mcp_server/server.py (Python MCP server) and masonry/src/dspy_pipeline/.
20 failures across 3 clusters. All tasks are independent and can run in parallel.

---

## Wave 1 — All tasks parallel

- [ ] **Task 1** — Implement `masonry/src/dspy_pipeline/optimizer.py` and `masonry/src/dspy_pipeline/training_extractor.py`. Read `masonry/tests/dspy_pipeline/test_optimizer.py` and `masonry/tests/dspy_pipeline/test_run_optimization.py` first to discover the exact API. Key requirements from tests: `optimizer.py` must expose `optimize_all(registry, dataset, output_dir, optimize_agent_fn=None)` with a per-agent dispatch table mapping agent names to signature classes (KarenSig for karen, ResearchAgentSig for others); it must skip agents with fewer than 5 examples. Also needs `masonry/src/dspy_pipeline/signatures.py` with `KarenSig` and `ResearchAgentSig` DSPy signature classes (can be stubs — tests mock the LLM calls). `training_extractor.py` must expose `TrainingExtractor` class with `extract(findings_dir)` returning list of dicts. Read `tests/test_training_extractor.py` for exact API contract.

- [ ] **Task 2** — Add `masonry_optimization_status` tool to `masonry/mcp_server/server.py`. This is the Python MCP server (NOT masonry/bin/masonry-mcp.js). Read `tests/test_mcp_new_tools.py` TestMasonryOptimizationStatus tests for the exact contract. The tool takes `optimized_dir` (str path), reads JSON files from that directory where each file is named `{agent_name}.json` and contains `{"score": 0.87, ...}`, returns `{"agents": [{"agent": name, "score": score}, ...], "count": N}`. Add to the TOOLS dict in server.py following the existing pattern (fn + schema keys).

- [ ] **Task 3** — Fix `masonry_onboard` returning empty `onboarded: []` list. Read `tests/test_mcp_new_tools.py` TestMasonryOnboard tests. The tool calls `masonry.scripts.onboard_agent.onboard(agents_dirs, registry_path, dspy_output_dir)`. The bug: when the test passes a tmp_path as `agents_dirs`, the onboard function is not finding or registering the agent. Read `masonry/scripts/onboard_agent.py` starting at the `onboard()` function (line 430) to trace the bug — check if the agents_dirs path scanning, YAML frontmatter parsing, or registry write is silently failing. Fix the root cause in `onboard_agent.py` (or the server tool handler if the params are being passed wrong). The test passes `dspy_output_dir` but the tool currently passes `Path(os.devnull)` — that may be the issue if onboard_agent writes to dspy_output_dir and fails silently on devnull.

- [ ] **Task 4** — Fix `tests/test_server.py` collection error. The file does `from test_mcp_mas_status import *` at line 11, but `tests/` is not in sys.path when pytest runs from repo root, so Python can't find `test_mcp_mas_status` module even though it exists at `tests/test_mcp_mas_status.py`. Fix: add `sys.path.insert(0, str(Path(__file__).parent))` before the import in `tests/test_server.py`. Also verify `tests/test_training_extractor.py` passes once Task 1 creates `training_extractor.py`.
