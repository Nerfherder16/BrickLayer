# Question Bank — Masonry Self-Research

**Campaign type**: BrickLayer 2.0
**Generated**: 2026-03-21T00:00:00Z
**Modes selected**: diagnose, research, validate

**Mode selection rationale:**
- `diagnose` — The project-brief.md identifies 7 known uncertainties with specific code locations. These are suspected failure modes requiring targeted investigation: hook double-firing, race conditions, registry path resolution failures, timeout corruption. These are not hypothetical — they are architectural concerns with concrete code paths.
- `research` — The semantic threshold (0.70), LLM timeout (8s), and embedding model choice are unvalidated assumptions. No calibration data exists. The 60%+ deterministic coverage claim is unverified. These require evidence gathering against real request distributions.
- `validate` — The typed payload schemas (`extra="forbid"`), the four-layer pipeline contract, and the hook interaction model make architectural claims that can be verified by tracing code paths and checking invariant preservation.

---

## Wave 1

### D1.1: Do masonry-observe, masonry-guard, and masonry-agent-onboard fire twice per PostToolUse event when working inside the masonry project directory?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: Both `hooks.json` (project-scoped, lines 16-45) and `~/.claude/settings.json` (global) register the same three async PostToolUse hooks (masonry-observe, masonry-guard, masonry-agent-onboard). When CWD is the masonry project, Claude Code loads both configurations and fires each hook twice per tool call, causing duplicate Recall writes, double strike counting, and double agent registration attempts.
**Agent**: diagnose-analyst
**Success criterion**: Definitive evidence (from Claude Code hook loading behavior documentation or empirical trace) showing whether project-scoped hooks.json entries are additive to or override global settings.json entries for the same event type.

---

### D1.2: Can masonry-guard's 3-strike counter be corrupted by a timeout-killed partial write?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: masonry-guard (async, 3s timeout per `hooks.json` line 33) uses a file-based strike queue. If the hook exceeds its 3-second timeout mid-write, Claude Code kills the process, leaving the strike counter file in a partially-written state. The next invocation reads a corrupt counter and either (a) resets to zero (losing strikes) or (b) throws a parse error and silently fails, effectively disabling the guard.
**Agent**: diagnose-analyst
**Success criterion**: Trace the exact file I/O path in `masonry-guard.js` for the strike counter. Identify whether writes are atomic (rename-based) or direct, and whether reads have error recovery for malformed data. Verdict: FAILURE if writes are non-atomic and no read-side recovery exists.

---

### D1.3: Does `_load_registry` in `router.py` silently return an empty list when CWD is not the repository root?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: The registry loader tries `{project_dir}/masonry/agent_registry.yml` first, then relative `masonry/agent_registry.yml` from CWD (per `routing_architecture.md` lines 121-123). When Masonry is invoked from a subprocess whose CWD is a subdirectory (e.g., `src/` or a project within the BrickLayer repo), both paths fail. The function returns an empty list without logging. This silently disables Layer 1 Rule 5, all of Layer 2, and causes Layer 3 to prompt with zero agents.
**Agent**: diagnose-analyst
**Success criterion**: Read `router.py:_load_registry` and confirm the exact path resolution logic, whether it logs on failure, and what downstream behavior results from an empty registry. Provide the specific code path that leads to silent empty return.

---

### D1.4: Do masonry-observe and masonry-guard race on shared session state when both fire as async PostToolUse hooks on the same tool call?

**Status**: DONE
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: Both hooks are async PostToolUse handlers (per `hook_inventory.md` lines 32-33). Claude Code fires them in parallel without waiting. If both read and write the same session state file (e.g., a campaign state JSON or a shared temp file), the last writer wins. Specifically: masonry-observe could write a finding detection result that masonry-guard then overwrites with error pattern data, or vice versa, producing inconsistent state.
**Agent**: diagnose-analyst
**Success criterion**: Identify every file path that both `masonry-observe.js` and `masonry-guard.js` read from or write to. If they share any mutable file, confirm whether concurrent writes are serialized (e.g., via lockfile) or unprotected. Verdict: FAILURE if shared mutable state exists without serialization.

---

### D1.5: Does masonry-stop-guard block Stop before masonry-build-guard can run, hiding the build-guard's block reason?

**Status**: DONE
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: Both are synchronous Stop hooks registered in `~/.claude/settings.json` (per `hook_inventory.md` lines 36-38). If Claude Code processes Stop hooks sequentially and the first hook exits with code 2 (block), the second hook may not execute. This means the block reason shown to the user depends on hook registration order, not on which condition is more important. If masonry-stop-guard blocks first (uncommitted changes), the user never learns about pending autopilot tasks from masonry-build-guard.
**Agent**: diagnose-analyst
**Success criterion**: Determine Claude Code's behavior when multiple synchronous Stop hooks are registered: does it run all hooks and merge block reasons, or short-circuit on the first exit-code-2? Document the observed or documented behavior.

---

### D1.6: Does `shlex.quote` in `llm_router.py` produce correct escaping for Windows cmd.exe when `shell=True`?

**Status**: DONE
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: On Windows (`llm_router.py` lines 46-48), the LLM router uses `shlex.quote(full_prompt)` to escape the prompt before passing it as a shell string with `shell=True`. However, `shlex.quote` uses POSIX quoting rules (wrapping in single quotes), which are not recognized by Windows cmd.exe. A prompt containing single quotes, ampersands (`&`), pipe characters (`|`), or angle brackets (`>`, `<`) could cause command breakage or truncation when executed via cmd.exe.
**Agent**: diagnose-analyst
**Success criterion**: Determine whether `shlex.quote` produces cmd.exe-safe output on Windows. Test with prompt strings containing double quotes, ampersands, and pipe characters. If any cause command breakage, verdict: FAILURE.

---

### D1.7: Does masonry-agent-onboard lose entries during concurrent Write events to multiple agent .md files?

**Status**: DONE
**Mode**: diagnose
**Priority**: LOW
**Hypothesis**: `masonry-agent-onboard` (async, 5s timeout) detects new `.md` files in agent directories and appends to `agent_registry.yml`. If two agent files are written in rapid succession (e.g., during batch copy), both hook invocations read the same YAML state, compute their append independently, and write back. The second write overwrites the first agent's entry — a classic read-modify-write race.
**Agent**: diagnose-analyst
**Success criterion**: Read `masonry-agent-onboard.js` and trace the YAML file append logic. Determine whether it uses atomic append or read-modify-write. If read-modify-write without locking, verdict: FAILURE.

---

### R1.1: Is the semantic routing threshold of 0.70 well-calibrated for `qwen3-embedding:0.6b` and the current agent registry?

**Status**: DONE
**Mode**: research
**Priority**: HIGH
**Hypothesis**: The threshold `_DEFAULT_THRESHOLD = 0.70` in `semantic_layer.py` line 29 was set without calibration (per `routing_architecture.md` line 72). For a small embedding model (0.6B parameters), cosine similarity distributions may be compressed into a narrow band (e.g., 0.60-0.85 for all pairs), making 0.70 either too permissive (everything matches) or too restrictive (nothing matches). Without empirical distribution data, the threshold is arbitrary.
**Agent**: research-analyst
**Success criterion**: Estimate the expected cosine similarity distribution for `qwen3-embedding:0.6b` across typical agent description pairs. Determine whether 0.70 falls in a discriminative region or in a plateau where small threshold changes produce large match-rate swings.

---

### R1.2: What percentage of real Masonry requests are routed deterministically, and does this meet the claimed 60%+ coverage?

**Status**: PENDING
**Mode**: research
**Priority**: HIGH
**Hypothesis**: The 60%+ claim (per `deterministic_layer.py` docstring and `routing_architecture.md` line 33) is an assertion, not a measurement. The deterministic layer handles 5 rule types: slash commands, autopilot state, campaign state, UI state, and Mode field. In practice, many user requests are freeform text matching none of these patterns. Actual deterministic coverage may be 30-40% for mixed-use sessions.
**Agent**: research-analyst
**Success criterion**: Enumerate request categories that deterministic routing can and cannot handle. Estimate coverage for at least 3 session types: (a) pure BrickLayer campaign, (b) mixed dev session, (c) ad-hoc conversation. Provide a justified coverage estimate for each.

---

### R1.3: Is the LLM router's 8-second timeout sufficient for Claude Haiku subprocess invocations on Windows?

**Status**: PENDING
**Mode**: research
**Priority**: HIGH
**Hypothesis**: The LLM router (`llm_router.py` line 16) sets `_LLM_TIMEOUT = 8` seconds. On Windows with `shell=True` (lines 46-48), cmd.exe shell startup overhead is added. Claude Haiku cold-start latency plus shell overhead may regularly exceed 8 seconds, causing the LLM layer to timeout and fall through to Layer 4 on a significant fraction of calls, making Layer 3 unreliable on Windows.
**Agent**: research-analyst
**Success criterion**: Estimate typical subprocess latency for `claude --model claude-haiku-4-5 --print -p "..."` on Windows with `shell=True`. Compare against the 8-second budget. If median latency exceeds 6 seconds (leaving <2s margin), verdict: the timeout is too tight.

---

### R1.4: Does the `_SLASH_COMMANDS` table in `deterministic.py` cover all slash commands defined in Masonry skills?

**Status**: PENDING
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: The slash command table (`deterministic_layer.py` lines 25-32) hardcodes 6 patterns: `/plan`, `/build`, `/fix`, `/verify`, `/bl-run`, `/masonry-run`. CLAUDE.md lists 15+ additional skills (`/masonry-init`, `/masonry-status`, `/masonry-fleet`, `/ultrawork`, `/pipeline`, `/masonry-team`, `/masonry-code-review`, `/masonry-security-review`, `/ui-init`, `/ui-compose`, `/ui-review`, `/ui-fix`, `/retro-apply`). Each missed command traverses Layers 2-3, adding latency and LLM cost.
**Agent**: research-analyst
**Success criterion**: List every slash command in Masonry skills. Compare against `_SLASH_COMMANDS`. Report the gap count and the routing cost per missed command.

---

### R1.5: What is the failure behavior when Ollama at `192.168.50.62:11434` is unreachable during semantic routing?

**Status**: PENDING
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: When Ollama is down, `route_semantic` catches the exception and returns None. However, the 15-second timeout (`_TIMEOUT = 15.0`, `semantic_layer.py` line 30) means each routing call blocks for up to 15 seconds before falling through to Layer 3. With no circuit-breaker or fast-fail after repeated failures, every non-deterministic request during an Ollama outage adds 15 seconds of latency.
**Agent**: research-analyst
**Success criterion**: Trace the exact timeout path in `route_semantic`. Confirm whether Ollama unavailability adds a full 15-second delay per call. Determine if any caching, circuit-breaking, or fast-fail mechanism exists.

---

### R1.6: What classes of requests reliably reach Layer 4 (fallback), and is this correct behavior or a gap?

**Status**: PENDING
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: Layer 4 returns `target_agent="user"` for "genuinely ambiguous" requests. But if the registry is empty (D1.3), Ollama is down (R1.5), and the LLM times out (R1.3), then ALL non-deterministic requests reach fallback regardless of clarity. The fallback rate is a compound function of infrastructure availability, not just request ambiguity. A caller cannot distinguish "correct fallback" from "infrastructure fallback" using only the RoutingDecision.
**Agent**: research-analyst
**Success criterion**: Enumerate independent failure modes causing fallback. Distinguish "correct fallback" (ambiguous request) from "infrastructure fallback" (system failure). Propose how a caller could differentiate these from the RoutingDecision fields.

---

### V1.1: Does the LLM router safely construct RoutingDecision without passing extra JSON fields to the `extra="forbid"` schema?

**Status**: PENDING
**Mode**: validate
**Priority**: HIGH
**Hypothesis**: `RoutingDecision` uses `ConfigDict(extra="forbid")` (`payloads.py` line 130). The `routing_architecture.md` (line 88) claims this is safe because `llm_router.py` constructs `RoutingDecision` from named arguments, not by unpacking the parsed dict. This claim can be verified by reading `llm_router.py` lines 100-105 and confirming only `target_agent`, `layer`, `confidence`, and `reason` are passed.
**Agent**: design-reviewer
**Success criterion**: Confirm the `RoutingDecision` constructor call in `llm_router.py` uses only named arguments. If it passes `**parsed` or any unfiltered dict, verdict: FAILURE. If only named arguments: CONFIRMED SAFE.

---

### V1.2: Does the `_MODE_FIELD_RE` regex correctly extract Mode values from all valid BrickLayer question formats?

**Status**: PENDING
**Mode**: validate
**Priority**: MEDIUM
**Hypothesis**: The regex `r"\*\*Mode\*\*:\s*(\w+)"` (`deterministic_layer.py` line 36) is case-sensitive. It matches `**Mode**: diagnose` but misses `**mode**: diagnose` (lowercase M). If any agent or tool produces lowercase mode fields, the deterministic layer misses them, forcing unnecessary Layer 2/3 routing.
**Agent**: design-reviewer
**Success criterion**: Test the regex against all format variations appearing in BrickLayer question banks and agent outputs. List any valid Mode field formats the regex fails to match.

---

### V1.3: Does the semantic layer's in-memory embedding cache handle registry changes (new/modified agents) correctly?

**Status**: PENDING
**Mode**: validate
**Priority**: MEDIUM
**Hypothesis**: The cache `_embedding_cache` (`semantic_layer.py` line 23) is keyed by `agent.description + " " + ", ".join(agent.capabilities)`. If an agent's description changes, the old cache entry becomes dead weight and a new entry is created. If an agent is removed from the registry, its cached embedding is never evicted. Over a long-running process, the cache grows monotonically. More importantly, the cache never invalidates — stale entries cannot cause misrouting because similarity is only computed against current registry entries, but they do waste memory.
**Agent**: design-reviewer
**Success criterion**: Confirm whether stale cache entries can cause incorrect routing or only waste memory. If routing correctness is preserved despite stale entries, verdict: WARNING (memory waste). If stale entries could cause routing to a non-existent agent, verdict: FAILURE.

---

### V1.4: Does the LLM router validate that the returned `target_agent` exists in the registry before constructing the RoutingDecision?

**Status**: PENDING
**Mode**: validate
**Priority**: HIGH
**Hypothesis**: `llm_router.py` lines 93-105 extract `target_agent` from the LLM's JSON response and pass it directly to `RoutingDecision` without checking membership in the registry. Claude Haiku could hallucinate an agent name, and the invalid name would propagate to the caller unchecked, causing a downstream dispatch failure.
**Agent**: design-reviewer
**Success criterion**: Read `llm_router.py` and confirm whether `target_agent` is validated against the registry. If no validation exists, determine whether the caller (`router.py`) validates, or whether a hallucinated name propagates unchecked.

---

### V1.5: Does masonry-approver auto-approve writes to Tier 1/2 authority files during build mode?

**Status**: PENDING
**Mode**: validate
**Priority**: MEDIUM
**Hypothesis**: `masonry-approver` (PreToolUse, synchronous) auto-approves Write/Edit/Bash when `.autopilot/mode` is "build" or `.ui/mode` is "compose". If it checks mode but not target file path, it would auto-approve writes to `project-brief.md`, `agent_registry.yml`, or other Tier 1/2 files during automated builds, violating the source authority hierarchy.
**Agent**: design-reviewer
**Success criterion**: Read `masonry-approver.js` and determine whether it filters auto-approval by target file path or only by active mode. If it approves all writes when mode is active regardless of path, assess the risk to Tier 1/2 files.

---
