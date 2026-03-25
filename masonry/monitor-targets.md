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

**Check frequency**: Manually when MCP server has been running > 24 hours.

**Quick fix if threshold exceeded**: No code changes needed — restart the MCP server process to clear the module-level cache.

**Permanent fix if frequently exceeded**: Add a cache size limit to `semantic.py`:
```python
# After writing to _embedding_cache:
if len(_embedding_cache) > 200:
    _embedding_cache.clear()  # conservative: clear all and re-warm on next request
```

---

## `ollama_backend_reachable`

**Source**: `masonry/src/routing/semantic.py` (Ollama embedding calls)
**Motivated by**: M32.1 — confirmed OFFLINE 2026-03-23; no local `ollama` binary on PATH either

**What it measures**: Whether the Ollama inference backend at `192.168.50.62:11434` is reachable and responding to API requests. Semantic routing uses this endpoint for cosine-similarity embedding at similarity threshold 0.75. When unreachable, semantic routing falls back to the LLM layer (one Haiku call per route), increasing latency and API cost.

**How to measure**:
```bash
curl -s --connect-timeout 3 http://192.168.50.62:11434/api/tags
```
A 200 response with JSON body indicates the backend is up. A timeout, connection refused, or non-200 response indicates degraded or unavailable state.

**Current status**: OFFLINE (confirmed 2026-03-23; re-confirmed M35.1 2026-03-23, exit code 28, 5 s timeout). No local `ollama` binary on PATH, so localhost fallback (`127.0.0.1:11434`) is also unavailable. Semantic routing is degraded — all routing falls through to LLM layer. Three health checks (M32.1, M33.1, M35.1) all confirm OFFLINE within the same campaign date.

**Thresholds**:

| Level | Condition | Action |
|-------|-----------|--------|
| OK | 200 response within 3 s | Normal operation — semantic routing active |
| WARNING | Any non-200 response or timeout (single check) | Investigate host status; semantic routing degraded; increase monitoring frequency |
| FAILURE | Unreachable for > 7 consecutive campaign days | Update `constants.py` `SEMANTIC_ROUTING_ENABLED` to `False` and document the outage |

**Threshold rationale**:
- Single failure is likely transient (host reboot, CasaOS restart, Docker restart)
- 7-day threshold is conservative: a week of absence means the host is not coming back on its own; the campaign planning assumption of local-model optimization is invalid
- No localhost fallback means there is no secondary path — the WARNING state is meaningful even for a single miss

**Check frequency**: At each `masonry_status` call. Also check manually if semantic routing appears to be running slower than expected (indicates LLM fallback is active).

**Quick fix if WARNING**: SSH into CasaOS (`192.168.50.19`) and check whether the Ollama container/service is running. Restart with `docker compose restart ollama` if the container is stopped.

**Permanent fix if FAILURE threshold reached**: Either restore the Ollama host or update the routing configuration to treat semantic routing as optional.

### Recovery Procedure

*Established: M33.1, 2026-03-23. Outage confirmed: M32.1 / M33.1 / M35.1 — all 2026-03-23 (exit code 28 timeout, 3 consecutive checks).*

**Step 1 — SSH into CasaOS host**
```bash
ssh tim@192.168.50.19
```

**Step 2 — Check Ollama container status**
```bash
docker ps -a --filter name=ollama
```
If status shows `Exited`, proceed to Step 3.
If no container is listed at all, re-deploy from CasaOS app store.

**Step 3 — Restart the container**

Via Docker Compose (preferred — standard CasaOS app store path):
```bash
cd /DATA/AppData/ollama
docker compose up -d
```

Via Docker directly (fallback if compose file path differs):
```bash
docker start ollama
```

**Step 4 — Verify Ollama responds locally**
```bash
curl -s http://localhost:11434/api/tags
```
Expected: JSON body with model list. Exit code 0.

**Step 5 — Verify from campaign host**
```bash
curl -s --connect-timeout 3 http://192.168.50.62:11434/api/tags
```
Expected: JSON body. Exit code 0. If timeout persists, check firewall/network: `ping 192.168.50.62` from CasaOS host and confirm port 11434 is not blocked.

**Step 6 — Confirm qwen3:14b is present**
```bash
docker exec ollama ollama list
```
If `qwen3:14b` is missing (unlikely unless volume was wiped with `down -v`):
```bash
docker exec ollama ollama pull qwen3:14b
```

**Step 7 — Smoke test embedding (confirms semantic routing layer)**
```bash
curl -s http://192.168.50.62:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3:14b","prompt":"test routing query"}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print(f'OK — embedding dims: {len(d[\"embedding\"])}')"
```
Expected: `OK — embedding dims: 5120` (or model-specific dimension). Semantic routing is operational.

**Common failure reasons (ranked by likelihood)**:
1. Container stopped after CasaOS host reboot (no `restart: unless-stopped` policy set) → Fix: restart container; add `restart: unless-stopped` to compose file
2. OOM kill (exit code 137 in `docker ps`) → Fix: restart; consider memory limit in compose file
3. GPU/CUDA driver issue after host update → Fix: `docker logs ollama` for CUDA errors; may need GPU driver reinstall
4. CasaOS host itself unreachable → Fix: check `ping 192.168.50.19` from local network; may require physical access

**Note on model data persistence**: Docker volumes persist across container stop/start/restart. `qwen3:14b` weights survive all restart operations. They are only lost if `docker compose down -v` was explicitly run or the host storage volume was deleted.

---
