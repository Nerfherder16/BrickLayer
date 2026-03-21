# Masonry Routing Architecture

Four-layer routing engine that dispatches user requests to specialist agents. Lives in `src/routing/`.

---

## Overview

Every request received by Masonry (via the `masonry_route` MCP tool or direct Python call) passes through the same pipeline. Each layer either returns a `RoutingDecision` or returns `None`, triggering the next layer. Layer 4 (fallback) always returns — it never returns None.

```
Request text + project_dir
        |
        v
  Layer 1: Deterministic   ─── match ──→ RoutingDecision (confidence=1.0)
        | no match
        v
  Layer 2: Semantic (Ollama) ─ match ──→ RoutingDecision (confidence=cosine score)
        | no match or Ollama down
        v
  Layer 3: LLM (claude-haiku) ─ match ─→ RoutingDecision (confidence=0.6)
        | timeout or failure
        v
  Layer 4: Fallback           ─────────→ RoutingDecision (target_agent="user", confidence=0.0)
```

---

## Layer 1 — Deterministic

**File:** `src/routing/deterministic.py`
**LLM calls:** 0
**Expected coverage:** 60%+ of real requests

Runs five rules in priority order. Returns the first match with `confidence=1.0`.

| Rule | Pattern | Target Agent | Notes |
|------|---------|--------------|-------|
| 1. Slash commands | `/plan`, `/build`, `/fix`, `/verify`, `/bl-run`, `/masonry-run` | spec-writer, build-workflow, fix-workflow, verify-workflow, campaign-conductor | Regex match on request text |
| 2. Autopilot state | `.autopilot/mode` file content | build-workflow, fix-workflow, verify-workflow | Reads file from project_dir |
| 3. Campaign state | `masonry-state.json` `active_agent` field | (dynamic) | Only fires if mode=campaign and active_agent is set |
| 4. UI state | `.ui/mode` file content | ui-compose-workflow, ui-review-workflow | Reads file from project_dir |
| 5. Mode field | `**Mode**: <value>` in request text | First agent in registry with matching mode | Uses `get_agents_for_mode(registry, mode_value)` |

**Known gaps:** The slash command table is hardcoded. New slash commands added to skills/ are not automatically picked up — they require a manual addition to the `_SLASH_COMMANDS` list in `deterministic.py`.

**Registry dependency:** Rule 5 (Mode field) requires a populated registry. If the registry fails to load (see path resolution issue below), Rule 5 always misses.

---

## Layer 2 — Semantic

**File:** `src/routing/semantic.py`
**LLM calls:** 0 (uses local Ollama)
**Threshold:** cosine similarity >= 0.70
**Model:** `qwen3-embedding:0.6b`
**Ollama host:** `http://192.168.50.62:11434` (configurable via `OLLAMA_URL` env var)
**Timeout:** 15s per batch call

Embeds the request text and all agent descriptions+capabilities using the Ollama embedding model. Computes cosine similarity between the request embedding and each agent corpus. Returns the best match if its score meets or exceeds the threshold.

**Caching:** Agent corpus embeddings are cached in a module-level dict (`_embedding_cache`) keyed by the agent's description+capabilities string. The cache is in-memory only — it resets on every Python process restart. Within a session, the first routing call embeds all agents; subsequent calls only embed the request.

**Batch strategy:** All uncached agents are embedded in a single `/api/embed` batch call. If the batch call fails, the function returns `None` (falls through to Layer 3). It does not attempt per-agent retry.

**Failure modes:**
- Ollama unreachable: returns None silently after logging to stderr
- Ollama returns empty embeddings list: returns None
- Any exception: returns None (broad except clause)
- Threshold not met: returns None (best score below 0.70)

**Threshold calibration concern:** The 0.70 threshold was set as a default without documented calibration against real request distributions. A threshold that is too high causes premature fallthrough to the LLM layer on every ambiguous request. A threshold that is too low causes misrouting (a request goes to a semantically similar but wrong agent).

---

## Layer 3 — LLM Router

**File:** `src/routing/llm_router.py`
**LLM calls:** 1 (claude-haiku-4-5-20251001)
**Confidence:** Fixed at 0.6 for all matches
**Timeout:** 8 seconds
**Platform note:** On Windows, uses `shell=True` with a single string command (required because `claude` is a `.cmd` file on Windows)

Constructs a prompt listing all registry agents with their descriptions/capabilities, then asks Claude Haiku to select the best agent and return a JSON object: `{"target_agent": "agent-name", "reason": "brief reason"}`.

**JSON parsing:** First tries `json.loads(stdout)` directly. If that fails, uses regex `\{[^}]+\}` to extract embedded JSON. If neither succeeds, returns None.

**Pydantic validation risk:** The LLM may include extra fields in the JSON response (e.g., `{"target_agent": "...", "reason": "...", "confidence": 0.9}`). The `RoutingDecision` model uses `extra="forbid"` — but the LLM router constructs the `RoutingDecision` directly from `target` and `reason` fields, not from unpacking the full parsed dict. Extra JSON fields are ignored. This is safe.

**Failure modes:**
- Timeout (8s): returns None
- Non-zero exit from claude: returns None
- JSON parse failure: returns None
- No `target_agent` key in JSON: returns None

---

## Layer 4 — Fallback

Always returns:
```python
RoutingDecision(
    target_agent="user",
    layer="fallback",
    confidence=0.0,
    reason="Ambiguous request -- asking user for clarification",
)
```

This is the safety net. Any request reaching Layer 4 should be investigated — it means all three automated layers failed to classify it.

---

## Registry Loading

**File:** `src/routing/router.py`, function `_load_registry`

The router loads `agent_registry.yml` at the start of every `route()` call. It does not cache the registry — each call reloads from disk.

Path resolution order:
1. `{project_dir}/masonry/agent_registry.yml`
2. Relative `masonry/agent_registry.yml` (from CWD)
3. Returns empty list if neither exists

**CWD dependency issue:** If the process CWD is not the repository root, both paths may fail to resolve, producing an empty registry. An empty registry causes:
- Layer 1, Rule 5 (Mode field): always misses (no agents to match)
- Layer 2 (Semantic): returns None immediately (`if not registry: return None`)
- Layer 3 (LLM): produces a prompt listing zero agents, likely causing the LLM to hallucinate or return a nonsensical target

---

## RoutingDecision Schema

```python
class RoutingDecision(BaseModel):
    target_agent: str
    layer: Literal["deterministic", "semantic", "llm", "fallback"]
    confidence: float  # 0.0–1.0
    reason: str        # max 100 chars
    fallback_agents: list[str]  # default empty
```

`extra="forbid"` is set — unknown fields cause a ValidationError. The `reason` field is truncated to 100 chars in deterministic and semantic layers but the LLM layer sets it directly from parsed JSON (also truncated to 100 in the code).

---

## Known Thresholds and Constants

| Constant | Value | File | Notes |
|----------|-------|------|-------|
| Semantic threshold | 0.70 | `semantic.py:_DEFAULT_THRESHOLD` | Not documented as calibrated |
| Embedding model | qwen3-embedding:0.6b | `semantic.py:_DEFAULT_MODEL` | Must be pulled on Ollama host |
| Ollama timeout | 15s | `semantic.py:_TIMEOUT` | Per batch call |
| LLM model | claude-haiku-4-5-20251001 | `llm_router.py:_LLM_MODEL` | Pinned version |
| LLM timeout | 8s | `llm_router.py:_LLM_TIMEOUT` | Subprocess timeout |
| LLM confidence | 0.6 | `llm_router.py:_LLM_CONFIDENCE` | Fixed for all LLM matches |
| Reason max length | 100 chars | `deterministic.py:_decision` | Truncated before schema validation |
