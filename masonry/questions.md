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

**Status**: DONE
**Mode**: research
**Priority**: HIGH
**Hypothesis**: The 60%+ claim (per `deterministic_layer.py` docstring and `routing_architecture.md` line 33) is an assertion, not a measurement. The deterministic layer handles 5 rule types: slash commands, autopilot state, campaign state, UI state, and Mode field. In practice, many user requests are freeform text matching none of these patterns. Actual deterministic coverage may be 30-40% for mixed-use sessions.
**Agent**: research-analyst
**Success criterion**: Enumerate request categories that deterministic routing can and cannot handle. Estimate coverage for at least 3 session types: (a) pure BrickLayer campaign, (b) mixed dev session, (c) ad-hoc conversation. Provide a justified coverage estimate for each.

---

### R1.3: Is the LLM router's 8-second timeout sufficient for Claude Haiku subprocess invocations on Windows?

**Status**: DONE
**Mode**: research
**Priority**: HIGH
**Hypothesis**: The LLM router (`llm_router.py` line 16) sets `_LLM_TIMEOUT = 8` seconds. On Windows with `shell=True` (lines 46-48), cmd.exe shell startup overhead is added. Claude Haiku cold-start latency plus shell overhead may regularly exceed 8 seconds, causing the LLM layer to timeout and fall through to Layer 4 on a significant fraction of calls, making Layer 3 unreliable on Windows.
**Agent**: research-analyst
**Success criterion**: Estimate typical subprocess latency for `claude --model claude-haiku-4-5 --print -p "..."` on Windows with `shell=True`. Compare against the 8-second budget. If median latency exceeds 6 seconds (leaving <2s margin), verdict: the timeout is too tight.

---

### R1.4: Does the `_SLASH_COMMANDS` table in `deterministic.py` cover all slash commands defined in Masonry skills?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: The slash command table (`deterministic_layer.py` lines 25-32) hardcodes 6 patterns: `/plan`, `/build`, `/fix`, `/verify`, `/bl-run`, `/masonry-run`. CLAUDE.md lists 15+ additional skills (`/masonry-init`, `/masonry-status`, `/masonry-fleet`, `/ultrawork`, `/pipeline`, `/masonry-team`, `/masonry-code-review`, `/masonry-security-review`, `/ui-init`, `/ui-compose`, `/ui-review`, `/ui-fix`, `/retro-apply`). Each missed command traverses Layers 2-3, adding latency and LLM cost.
**Agent**: research-analyst
**Success criterion**: List every slash command in Masonry skills. Compare against `_SLASH_COMMANDS`. Report the gap count and the routing cost per missed command.

---

### R1.5: What is the failure behavior when Ollama at `192.168.50.62:11434` is unreachable during semantic routing?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: When Ollama is down, `route_semantic` catches the exception and returns None. However, the 15-second timeout (`_TIMEOUT = 15.0`, `semantic_layer.py` line 30) means each routing call blocks for up to 15 seconds before falling through to Layer 3. With no circuit-breaker or fast-fail after repeated failures, every non-deterministic request during an Ollama outage adds 15 seconds of latency.
**Agent**: research-analyst
**Success criterion**: Trace the exact timeout path in `route_semantic`. Confirm whether Ollama unavailability adds a full 15-second delay per call. Determine if any caching, circuit-breaking, or fast-fail mechanism exists.

---

### R1.6: What classes of requests reliably reach Layer 4 (fallback), and is this correct behavior or a gap?

**Status**: DONE
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: Layer 4 returns `target_agent="user"` for "genuinely ambiguous" requests. But if the registry is empty (D1.3), Ollama is down (R1.5), and the LLM times out (R1.3), then ALL non-deterministic requests reach fallback regardless of clarity. The fallback rate is a compound function of infrastructure availability, not just request ambiguity. A caller cannot distinguish "correct fallback" from "infrastructure fallback" using only the RoutingDecision.
**Agent**: research-analyst
**Success criterion**: Enumerate independent failure modes causing fallback. Distinguish "correct fallback" (ambiguous request) from "infrastructure fallback" (system failure). Propose how a caller could differentiate these from the RoutingDecision fields.

---

### V1.1: Does the LLM router safely construct RoutingDecision without passing extra JSON fields to the `extra="forbid"` schema?

**Status**: DONE
**Mode**: validate
**Priority**: HIGH
**Hypothesis**: `RoutingDecision` uses `ConfigDict(extra="forbid")` (`payloads.py` line 130). The `routing_architecture.md` (line 88) claims this is safe because `llm_router.py` constructs `RoutingDecision` from named arguments, not by unpacking the parsed dict. This claim can be verified by reading `llm_router.py` lines 100-105 and confirming only `target_agent`, `layer`, `confidence`, and `reason` are passed.
**Agent**: design-reviewer
**Success criterion**: Confirm the `RoutingDecision` constructor call in `llm_router.py` uses only named arguments. If it passes `**parsed` or any unfiltered dict, verdict: FAILURE. If only named arguments: CONFIRMED SAFE.

---

### V1.2: Does the `_MODE_FIELD_RE` regex correctly extract Mode values from all valid BrickLayer question formats?

**Status**: DONE
**Mode**: validate
**Priority**: MEDIUM
**Hypothesis**: The regex `r"\*\*Mode\*\*:\s*(\w+)"` (`deterministic_layer.py` line 36) is case-sensitive. It matches `**Mode**: diagnose` but misses `**mode**: diagnose` (lowercase M). If any agent or tool produces lowercase mode fields, the deterministic layer misses them, forcing unnecessary Layer 2/3 routing.
**Agent**: design-reviewer
**Success criterion**: Test the regex against all format variations appearing in BrickLayer question banks and agent outputs. List any valid Mode field formats the regex fails to match.

---

### V1.3: Does the semantic layer's in-memory embedding cache handle registry changes (new/modified agents) correctly?

**Status**: DONE
**Mode**: validate
**Priority**: MEDIUM
**Hypothesis**: The cache `_embedding_cache` (`semantic_layer.py` line 23) is keyed by `agent.description + " " + ", ".join(agent.capabilities)`. If an agent's description changes, the old cache entry becomes dead weight and a new entry is created. If an agent is removed from the registry, its cached embedding is never evicted. Over a long-running process, the cache grows monotonically. More importantly, the cache never invalidates — stale entries cannot cause misrouting because similarity is only computed against current registry entries, but they do waste memory.
**Agent**: design-reviewer
**Success criterion**: Confirm whether stale cache entries can cause incorrect routing or only waste memory. If routing correctness is preserved despite stale entries, verdict: WARNING (memory waste). If stale entries could cause routing to a non-existent agent, verdict: FAILURE.

---

### V1.4: Does the LLM router validate that the returned `target_agent` exists in the registry before constructing the RoutingDecision?

**Status**: DONE
**Mode**: validate
**Priority**: HIGH
**Hypothesis**: `llm_router.py` lines 93-105 extract `target_agent` from the LLM's JSON response and pass it directly to `RoutingDecision` without checking membership in the registry. Claude Haiku could hallucinate an agent name, and the invalid name would propagate to the caller unchecked, causing a downstream dispatch failure.
**Agent**: design-reviewer
**Success criterion**: Read `llm_router.py` and confirm whether `target_agent` is validated against the registry. If no validation exists, determine whether the caller (`router.py`) validates, or whether a hallucinated name propagates unchecked.

---

### V1.5: Does masonry-approver auto-approve writes to Tier 1/2 authority files during build mode?

**Status**: DONE
**Mode**: validate
**Priority**: MEDIUM
**Hypothesis**: `masonry-approver` (PreToolUse, synchronous) auto-approves Write/Edit/Bash when `.autopilot/mode` is "build" or `.ui/mode` is "compose". If it checks mode but not target file path, it would auto-approve writes to `project-brief.md`, `agent_registry.yml`, or other Tier 1/2 files during automated builds, violating the source authority hierarchy.
**Agent**: design-reviewer
**Success criterion**: Read `masonry-approver.js` and determine whether it filters auto-approval by target file path or only by active mode. If it approves all writes when mode is active regardless of path, assess the risk to Tier 1/2 files.

---

## Wave 2

**Generated from findings**: D1.1, D1.5, R1.1, R1.3, V1.5, synthesis open threads
**Mode transitions applied**:
- D1.1 FAILURE (root cause identified: double-fire) → F2.1 Fix (minimum safe fix verification — remove plugin hooks.json entries)
- V1.5 FAILURE (DIAGNOSIS_COMPLETE: path blocklist spec fully defined) → F2.2 Fix (implement blocklist)
- D1.5 FAILURE (insufficient evidence: Stop hook ordering empirically unresolved) → D2.1 narrowing Diagnose
- R1.1 UNCALIBRATED → R2.1 Research (live calibration benchmark)
- R1.3 FAILURE → R2.2 Research (empirical subprocess latency measurement)
- synthesis thread (masonry-subagent-tracker uninvestigated) → D2.2 Diagnose
- synthesis thread (DSPy pipeline correctness uninvestigated) → D2.3 Diagnose
- synthesis thread (masonry-approver path traversal edge case) → V2.1 Validate
- V1.3 WARNING (stale cache) → M2.1 Monitor

---

### F2.1: What is the minimum safe change to eliminate hook double-fire, and does removing observe+guard from the plugin hooks.json break any functionality that the global settings.json registration does not already provide?

**Status**: DONE
**Operational Mode**: Fix
**Priority**: HIGH
**Motivated by**: D1.1 — FAILURE: masonry-observe and masonry-guard are registered in both the project-level `hooks/hooks.json` (no event matcher, fires on ALL PostToolUse) and the global `~/.claude/settings.json` (matcher: `Write|Edit`). The synthesis identified the fix as "remove the duplicate registrations from either the plugin config or the global settings, not both" and recommends keeping global settings.json and removing the observe+guard entries from `hooks/hooks.json`.
**Hypothesis**: Removing masonry-observe and masonry-guard from `hooks/hooks.json` (keeping only masonry-stop in that file, or removing it entirely) eliminates the double-fire with no loss of coverage because the global `~/.claude/settings.json` registrations remain active. No functionality is lost because the global registrations already cover the exact same event type with a more specific matcher (`Write|Edit` vs. no matcher).
**Method**: diagnose-analyst
**Success criterion**: (1) Confirm which hooks are currently listed in `hooks/hooks.json` and whether any of them are NOT duplicated in `~/.claude/settings.json`. (2) Confirm that removing the duplicates from `hooks/hooks.json` leaves all intended coverage intact. (3) Identify any hook listed in `hooks/hooks.json` that serves a project-specific purpose not replicated in global config — if any such hook exists, it must be preserved. Verdict: DIAGNOSIS_COMPLETE if a safe, zero-loss removal list can be specified; FAILURE if removing entries from hooks.json would drop coverage for any event.

---

### F2.2: Does the Tier 1/2 path blocklist fix specified in V1.5 correctly reject `../`-traversed paths that resolve to Tier 1/2 targets, or can a path like `../../masonry/project-brief.md` bypass the regex patterns?

**Status**: DONE
**Operational Mode**: Fix
**Priority**: HIGH
**Motivated by**: V1.5 — FAILURE: masonry-approver auto-approves all writes during build mode with no path filtering. The finding specifies a 6-pattern blocklist using regex. The fix specification is structurally complete but has one untested edge case: whether the patterns handle path traversal (`../`) in `file_path` values, since a developer agent could write `file_path: "../../masonry/project-brief.md"` which the pattern `/project-brief\.md$/i` would match by suffix — but only if the suffix check is applied to the raw string.
**Hypothesis**: The proposed regex patterns in V1.5 (`/project-brief\.md$/i`, `/agent_registry\.yml$/i`, etc.) match on the raw `file_path` string by suffix or substring. A path like `../../masonry/project-brief.md` ends with `project-brief.md` and would be caught by the `/project-brief\.md$/i` pattern. Similarly, `/[/\\]src[/\\]/` would NOT match `src/hooks/foo.js` if the path starts without a slash, but WOULD match if the path uses `./src/hooks/foo.js`. Verify all 6 proposed patterns against at least 4 path formats: relative, absolute Windows, absolute Unix, and `../`-traversed.
**Method**: design-reviewer
**Success criterion**: For each of the 6 proposed blocklist patterns from V1.5, provide at least one bypass path format (if any exists) and one confirmed-blocked path format. If all 6 patterns correctly block traversal paths AND cover all Tier 1/2 canonical locations, verdict: DIAGNOSIS_COMPLETE with fix implementation ready. If any pattern has a bypass, specify the corrected pattern. The fix spec must be complete enough to implement without ambiguity.

---

### D2.1: Does Claude Code run all registered Stop hooks regardless of individual exit codes, or does it short-circuit after the first hook exits with code 2?

**Status**: DONE
**Operational Mode**: Diagnose
**Priority**: MEDIUM
**Motivated by**: D1.5 — FAILURE (insufficient evidence): The finding concluded that masonry-stop-guard may prevent masonry-build-guard from executing because Claude Code may short-circuit on the first exit-code-2 Stop hook, but the exact ordering behavior could not be confirmed from documentation alone.
**Hypothesis**: Claude Code processes synchronous Stop hooks in registration order (as they appear in `~/.claude/settings.json`). If the first hook exits with code 2 (block), Claude Code short-circuits and does not execute subsequent Stop hooks. This means the block reason shown to the user is always from whichever hook is registered first — masonry-stop-guard (uncommitted changes) would mask masonry-build-guard (pending autopilot tasks) if stop-guard is listed first.
**Method**: diagnose-analyst
**Success criterion**: (1) Determine the registration order of masonry-stop-guard and masonry-build-guard in `~/.claude/settings.json`. (2) Find any Claude Code documentation, source reference, or empirical test result that definitively describes Stop hook execution policy (run-all vs. short-circuit-on-block). (3) If documentation is absent, construct a minimal empirical test: two Stop hooks with different exit-code-2 conditions and distinct stdout messages — run both conditions and observe which block reason appears. Verdict: FAILURE if short-circuit is confirmed and stop-guard is registered before build-guard; HEALTHY if all Stop hooks run regardless of exit codes.

---

### D2.2: Does masonry-subagent-tracker.js correctly handle concurrent SubagentStart events, and does its routing_log.jsonl write introduce a race condition or data loss under rapid agent spawning?

**Status**: DONE
**Operational Mode**: Diagnose
**Priority**: MEDIUM
**Motivated by**: synthesis open thread — masonry-subagent-tracker.js was not investigated in Wave 1. The hook writes to two shared files per invocation: `~/.masonry/state/agents.json` (global) and `{cwd}/masonry/routing_log.jsonl`. The agents.json write is a read-modify-write (load state, push entry, save). Under rapid agent spawning (e.g., `/ultrawork` dispatching 5 agents simultaneously), multiple SubagentStart events fire concurrently.
**Hypothesis**: The `agents.json` write in masonry-subagent-tracker.js uses `tryJSON` (read) → mutate → `safeWrite` (write) without any file locking or atomic rename. Under concurrent SubagentStart events, the last writer wins and earlier entries are silently lost. The `routing_log.jsonl` write uses `fs.appendFileSync` which is atomic for the single append but the active agent count in `masonry-state.json` will be incorrect if two hooks race on that file simultaneously.
**Method**: diagnose-analyst
**Success criterion**: Trace every file write in `masonry-subagent-tracker.js`. For each write: (1) determine if it is atomic (rename-based or append-only) or non-atomic (read-modify-write); (2) identify which files are shared across concurrent hook invocations; (3) for non-atomic writes, confirm whether data loss or corruption is possible. Verdict: FAILURE if agents.json or masonry-state.json can lose entries under concurrent writes; WARNING if routing_log.jsonl is safe but agents.json is not; HEALTHY if all writes are atomic or isolated.

---

### D2.3: Does the DSPy drift detector correctly compute `drift_pct` when `baseline_score` is 0.0, and does the training extractor produce valid training examples from findings that use non-standard verdict strings like `UNCALIBRATED`?

**Status**: DONE
**Operational Mode**: Diagnose
**Priority**: MEDIUM
**Motivated by**: synthesis open thread — the DSPy pipeline (drift_detector.py, training_extractor.py) was not investigated in Wave 1 despite being a core part of the Masonry optimization loop.
**Hypothesis**: Two distinct correctness issues may exist: (1) In `drift_detector.py` line 81-84: when `baseline_score == 0.0`, `drift_pct` is forced to `0.0` regardless of `current_score`. This means a brand-new agent (score 0.0) that consistently produces FAILURE verdicts (current_score = 0.0) would report drift_pct = 0.0 and alert_level = "ok" — a false negative. (2) In `training_extractor.py`, the `_VERDICT_RE` regex matches `**Verdict**: UNCALIBRATED` and extracts the string "UNCALIBRATED". The `_score_verdict` function in drift_detector.py scores this as 0.0 (failure tier), but "UNCALIBRATED" is not a failure — it is a data-gap finding that should arguably score 0.5. If the training extractor passes "UNCALIBRATED" into drift scoring, it penalizes the research-analyst agent unfairly.
**Method**: diagnose-analyst
**Success criterion**: (1) Confirm whether `drift_pct = 0.0` when `baseline_score = 0.0` regardless of `current_score` — if yes, specify whether this is intentional guard behavior or a logic error. (2) Confirm whether "UNCALIBRATED" appears in `_OK_VERDICTS`, `_PARTIAL_VERDICTS`, or neither in `drift_detector.py`. If it is absent from both sets (scoring 0.0), determine whether this is a known gap in the verdict taxonomy or an omission. Verdict: FAILURE for each confirmed correctness defect; HEALTHY if both behaviors are intentional and documented.

---

### R2.1: What is the actual cosine similarity distribution produced by `qwen3-embedding:0.6b` for the current agent registry descriptions, and does the 0.70 threshold fall in a discriminative region or a plateau?

**Status**: DONE
**Operational Mode**: Research
**Priority**: HIGH
**Motivated by**: R1.1 UNCALIBRATED — the threshold 0.70 for semantic routing was set without calibration data. The finding could not estimate the distribution without live measurement. This question targets the specific data gap that caused UNCALIBRATED.
**Hypothesis**: For a 0.6B embedding model, cosine similarities between unrelated short-text descriptions (agent capability strings of 10-30 words) typically cluster between 0.55 and 0.80 due to the model's limited representational capacity. The threshold 0.70 may fall inside this cluster, making it highly sensitive to small description wording changes. A discriminative threshold would be one where the similarity gap between a true positive (correct agent) and the next-best match exceeds 0.10.
**Method**: research-analyst
**Success criterion**: Using the agent descriptions in `agent_registry.yml`, compute (or estimate from qwen3-embedding literature/benchmarks) the expected pairwise similarity range between: (a) agents in the same mode (e.g., all diagnose-mode agents), (b) agents in different modes, and (c) a query string against its correct target agent vs. the second-best match. If the threshold 0.70 falls within a dense cluster where most pairs score 0.65-0.80, verdict: FAILURE (threshold not discriminative). If the threshold lies in a clear gap between positive and negative matches, verdict: CALIBRATED. Minimum acceptable evidence: cite published benchmarks for qwen3-embedding or similar small embedding models on short-text retrieval tasks.

---

### R2.2: What is the actual subprocess invocation latency for `claude --print` on this Windows 11 machine, and does it confirm or falsify the R1.3 finding that the 8-second timeout is too tight?

**Status**: DONE
**Operational Mode**: Research
**Priority**: HIGH
**Motivated by**: R1.3 FAILURE — the finding estimated 6-9 second median latency for `claude --print` on Windows based on known startup costs, but this was not empirically measured. The synthesis flags this as the highest-value Wave 2 benchmark.
**Hypothesis**: Shell startup (cmd.exe) on Windows 11 adds 200-400ms. Claude CLI cold-start (process initialization, model connection) adds 2-5s. A minimal `claude --print -p "echo 1"` invocation should complete in 3-6 seconds total, leaving no margin against an 8-second timeout. Under any network latency or resource contention, the call will regularly exceed 8 seconds.
**Method**: benchmark-engineer
**Success criterion**: Measure wall-clock time for at least 3 invocations of `claude --model claude-haiku-4-5 --print -p "reply with the single word ok"` using `subprocess.run` with `shell=True` on this machine (Windows 11, PowerShell or cmd.exe). Report: min, median, max latency. Compare against the `_LLM_TIMEOUT = 8` budget. If median > 6s: verdict FAILURE (confirms R1.3, timeout confirmed too tight). If median <= 5s: verdict HEALTHY (R1.3 estimate was pessimistic). If the `claude` CLI is unavailable or errors on all 3 attempts, report INCONCLUSIVE with the error.

---

### V2.1: Does the `getCandidateDirs` function in masonry-approver.js correctly extract the target file path for Bash tool calls, and could a Bash command that writes to a Tier 1/2 file (e.g., `echo x >> project-brief.md`) bypass the proposed path blocklist?

**Status**: DONE
**Operational Mode**: Validate
**Priority**: MEDIUM
**Motivated by**: V1.5 FAILURE — the V1.5 fix specification (path blocklist) addresses Write and Edit tool calls but the `tool_input` for a Bash call does not have a `file_path` field — it has a `command` field. A developer agent using `Bash` to append to `project-brief.md` would pass `toolInput.command = "echo x >> project-brief.md"` with `toolInput.file_path = undefined`, causing `isTier1Tier2("")` to return false and the write to be auto-approved.
**Hypothesis**: The proposed blocklist in V1.5 checks `toolInput.file_path || toolInput.path || ''`. For Bash tool calls, both `file_path` and `path` are undefined, so the effective path is `''`. The blocklist returns false for empty string, meaning ALL Bash commands are auto-approved during build mode regardless of what files they write to. Since developer agents routinely use Bash (`cp`, `echo >>`, `python scripts/...`) during builds, this represents a complete bypass for the Bash tool vector.
**Method**: design-reviewer
**Success criterion**: (1) Read `masonry-approver.js` `getCandidateDirs` and determine exactly what it extracts from a Bash tool call's `tool_input`. (2) Determine whether the proposed `isTier1Tier2` check from V1.5 would be applied to the Bash `command` string or only to `file_path`. (3) If the Bash vector is unblocked, specify the additional check needed (e.g., scan the `command` string for Tier 1/2 filename patterns). Verdict: FAILURE if Bash writes to Tier 1/2 files are not covered by the V1.5 fix specification; DIAGNOSIS_COMPLETE if a supplementary pattern for Bash command scanning can be fully specified.

---

### M2.1: Add `_embedding_cache` size to monitor-targets.md with a WARNING threshold at 150 entries and a FAILURE threshold at 500 entries, measured by inspecting the cache dict length in `semantic.py` during long-running MCP server sessions.

**Status**: DONE
**Operational Mode**: Monitor
**Priority**: LOW
**Motivated by**: V1.3 WARNING — the stale embedding cache grows monotonically and cannot cause misrouting but represents unbounded memory growth in long-running MCP server processes. The finding recommended a cache size limit as a future action.
**Hypothesis**: In normal operation (20-40 agents, stable registry), the cache will stay well under 150 entries. The WARNING threshold triggers only during extended testing scenarios with frequent agent description churn. The FAILURE threshold (500 entries) would indicate a cache growth bug rather than normal operation.
**Method**: research-analyst
**Success criterion**: (1) Confirm whether a `monitor-targets.md` file exists in the masonry project; if not, create it with a standard header. (2) Add a monitor entry for `_embedding_cache_size` with: metric name, measurement method (inspect `len(semantic._embedding_cache)` via MCP server diagnostic endpoint or log line), WARNING threshold = 150, FAILURE threshold = 500, check frequency = on each `masonry_optimization_status` MCP tool call. Verdict: COMPLETE when the monitor entry is written and the measurement method is actionable without code changes.

---

## Wave 3

**Generated from findings**: F2.1, F2.2, D2.2, D2.3, R2.1, V2.1, R1.6, V1.2, synthesis_wave2.md open threads
**Mode transitions applied**:
- F2.1 DIAGNOSIS_COMPLETE → F3.1 Fix (implement the hooks.json emptying)
- V2.1 DIAGNOSIS_COMPLETE (embedded in F2.2 chain) → F3.2 Fix (complete masonry-approver Bash vector + pattern fix)
- D2.3 FAILURE (DSPy taxonomy defects, root cause at code level) → F3.3 Fix (2-line verdict taxonomy patch)
- R1.6 FAILURE (RoutingDecision missing fallback_reason, fix spec known) → F3.4 Fix (schema field addition)
- R2.1 FAILURE (threshold not discriminative, data gap = no live calibration) → R3.1 Research (live calibration benchmark)
- synthesis thread (masonry-register.js UserPromptSubmit double-fire uninvestigated) → D3.1 Diagnose
- synthesis thread (masonry-session-start.js SessionStart double-fire side effects uninvestigated) → D3.2 Diagnose
- synthesis thread (DSPy build_dataset correctness with 27 Wave 1+2 findings) → R3.2 Research
- V1.2 WARNING (re.IGNORECASE 2-line fix known) → F3.5 Fix

---

### F3.1: Implement the fix specified in F2.1 — empty the `hooks` object in the plugin-level `hooks/hooks.json` to eliminate double-fire across all 10 hook registrations.

**Status**: DONE
**Operational Mode**: Fix
**Priority**: HIGH
**Motivated by**: F2.1 DIAGNOSIS_COMPLETE — the finding fully specified the safe fix: the plugin `hooks/hooks.json` contains 10 hook registrations that are exact duplicates of entries in `~/.claude/settings.json`. Setting `"hooks": {}` in `hooks/hooks.json` eliminates double-fire for every event type (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, SubagentStart, Stop) with zero coverage loss.
**Hypothesis**: After the fix, each hook fires exactly once per lifecycle event. The race conditions identified in D1.4, D2.2, and the duplicate Stop output from D2.1 are resolved as a side effect. No new test infrastructure is needed — the fix is a JSON object change.
**Method**: fix-implementer
**Success criterion**: (1) Read `hooks/hooks.json` and confirm its current `hooks` array contents. (2) Replace the `hooks` array with an empty object `{}` or empty array `[]`. (3) Verify that `~/.claude/settings.json` still contains all required hook registrations for this project. (4) Confirm the change by reading back the modified file. Verdict: FIX_APPLIED when `hooks/hooks.json` `hooks` object is empty and global settings.json retains all registrations.

---

### F3.2: Implement the complete masonry-approver path blocklist fix specified across V1.5, F2.2, and V2.1 — corrected directory patterns plus full Bash tool exclusion.

**Status**: DONE
**Operational Mode**: Fix
**Priority**: HIGH
**Motivated by**: V2.1 DIAGNOSIS_COMPLETE (embedded in F2.2 finding chain) — the complete fix specification is: (1) patterns 5 and 6 in the Tier 1/2 blocklist must use `(?:^|[/\\])` prefix instead of `/[/\\]/` to catch relative paths; (2) Bash tool calls must be excluded from auto-approval entirely because `toolInput.file_path` is undefined for Bash and command-string scanning is insufficiently reliable. The synthesis_wave2.md lines 69-80 provide the exact implementation-ready code block.
**Hypothesis**: With the corrected patterns and Bash exclusion in place, no developer agent path (`src/`, `docs/`, absolute, relative, traversal, or Bash-written) can auto-approve a write to a Tier 1/2 file. The fix requires changes to `masonry-approver.js` only.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/hooks/masonry-approver.js` and locate the `isTier1Tier2` function and the auto-approval logic block. (2) Update directory patterns 5 and 6 to use `(?:^|[/\\])` prefix. (3) Add the Bash tool exclusion block (`if (approve && toolName === 'bash') process.exit(0)`). (4) Verify the updated function against these 4 test paths: `src/hooks/foo.js`, `./src/hooks/foo.js`, `../../masonry/project-brief.md`, and an empty string for a Bash call. All Tier 1/2 paths must return true; the empty string must trigger the Bash exclusion branch. Verdict: FIX_APPLIED when all 4 test cases behave correctly per the specification.

---

### F3.3: Implement the DSPy drift detector verdict taxonomy patch — add `UNCALIBRATED` to `_PARTIAL_VERDICTS`, add `DIAGNOSIS_COMPLETE` to `_OK_VERDICTS`, and fix the `baseline_score == 0.0` division guard.

**Status**: DONE
**Operational Mode**: Fix
**Priority**: MEDIUM
**Motivated by**: D2.3 FAILURE — two confirmed correctness defects: (1) `baseline_score == 0.0` forces `drift_pct = 0.0` regardless of `current_score`, producing false-negative drift alerts for newly onboarded agents; (2) `UNCALIBRATED` verdict is absent from both `_OK_VERDICTS` and `_PARTIAL_VERDICTS`, scoring it 0.0 (failure) and unfairly penalizing the research-analyst agent for inconclusive data-gap findings.
**Hypothesis**: Adding `UNCALIBRATED` to `_PARTIAL_VERDICTS` (score 0.5) and `DIAGNOSIS_COMPLETE` to `_OK_VERDICTS` (score 1.0) fully corrects the taxonomy. The baseline=0.0 guard should be changed from `return 0.0` to use `current_score` directly (since there is no reference to compare against, treat it as initial calibration rather than zero-drift). Together these are a 6-line change to `drift_detector.py`.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/dspy_pipeline/drift_detector.py` and locate `_OK_VERDICTS`, `_PARTIAL_VERDICTS`, and the `baseline_score == 0.0` branch. (2) Add `DIAGNOSIS_COMPLETE` to `_OK_VERDICTS`. (3) Add `UNCALIBRATED` to `_PARTIAL_VERDICTS`. (4) Change the `baseline_score == 0.0` guard to emit `alert_level = "calibrating"` (or equivalent) with `drift_pct = None` rather than forcing `0.0`. (5) Confirm no other verdict strings in the Wave 1+2 findings fall outside both sets. Verdict: FIX_APPLIED when all three changes are in place and no known verdict string scores 0.0 incorrectly.

---

### F3.4: Add `fallback_reason` field to `RoutingDecision` in `payloads.py` to enable callers to distinguish correct fallback from infrastructure fallback.

**Status**: DONE
**Operational Mode**: Fix
**Priority**: LOW
**Motivated by**: R1.6 FAILURE — the `RoutingDecision` schema has no mechanism for the router to communicate why a request reached Layer 4. Callers cannot distinguish "genuinely ambiguous request" from "Ollama timed out + LLM timed out + registry empty." The synthesis_wave2.md P2 fix table specifies this as a 5-line schema addition.
**Hypothesis**: Adding an optional `fallback_reason: Optional[str] = None` field to `RoutingDecision` and populating it in `router.py` at the Layer 4 return site is a non-breaking change (no existing callers set this field). The field value should be one of: `"ambiguous"`, `"ollama_timeout"`, `"llm_timeout"`, `"registry_empty"`, or `"multi_failure"`. This enables downstream logging and alerting.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/schemas/payloads.py` and locate `RoutingDecision`. (2) Add `fallback_reason: Optional[str] = None` with appropriate Pydantic field annotation. (3) Read `src/routing/router.py` and find all Layer 4 return sites. (4) Populate `fallback_reason` at each return site with the appropriate value from the set above. (5) Confirm `extra="forbid"` still passes by verifying the field is declared in the model. Verdict: FIX_APPLIED when field is declared and populated at all Layer 4 return sites.

---

### F3.5: Apply the `re.IGNORECASE` fix to `_MODE_FIELD_RE` in `deterministic.py` and audit for other case-sensitivity issues in the deterministic layer.

**Status**: DONE
**Operational Mode**: Fix
**Priority**: LOW
**Motivated by**: V1.2 WARNING — `_MODE_FIELD_RE = re.compile(r"\*\*Mode\*\*:\s*(\w+)")` is case-sensitive, missing `**mode**: diagnose` (lowercase M). The synthesis_wave2.md P2 fix table identifies this as a 2-line change. The open thread from synthesis_wave2.md also asks whether other case-sensitivity issues exist in the deterministic layer.
**Hypothesis**: Adding `re.IGNORECASE` to `_MODE_FIELD_RE` is sufficient for the Mode field fix. A secondary audit of `deterministic.py` may reveal that slash command matching (`lower()` applied to `message`) is already case-insensitive, but autopilot state file names (`mode` vs `MODE`) or campaign file detection patterns may have similar case issues.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/routing/deterministic.py` and add `re.IGNORECASE` to `_MODE_FIELD_RE`. (2) Audit all other regex patterns and string comparisons in the file for case-sensitivity issues. (3) If additional case issues are found, fix them in the same pass or note them as separate findings. (4) Confirm the fix by testing `_MODE_FIELD_RE` against `**Mode**: diagnose`, `**mode**: diagnose`, and `**MODE**: diagnose`. Verdict: FIX_APPLIED when `_MODE_FIELD_RE` correctly matches all three variants and no other deterministic-layer case issues are found; FIX_APPLIED_WITH_FINDINGS if additional case issues were discovered and noted.

---

### R3.1: Run the 20-query calibration benchmark against the live `qwen3-embedding:0.6b` Ollama endpoint to determine whether the 0.70 threshold and the proposed 0.05 margin check are discriminative for the current agent registry.

**Status**: DONE
**Operational Mode**: Research
**Priority**: HIGH
**Motivated by**: R2.1 FAILURE — the threshold 0.70 was confirmed as non-discriminative from first-principles analysis, but the proposed fix (margin check `best - second >= 0.05`) was not validated with live similarity data. The synthesis_wave2.md recommends `_MARGIN_THRESHOLD = 0.05` pending calibration data.
**Hypothesis**: With 20 representative Masonry user prompts (4 per routing tier: code/build, research/campaign, audit/review, UI, and ad-hoc), the live similarity scores will show: (a) within-cluster pairs scoring 0.72-0.85, confirming the plateau identified in R2.1; (b) correct-agent vs. second-best margins typically 0.02-0.08; (c) the 0.05 margin threshold accepting roughly 60% of queries as unambiguous and deferring 40% to Layer 3. If the margin is below 0.02 for most queries, 0.05 is too aggressive; if above 0.10 for most, 0.05 is too conservative.
**Method**: benchmark-engineer
**Success criterion**: (1) Confirm Ollama is reachable at `http://192.168.50.62:11434` and `qwen3-embedding:0.6b` is loaded. If unreachable, mark INCONCLUSIVE per project-brief.md invariant 5. (2) Embed 20 sample prompts against the full agent registry. (3) For each prompt, record: top-1 similarity score, top-2 similarity score, margin (top1 - top2), whether the correct agent was top-1. (4) Report: mean margin, % of queries where margin >= 0.05, % of queries where correct agent was top-1. Verdict: CALIBRATED if >= 60% of queries have margin >= 0.05 and >= 80% of queries route to the correct agent at top-1; FAILURE if the margin distribution does not support the 0.05 threshold; INCONCLUSIVE if Ollama is unavailable.

---

### D3.1: What does `masonry-register.js` (UserPromptSubmit hook) do, and does its read-modify-write pattern on session state introduce a race condition analogous to the D2.2 agents.json race?

**Status**: DONE
**Operational Mode**: Diagnose
**Priority**: MEDIUM
**Motivated by**: synthesis_wave2.md open thread — `masonry-register.js` was identified in F2.1 as double-firing on every UserPromptSubmit event (fires twice per user prompt due to plugin + global registration). D2.2 found a similar race in masonry-subagent-tracker.js. Since register fires more frequently than SubagentStart (every prompt vs. every agent spawn), any race condition here has higher impact.
**Hypothesis**: `masonry-register.js` reads prompt metadata (session ID, model, prompt text) and writes to a shared session log file using a read-modify-write pattern similar to agents.json. With double-fire, two instances run concurrently per prompt. If they write to the same session file without file locking, interleaved writes could corrupt the session log or drop entries, causing the routing log to show phantom duplicates.
**Method**: diagnose-analyst
**Success criterion**: (1) Read `src/hooks/masonry-register.js` (or `hooks/masonry-register.js` if at root) in full. (2) Identify every file it reads and writes. (3) For each write: determine if it is atomic or read-modify-write. (4) Determine what happens when two instances of the hook run concurrently on the same UserPromptSubmit event (as happens due to double-fire). Verdict: FAILURE if concurrent writes can corrupt shared state; WARNING if writes are safe but produce duplicate log entries; HEALTHY if all writes are idempotent or atomic.

---

### D3.2: Does double-firing of `masonry-session-start.js` on SessionStart cause harmful side effects — specifically, does it initialize session state twice in a way that drops the first initialization's data?

**Status**: DONE
**Operational Mode**: Diagnose
**Priority**: MEDIUM
**Motivated by**: F2.1 DIAGNOSIS_COMPLETE — the finding confirmed masonry-session-start.js fires twice per session (registered in both plugin hooks.json and global settings.json). F3.1 will fix this, but before the fix is applied it is worth understanding whether the current double-fire is actively harmful (data loss) or merely wasteful (redundant work). If harmful, this elevates F3.1 urgency.
**Hypothesis**: masonry-session-start.js initializes session context: loading saved context from Recall, restoring autopilot/UI/campaign state, and writing an initial session record. If two instances run concurrently, the second initialization may overwrite the first's Recall-loaded context with a stale or empty snapshot. Alternatively, if the hook is idempotent (always reads the same Recall data and writes the same session record), double-fire is harmless beyond the extra API call.
**Method**: diagnose-analyst
**Success criterion**: (1) Read `src/hooks/masonry-session-start.js` in full. (2) Identify all writes it performs (Recall store, local file writes, state initialization). (3) Determine if these writes are idempotent under concurrent execution. (4) Specifically: if the hook writes a "session start" record, does a second concurrent write create a duplicate record or overwrite the first? If it initializes state from Recall, does a second concurrent read-modify-write on that state cause data loss? Verdict: FAILURE if concurrent execution causes state corruption or data loss; WARNING if it causes duplicate records only; HEALTHY if fully idempotent.

---

### R3.2: Does `build_dataset()` in `training_extractor.py` correctly produce training examples from the 27 Wave 1+2 findings, and which agents receive training examples and how many?

**Status**: DONE
**Operational Mode**: Research
**Priority**: MEDIUM
**Motivated by**: synthesis_wave2.md open thread — the DSPy training pipeline was partially investigated in D2.3 (drift detector defects) but `training_extractor.py`'s `build_dataset()` function was not checked. With 27 completed findings across Waves 1 and 2, the pipeline now has enough data to produce meaningful training sets. Before Wave 3 findings accumulate further, the extractor's correctness and agent coverage should be verified.
**Hypothesis**: `build_dataset()` extracts (question_text, finding_summary, verdict) triples from findings/*.md. The 27 findings are dominated by diagnose-analyst (7 questions) and design-reviewer (5 questions), with research-analyst (5) and benchmark-engineer (2) less represented. Some agents (frontier-analyst, competitive-analyst) have zero findings and will produce empty training sets. The D2.3 finding suggests UNCALIBRATED verdicts may produce incorrect training labels — if UNCALIBRATED is scored as failure, research-analyst's training data will be polluted with false-negative examples.
**Method**: research-analyst
**Success criterion**: (1) Read `src/dspy_pipeline/training_extractor.py` and trace `build_dataset()` for the 27 existing findings. (2) For each agent name found in findings, count how many training examples it receives. (3) Confirm whether UNCALIBRATED findings are excluded, included as partial-credit, or included as failures in training data. (4) Identify any agents that are over-represented (>10 examples) or under-represented (0 examples). Verdict: HEALTHY if the distribution is reasonable and UNCALIBRATED findings are handled correctly; FAILURE if the extractor would poison any agent's training set with incorrectly labeled examples; INCONCLUSIVE if findings lack agent attribution fields needed for extraction.

---

## Wave 4

**Generated from findings**: R3.2, R3.1, D1.6, R2.2, R1.3, D3.2
**Mode transitions applied**: R3.2 FAILURE (Research, fix spec complete) → F4.1 Fix; D1.6 FAILURE (Diagnose, diagnosis complete in prior wave) → F4.2 Fix; R2.2 FAILURE (Research, blocked on D1.6) → F4.3 Fix; R3.1 FAILURE (Research, fix spec complete) → F4.4 Fix; F4.1 FIX_APPLIED → R4.1 Validate; all P0/P1 fixes combined → R4.2 Research end-to-end measurement

---

### F4.1: Fix `training_extractor.py` — add agent attribution lookup from `questions.md` so `build_dataset()` produces non-empty training examples for all 35 findings

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R3.2 FAILURE (High) — `extract_finding()` never populates the "agent" field; `score_example()` requires it; `build_dataset()` silently excludes all 35 findings, making DSPy optimization non-functional. Fix Specification Option A: add `_build_qid_to_agent_map(questions_md_path)` that parses `**Agent**:` / `**Method**:` fields from `questions.md`, then pass the resulting map into `extract_finding()` or `build_dataset()` to populate `finding["agent"]` before scoring.
**Hypothesis**: After adding a `_build_qid_to_agent_map()` function and wiring it into `extract_finding()` or `build_dataset()`, at least 32 of the 35 findings will receive a non-None agent field, allowing `score_example()` to compute a non-zero weight, and `build_dataset()` to return a non-empty dict keyed by agent name.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/dspy_pipeline/training_extractor.py` and implement Option A: a regex-based `_build_qid_to_agent_map()` that extracts `question_id → agent_name` from `questions.md` using the `**Agent**:` and `**Method**:` fields. (2) Wire the map into `extract_finding()` (add optional `agent_map` param) or into `build_dataset()` before calling `score_example()`. (3) Verify by calling `build_dataset()` with the path to the findings directory — confirm the returned dict is non-empty and contains at least one agent key. (4) Count training examples per agent and compare to the expected distribution from R3.2 (diagnose-analyst ~11, research-analyst ~8, design-reviewer ~5, fix-implementer ~7). Verdict: FIX_APPLIED when `build_dataset()` returns a non-empty dict with correct agent attributions; FIX_FAILED if the dict remains empty or agent keys are systematically wrong.

---

### F4.2: Fix `llm_router.py` — replace `shlex.quote + shell=True` with list-form subprocess to eliminate Windows cmd.exe injection risk and Layer 3 overhead

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: D1.6 FAILURE (Medium) — on Windows, `shlex.quote()` uses POSIX single-quote escaping that cmd.exe does not recognize. A prompt containing `&`, `|`, `>`, `<`, or `"` can break or hijack the shell command. Additionally, `shell=True` adds cmd.exe process overhead that contributes to Layer 3 timeout failures (R2.2). Fix: use list-form `subprocess.run([sys.executable, "-c", llm_script, "--prompt", full_prompt], ...)` without `shell=True`, eliminating both the injection vector and the extra shell spawn.
**Hypothesis**: Replacing the `shlex.quote(full_prompt) ... shell=True` pattern in `llm_router.py` with `subprocess.run(["python", "-c", ..., full_prompt], shell=False)` (or equivalent list-form) will eliminate the Windows escaping vulnerability and reduce subprocess overhead by removing the cmd.exe intermediary. This is a prerequisite for the `_LLM_TIMEOUT` fix (F4.3).
**Method**: fix-implementer
**Success criterion**: (1) Read `src/routing/llm_router.py` in full. (2) Locate the `subprocess.run` / `subprocess.Popen` call that uses `shell=True` and `shlex.quote`. (3) Rewrite the call to use list form (no `shell=True`). (4) Verify the function signature and argument passing are preserved — the LLM subprocess must still receive the full prompt as an argument. (5) Confirm no other `shell=True` usage exists in the file. Verdict: FIX_APPLIED when the `shell=True` usage is eliminated and the subprocess call uses list form; FIX_FAILED if the function's behavior changes in any way other than the escaping mechanism.

---

### F4.3: Set `_LLM_TIMEOUT = 20` on Windows in `llm_router.py` to prevent Layer 3 timeout failures on this machine

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R2.2 FAILURE / R1.3 FAILURE — Layer 3 LLM router times out at 8 seconds on Windows (R2.2: median 6.2s cold, 2.1s warm; 8s limit fails ~30% of cold calls). R1.3 identified the 8s timeout as a root cause of Layer 3 being effectively dead on Windows. The synthesis_wave3.md P0 table prescribes `_LLM_TIMEOUT = 20 if sys.platform == "win32" else 10`. Requires F4.2 first (list-form subprocess eliminates cmd.exe overhead, reducing cold-start time).
**Hypothesis**: After the F4.2 list-form subprocess fix, the cold-start overhead will decrease by approximately 1-2 seconds. Setting `_LLM_TIMEOUT = 20` for Windows will give the LLM router sufficient headroom for cold starts (estimated 4-6s post-F4.2) while remaining below Claude Code's hook timeout threshold, eliminating the ~30% Layer 3 failure rate on this machine.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/routing/llm_router.py` and locate the `_LLM_TIMEOUT` constant (or equivalent timeout parameter). (2) Apply platform-conditional timeout: `_LLM_TIMEOUT = 20 if sys.platform == "win32" else 10`. (3) Verify `import sys` is present or add it. (4) Confirm no other hardcoded 8s timeout values exist in the file. Verdict: FIX_APPLIED when the platform-conditional timeout is in place and no hardcoded 8s values remain; note if F4.2 was not applied first (dependency warning only, not a blocker for this change).

---

### F4.4: Implement `_DEFAULT_THRESHOLD = 0.60` and `_MARGIN_THRESHOLD = 0.05` in `semantic.py` to increase Layer 2 routing coverage from 15% to ~40%

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R3.1 FAILURE (High) — live calibration benchmark confirmed only 15% of queries reach the 0.70 threshold. The recommended change (`_DEFAULT_THRESHOLD = 0.60`, `_MARGIN_THRESHOLD = 0.05`, margin check in `route_semantic()`) would increase Layer 2 acceptance to ~40% of queries while maintaining routing precision (7/8 margin-passing queries route correctly per benchmark data).
**Hypothesis**: Lowering `_DEFAULT_THRESHOLD` from 0.70 to 0.60 and adding a margin gate (`sims[0][1] - sims[1][1] >= 0.05`) will route approximately 40% of queries through Layer 2 (up from 15%) while routing thin-margin cases to Layer 3. The benchmark showed 8/20 queries have margin >= 0.05, and 7 of those route to correct or plausible agents — implementing this change preserves precision while increasing recall.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/routing/semantic.py` in full. (2) Change `_DEFAULT_THRESHOLD` from 0.70 to 0.60 (or add the constant if it does not exist). (3) Add `_MARGIN_THRESHOLD = 0.05` constant. (4) In `route_semantic()`, after sorting similarities, add the margin check: if `len(sims) >= 2` and `sims[0][1] - sims[1][1] < _MARGIN_THRESHOLD`, return `None` (fall through to Layer 3) rather than routing to the top-1 agent. (5) Handle the single-agent case (only one agent in registry — no margin to compute, route directly). Verdict: FIX_APPLIED when both constants are in place and the margin check is correctly wired into the routing logic; FIX_FAILED if the margin check inverts the routing behavior (blocks instead of falls through).

---

### R4.1: After F4.1 is applied, verify `build_dataset()` produces non-empty training examples — count examples per agent and confirm verdict labels are correct

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Motivated by**: F4.1 Fix — R3.2 confirmed zero training examples across 35 findings. After F4.1 adds agent attribution, this research question verifies the fix worked end-to-end: that `build_dataset()` returns non-empty data, the agent distribution matches expectations, and the verdict labels (1.0 for FIX_APPLIED/HEALTHY, 0.5 for WARNING/INCONCLUSIVE, 0.0 for FAILURE) are assigned correctly for the known corpus.
**Hypothesis**: After F4.1, `build_dataset()` will return a dict with at least 5 agent keys. diagnose-analyst will have the most examples (~11), followed by fix-implementer (~7), research-analyst (~8), and design-reviewer (~5). FIX_APPLIED findings from Wave 3 will score 1.0; FAILURE findings will score 0.0; WARNING findings will score 0.5. The total example count will be 32-35 (3 findings may still lack mappable question IDs).
**Method**: research-analyst
**Success criterion**: (1) Read `src/dspy_pipeline/training_extractor.py` (post-F4.1). (2) Call `build_dataset()` with the findings directory path and confirm the return value is non-empty. (3) Count examples per agent key and compare to the expected distribution (R3.2 table: diagnose-analyst ~11, research-analyst ~8, design-reviewer ~5, fix-implementer ~7, benchmark-engineer ~1). (4) Spot-check 3-5 examples: verify verdict label matches the finding's actual verdict (e.g., F3.1 FIX_APPLIED → 1.0, R3.1 FAILURE → 0.0, D3.2 WARNING → 0.5). Verdict: HEALTHY if `build_dataset()` returns non-empty data with correct agent distribution and correct verdict labels; FAILURE if data is still empty or labels are systematically wrong; INCONCLUSIVE if F4.1 was not applied before this question runs.

---

### R4.2: Measure end-to-end routing pipeline coverage after F4.2 + F4.3 + F4.4 fixes — what percentage of requests does each layer handle empirically?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: synthesis_wave3.md Wave 4 recommendation — after D1.6/F4.2 (list-form subprocess), R2.2/F4.3 (timeout 20s), and R3.1/F4.4 (threshold 0.60 + margin 0.05) are applied, the routing pipeline should have all four layers functional. The current empirical distribution (L1: ~15-20%, L2: ~15%, L3: 0% dead, L4: ~65-70%) should shift toward (L1: ~15-20%, L2: ~40%, L3: ~20-25%, L4: ~15-20%). This question measures the actual post-fix distribution.
**Hypothesis**: After F4.2+F4.3+F4.4, the 20-query benchmark will show: L2 acceptance increases from 3/20 to ~8/20 (40%); L3 will handle at least 3-4 of the remaining thin-margin cases that previously fell to L4; L4 will handle only the genuinely ambiguous queries (1-3/20). Net improvement: fewer than 5/20 queries requiring user clarification, down from ~13/20 before fixes.
**Method**: benchmark-engineer
**Success criterion**: (1) Confirm F4.2, F4.3, and F4.4 have been applied (read the relevant source files to verify). If any are missing, mark INCONCLUSIVE with a note on which fix is missing. (2) Re-run the 20-query benchmark from R3.1 against the same Ollama endpoint (`http://192.168.50.62:11434`, `qwen3-embedding:0.6b`). (3) For each query, record which layer routed it (L1/L2/L3/L4) and the routing decision. (4) Compare per-layer coverage against the R3.1 baseline and the projected targets from synthesis_wave3.md. Verdict: IMPROVEMENT if L2 coverage >= 35% and L4 fallback <= 30%; FAILURE if coverage is unchanged or worse; INCONCLUSIVE if Ollama is unreachable or prerequisite fixes are not applied.
