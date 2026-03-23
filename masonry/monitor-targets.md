# Masonry Monitor Targets

Metrics that should be checked periodically during long-running MCP server sessions.
Each entry specifies the metric, how to measure it, thresholds, and check frequency.

---

## `_embedding_cache_size`

**Source**: `masonry/src/routing/semantic.py`
**Motivated by**: V1.3 (WARNING — stale cache grows monotonically)

**What it measures**: The number of entries in the module-level `_embedding_cache` dict in `semantic.py`. Each entry is a cached Ollama embedding vector (~4KB). Entries are never evicted, so the cache grows throughout the MCP server process lifetime. Stale entries (for agents removed from registry or whose descriptions changed) accumulate as dead weight.

**How to measure**:
1. Via MCP server diagnostic endpoint (when implemented): `GET /masonry/diagnostics/cache_size`
2. Via log inspection: look for `[semantic] cache size=N` lines in MCP server stderr
3. Via Python inspection in a running process:
   ```python
   from masonry.src.routing import semantic
   print(len(semantic._embedding_cache))
   ```

**Thresholds**:

| Level | Cache entries | Action |
|-------|--------------|--------|
| OK | < 150 | No action — normal operation |
| WARNING | 150–500 | Monitor more closely; consider restarting MCP server at next opportunity |
| FAILURE | > 500 | Cache growth likely pathological (schema churn or test loop). Restart MCP server process; investigate cause of churn |

**Threshold rationale**:
- Normal registry: ~40–50 agents → cache size ≤ 50 at stable state
- WARNING at 150: 3× normal indicates significant agent churn (testing/refactoring)
- FAILURE at 500: 10× normal indicates a pathological growth pattern (e.g., programmatic description updates in a loop, integration test runs)

**Check frequency**: On each `masonry_optimization_status` MCP tool call; or manually when MCP server has been running > 24 hours.

**Quick fix if threshold exceeded**: No code changes needed — restart the MCP server process to clear the module-level cache.

**Permanent fix if frequently exceeded**: Add a cache size limit to `semantic.py`:
```python
# After writing to _embedding_cache:
if len(_embedding_cache) > 200:
    _embedding_cache.clear()  # conservative: clear all and re-warm on next request
```

---

## `ollama_backend_reachable`

**Source**: `masonry/src/routing/semantic.py` (Ollama embedding calls), `masonry/src/dspy_pipeline/optimizer.py` (local model fallback)
**Motivated by**: M32.1 — confirmed OFFLINE 2026-03-23; no local `ollama` binary on PATH either

**What it measures**: Whether the Ollama inference backend at `192.168.50.62:11434` is reachable and responding to API requests. This host is the designated fallback for zero-credential optimization (DSPy MIPROv2 via local Ollama rather than Anthropic API). Semantic routing also uses this endpoint for cosine-similarity embedding at similarity threshold 0.75. When unreachable, semantic routing falls back to the LLM layer (one Haiku call per route), increasing latency and API cost.

**How to measure**:
```bash
curl -s --connect-timeout 3 http://192.168.50.62:11434/api/tags
```
A 200 response with JSON body indicates the backend is up. A timeout, connection refused, or non-200 response indicates degraded or unavailable state.

**Current status**: OFFLINE (confirmed 2026-03-23). No local `ollama` binary on PATH, so localhost fallback (`127.0.0.1:11434`) is also unavailable. Semantic routing is degraded — all routing falls through to LLM layer.

**Thresholds**:

| Level | Condition | Action |
|-------|-----------|--------|
| OK | 200 response within 3 s | Normal operation — semantic routing active, zero-credential optimization available |
| WARNING | Any non-200 response or timeout (single check) | Investigate host status; semantic routing degraded; increase monitoring frequency |
| FAILURE | Unreachable for > 7 consecutive campaign days | Blocks zero-credential optimization fallback. Update `constants.py` `SEMANTIC_ROUTING_ENABLED` to `False` and document the outage; switch DSPy optimization to `ANTHROPIC_API_KEY` mode |

**Threshold rationale**:
- Single failure is likely transient (host reboot, CasaOS restart, Docker restart)
- 7-day threshold is conservative: a week of absence means the host is not coming back on its own; the campaign planning assumption of local-model optimization is invalid
- No localhost fallback means there is no secondary path — the WARNING state is meaningful even for a single miss

**Check frequency**: At the start of each optimization run (`masonry_optimize_agent`) and each `masonry_status` call. Also check manually if semantic routing appears to be running slower than expected (indicates LLM fallback is active).

**Quick fix if WARNING**: SSH into CasaOS (`192.168.50.19`) and check whether the Ollama container/service is running. Restart with `docker compose restart ollama` if the container is stopped.

**Permanent fix if FAILURE threshold reached**: Either restore the Ollama host or update the routing configuration to treat semantic routing as optional. Document in `project-brief.md` that zero-credential optimization is unavailable for the current campaign.

---

## `miprov2_run_duration`

**Source**: `masonry/src/dspy_pipeline/optimizer.py`
**Motivated by**: M24.1 (Wave 24) — R23.1 (WARNING) reported 5-7 hour run times for full MIPROv2 optimization

**What it measures**: Wall-clock time from `optimize_agent()` invocation to completion, measured per agent per run. Extended runtimes indicate either Ollama inference bottlenecks (local model) or Anthropic API throughput limits (cloud model), or unexpectedly large training data sets passed to the optimizer.

**How to measure**:
1. Check the optimizer log output: `[optimizer] agent={name} trials={n} elapsed={seconds}s`
2. Via Kiln UI: the "OPTIMIZE" button panel shows elapsed time during an active run
3. Via `masonry_optimization_status` MCP tool: returns `last_run_duration_s` per agent when available

**Thresholds**:

| Level | Duration | Action |
|-------|----------|--------|
| OK | < 6 hours | Normal operation |
| WARNING | 6–10 hours | Monitor — check `num_trials` setting and training data size; consider reducing `num_instruct_candidates` |
| FAILURE | > 10 hours | Optimization likely stalled or looping. Kill the run, inspect logs, reduce search space before retrying |

**Threshold rationale**:
- Normal full run (13 trials, Ollama local): ~4 hours
- Normal full run (20 trials, Anthropic API): ~8-15 minutes — FAILURE threshold applies to local Ollama runs
- WARNING at 6h: exceeds expected ceiling for 13-trial run, likely due to Ollama inference slowdown or oversized training data
- FAILURE at 10h: run is effectively stalled; no expected configuration produces a legitimate 10h+ run

**Check frequency**: At start and end of each optimization run; also if Kiln shows an optimization task as active for > 3 hours.

**Quick fix if threshold exceeded**: Kill the optimization process. Reduce `num_trials` to 10 and `max_bootstrapped_demos` to 2. Restart. If Ollama is the bottleneck, switch to `ANTHROPIC_API_KEY` mode for faster iteration.

---
