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
