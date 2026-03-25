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

---

## Wave 5

**Generated from findings**: R4.2 IMPROVEMENT, synthesis_wave4.md P1 open items
**Mode transitions applied**: synthesis_wave4.md P1 items (D1.2, V1.4, D2.2) → Fix questions; R5.1 from R4.2 IMPROVEMENT (Layer 3 now active, validate behavior); R5.2 from R4.1 HEALTHY (DSPy pipeline unblocked, run optimization)

---

### F5.1: Fix `masonry-guard.js` — replace direct `writeFileSync` on the strike counter with atomic rename-based write

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: D1.2 FAILURE (High) — `masonry-guard.js` uses `fs.writeFileSync(guardCountFile, JSON.stringify(counts))` (line 109) which is a direct non-atomic write. Under concurrent PostToolUse events (now rare post-F3.1 but still possible with genuine parallel tool calls), the last writer wins and can corrupt the strike counter. The fix is a rename-based atomic write: write to `guardCountFile + '.tmp.' + process.pid`, then `fs.renameSync(tmp, guardCountFile)`.
**Hypothesis**: The atomic rename pattern prevents torn writes since POSIX rename is atomic. Even if two instances run concurrently, the rename ensures only one complete JSON payload reaches `guardCountFile`. The prior double-fire issue (resolved by F3.1) was the primary trigger, but genuine concurrent PostToolUse events on multi-file operations can still occur.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/hooks/masonry-guard.js`. (2) Replace the `fs.writeFileSync(guardCountFile, ...)` call with a write-to-tmp + rename pattern. (3) Verify `import`/`require` does not need additions (fs is already required). (4) Confirm no other non-atomic writes exist on session state files in the hook. Verdict: FIX_APPLIED when the strike counter write is atomic (rename-based) and no other bare `writeFileSync` calls on shared state remain.

---

### F5.2: Fix `llm_router.py` — add registry membership validation for `target_agent` returned by LLM

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: V1.4 FAILURE (Medium) — `route_llm()` returns whatever `target_agent` the LLM provides without checking if it exists in the registry. The LLM can hallucinate an agent name ("prompt-engineer", "code-fixer", "general") not present in `agent_registry.yml`. Mortar would then attempt to spawn a non-existent agent. Fix: validate `target` against `{a.name for a in registry}` before constructing `RoutingDecision`.
**Hypothesis**: Adding a registry membership check (3 lines) will prevent hallucinated agent names from reaching Layer 4 or Mortar dispatch. If the LLM returns an unknown name, `route_llm()` logs a warning and returns `None` (falls to L4), same as a timeout or parse failure. This is a correctness fix — it prevents silent routing to unknown agents under ambiguous queries.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/routing/llm_router.py`. (2) After extracting `target = parsed.get("target_agent")`, add: `registry_names = {a.name for a in registry}; if target not in registry_names: print(..., file=sys.stderr); return None`. (3) Confirm the check runs before constructing `RoutingDecision`. (4) Verify the check uses the `registry` parameter (not a hardcoded list). Verdict: FIX_APPLIED when the membership check is in place and returns None for unrecognized agent names.

---

### F5.3: Fix `masonry-subagent-tracker.js` — replace `safeWrite` with atomic rename to prevent agents.json corruption under concurrent SubagentStart events

**Status**: DONE
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: D2.2 FAILURE (Medium) — `safeWrite()` in `masonry-subagent-tracker.js` uses `fs.writeFileSync()` (direct write). Under concurrent SubagentStart events (spawning multiple agents simultaneously — now possible post-F3.1 without the artificial double-fire), two instances could read the same `agents.json`, each add their entry, and the last write discards the first agent's entry. Fix: atomic rename write using a tmp file with process.pid suffix.
**Hypothesis**: After F3.1 eliminated double-fire, genuine concurrent SubagentStart events are the remaining race condition. Under parallel agent spawns (e.g., two Agent tool calls in one message), two subagent-tracker instances run with ~10ms separation. Atomic rename prevents the TOCTOU race. The routing_log.jsonl `appendFileSync` (line 95) is already append-only and is not a race — no change needed there.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/hooks/masonry-subagent-tracker.js`. (2) Replace the `safeWrite(stateFile, state)` call (which uses `writeFileSync`) with a write-to-tmp + rename pattern. (3) Keep `safeWrite` for masonry-state.json (that write is also non-critical, deferred). (4) Ensure the tmp file uses a unique name (`stateFile + '.tmp.' + process.pid`). Verdict: FIX_APPLIED when the agents.json write is atomic and the routing_log.jsonl append is unchanged.

---

### R5.1: Validate `route_llm()` behavior post-F5.2 — confirm hallucinated agent names are rejected and valid names route correctly

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: F5.2 Fix — after adding registry membership validation to `route_llm()`, verify the check works correctly for both valid and invalid agent names. This is a unit-level validation of the fix, not a live benchmark (cannot invoke `claude` recursively).
**Hypothesis**: After F5.2, `route_llm()` will return `None` for any `target_agent` not in the registry (e.g., "general-assistant", "code-helper", "Claude"). Valid names from the 46-agent registry (e.g., "developer", "trowel", "security") will still produce a `RoutingDecision`. The check is a set membership test — O(1), no performance impact.
**Method**: research-analyst
**Success criterion**: (1) Read `src/routing/llm_router.py` post-F5.2. (2) Trace the registry membership check code path for both a valid name ("developer") and an invalid name ("code-helper"). (3) Confirm valid name → `RoutingDecision` returned; invalid name → `None` returned with stderr log. (4) Check if the empty-registry edge case is handled (registry = [] → all names invalid, returns None immediately). Verdict: HEALTHY if the check correctly handles valid, invalid, and empty-registry cases; FAILURE if valid agent names are incorrectly rejected or invalid names pass through.

---

### R5.2: DSPy dry run — attempt `build_dataset()` + optimizer initialization with 39 training examples to confirm the pipeline produces valid optimized prompts

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: R4.1 HEALTHY — `build_dataset()` now produces 39 training examples across 5 agents. DSPy 3.1.3 is confirmed installed. This research question validates the end-to-end DSPy pipeline: can the optimizer initialize, accept the training data, and produce a non-empty optimized prompt JSON without errors? Does not require a full MIPROv2 training run — just initialization and a dry run with minimal iterations.
**Hypothesis**: With 39 training examples and DSPy 3.1.3, `masonry_optimize_agent` (or direct `optimizer.py` invocation) will initialize a `MIPROv2` optimizer for `diagnose-analyst` (largest example set: 13 examples), compile a `dspy.Module` using 1-2 examples as a dry run, and write a non-empty JSON to `masonry/optimized_prompts/diagnose-analyst.json`. The main failure modes are: (a) the `ResearchAgentSig` signature fields don't match the example keys, (b) Ollama is not configured as the LLM for DSPy, or (c) the MIPROv2 optimizer requires a minimum example count not met.
**Method**: research-analyst
**Success criterion**: (1) Read `src/dspy_pipeline/optimizer.py` and trace the `masonry_optimize_agent` function. (2) Identify which LLM backend is configured for DSPy (should be Ollama or Claude). (3) Check if `ResearchAgentSig` input/output fields match the example dict keys from `build_dataset()`. (4) If the fields match and the LLM is configured, attempt a minimal dry run (max_bootstrapped_demos=1, num_trials=1). (5) Report whether an optimized prompt JSON is written. Verdict: COMPLETE if the pipeline initializes and writes a non-empty prompt; FAILURE if field mismatch or backend misconfiguration prevents initialization; INCONCLUSIVE if the LLM backend is unavailable in this session.
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: synthesis_wave3.md Wave 4 recommendation — after D1.6/F4.2 (list-form subprocess), R2.2/F4.3 (timeout 20s), and R3.1/F4.4 (threshold 0.60 + margin 0.05) are applied, the routing pipeline should have all four layers functional. The current empirical distribution (L1: ~15-20%, L2: ~15%, L3: 0% dead, L4: ~65-70%) should shift toward (L1: ~15-20%, L2: ~40%, L3: ~20-25%, L4: ~15-20%). This question measures the actual post-fix distribution.
**Hypothesis**: After F4.2+F4.3+F4.4, the 20-query benchmark will show: L2 acceptance increases from 3/20 to ~8/20 (40%); L3 will handle at least 3-4 of the remaining thin-margin cases that previously fell to L4; L4 will handle only the genuinely ambiguous queries (1-3/20). Net improvement: fewer than 5/20 queries requiring user clarification, down from ~13/20 before fixes.
**Method**: benchmark-engineer
**Success criterion**: (1) Confirm F4.2, F4.3, and F4.4 have been applied (read the relevant source files to verify). If any are missing, mark INCONCLUSIVE with a note on which fix is missing. (2) Re-run the 20-query benchmark from R3.1 against the same Ollama endpoint (`http://192.168.50.62:11434`, `qwen3-embedding:0.6b`). (3) For each query, record which layer routed it (L1/L2/L3/L4) and the routing decision. (4) Compare per-layer coverage against the R3.1 baseline and the projected targets from synthesis_wave3.md. Verdict: IMPROVEMENT if L2 coverage >= 35% and L4 fallback <= 30%; FAILURE if coverage is unchanged or worse; INCONCLUSIVE if Ollama is unreachable or prerequisite fixes are not applied.

---

## Wave 6

**Wave generation source**: synthesis_wave5.md P1 carry-forwards + new issues discovered during Wave 5 source review.
**Mode transitions applied**: R5.2 FAILURE (DiagnoseAgentSig mismatch) → Fix question F6.2; MCP server gap (masonry_optimize_agent missing) → Diagnose question D6.2; V1.4 carry-forward → Fix question F6.1; new TOCTOU race in onboard_agent.py → D6.1; shell:true path-with-spaces bug → R6.1; post-Wave5 state validation → V6.1.

---

### F6.1: Fix `_load_registry` — add path-level diagnostic logging when registry YAML is not found

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: D1.3 FAILURE (High) + V1.4 carry-forward — `_load_registry()` in `router.py` returns `[]` silently when both the primary path (`{project_dir}/masonry/agent_registry.yml`) and the CWD fallback (`masonry/agent_registry.yml`) fail to exist. The `route()` function does log `[ROUTER] Layer fallback resolved: user (registry empty, ...)` after the empty-registry check, but does not explain WHY the registry is empty (missing file? wrong CWD?). Operators see "registry empty" but cannot tell if this is a config error or a cold start.
**Hypothesis**: Adding two `print(..., file=sys.stderr)` statements inside `_load_registry()` — one for each failed path attempt — requires three lines of code and gives operators the information needed to distinguish between "file not found" (config error) and "empty registry file" (data issue). The logging should use the same `[ROUTER]` prefix for consistency with existing router logs.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/routing/router.py` `_load_registry()` (lines 29-38). (2) Add a `print(f"[ROUTER] Registry not found at {registry_path}", file=sys.stderr)` before the fallback try. (3) Add a `print(f"[ROUTER] Registry not found at {fallback} (fallback)", file=sys.stderr)` before `return []`. (4) Confirm the log fires before the empty return, not after. (5) Confirm `route()` still logs its own "registry empty" message — the two levels of logging (path level + router level) together give complete diagnosis. Verdict: FIX_APPLIED when both path-level logs are in place and `return []` is preceded by a diagnostic.

---

### F6.2: Fix `optimize_all()` — remove `DiagnoseAgentSig` branch to unblock `diagnose-analyst` DSPy training

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R5.2 FAILURE (Medium) — `optimize_all()` in `optimizer.py` selects `DiagnoseAgentSig` for agents with `input_schema: DiagnosePayload`, but `build_dataset()` always shapes examples to `ResearchAgentSig` fields. This causes a field mismatch for `diagnose-analyst` (13 examples — largest training set). Option B (simplest): remove the `DiagnoseAgentSig` branch and always use `ResearchAgentSig`. This unblocks training for all 4 qualifying agents (39 examples total).
**Hypothesis**: `DiagnoseAgentSig` exists as a specialization for symptoms/root-cause analysis, but since `build_dataset()` does not shape examples to those fields, the specialization is currently unusable anyway. Removing the branch (2-line change) restores a working state. If `DiagnoseAgentSig` training is needed in the future, `build_dataset()` must be updated to produce `symptoms`/`affected_files` example shapes for diagnose agents — that is a separate future task.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/dspy_pipeline/optimizer.py` lines 191-198. (2) Remove the `DiagnoseAgentSig if agent.input_schema == "DiagnosePayload" else` conditional — replace with `sig = ResearchAgentSig` for all agents. (3) Remove the `DiagnoseAgentSig` import if it becomes unused. (4) Confirm `optimize_all()` now calls `optimize_agent(agent.name, ResearchAgentSig, agent_dataset, output_dir)` for all agents including `diagnose-analyst`. (5) Confirm `build_dataset()` example keys (`question_text`, `project_context`, `constraints`, `verdict`, `severity`, `evidence`, `mitigation`, `confidence`) still match all fields of `ResearchAgentSig`. Verdict: FIX_APPLIED when the branch is removed and field alignment is verified for all agents.

---

### D6.1: Does `upsert_registry_entry()` in `onboard_agent.py` use a non-atomic write that can corrupt `agent_registry.yml`?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `upsert_registry_entry()` (and `append_to_registry()`) in `onboard_agent.py` write the updated YAML via `registry_path.write_text(yaml.dump(data, ...), encoding="utf-8")` — a direct overwrite with no atomic rename. If the Python process is killed mid-write (e.g., by OS due to memory pressure, or by Claude Code's hook timeout on Windows), the YAML file is left in a partially-written state. The next read of `agent_registry.yml` by any component (`router.py`, `_tool_masonry_registry_list`, etc.) would fail to parse and silently return an empty registry — losing all 46 registered agents. This is the same class of bug as masonry-guard.js strike counter (F5.1) and masonry-subagent-tracker.js agents.json (F5.3), both now fixed with atomic rename.
**Agent**: diagnose-analyst
**Success criterion**: (1) Read `onboard_agent.py` `upsert_registry_entry()` and `append_to_registry()`. (2) Identify whether the write uses `Path.write_text()` directly (non-atomic) or a temp+rename pattern (atomic). (3) Assess kill-mid-write risk: how long does yaml.dump() + write_text() take for a 46-agent YAML file? (4) Confirm whether `load_registry()` has parse-error recovery that would catch a partial write. Verdict: FAILURE if write is non-atomic AND `load_registry()` lacks recovery; WARNING if non-atomic but recovery exists; HEALTHY if atomic write is in place.

---

### D6.2: Is `masonry_optimize_agent` MCP tool missing from `mcp_server/server.py`?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: CLAUDE.md references `masonry_optimize_agent` as an MCP tool ("Trigger from Kiln UI 'OPTIMIZE' button or via `masonry_optimize_agent` MCP tool"). The `mcp_server/server.py` TOOLS dict was read during Wave 6 question generation and does NOT contain a `masonry_optimize_agent` handler — only `masonry_optimization_status` (read-only, returns existing JSON scores). This means the DSPy optimization pipeline cannot be triggered via MCP at all. The only way to run optimization is by calling `optimizer.py` directly from the command line. This is a missing implementation blocking the Phase 16 DSPy training roadmap item.
**Agent**: diagnose-analyst
**Success criterion**: (1) Read `mcp_server/server.py` TOOLS dict (lines 434-662). (2) Confirm whether `masonry_optimize_agent` or any equivalent optimization-trigger tool exists. (3) If absent, confirm that `masonry_optimization_status` is read-only (reads existing JSON) and cannot trigger a new optimization run. (4) Identify what `configure_dspy()` call order would be needed if the tool were implemented. Verdict: FAILURE (missing implementation) if no optimization-trigger tool exists; HEALTHY if it exists under a different name.

---

### R6.1: Does `masonry-lint-check.js` `runBackground()` break on Windows when file paths contain spaces?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Hypothesis**: `runBackground()` in `masonry-lint-check.js` uses `spawn(cmd, args, { shell: process.platform === "win32" })`. On Windows, `shell: true` causes Node.js to join the args array with spaces and invoke `cmd.exe /c cmd arg1 arg2 ...`. If `winPath` or `filePath` contains spaces (e.g., `C:\Users\trg16\My Documents\project\file.py`), the space splits the path into two separate arguments, breaking the ruff/prettier/eslint invocation. The background process would exit with a "file not found" error, but since `stdio: "ignore"` + `proc.unref()` discards all output, this failure is completely silent.
**Method**: research-analyst
**Success criterion**: (1) Read `masonry-lint-check.js` `runBackground()` implementation and the three call sites (ruff format, prettier, eslint). (2) Assess whether Node.js `spawn()` with `shell: true` and an args array quotes individual arguments automatically on Windows (check Node.js docs or source behavior). (3) Identify which invocations pass user-provided file paths as array elements: `runBackground(ruff, ["format", winPath], ...)`, `runBackground("npx", ["prettier", "--write", filePath], ...)`, `runBackground("npx", ["eslint", "--fix", winPath], ...)`. (4) Assess the blast radius: what fraction of real Windows user paths contain spaces? Verdict: FAILURE if args are not quoted and paths-with-spaces break the invocation; WARNING if the failure is silent but non-critical (background formatters); HEALTHY if Node.js automatically quotes args in this configuration.

---

### V6.1: Validate `mcp_server/server.py` error handling — does `_tool_masonry_route` correctly return a safe fallback when the routing import fails?

**Status**: DONE
**Operational Mode**: validate
**Priority**: MEDIUM
**Hypothesis**: `_tool_masonry_route()` imports `masonry.src.routing.router` inside the function body (lazy import, line 297). If the import fails (e.g., `masonry` package not on sys.path, or a dependency like `yaml` missing), the `except Exception as exc` block returns `{"error": str(exc), "target_agent": "user", "layer": 4, "confidence": 0.0}`. This is a safe degradation: the caller gets a valid-shaped response (no crash), routing falls to user, and the error is surfaced in the `error` field. However: (a) `layer` is `4` (integer) but `RoutingDecision.layer` is a `str` in the schema — this type mismatch could cause downstream issues if the caller deserializes expecting a string; (b) `fallback_reason` is absent from the fallback dict but present in `RoutingDecision` — also a mismatch.
**Method**: research-analyst
**Success criterion**: (1) Read `_tool_masonry_route()` in `mcp_server/server.py` (lines 288-302). (2) Check the `RoutingDecision` schema for the `layer` field type — is it `str`, `int`, or `Literal`? (3) Confirm whether the error fallback dict `{"error": ..., "target_agent": "user", "layer": 4, "confidence": 0.0}` matches the schema shape that callers expect. (4) Check if `fallback_reason` being absent causes issues for any known callers. Verdict: HEALTHY if the fallback is schema-compatible; WARNING if `layer` type is wrong but callers tolerate it; FAILURE if the type mismatch causes callers to crash or misinterpret the response.

---

## Wave 7

**Generated**: 2026-03-21
**Mode transitions applied**: V6.1 FAILURE (error fallback schema mismatch) → Fix question F7.1; D6.1 FAILURE (non-atomic registry write) → Fix question F7.2; Wave 6 synthesis identifies DSPy training data quality gap → R7.1; drift detector verdicts-always-empty → D7.1; agent_db_path resolution gap in masonry_drift_check → V7.1; training_extractor multi-project scan validation → R7.2.

---

### F7.1: Fix `_tool_masonry_route()` error fallback to be schema-compatible with `RoutingDecision`

**Status**: DONE
**Operational Mode**: fix
**Priority**: MEDIUM
**Hypothesis**: V6.1 confirmed three schema mismatches in the error fallback dict: `layer: 4` (int) vs `Literal["deterministic","semantic","llm","fallback"]` (str); `reason` missing (required field); `error` is an extra field (rejected by `extra="forbid"`). Fix is to replace the error dict with a properly shaped fallback matching `decision.model_dump()` shape: `layer: "fallback"`, add `reason` field, and optionally keep `error` only as a diagnostic addition.
**Method**: fix-implementer
**Success criterion**: (1) Edit `mcp_server/server.py` line 302 to return `{"error": str(exc), "target_agent": "user", "layer": "fallback", "confidence": 0.0, "reason": f"Router import failed: {str(exc)[:80]}", "fallback_agents": [], "fallback_reason": "multi_failure"}`. (2) Confirm the new dict is shape-compatible with `decision.model_dump()` output (same keys, compatible types). (3) Verify `layer` is now a string `"fallback"` not int `4`. Verdict: FIX_APPLIED if all three mismatches are corrected.

---

### F7.2: Fix `upsert_registry_entry()` and `append_to_registry()` to use atomic writes in `onboard_agent.py`

**Status**: DONE
**Operational Mode**: fix
**Priority**: MEDIUM
**Hypothesis**: D6.1 confirmed that `upsert_registry_entry()` uses `registry_path.write_text(yaml.dump(data, ...), encoding="utf-8")` — a direct truncate-then-write with no atomic rename. A mid-write process kill truncates all 46 registry entries to zero/partial YAML, silently emptying `load_registry()` output to `[]`. The fix is the same atomic pattern applied in masonry-guard.js (F5.1) and masonry-subagent-tracker.js (F5.3): write to `.tmp.{pid}`, then `Path.replace()`.
**Method**: fix-implementer
**Success criterion**: (1) Find `upsert_registry_entry()` in `scripts/onboard_agent.py` (lines 317-318) and replace `registry_path.write_text(...)` with: `tmp = registry_path.with_suffix(f".yml.tmp.{os.getpid()}"); tmp.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8"); tmp.replace(registry_path)`. (2) Apply the same change to `append_to_registry()` if it also writes `registry_path` directly. (3) Add `import os` if not already present. Verdict: FIX_APPLIED if both write sites use atomic rename.

---

### R7.1: Does `build_dataset()` produce semantically degenerate training examples due to `question_text = question_id`?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Hypothesis**: `build_dataset()` in `training_extractor.py` (line 214) sets `"question_text": finding.get("question_id", "")` — the question ID string (e.g., "R5.1") rather than the actual question text from questions.md. It also sets `"project_context": ""` and `"constraints": ""` (always empty). These are the three PRIMARY INPUT FIELDS of `ResearchAgentSig`. MIPROv2 optimizes prompt instructions by learning from input/output distribution — if inputs are degenerate short IDs with empty context, the optimizer cannot extract meaningful prompt patterns. The resulting "optimized" prompt may be no better than the default.
**Method**: research-analyst
**Success criterion**: (1) Confirm `training_extractor.py:214` uses `question_id` as `question_text` (not the actual question text from questions.md). (2) Assess whether `_build_qid_to_agent_map()` extracts question text alongside agent attribution — it does not (only extracts agent name). (3) Assess the semantic quality of training examples where `question_text="R5.1"`, `project_context=""`, `constraints=""`. (4) Determine whether MIPROv2 can learn meaningful prompt optimizations from such degenerate inputs. Verdict: FAILURE if inputs are provably degenerate (ID strings + empty fields across all examples); WARNING if only some examples are degenerate; HEALTHY if the quality is adequate for optimization purposes.

---

### D7.1: Does `run_drift_check()` return zero reports because `agent_db.json` has `"verdicts": []` for all agents?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: `run_drift_check()` in `drift_detector.py` (line 155) skips agents with empty `verdicts` list: `if not verdicts: continue`. The current `agent_db.json` (at `C:/Users/trg16/Dev/Bricklayer2.0/agent_db.json`) has `"verdicts": []` for every agent. This means `run_drift_check()` always returns an empty list — the drift detection system is completely non-functional. `masonry_drift_check` MCP tool would return `{"reports": [], "count": 0}` for any valid input. The `verdicts` field is never populated because nothing writes to it — `masonry_observe.js` hook writes to Recall (the memory system) but not to `agent_db.json`.
**Method**: diagnose-analyst
**Success criterion**: (1) Confirm `agent_db.json` has `"verdicts": []` for all agents. (2) Trace who is responsible for populating `agent_db.json` `verdicts` field — is it `masonry-observe.js`, a scoring script, or another component? (3) Determine if `masonry_drift_check` MCP tool has ever returned a non-empty `reports` list. (4) Identify whether the missing verdicts population is a gap in the implementation or an intentional design (verdicts populated by an external scorer). Verdict: FAILURE if `verdicts` is never populated by any component and drift detection is permanently non-functional; WARNING if it is populated but population is unreliable.

---

### V7.1: Validate `masonry_drift_check` MCP tool: does it correctly resolve `agent_db_path` and handle the case where the path is unknown to callers?

**Status**: DONE
**Operational Mode**: validate
**Priority**: MEDIUM
**Hypothesis**: `_tool_masonry_drift_check()` in `server.py` (line 379) requires `agent_db_path` as an explicit argument — if not provided, it returns `{"error": "agent_db_path is required", "reports": []}`. There is no default path. The actual `agent_db.json` lives at `C:/Users/trg16/Dev/Bricklayer2.0/agent_db.json` — one directory above `_REPO_ROOT` (which is `C:/Users/trg16/Dev/Bricklayer2.0`). Wait — `_REPO_ROOT = Path(__file__).resolve().parent.parent.parent` where `__file__` is `masonry/mcp_server/server.py`. So `_REPO_ROOT` = `Bricklayer2.0/`. Therefore `_REPO_ROOT / "agent_db.json"` would be correct. The issue is the tool has no default for `agent_db_path` — callers must supply it explicitly.
**Method**: research-analyst
**Success criterion**: (1) Verify `_REPO_ROOT` value in `server.py` (line 38: `Path(__file__).resolve().parent.parent.parent`). (2) Confirm `agent_db.json` location relative to `_REPO_ROOT`. (3) Assess whether `agent_db_path` should have a default of `str(_REPO_ROOT / "agent_db.json")` — matching the pattern used by `masonry_run_question`, `masonry_optimization_status`, etc. (4) Confirm whether the missing default causes Kiln to always receive the error response when calling this tool. Verdict: FAILURE if default is missing and no caller supplies the path; WARNING if callers supply it but it's undocumented; HEALTHY if the default is present or the interface is intentional.

---

### R7.2: Does `extract_training_data()` correctly attribute findings to agents when `questions.md` uses `**Method**:` (Wave 2+) rather than `**Agent**:`?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Hypothesis**: `_build_qid_to_agent_map()` in `training_extractor.py` (lines 24-43) handles both `**Agent**:` (Wave 1) and `**Method**:` (Wave 2+) fields: `re.search(r"\*\*(?:Agent|Method)\*\*:\s*(\S+)", block)`. The Masonry self-research campaign uses `**Method**:` in questions.md from Wave 2 onwards. The extraction should work correctly, but needs validation: (1) does the regex correctly split on `\n---\n` to isolate question blocks? (2) Are there Wave 7 questions (which now use `**Method**:`) correctly attributed? The `score_example()` function returns 0.0 for unrecognized agents, silently excluding them.
**Method**: research-analyst
**Success criterion**: (1) Confirm `_build_qid_to_agent_map()` regex `\*\*(?:Agent|Method)\*\*` matches the `**Method**:` field in questions.md waves 2+. (2) Verify the `\n---\n` block split correctly isolates question blocks (the questions.md format uses `---` as separator). (3) Test with a sample question from Wave 2+ to confirm agent attribution works. (4) Confirm that agents in `agent_db.json` have matching names to those in `**Method**:` fields (e.g., "research-analyst" in `**Method**: research-analyst` matches `agent_db["research-analyst"]`). Verdict: HEALTHY if attribution works correctly end-to-end; FAILURE if the regex misses `**Method**:` fields or the name normalization breaks.

---

## Wave 8

**Generated**: 2026-03-21
**Mode transitions applied**: R7.1 FAILURE (degenerate question_text) → Fix question F8.1; V7.1 FAILURE (missing agent_db_path default) → Fix question F8.2; D6.2 unimplemented MCP tool → investigate feasibility D8.1; D7.1 verdicts never populated → investigate fix path D8.2; masonry-observe.js Recall storage effectiveness → R8.1; score_example() exclusion behavior when agent_db is absent → R8.2.

---

### F8.1: Fix `build_dataset()` to extract actual question text instead of using question ID as `question_text`

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Hypothesis**: R7.1 confirmed that `build_dataset()` sets `"question_text": finding.get("question_id", "")` — using the ID ("R5.1") instead of the actual question text. `_build_qid_to_agent_map()` extracts only `{question_id: agent_name}` and discards the question text from `### R7.1: text...` header lines. Fix: extend the function to return `{question_id: {agent: name, question_text: text}}` by capturing group 2 of `r"###\s+(\w+\d+\.\d+):\s*(.+)"`, and update `build_dataset()` to use the extracted question text.
**Method**: fix-implementer
**Success criterion**: (1) Modify `_build_qid_to_agent_map()` in `training_extractor.py` to return `dict[str, dict[str, str]]` with `{qid: {agent: str, question_text: str}}` — or create a new `_build_qid_to_metadata_map()` that returns both fields. (2) Update `build_dataset()` to populate `"question_text"` from the extracted question text instead of `question_id`. (3) Also fix `"confidence"` extraction: extract `**Confidence**: 0.85` from finding files instead of hardcoding `"0.75"`. Verdict: FIX_APPLIED if training examples have actual question text in `question_text` field.

---

### F8.2: Fix `masonry_drift_check` to provide a default `agent_db_path`

**Status**: DONE
**Operational Mode**: fix
**Priority**: LOW
**Hypothesis**: V7.1 confirmed that `_tool_masonry_drift_check()` requires `agent_db_path` as an explicit argument with no default. `agent_db.json` is at `_REPO_ROOT / "agent_db.json"` (deterministic path). Fix: change `args.get("agent_db_path", "")` to `args.get("agent_db_path", str(_REPO_ROOT / "agent_db.json"))`, remove the "required" error check (or make it a non-blocking warning), and remove `agent_db_path` from the tool schema `"required"` list.
**Method**: fix-implementer
**Success criterion**: (1) Edit `mcp_server/server.py` `_tool_masonry_drift_check()` to provide a default value for `agent_db_path`. (2) Remove `agent_db_path` from `"required"` in the tool schema. (3) Confirm that calling `masonry_drift_check` with no arguments uses the default path and returns `{"reports": [], "count": 0}` (empty because D7.1 verdicts issue, but no error). Verdict: FIX_APPLIED if the tool returns reports (or empty reports) instead of an error when `agent_db_path` is not provided.

---

### D8.1: Is `masonry_optimize_agent` implementable? Does `dspy` package exist and does the fix spec in D6.2 have import/dependency gaps?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: D6.2's fix spec imports `from masonry.src.dspy_pipeline.optimizer import configure_dspy, optimize_agent` and `from masonry.src.dspy_pipeline.signatures import ResearchAgentSig`. The optimizer (`optimizer.py`) imports `import dspy` at the top level (line 15) — if `dspy` is not installed in the MCP server's Python environment, this import fails and `masonry_optimize_agent` would always return an error. Additionally, `configure_dspy()` requires `ANTHROPIC_API_KEY` to be set. If the environment lacks either, the tool is useless even after implementation. The D6.2 fix spec defers this check but it must be resolved before Phase 16 DSPy training can proceed.
**Method**: diagnose-analyst
**Success criterion**: (1) Check whether `dspy` is importable in the current Python environment (look for `dspy` in `requirements.txt`, `pyproject.toml`, or installed packages). (2) Verify `configure_dspy()` and `optimize_agent()` exist in `optimizer.py` (confirmed by Wave 7 reading). (3) Check whether `ANTHROPIC_API_KEY` environment variable is required by `configure_dspy()`. (4) Confirm whether `dspy.MIPROv2` exists in the installed version of DSPy (API changed between versions). Verdict: FAILURE if dspy is not installed; WARNING if dspy is installed but API mismatches exist; HEALTHY if all prerequisites are met.

---

### D8.2: Does the `score_example()` exclusion gate silently block all training data when `agent_db.json` is missing or has all agents with score=0.0?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `score_example()` in `training_extractor.py` (lines 153–172) returns `0.0` when: (a) `agent_name` is None or not in `agent_db`, (b) agent score < 0.5. If `agent_db.json` is missing or has `score: 0.0` (not the current 0.85), ALL findings are excluded from training and `build_dataset()` returns `{}`. The call site `if weight == 0.0: continue` silently drops them. The current `agent_db.json` has `score: 0.85` for most agents, so this gate passes — but if `agent_db.json` were absent (common in fresh deployments), `build_dataset()` returns `{}` with no error, blocking DSPy optimization silently.
**Method**: diagnose-analyst
**Success criterion**: (1) Trace `build_dataset()` when `agent_db_path` doesn't exist — `json.JSONDecodeError` except block at line 197-198 returns `{}` immediately (returns empty dataset before any findings are read). (2) Confirm this is a silent failure — no error is logged, caller receives `{}`. (3) Assess the blast radius: a fresh deployment with no `agent_db.json` would cause `masonry_optimize_agent` (once implemented) to return "No training data for agent X" for all agents. Verdict: FAILURE if the silent return-empty has no diagnostic output; WARNING if it's logged.

---

### R8.1: Does `masonry-observe.js` correctly detect finding files written to `masonry/findings/` and store them to Recall?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Hypothesis**: `masonry-observe.js` is a PostToolUse hook that fires on Write/Edit events. It detects finding files by checking if the written path matches a `findings/*.md` pattern. The hook stores findings to Recall via `storeMemory()` and also updates `masonry-state.json` with verdict counts. If the hook is disabled (DISABLE_OMC=1), or if the CWD doesn't match the expected pattern, findings from this campaign are NOT being stored to Recall — meaning the retrieve-on-prompt Recall context that Mortar injects is missing this campaign's findings. This would explain why Wave 7+ questions start without prior campaign context.
**Method**: research-analyst
**Success criterion**: (1) Read `masonry-observe.js` finding detection logic — what path pattern must a written file match? (2) Confirm the hook is registered in settings.json for PostToolUse events. (3) Assess whether `DISABLE_OMC=1` (the BL research kill switch) would prevent finding storage to Recall during this campaign. (4) Determine if findings from this campaign appear in Recall via the `masonry:finding` tag. Verdict: FAILURE if findings are not stored to Recall; WARNING if stored but missing context; HEALTHY if correctly stored and retrievable.

---

### R8.2: Does `build_dataset()` `project_context` gap prevent meaningful DSPy optimization even after R7.1 fix?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Hypothesis**: R7.1's fix spec suggests populating `project_context` from `project-brief.md`. But `project_context` is described as "Project brief summary, prior findings, and key constraints" — a dynamically constructed field that should include both the project brief AND prior findings context. If only `project-brief.md` is injected (static), the optimizer still can't learn "when prior findings show X pattern, adjust reasoning to Y." The fix needs to also inject a summary of prior findings per question. This is a deeper architectural gap: training examples need to be constructed with context that was available at the time the question was answered, not just the static project brief.
**Method**: research-analyst
**Success criterion**: (1) Assess whether injecting only `project-brief.md` into `project_context` is sufficient for MIPROv2 to learn useful prompt optimizations (is static context better than empty?). (2) Determine what "prior findings context" means for a training example dated Wave 3 — should it include Wave 1+2 findings only (context available at that time)? (3) Assess whether a simpler `project_context = first 1000 chars of project-brief.md` is good enough for initial DSPy training, or if the temporal context gap fundamentally limits optimization quality. Verdict: FAILURE if static project-brief alone is insufficient (too generic for meaningful optimization); WARNING if adequate for initial training but limited; HEALTHY if static context is sufficient.

---

## Wave 9

### F9.1: Fix `build_dataset()` to inject `project-brief.md` as `project_context`

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Hypothesis**: R8.2 confirmed that `project-brief.md` is sufficient context and exists on disk, but `build_dataset()` still passes `project_context: ""`. The fix is to read `project-brief.md` from the project root (parent of each `findings/` directory) and inject up to 2000 chars as `project_context` for all examples from that project. This is the last non-trivial gap in training example quality before Phase 16 optimization can produce meaningful results.
**Method**: fix-implementer
**Success criterion**: After fix, `build_dataset()` returns examples with `project_context` containing the first 2000 chars of `project-brief.md` (or full text if shorter). Empty string is no longer used for projects that have a brief. Verify by inspecting example output for a sample masonry finding.

---

### R9.1: How many training examples does `build_dataset()` produce for the `research-analyst` agent in the current masonry findings?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Hypothesis**: The masonry self-research campaign has 60+ findings across 8 waves. `build_dataset()` attributes each finding to an agent via questions.md. `research-analyst` is the most-used agent (handles R-type questions, ~40% of all questions). With all agent scores at 0.85 (gold), every attributed research-analyst finding should pass the exclusion gate. The question is: how many examples actually flow through the full pipeline (attribution → score_example → dataset)?
**Method**: research-analyst
**Success criterion**: Count of training examples for `research-analyst` after full pipeline. Verdict: HEALTHY if >= 5 examples (optimizer minimum); FAILURE if < 5 examples (insufficient for optimization).

---

### D9.1: Design the `sync_verdicts_to_agent_db.py` pipeline for D7.1 remediation

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: D7.1 confirmed that `agent_db.json` `verdicts` is never populated because the attribution pipeline from findings → agent_db was explicitly deferred to Phase 2. `training_extractor.py` already implements `_build_qid_to_agent_map()` which does findings-to-agent attribution. The question is: can we reuse this existing attribution logic to populate `verdicts` in `agent_db.json` without writing a fully new pipeline? The fix spec in D7.1 describes a `sync_verdicts_to_agent_db.py` script.
**Method**: diagnose-analyst
**Success criterion**: Design the minimal implementation of `sync_verdicts_to_agent_db.py` that reuses `extract_training_data()` to get `{question_id, verdict, agent}` tuples, groups by agent, and writes `agent_db[agent]["verdicts"]` list. Include atomic write. Identify whether this script should be invoked from `score_all_agents.py` or run standalone.

---

### R9.2: Does the deterministic routing layer (Layer 1) achieve the claimed 60%+ coverage for real Masonry requests?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Hypothesis**: The project-brief claims Layer 1 handles 60%+ of routing deterministically. R2.1 validated the semantic threshold (0.70 WARNING) but coverage was never directly measured. The deterministic layer handles: slash commands, autopilot state files, `**Mode**:` field matches. For real Masonry usage (campaign running, questions being routed, agents being invoked), the proportion that has a deterministic match may be much lower than 60% — most requests are conversational or ambiguous.
**Method**: research-analyst
**Success criterion**: Trace `src/routing/deterministic.py` coverage paths. Categorize which request types deterministically route vs. fall through. Estimate coverage fraction for a realistic request distribution (campaign questions, git ops, UI work, ad-hoc queries). Verdict: HEALTHY if ≥ 60%; WARNING if 40-60%; FAILURE if < 40%.

---

### V9.1: Does `_tool_masonry_optimize_agent()` correctly handle the case where `ResearchAgentSig.input_fields` is not a dict in dspy 3.1.3?

**Status**: DONE
**Operational Mode**: validate
**Priority**: MEDIUM
**Hypothesis**: `optimize_agent()` in `optimizer.py` calls `list(signature_cls.input_fields.keys())` at line 112. In dspy 3.1.3, DSPy Signatures use a class-level `model_fields` (Pydantic v2) rather than a separate `input_fields` attribute. The `input_fields` attribute may be a property, a cached value, or may not exist. If `signature_cls.input_fields` raises AttributeError, the optimizer silently falls back to the unoptimized module but the error is only printed to stderr, not returned in the MCP response.
**Method**: design-reviewer
**Success criterion**: Verify that `ResearchAgentSig.input_fields` exists and returns the expected dict-like object in dspy 3.1.3. If not, identify what attribute/method provides the input field list and confirm whether the fallback path in optimizer.py is correct.

---

### D9.2: Does `masonry-subagent-tracker.js` correctly write to `agents.json` after the F5.3 atomic write fix?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: LOW
**Hypothesis**: F5.3 applied atomic write to `masonry-subagent-tracker.js`. The fix changed `fs.writeFileSync(agentsFile, ...)` to a `tmp.{pid} + rename()` pattern. However, the deployed hook in `src/hooks/masonry-subagent-tracker.js` has been further modified since F5.3 was applied (Wave 5). The current file state should be verified to confirm the atomic write is still in place and the hook functions correctly.
**Method**: diagnose-analyst
**Success criterion**: Confirm current state of `masonry-subagent-tracker.js` write path. Verify the atomic tmp+rename pattern exists, not the original `writeFileSync` direct write. Verdict: HEALTHY if atomic write confirmed; FAILURE if reverted or never applied.

---

## Wave 10 Questions

### F10.1: Fix `_MODE_FIELD_RE` to match `**Operational Mode**:` in `deterministic.py`

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Hypothesis**: R9.2 confirmed that `_MODE_FIELD_RE = re.compile(r"\*\*Mode\*\*:\s*(\w+)")` never matches BL 2.0 questions because they use `**Operational Mode**:` not `**Mode**:`. Every campaign question that enters the router falls through Rule 5 to Layer 2/3, costing an Ollama semantic lookup or LLM call for something that should be free. The fix is a one-line regex extension.
**Method**: fix-implementer
**Success criterion**: Change `_MODE_FIELD_RE` to `re.compile(r"\*\*(?:Operational\s+)?Mode\*\*:\s*(\w+)", re.IGNORECASE)`. Verify that `route_deterministic()` now returns a match for a question block containing `**Operational Mode**: research`. Verdict: FIX_APPLIED when the regex matches and the routing test passes.

---

### R10.1: Is `sync_verdicts_to_agent_db.py` integrated into the wave-end workflow or must it be run manually?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Hypothesis**: D9.1 created `sync_verdicts_to_agent_db.py` as a standalone script. For drift detection to remain current, it needs to run after each campaign wave. Neither `synthesizer-bl2.md` nor `trowel.md` currently invoke it. If it requires manual invocation, agent verdict history will drift unless the user remembers to run it.
**Method**: research-analyst
**Success criterion**: Check `synthesizer-bl2.md`, `trowel.md`, `karen.md`, and `masonry_run` skill for any reference to `sync_verdicts_to_agent_db`. If absent: propose where the invocation should live and what the integration looks like. Verdict: HEALTHY if integrated; WARNING if manual-only (with integration plan); FAILURE if no integration path exists.

---

### R10.2: Does `masonry_drift_check` produce actionable output now that `agent_db.json["verdicts"]` is populated?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Hypothesis**: D7.1 and D9.1 established that `masonry_drift_check` was broken because `verdicts` was always empty. Now that D9.1 has populated 81 verdicts across 6 agents, the drift check should run for the first time against real data. The question is whether the output is actionable or whether the drift thresholds, output format, or metric calculations are themselves untested.
**Method**: research-analyst
**Success criterion**: Run `masonry_drift_check` via the MCP tool or direct `drift_detector.py` call. Verify it produces a verdict (HEALTHY/WARNING/FAILURE) with per-agent drift scores. Check whether thresholds in `drift_detector.py` are calibrated or placeholder values. Verdict: HEALTHY if actionable output with calibrated thresholds; WARNING if output exists but thresholds need calibration; FAILURE if still broken.

---

### R10.3: Does `masonry_optimize_agent` complete end-to-end for `diagnose-analyst` (28 examples)?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Hypothesis**: D8.1 implemented `_tool_masonry_optimize_agent()` in `server.py`. V9.1 confirmed `input_fields` is correct. F9.1 confirmed training data is meaningful. The end-to-end pipeline has never been run — it may fail at `MIPROv2.compile()` (LLM calls required), at `optimized.save()`, or produce a `.json` that Kiln cannot load. `diagnose-analyst` has the most data (28 examples → actually 21 post-filter) and should be the first agent to try.
**Method**: research-analyst
**Success criterion**: Trace `optimize_agent()` call path for `diagnose-analyst`. Identify whether `configure_dspy(model="claude-sonnet-4-6")` will actually invoke the Anthropic API during `compile()`. Determine if `optimized.save()` produces a valid `.json` loadable by `optimized.load()`. Note: an actual live run may be cost-prohibitive; static code analysis to find failure modes is acceptable. Verdict: HEALTHY if no blocking issues; WARNING if LLM API call or save format issues; FAILURE if MIPROv2 compile will definitely fail.

---

### D10.1: Does `masonry_drift_check` in `server.py` use the updated `agent_db.json` format with populated `verdicts`, or does it read stale in-memory data?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: `_tool_masonry_drift_check()` in `server.py` reads `agent_db.json` from disk at call time. However, `sync_verdicts_to_agent_db.py` writes to the same file. If the MCP server cached `agent_db.json` in memory at startup, the drift check would always see empty `verdicts` even after the sync script runs. Checking whether the server reads fresh from disk vs. uses a module-level cache is critical for the D7.1 fix to be effective.
**Method**: diagnose-analyst
**Success criterion**: Read `_tool_masonry_drift_check()` in `server.py` and `drift_detector.py`. Confirm agent_db is read from disk at each call (not from a module-level cache). Verdict: HEALTHY if fresh read per call; FAILURE if cached at import time.

---

### F10.2: Fix `runBackground()` path-with-spaces on Windows (R6.1 open issue)

**Status**: DONE
**Operational Mode**: fix
**Priority**: LOW
**Hypothesis**: R6.1 identified that `runBackground()` in Masonry hooks may fail on Windows when `cwd` contains spaces (e.g., `C:\Users\trg16\Dev\Bricklayer2.0`). The issue is in the `spawn()` call's `cwd` option or the shell argument quoting. This affects async hook operations on Windows (the primary development platform).
**Method**: fix-implementer
**Success criterion**: Read the `runBackground()` implementation in the relevant hook(s). If path quoting is missing, add `JSON.stringify(cwd)` or wrap in quotes. Verify the fix handles `C:\Users\trg16\Dev\Bricklayer2.0` as a cwd argument. Verdict: FIX_APPLIED if quoting is added; ALREADY_FIXED if path quoting is already present; NOT_REPRODUCIBLE if the issue cannot be located.

---

## Wave 11 Questions

### F11.1: Fix `AgentRegistryEntry` `extra="forbid"` to allow onboarding-added fields

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Hypothesis**: R10.2 found that `AgentRegistryEntry` uses `model_config = ConfigDict(extra="forbid")` in `masonry/src/schemas/payloads.py`. The `masonry-agent-onboard.js` hook adds extra fields (`dspy_status`, `drift_status`, `last_score`, `runs_since_optimization`, `registrySource`) to `agent_registry.yml` entries during auto-onboarding. This causes 14 agents to be silently skipped by `load_registry()`, excluding them from drift checking. Fix: change `extra="forbid"` to `extra="ignore"` in `AgentRegistryEntry`.
**Method**: fix-implementer
**Success criterion**: Change `extra="forbid"` to `extra="ignore"` in `AgentRegistryEntry`. Re-run `load_registry(Path("masonry/agent_registry.yml"))` and confirm that all agents (including `fix-implementer`, `code-reviewer`, etc.) are loaded without validation errors. Verdict: FIX_APPLIED when no `[registry_loader] Skipping invalid agent` stderr output.

---

### F11.2: Scope `sync_verdicts_to_agent_db.py` to masonry-project verdicts only

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Hypothesis**: R10.2 found that verdict counts include FAILURE verdicts from other BL2.0 projects (adbp2, bl2, etc.) because `sync_verdicts_to_agent_db.py` scans the entire BL2.0 root. For `research-analyst`, 11/19 verdicts are FAILURE from non-masonry projects. This produces current_score=0.34 and false "critical drift" alerts. Fix: pass `--questions-md masonry/questions.md` to limit attribution to masonry questions only.
**Method**: fix-implementer
**Success criterion**: Modify the default invocation in `sync_verdicts_to_agent_db.py` to use `masonry/questions.md` when `--base-dir` is the BL2.0 root, or add a `--project` flag. Re-run and verify verdict counts reflect only masonry findings. Verdict: FIX_APPLIED when cross-project FAILURE verdicts are excluded.

---

### R11.1: After F11.1 + F11.2, does `masonry_drift_check` produce accurate per-agent drift reports?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Hypothesis**: R10.2 found two drift check defects: (1) 14 agents excluded by registry validation; (2) cross-project verdict contamination. F11.1 and F11.2 should fix both. This question validates the fixes end-to-end: after both fixes, drift check should show all 44 agents in the registry, with masonry-only verdict distributions, and alert levels that match actual masonry campaign performance.
**Method**: research-analyst
**Success criterion**: Run `masonry_drift_check` after F11.1 + F11.2. Verify: (1) No `Skipping invalid agent` messages; (2) Verdict distributions reflect only masonry findings; (3) Alert levels are consistent with known agent quality (research-analyst at 0.85 baseline should show "ok" or "warning", not "critical"). Verdict: HEALTHY if all three criteria pass; WARNING if partial; FAILURE if still broken.

---

### F11.3: Integrate `sync_verdicts_to_agent_db.py` into `synthesizer-bl2.md` wave-end workflow

**Status**: DONE
**Operational Mode**: fix
**Priority**: MEDIUM
**Hypothesis**: R10.1 found no integration between the verdict sync script and the wave-end workflow. `synthesizer-bl2.md` runs at wave end and already commits docs changes. Adding a non-blocking `sync_verdicts_to_agent_db.py` invocation here ensures verdict history stays current without manual intervention.
**Method**: fix-implementer
**Success criterion**: Add the following to `synthesizer-bl2.md` (in the "Commit" or "Post-synthesis" step): `python -m masonry.scripts.sync_verdicts_to_agent_db --questions-md masonry/questions.md || echo "[SYNTHESIS] verdict sync failed (non-blocking)"`. The addition should be non-blocking (failure continues synthesis). Verdict: FIX_APPLIED when the invocation is present in the agent file.

---

### F11.4: Fix `best_score = 0.0` in `optimize_agent()` result

**Status**: DONE
**Operational Mode**: fix
**Priority**: LOW
**Hypothesis**: R10.3 found that `optimizer.best_score` does not exist on `MIPROv2` in dspy 3.1.3 — the hasattr check returns False and score stays 0.0. The optimize result dict always shows `"score": 0.0`. Kiln displays this as "0% improvement." The fix is to find the correct attribute or compute a post-compile score.
**Method**: fix-implementer
**Success criterion**: Inspect dspy 3.1.3 `MIPROv2` attributes after `compile()` to find the actual best-program score. If no direct attribute exists, evaluate `optimized` on a subset of the trainset using `build_metric()` and use that as the score. Verdict: FIX_APPLIED when result["score"] > 0.0 for a known-healthy agent with good training data.

---

### R11.2: Does `masonry-lint-check.js` correctly handle the case where `ruff` is not in PATH on Windows after the F10.2 spawn fix?

**Status**: DONE
**Operational Mode**: research
**Priority**: LOW
**Hypothesis**: F10.2 changed `runBackground()` from `shell: true` to `shell: false` with explicit `cmd.exe /c` wrapping. When `shell: true` was used, cmd.exe searched PATH for executables. With `shell: false`, `spawn("cmd", ["/c", "ruff", ...])` still invokes cmd.exe which searches PATH. However, if `ruff` is in a virtual environment or not in system PATH, the PATH search may differ. The `findRuff()` helper uses an absolute path for ruff — this should be unaffected. But verify the change doesn't regress the `findRuff()` absolute path case or the `npx` resolution.
**Method**: research-analyst
**Success criterion**: Trace the `findRuff()` return value and how it's passed to `runBackground()`. Confirm that with `["cmd", "/c", absoluteRuffPath, "format", filePath]`, cmd.exe correctly resolves the absolute path even with spaces. Verdict: HEALTHY if no regression; WARNING if a new failure mode is introduced.

---

## Wave 12 — Drift Metric Accuracy, Sync Correctness, and DSPy Validation

### F12.1: Replace verdict-based drift scoring with confidence-based metric in `drift_detector.py`

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Hypothesis**: F11.2 identified a semantic mismatch: `_score_verdict()` scores FAILURE=0.0, but FAILURE verdicts from research agents represent correct behavior (finding a real problem), not agent degradation. Drift should measure *agent certainty* (confidence field), not *finding polarity* (verdict field). All 75+ masonry findings include a `**Confidence**:` float. The fix: add confidence scores to `agent_db.json` via a new `confidences` field in `sync_verdicts_to_agent_db.py`, then update `drift_detector.py` to use mean confidence as `current_score` when `confidences` is present.
**Method**: fix-implementer
**Success criterion**: (1) Update `sync_verdicts_to_agent_db.py` to extract confidence floats alongside verdicts, writing `agent_db[agent]["confidences"] = [float, ...]`. (2) Update `drift_detector.py` to use `mean(confidences)` as `current_score` when `confidences` is non-empty (fall back to verdict scoring when absent for backward compatibility). (3) Re-run drift check and verify research-analyst and diagnose-analyst show alert_level != "critical". Verdict: FIX_APPLIED when confidence-based scoring produces sensible alerts for all 5 agents with history.

---

### F12.2: Add scope-clear behavior to `sync_verdicts_to_agent_db.py` when `--questions-md` is specified

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Hypothesis**: R11.1 found that narrowing sync scope (from all-projects to masonry-only) leaves stale verdicts in `agent_db.json` for agents not in the current scope (compliance-auditor retains 3 cross-project verdicts). The sync script writes only agents found in the current scan; agents outside the scope are untouched. Fix: when `--questions-md` is specified (scoped run), zero out `verdicts` and `confidences` for ALL agents before writing the scoped results. This makes scoped sync authoritative for the entire agent_db.
**Method**: fix-implementer
**Success criterion**: Modify `sync_verdicts()`  to clear `verdicts: []` and `confidences: []` for all agents in agent_db before writing scoped results (only when `questions_md_path` is not None). Re-run with `--questions-md masonry/questions.md` and verify compliance-auditor has `verdicts: []`. Verdict: FIX_APPLIED when stale-scope data is cleared on scoped sync.

---

### R12.1: After F12.1 + F12.2, do all masonry agents show accurate drift alert levels?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Hypothesis**: After confidence-based drift metric (F12.1) and scope-clear sync (F12.2), the drift check should reflect actual agent quality. research-analyst and diagnose-analyst have consistently high-confidence findings (0.85–0.95) — they should show "ok" or "warning", not "critical". fix-implementer should continue to show "ok". compliance-auditor should disappear (no verdicts). benchmark-engineer (2 findings, both FAILURE but high confidence) should show "ok" if confidence > 0.75.
**Method**: research-analyst
**Success criterion**: Run `masonry_drift_check` after F12.1 + F12.2. For each of the 5 agents with history: report alert_level and current_score. Verdict: HEALTHY if research-analyst and diagnose-analyst both show alert != "critical" AND compliance-auditor shows 0 verdicts; WARNING if partial improvement; FAILURE if confidence-based metric doesn't help.

---

### R12.2: Is the `masonry_drift_check` MCP tool (`mcp__masonry__masonry_drift_check` equivalent) functional end-to-end?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Hypothesis**: The `masonry_drift_check` MCP tool (exposed via `masonry/src/core/registry.js` or similar) has never been tested since F11.1 fixed the registry loader and F11.2 scoped the verdicts. The MCP layer wraps the Python drift check via a Node.js subprocess or direct Python call. There may be import path issues, missing environment setup, or response schema mismatches that prevent the tool from returning structured results to Kiln.
**Method**: diagnose-analyst
**Success criterion**: (1) Locate the MCP tool implementation for `masonry_drift_check`. (2) Determine how it invokes the Python drift check (subprocess? direct import?). (3) Trace the full call path and identify any failure modes (missing deps, wrong cwd, schema mismatch). (4) If testable without ANTHROPIC_API_KEY, run it and capture output. Verdict: HEALTHY if the tool returns structured results; WARNING if it runs but with incorrect data; FAILURE if it errors out or returns empty.

---

### R12.3: Does `ResearchAgentSig` in `dspy_pipeline/signatures.py` match the fields populated by `build_dataset()` in `training_extractor.py`?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Hypothesis**: R5.2 (Wave 5) identified that `DiagnoseAgentSig` fields (`symptoms`, `affected_files`) are not populated by `build_dataset()`, causing a silent field mismatch. It was noted that all agents currently use `ResearchAgentSig` via `optimize_all()`. This question validates that `ResearchAgentSig` fields (input: `question_text`, `project_context`, `constraints`; output: `verdict`, `severity`, `evidence`, `mitigation`, `confidence`) are exactly populated by `build_dataset()` and that no field is systematically missing or misnamed.
**Method**: research-analyst
**Success criterion**: (1) Read `ResearchAgentSig` input and output fields. (2) Read `build_dataset()` / `extract_finding()` to see what dict keys are produced. (3) Check that input fields match the dict keys used as `with_inputs()`. (4) Check that output fields match verdict/severity/evidence/mitigation/confidence keys. Verdict: HEALTHY if all fields match; WARNING if minor naming drift; FAILURE if systematic mismatch that would cause `dspy.Example` construction to fail.

---

### D12.1: Why does `masonry-subagent-tracker.js` have unstaged modifications in the current git status?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: LOW
**Hypothesis**: The session-start git status shows `M src/hooks/masonry-subagent-tracker.js` (modified, unstaged). This file was last touched by F5.3 (atomic write fix) and should be clean. An unstaged modification may indicate: (1) a lint hook auto-formatted the file after F5.3 but the change wasn't committed; (2) a hook ran and modified the file during the campaign; (3) the DISABLE_OMC=1 kill switch change (7b4472f) modified it as part of that commit but left something unstaged.
**Method**: diagnose-analyst
**Success criterion**: Run `git diff src/hooks/masonry-subagent-tracker.js` to see what changed. Determine the cause and whether the change should be committed or reverted. Verdict: DIAGNOSIS_COMPLETE with a clear root cause and recommended action (commit or revert).

---

## Wave 13

### R13.1: Does `score_all_agents.py` produce correct `scored_all.jsonl` when run against the current masonry findings?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Hypothesis**: The phase-16 commit (8c73818) introduced a full-fleet scoring pipeline (`score_all_agents.py` → `scored_all.jsonl`). The file already exists with 64 entries, all from the ADBP project (quantitative-analyst). Masonry's own findings (research-analyst, diagnose-analyst, fix-implementer, etc.) should also produce scoring entries, but may not be included because `backfill_agent_fields.py` has not been run to populate `**Agent**:` fields. Running `score_all_agents.py` against the masonry project should now include masonry-attributed findings via confidence-based rubric scoring.
**Method**: research-analyst
**Success criterion**: Run `python -m masonry.scripts.score_all_agents --base-dir . --output masonry/training_data/scored_all.jsonl`. Check: (1) Does it run without errors? (2) Are masonry agent findings included (research-analyst, diagnose-analyst, fix-implementer, design-reviewer, benchmark-engineer)? (3) What scores do they receive? (4) How many entries pass `min_training_score=60`? Verdict: HEALTHY if masonry agents appear with scores ≥60; WARNING if ADBP-only; FAILURE if errors.

---

### R13.2: Does `score_routing.py` produce useful training signal from the current `routing_log.jsonl`?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Hypothesis**: `masonry-subagent-tracker.js` (phase-16) writes to `routing_log.jsonl` on every SubagentStart event. The file currently has 4 "start" entries (karen, planner, question-designer-bl2, and one other) but zero "finding" events. `score_routing.py` scores mortar/trowel by checking: `correct_agent_dispatched` (70pts) — whether the agent name is in AGENT_CATEGORIES — and `downstream_success` (30pts) — whether a finding was written (verdict != INCONCLUSIVE). With no "finding" events in the log, all routing sessions would score at most 70/100, below the `min_training_score=65` threshold... or exactly 70 which passes. The log format must be verified end-to-end.
**Method**: research-analyst
**Success criterion**: Run `python -m masonry.scripts.score_routing --base-dir .`. Check: (1) Does it run without errors? (2) What sessions does it find? (3) What scores are assigned? (4) Are any sessions above min_training_score=65? (5) Does the log format from masonry-subagent-tracker.js match what score_routing.py expects? Verdict: HEALTHY if at least one session scores ≥65; WARNING if format issues or all below threshold; FAILURE if errors.

---

### D13.1: Why do existing masonry findings score 60/100 (minimum threshold) in `scored_all.jsonl` — are confidence scores missing or is the rubric scoring correctly?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: The 64 existing `scored_all.jsonl` entries show score=60 for all ADBP quantitative-analyst findings. The findings rubric has `confidence_calibration: 40`, `evidence_quality: 40`, `verdict_clarity: 20`. A score of 60 suggests either: (1) confidence is null → confidence_calibration dimension scores 0, evidence_quality=40, verdict_clarity=20 = 60; or (2) the scoring has a bug where partial credit is given. ADBP findings have `"confidence": null` per the jsonl entries. Masonry findings have explicit confidence values (0.88–1.00) — they should score much higher (e.g., confidence_calibration=40, evidence_quality=40, verdict_clarity=20 = 100).
**Method**: diagnose-analyst
**Success criterion**: (1) Read `scripts/score_findings.py` to understand how `confidence_calibration` is scored. (2) Confirm that null confidence → 0 pts on that dimension. (3) Confirm that masonry findings with explicit confidence 0.88–1.00 would score 90+ points. (4) Verify the dimension scoring formula. Verdict: DIAGNOSIS_COMPLETE with the exact scoring formula and expected score for masonry findings.

---

### R13.3: Does `backfill_agent_fields.py` correctly identify and write `**Agent**:` fields for existing masonry findings without one?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Hypothesis**: `backfill_agent_fields.py` uses a question_id prefix mapping (D→diagnose-analyst, F→fix-implementer, R→research-analyst, V→benchmark-engineer, etc.) to backfill `**Agent**:` fields in finding files that lack them. Masonry findings use the same ID scheme. If existing masonry findings already have `**Agent**:` fields (populated during the research loop), `backfill_agent_fields.py` would be a no-op. If they lack the field, the backfill would populate it, enabling `build_dataset()` to correctly attribute training examples.
**Method**: research-analyst
**Success criterion**: (1) Check whether existing masonry findings have `**Agent**:` fields by grepping findings/. (2) Run `python -m masonry.scripts.backfill_agent_fields --base-dir .` (dry run if supported). (3) Confirm the prefix-to-agent mapping matches masonry question naming. Verdict: HEALTHY if findings already have Agent fields or backfill correctly adds them; WARNING if mapping is wrong; FAILURE if backfill errors.

---

### R13.4: After running `score_all_agents.py` against masonry findings, how many training examples per masonry agent pass `min_training_score` for MIPROv2 optimization?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Hypothesis**: MIPROv2 requires at minimum ~5-10 examples per agent to produce meaningful prompt optimization. Masonry's research-analyst has 28+ findings, fix-implementer 43+, diagnose-analyst 34+. If these all pass min_training_score (expected 90+ due to explicit confidence), the training dataset should be sufficient. However, the current `build_dataset()` path reads from `extract_training_data()` which uses `findings/` — it may not use `scored_all.jsonl` at all. The two pipelines (score_all_agents.py → scored_all.jsonl vs. build_dataset() → DSPy Examples) may be parallel tracks that don't intersect.
**Method**: research-analyst
**Success criterion**: (1) Determine whether `optimizer.py` uses `build_dataset()` (training_extractor path) or `scored_all.jsonl`. (2) Count training examples per masonry agent in whichever path is used. (3) Assess whether MIPROv2 would receive ≥5 examples per agent. Verdict: HEALTHY if ≥5 examples per agent on the active path; WARNING if 2-4; FAILURE if 0-1 or pipeline paths don't connect.

---

### R13.5: Does `masonry_nl_generate` produce BL 2.0-compatible questions with correct `Mode` and `Status` fields from a natural language description?

**Status**: DONE
**Operational Mode**: research
**Priority**: LOW
**Hypothesis**: The `masonry_nl_generate` MCP tool calls `bl.nl_entry.generate_from_description()`. This function generates questions from a natural language description. BL 2.0 requires questions with `**Operational Mode**:` (diagnose/research/validate), `**Status**: PENDING`, `**Priority**:`, `**Hypothesis**:`, `**Method**:`, and `**Success criterion**:` fields. If the generator was written for BL 1.x format, it may omit the `**Operational Mode**:` and `**Method**:` fields, making generated questions incompatible with Trowel routing.
**Method**: research-analyst
**Success criterion**: (1) Read `bl/nl_entry.py` to see the question template. (2) Check whether generated questions include `**Operational Mode**:` and `**Method**:` fields. (3) If testable, call `generate_from_description("test question about hook latency")` and inspect the output. Verdict: HEALTHY if BL 2.0-compatible output; WARNING if missing optional fields; FAILURE if missing Mode or Method which would break Trowel routing.


---

## Wave 14

### F14.1: Fix `_question_to_md()` in `bl/nl_entry.py` to use `**Operational Mode**:` and `**Method**:` instead of `**Mode**:` and `**Test**:`

**Status**: DONE
**Finding**: [F14.1](findings/F14.1.md) — FIX_APPLIED
**Operational Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: R13.5 identified that `masonry_nl_generate` outputs `**Mode**:` (not `**Operational Mode**:`) and `**Test**:` (not `**Method**:`). While Trowel's `_MODE_FIELD_RE` regex accepts `**Mode**:`, agents receive degraded context because they expect `**Method**:` to identify the specialist agent. The fix is a one-line template change in `_question_to_md()` in `bl/nl_entry.py`.
**Method**: fix-implementer
**Success criterion**: (1) Update `_question_to_md()` to use `**Operational Mode**:` instead of `**Mode**:` and `**Method**: {agent-from-mode}` instead of `**Test**:`. (2) Update `**Verdict threshold**:` to `**Success criterion**:`. (3) Verify `generate_from_description()` output matches BL 2.0 format. Verdict: FIX_APPLIED if all three fields corrected; PARTIAL if only Mode fixed; FAILURE if changes break anything.

---

### F14.2: Add `downstream_success` event emission to `masonry-observe.js` for routing training signal

**Status**: DONE
**Finding**: [F14.2](findings/F14.2.md) — FIX_APPLIED
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: R13.2 found that `score_routing.py`'s `downstream_success` dimension (30pts) is permanently 0 because `masonry-subagent-tracker.js` never writes "finding" events to `routing_log.jsonl`. A "finding" event `{"event":"finding","agent":"...","session_id":"...","verdict":"..."}` should be emitted after a research agent writes a finding file. `masonry-observe.js` (PostToolUse Write/Edit hook) already detects when findings are written — it's the right place to emit this event.
**Method**: fix-implementer
**Success criterion**: (1) Locate where `masonry-observe.js` detects finding writes. (2) Add routing_log.jsonl append with `{"event":"finding","agent":"...","session_id":"...","verdict":"...","timestamp":"..."}` after finding detection. (3) Verify the format matches `score_routing.py`'s expected schema. Verdict: FIX_APPLIED if finding events are emitted and score_routing.py produces downstream_success>0.

---

### R14.1: Does `run_vigil.py` correctly classify masonry agents using the new `scored_all.jsonl` + `src/scoring/rubrics.py` integration?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Hypothesis**: The phase-16 commit modified `run_vigil.py` to integrate `masonry.src.scoring.rubrics.max_score()` for normalizing scores when classifying agents into Roses/Buds/Thorns. Previously vigil only classified findings-category agents. Now it should classify code, ops, and routing agents too. Since scored_all.jsonl excludes masonry's own research agents (R13.1), vigil's masonry-scope view should only show findings agents from ADBP, plus code/ops/routing agents from the recent sessions.
**Method**: research-analyst
**Success criterion**: Run `python -m masonry.scripts.run_vigil --project .` and check: (1) Does it run without errors? (2) Does it use rubrics.py for normalization? (3) What agents appear in each category (Roses/Buds/Thorns)? (4) Are any masonry-specific research agents (fix-implementer, diagnose-analyst) incorrectly absent? Verdict: HEALTHY if vigil produces a meaningful Roses/Buds/Thorns report; WARNING if masonry agents absent; FAILURE if errors.

---

### R14.2: Are the `masonry.src.scoring.rubrics` import guards in `run_vigil.py` functioning correctly — does graceful fallback work when rubrics is unavailable?

**Status**: DONE
**Operational Mode**: research
**Priority**: LOW
**Hypothesis**: `run_vigil.py` has a try/except import guard for `masonry.src.scoring.rubrics`: `try: from masonry.src.scoring.rubrics import max_score as _rubric_max_score; _HAS_RUBRICS = True except ImportError: _HAS_RUBRICS = False; def _rubric_max_score(agent_name): return 100`. When `_HAS_RUBRICS=True`, scores are normalized against per-category maxima. When False, all agents use 100 as denominator. The guard has never been explicitly tested with rubrics unavailable.
**Method**: research-analyst
**Success criterion**: (1) Confirm `_HAS_RUBRICS=True` in the current environment. (2) Trace how `_rubric_max_score()` is used in classification logic. (3) Verify that `max_score("research-analyst")` returns 100 (findings category). (4) Verify `max_score("developer")` returns 100 (code: 50+20+30=100). Verdict: HEALTHY if rubrics loads correctly and max_scores are accurate; WARNING if normalization has bugs.

---

### D14.1: Why does `score_all_agents.py` count 238 total records but only write 64 to `scored_all.jsonl` — what filter reduces 238 to 64?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: LOW
**Hypothesis**: `score_all_agents.py` reports 238 total raw records across all scorers, but only 64 pass to `scored_all.jsonl`. A filter is applied — likely `min_training_score` per category (findings=60, code=70, ops=60, routing=65). The 238→64 reduction (73% filtered out) seems high. If most ops agent findings are being filtered, the training signal for git-nerd and karen is thin despite 170 raw records.
**Method**: diagnose-analyst
**Success criterion**: (1) Read `score_all_agents.py`'s merge/filter logic. (2) Identify what threshold each category applies. (3) Count how many records fail the threshold per category. (4) Verify whether the 170 ops records include many duplicate or low-quality entries. Verdict: DIAGNOSIS_COMPLETE with exact filter counts per category.

---

## Wave 15

### F15.1: Fix the ops dedup key collision — include `commit_hash` in `_dedup_records()` else-branch so git-nerd/karen training records survive

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: HIGH
**Source**: synthesis_wave14
**Hypothesis**: D14.1 identified that 173 ops records collapse to 2 in `_dedup_records()` because the else-branch key `f"src:{source}:{branch}:{agent}:{score}"` has no discriminator — all ops records share source="git_log", branch="", and score=100. Adding `commit_hash` to the key restores full training signal for git-nerd (3 → 3) and karen (170 → 170) in scored_all.jsonl.
**Method**: fix-implementer
**Success criterion**: Modify `_dedup_records()` in `score_all_agents.py` to use `commit_hash` in the else-branch. Re-run `score_all_agents.py` and verify `scored_all.jsonl` grows from 64 to ~235 records with karen=170 and git-nerd=3. Verdict: FIX_APPLIED if counts are correct.

---

### R15.1: Does `masonry-subagent-tracker.js` correctly emit "start" events with session_id that matches the session_id used by `masonry-observe.js` when writing findings?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Source**: synthesis_wave14
**Hypothesis**: F14.2 fixed masonry-observe.js to emit "finding" events with the session_id from the PostToolUse hook input. masonry-subagent-tracker.js emits "start" events with session_id from SubagentStart hook input. For score_routing.py to pair them, both hooks must use the same Claude Code session_id. If the session_id values differ between SubagentStart and PostToolUse events, downstream_success would never trigger even after F14.2.
**Method**: research-analyst
**Success criterion**: (1) Read masonry-subagent-tracker.js and confirm how session_id is extracted. (2) Read masonry-observe.js and confirm session_id extraction. (3) Verify both use `input.session_id` or equivalent from their respective hook payloads. (4) Check if SubagentStart and PostToolUse hooks receive the same session_id for the same Claude Code session. Verdict: HEALTHY if session_ids match; WARNING if there's a structural mismatch.

---

### D15.1: Why does `score_findings.py` report 61 training_ready records from only 1 agent — which agent has 61 findings and are any masonry findings accidentally included?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Source**: synthesis_wave14
**Hypothesis**: `score_all_agents.py` summary shows score_findings produced 61 records from 1 agent (the `agents_with_10_plus` count is 1, meaning only 1 agent has 10+ training examples). This single agent with 61 records is likely research-analyst or quantitative-analyst from ADBP. But the scored_all.jsonl shows quantitative-analyst=35, research-analyst=5, competitive-analyst=6, regulatory-researcher=5, synthesizer-bl2=6 = 57 findings-category records total. The 61 vs 57 discrepancy and the "1 agent with 10+" observation are inconsistent with 5 distinct agents having findings data.
**Method**: diagnose-analyst
**Success criterion**: (1) Run score_findings.py directly and capture its summary. (2) Identify which agent has 61 records (likely quantitative-analyst with ADBP simulation data). (3) Confirm no masonry findings are accidentally included. (4) Explain the discrepancy between score_findings output (61, 1 agent) and scored_all.jsonl breakdown (57 across 5 agents). Verdict: DIAGNOSIS_COMPLETE with exact record counts per agent before and after dedup.

---

### R15.2: What is the current state of `masonry/src/hooks/masonry-subagent-tracker.js` — does it correctly track the session_id and agent name for routing training?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Source**: synthesis_wave14
**Hypothesis**: masonry-subagent-tracker.js was the focus of the downstream_success gap (R13.2). After F14.2, it now has a pairing partner (masonry-observe.js emits "finding" events). But the tracker's own "start" event format must match score_routing.py's expected schema. The hook was modified in commit 7b4472f (DISABLE_OMC=1 kill switch). It's possible the kill switch or another recent change introduced a regression in the start event format or session_id extraction.
**Method**: research-analyst
**Success criterion**: (1) Read masonry-subagent-tracker.js in full. (2) Verify the "start" event JSON format matches score_routing.py's expected fields. (3) Verify DISABLE_OMC=1 kill switch is correct — it should disable the hook, not corrupt output. (4) Confirm agent name extraction from SubagentStart hook input. Verdict: HEALTHY if format correct; WARNING if schema mismatch detected.

---

## Wave 16

### F16.1: Fix CWD guard in `masonry-observe.js` and `masonry-subagent-tracker.js` to resolve routing_log.jsonl path correctly when CWD is the masonry/ directory itself

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: HIGH
**Source**: synthesis_wave15
**Hypothesis**: R15.1 identified that both hooks use `path.join(cwd, 'masonry')` to locate the masonry/ directory. When CWD = masonry/ (as in self-research sessions), this resolves to `masonry/masonry/` which doesn't exist → routing_log.jsonl writes are silently dropped. Fix: check if `path.basename(cwd) === 'masonry'` first and use cwd directly, else fall back to `path.join(cwd, 'masonry')`.
**Method**: fix-implementer
**Success criterion**: (1) Update CWD guard in both masonry-observe.js and masonry-subagent-tracker.js. (2) Syntax-check both files. (3) Write a finding and verify routing_log.jsonl receives a "finding" event. Verdict: FIX_APPLIED if finding events appear in routing_log.jsonl during current session.

---

### R16.1: After F16.1 is applied, does `score_routing.py` successfully pair a "start" + "finding" event pair and produce a session scoring >70/100?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Source**: synthesis_wave15
**Hypothesis**: Once the CWD guard is fixed, masonry self-research sessions can generate routing training signal. A "start" event (from SubagentStart when Mortar/Trowel spawns a specialist) + a matching "finding" event (from PostToolUse when the specialist writes a finding) with the same session_id → downstream_success=30pts → total=100pts for correctly dispatched known agents. This would exceed min_training_score=65 and produce the first routing training records from masonry self-research.
**Method**: research-analyst
**Success criterion**: Run `python masonry/scripts/score_routing.py` after F16.1 and verify at least 1 session scores >70/100. Verdict: HEALTHY if any session scores 100; WARNING if sessions score 70 (correct dispatch but no finding pair); FAILURE if no records produced.

---

### D16.1: Why does `score_findings.py` discovery include 675 findings but only 61 pass TRAINING_THRESHOLD=60 — which scoring dimension(s) fail for the rejected 614 findings?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: LOW
**Source**: synthesis_wave15
**Hypothesis**: 614 of 675 findings are below the 60-point training threshold. These are predominantly from recall and recall-arch-frontier projects (494 findings combined). These BL1.x-format findings likely fail on `confidence_calibration` (no `**Confidence**:` field → 0 pts) and/or `evidence_quality` (short or generic evidence → low pts). Quantifying which dimension fails most often would help prioritize whether backfilling missing fields or adjusting the threshold would most improve training data coverage.
**Method**: diagnose-analyst
**Success criterion**: (1) Run score_finding() on a sample of the 614 rejected findings. (2) Identify which dimensions score 0. (3) Determine if most rejections are from confidence_calibration=0 (missing field) or evidence_quality=0. (4) Count how many would pass if the threshold were 50 instead of 60. Verdict: DIAGNOSIS_COMPLETE with dimension-level failure breakdown.

---

### R16.2: Is the `score_findings.py` summary table "Agents: 1" column inconsistency worth fixing, and what would the correct unified metric be?

**Status**: DONE
**Operational Mode**: research
**Priority**: LOW
**Source**: synthesis_wave15
**Hypothesis**: D15.1 found that the "Agents" column in score_all_agents.py summary shows `agents_with_10_plus` for score_findings but `total agents covered` for other scorers. This inconsistency makes the TOTAL row meaningless for the "Agents" column (it sums across different semantics). The fix would standardize the column to always show total agents covered. But it may be intentional — agents_with_10_plus is the training-relevant metric for findings.
**Method**: research-analyst
**Success criterion**: (1) Read score_all_agents.py summary table logic. (2) Determine if the inconsistency is intentional or accidental. (3) Propose whether to fix or document. Verdict: HEALTHY if intentional/documented; WARNING if accidental inconsistency that misleads users.


---

## Wave 17

### F17.1: Fix `extractMarkdownField` regex in `masonry-observe.js` to include hyphens so hyphenated agent names extract correctly

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: HIGH
**Source**: synthesis_wave16
**Hypothesis**: R16.1 found that `extractMarkdownField()` regex `[\w]+` stops at hyphens. Agent names like `research-analyst`, `fix-implementer`, `synthesizer-bl2` are truncated to `research`, `fix`, `synthesizer` — none in `AGENT_CATEGORIES`. Fix: `[\w]+` → `[\w-]+`.
**Method**: fix-implementer
**Success criterion**: Verify `fix-implementer`, `research-analyst`, `synthesizer-bl2` extract fully. Verdict: FIX_APPLIED.

---

### R17.1: After F17.1, does the routing pipeline have a clear path to generating training records?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Source**: synthesis_wave16
**Hypothesis**: With agent name truncation fixed, remaining blocker is session ID mismatch. The NEVER STOP self-research loop writes findings directly without spawning subagents in the same session. A Mortar/Trowel-dispatched campaign from masonry/ would generate matching start+finding events.
**Method**: research-analyst
**Success criterion**: Re-run score_routing.py and verify record count. Describe minimum session structure needed. Verdict: HEALTHY if records produced; WARNING if 0 but path clear.

---

### F17.2: Fix `score_findings.run()` to return `agents_covered` key and standardize score_all_agents.py summary "Agents" column

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: LOW
**Source**: synthesis_wave16
**Hypothesis**: R16.2 found score_findings.run() returns only agents_with_10_plus, not agents_covered. This causes "Agents: 1" when 5 agents contribute. Fix: add agents_covered to return dict.
**Method**: fix-implementer
**Success criterion**: Summary shows "Agents: 5" for score_findings. Verdict: FIX_APPLIED.

---

### R17.2: Does `run_vigil.py` correctly reflect fleet health after Waves 14-16 fixes, or do false Thorn signals persist?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Source**: synthesis_wave14
**Hypothesis**: Wave 14 R14.1 found diagnose-analyst is a false Thorn (BL1.x findings with no Confidence in BL root findings/ dir). With scored_all.jsonl at 236 records, vigil may show a better picture. But the root cause (BL root findings/ having BL1.x format) is unfixed.
**Method**: research-analyst
**Success criterion**: Run run_vigil.py from masonry/ dir. Check for false Thorn signals. Verdict: HEALTHY if accurate; WARNING if false signals persist.

---

## Wave 18

### R18.1: Can the NEVER STOP loop generate matching session ID pairs by using the Agent tool to dispatch specialist subagents for investigations?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Source**: synthesis_wave17
**Hypothesis**: The sole remaining blocker for routing training records reaching 100pts is the session ID mismatch. The R17.1 finding identifies Option B: use Agent tool calls in the NEVER STOP loop instead of direct investigation. If the main session spawns a specialist via Agent tool, SubagentStart fires with parent_session=current, and if that agent writes a finding, PostToolUse fires with session_id=current — producing a matched pair at 100pts.
**Method**: research-analyst
**Success criterion**: Verify whether using Agent tool dispatch for a Wave 18 question produces a "start" event in routing_log.jsonl with the current session ID. Check whether the resulting finding event also carries the current session ID. Verdict: HEALTHY if matched pair produced; WARNING if still no match.

---

### D18.1: Why does `parse_findings_dir` in run_vigil.py classify 86% of masonry findings as "unknown" agent — is it a regex mismatch or a missing field in the finding template?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Source**: synthesis_wave17
**Hypothesis**: R17.2 shows 109/127 masonry findings are "unknown". Two possible root causes: (1) the BL2.0 finding template never included `**Agent**:` field — only Waves 16-17 findings have it; or (2) `_AGENT_PATTERN = re.compile(r"\*\*agent\*\*\s*:\s*(.+)", re.IGNORECASE)` fails to match even when the field exists due to encoding or whitespace variation. Need to distinguish which is the dominant cause and whether bulk backfill of `**Agent**:` field in pre-Wave 16 findings is warranted.
**Method**: diagnose-analyst
**Success criterion**: Read 5 pre-Wave 16 findings and check for `**Agent**:` field presence. Run the regex against those files to confirm parse behavior. If the field is absent: document which wave introduced it and propose a bulk backfill script. Verdict: DIAGNOSIS_COMPLETE.

---

### R18.2: Is quantitative-analyst's training data (36 findings, only agent ≥10) sufficient for a DSPy MIPROv2 optimization trial?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Source**: synthesis_wave17
**Hypothesis**: quantitative-analyst has 36 training records in scored_findings.jsonl — the only agent above the 10-record threshold. DSPy MIPROv2 typically needs 20-50 examples for a useful optimization. With 36 examples, a trial optimization is feasible. Key questions: Does the optimizer have all required dependencies? Are the training records in the correct schema for the DSPy signature? Is the Ollama endpoint available?
**Method**: research-analyst
**Success criterion**: Check the optimizer entry point (masonry/src/dspy_pipeline/optimizer.py), verify quantitative-analyst's signature file, confirm training record schema compatibility, and check Ollama availability. Verdict: HEALTHY if optimization can proceed; WARNING if blockers exist; INCONCLUSIVE if Ollama unavailable.

---

### F18.1: Fix `load_scored_all` path resolution in `run_vigil.py` to work when CWD is the masonry/ directory

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: LOW
**Source**: synthesis_wave17
**Hypothesis**: `run_vigil.py` line 53 hardcodes `base_dir / "masonry" / "training_data" / "scored_all.jsonl"`. When run from masonry/ dir, this resolves to `masonry/masonry/training_data/scored_all.jsonl` (non-existent). Fix: detect whether base_dir IS the masonry dir (by checking for `base_dir.name == "masonry"` or `(base_dir / "training_data").exists()`) and adjust path accordingly. This would allow the 243 scored records to augment the vigil health classification.
**Method**: fix-implementer
**Success criterion**: After fix, run vigil from masonry/ dir and confirm scored_all agents (quantitative-analyst, karen, git-nerd, etc.) appear in the Rose/Bud/Thorn classification via augmentation. Verdict: FIX_APPLIED.

---

## Wave 19

### D19.1: Is OVERCONFIDENT_PASS_RATE=0.95 miscalibrated for the masonry self-research campaign, causing false Thorn classifications for all agents?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: HIGH
**Source**: synthesis_wave18
**Hypothesis**: All masonry self-research agents (diagnose-analyst, fix-implementer, research-analyst, design-reviewer) have pass_rate=1.00 (every finding has confidence ≥ 0.70 — self-research findings consistently score 0.75-0.97). The OVERCONFIDENT_PASS_RATE=0.95 threshold was designed to catch agents that never express uncertainty. In self-research mode, high confidence is appropriate (targeted investigations with clear evidence). The threshold produces false Thorns for all self-research agents, making the CRITICAL verdict misleading.
**Method**: diagnose-analyst
**Success criterion**: Confirm whether pass_rate=1.00 is genuine overconfidence or expected high-quality signal. Propose threshold adjustment or context-specific classification mode. Verdict: DIAGNOSIS_COMPLETE.

---

### F19.1: Fix score_routing `agents_covered = []` hardcode in score_all_agents.py

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: LOW
**Source**: synthesis_wave18
**Hypothesis**: `score_all_agents.py` line 278 hardcodes `agents_covered: []` for the score_routing scorer entry. This causes the summary to always show "Agents: 0" for routing. The actual dispatched agents are in scored_routing.jsonl as `dispatched_agent` field — these should populate `agents_covered`. Fix: read scored_routing.jsonl and extract unique `dispatched_agent` values.
**Method**: fix-implementer
**Success criterion**: After fix, score_routing row in summary table shows "Agents: 3" (karen, planner, question-designer-bl2) or higher. Verdict: FIX_APPLIED.

---

### R19.1: After Wave 18 routing infrastructure fixes, does running all future investigations via Agent tool dispatch generate 100pt routing records at scale?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Source**: synthesis_wave18
**Hypothesis**: R18.1 empirically confirmed the first 100pt record (research-analyst dispatch). Waves 18+ should continue generating matched pairs for every Agent tool dispatch. After several waves, routing scorer should have enough 100pt records (R19.1 itself, D18.1, R18.2 each dispatched an agent — that's 3 more potential 100pt records). Check routing_log.jsonl event count and scored_routing.jsonl for new 100pt records.
**Method**: research-analyst
**Success criterion**: Count "start" events and "finding" events in routing_log.jsonl since Wave 18 started. Verify each Agent-dispatched finding generated a 100pt record. Verdict: HEALTHY if scale is working; WARNING if mismatches found.

---

### R19.2: Can `score_findings.py` be extended to also score masonry self-research findings from `masonry/findings/`, and what would the agent distribution look like?

**Status**: DONE
**Operational Mode**: research
**Priority**: LOW
**Source**: synthesis_wave18
**Hypothesis**: `score_findings.py:discover_findings()` explicitly excludes the `masonry/` subdirectory. After the backfill of `**Agent**:` fields (D18.1), masonry self-research findings could be scored and included in training data. ~115 findings across diagnose-analyst (25), research-analyst (41), fix-implementer (35), design-reviewer (9) — potentially pushing research-analyst well above the 10-record DSPy threshold.
**Method**: research-analyst
**Success criterion**: Run score_findings.py with masonry/findings/ as target (or modify discover path). Report how many masonry self-research findings pass the training threshold (≥60 score). Assess whether including them would improve DSPy training coverage. Verdict: HEALTHY if significant additions; WARNING if most score below threshold.

---

## Wave 20

**Generated from findings**: R19.1, R19.2, synthesis_wave19
**Mode transitions applied**: R19.1 WARNING → D20.1 narrowing Diagnose (session_id collision root cause); R19.1 DIAGNOSIS_COMPLETE (via D20.1) → F20.1 Fix; R19.2 WARNING → F20.2 Fix (3 concrete changes already specified); F20.1+F20.2 completion → R20.1 Research (verify training data health after fixes)

### D20.1: Does `score_routing._match_events()` use a flat `session_id`-keyed dict that causes last-write-wins collisions when multiple agents share a parent session, and can a compound `(session_id, agent_name)` key fix the match rate to 100%?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: HIGH
**Motivated by**: R19.1 — WARNING — 3/5 Wave 18+ dispatches produce 100pt records; R19.1 identifies `findings_by_session` dict keyed only by `session_id` (line 130 of score_routing.py) as the cause of last-write-wins collision when all Wave 18+ agents share session_id `315da739`
**Hypothesis**: `_match_events()` lines 130-135 build `findings_by_session: dict[str, dict]` keyed by `session_id` alone. When six start events all share `315da739`, the last finding event written wins, so five of the six start lookups (line 157) retrieve the same finding. A compound key `(session_id, agent_name)` — or a `list`-valued dict that accumulates all findings per session and then matches by agent_name — would pair each start event to its own downstream finding. Additionally, the fallback `AGENT_CATEGORIES` in score_routing.py (lines 31-43) omits `fix-implementer`, `diagnose-analyst`, `design-reviewer`, and `general-purpose`, causing those agents' start events to pass the `agent in AGENT_CATEGORIES` gate (line 98) but fall through to no record.
**Method**: diagnose-analyst
**Success criterion**: Confirm (a) the exact dict structure at line 130 and how `findings_by_session[sid] = ev` overwrites on duplicate sid; (b) whether a compound key or list-accumulation approach resolves the collision without breaking single-session matching; (c) whether the fallback AGENT_CATEGORIES at lines 31-43 is reached at runtime (i.e., the masonry import fails) and which agents are absent. Produce a Fix Specification covering both the compound-key change and the AGENT_CATEGORIES gap. Verdict: DIAGNOSIS_COMPLETE with Fix Specification ready for F20.1.

---

### F20.1: Fix `score_routing._match_events()` session_id collision and fallback AGENT_CATEGORIES gaps identified in D20.1

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: D20.1 DIAGNOSIS_COMPLETE — session_id collision in `_match_events()` (score_routing.py line 130) causes last-write-wins for all agents sharing a parent session; fallback AGENT_CATEGORIES (lines 31-43) missing `fix-implementer`, `diagnose-analyst`, `design-reviewer`, `general-purpose`
**Hypothesis**: Implementing the D20.1 Fix Specification — changing `findings_by_session` from a flat `dict[str, dict]` to a compound-key or list-accumulation structure, and adding the missing agents to the fallback AGENT_CATEGORIES dict — will raise the 100pt routing record rate from 60% (3/5) to 100% for all Agent-tool-dispatched specialist agents in future waves.
**Method**: fix-implementer
**Success criterion**: After fix, re-run `python scripts/score_routing.py` against the existing routing_log.jsonl. Verify: (a) `fix-implementer` start event (line 22 of routing_log) now produces a 100pt scored record matched to F19.1 finding; (b) `diagnose-analyst` start event (line 20) remains correctly matched; (c) no previously-scored 100pt records regress. Total Wave 18+ 100pt records should increase from 3 to at least 4. Verdict: FIX_APPLIED.

---

### F20.2: Implement the three `score_findings.py` changes to enable masonry self-research findings scoring (R19.2 fix specification)

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R19.2 WARNING — score_findings.py passes only 20/137 masonry findings (14.6%) due to three structural mismatches: (a) "masonry" in discovery exclusion list (line 282), (b) `_extract_section` regex stops at `###` subsections (line 130-134 approx), (c) `FIX_APPLIED` and `COMPLETE` absent from VALID_VERDICTS (lines 21-28)
**Hypothesis**: Three targeted changes — (1) remove "masonry" from the `child.name not in (...)` exclusion set at line 282, (2) tighten the `_extract_section` lookahead from `(?=^##|\Z)` to `(?=^## [^#]|\Z)` to skip `###` subsection headers, (3) add `"FIX_APPLIED"` and `"COMPLETE"` to the VALID_VERDICTS frozenset — will raise the masonry pass rate from 14.6% (20/137) to an estimated 90%+ (105-115/137). Source-tagging (`"source": "masonry-self-research"`) must be added to output records to prevent ADBP training data contamination.
**Method**: fix-implementer
**Success criterion**: After fix, run `python scripts/score_findings.py --base-dir . --output masonry/training_data/scored_findings_masonry.jsonl` (or equivalent). Count passing records: fix-implementer must go from 0% to ≥80% pass rate; research-analyst must reach ≥90%; total masonry passing records ≥100. All output records must include `"source": "masonry-self-research"` field. Verdict: FIX_APPLIED.

---

### R20.1: After F20.1 and F20.2 fixes, what is the new training data health state — routing 100pt record count, total scored_all records, and per-agent distribution?

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: F20.1 and F20.2 completion — both fixes are expected to materially change the training data counts that vigil and DSPy optimization read from; R19.1 WARNING and R19.2 WARNING each projected specific improvements that need empirical verification
**Hypothesis**: F20.1 should add at least 1 new 100pt routing record (fix-implementer Wave 18 dispatch now matched), bringing routing 100pt records from 3 to at least 4. F20.2 should add 100-115 masonry self-research records across research-analyst (~43), fix-implementer (~32), diagnose-analyst (~25), design-reviewer (~8), raising total training records from ~254 to ~360+. Per-agent, research-analyst should cross the 10-record DSPy threshold for the first time (5 ADBP + 43 masonry = 48 records). Vigil fleet health should reflect the improved signal when re-run.
**Method**: research-analyst
**Success criterion**: Run `python scripts/score_all_agents.py` and `python scripts/score_routing.py` after both fixes are applied. Report: (a) total records in scored_all.jsonl and per-agent breakdown; (b) 100pt routing records count in scored_routing.jsonl; (c) which agents now meet the DSPy 10-record threshold; (d) vigil verdict after re-running `python scripts/run_vigil.py --project . --output vigil`. Verdict: HEALTHY if routing 100pt ≥4 and masonry records ≥100 and research-analyst ≥40 records; WARNING if any projected threshold is missed by >20%.

---

## Wave 21

**Generated from findings**: R20.1, synthesis_wave20
**Mode transitions applied**: R20.1 HEALTHY (open issue: DSPy trial via Ollama) → R21.1 Research (test Ollama DSPy integration before committing); R20.1 HEALTHY (open issue: stale masonry/masonry/training_data/ path) → D21.1 Diagnose (determine path nature) → F21.1 Fix (remove stale copy); R20.1 HEALTHY (open issue: unknown thorn in vigil) → R21.2 Research (determine whether "unknown" thorn is removable or structurally unavoidable after D21.1+F21.1)

### R21.1: Can DSPy MIPROv2 optimization be run with Ollama qwen3:14b as the language model backend, using quantitative-analyst's 125 training records as the training set?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Motivated by**: R20.1 HEALTHY — synthesis_wave20 open issue #2 (DSPy trial blockers): ANTHROPIC_API_KEY not set, but Ollama qwen3:14b confirmed available at 192.168.50.62:11434; corpus is now 435 records with quantitative-analyst at 125 (largest single-agent corpus, well above any reasonable training minimum)
**Hypothesis**: DSPy's `dspy.OllamaLocal` (or `dspy.LM("ollama/qwen3:14b", api_base=...)`) can serve as a drop-in replacement for the Anthropic backend in `masonry/src/dspy_pipeline/optimizer.py`. quantitative-analyst's 125 records exceed the minimum viable training set. An end-to-end MIPROv2 trial should complete without the ANTHROPIC_API_KEY gate, produce at least one optimized prompt JSON in `masonry/optimized_prompts/quantitative-analyst.json`, and show measurable improvement (>5%) in held-out evaluation score vs the unoptimized baseline.
**Method**: research-analyst
**Success criterion**: Verify (a) whether `dspy.OllamaLocal` or equivalent Ollama backend is present in the installed DSPy version; (b) what configuration changes `optimizer.py` requires to swap the LM backend from Anthropic to Ollama; (c) whether a dry-run (no actual HTTP calls) can be simulated to validate the pipeline wiring without network dependency; (d) if a live run is feasible, report the pre/post evaluation score delta. Verdict: HEALTHY if Ollama backend is supported and optimizer.py can be wired with <10 lines of config change; WARNING if significant refactor required; FAILURE if DSPy version lacks Ollama support entirely.

---

### D21.1: Is `masonry/masonry/training_data/` a symlink, a copy produced by a path-resolution artifact in score_all_agents.py, or a manually created directory — and what is the safe removal procedure?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Motivated by**: R20.1 HEALTHY — synthesis_wave20 open issue #4: `masonry/masonry/training_data/` contains a stale 235-record copy (scored_all.jsonl 906K, scored_findings.jsonl 1.0M, scored_routing.jsonl 4.1K) while the authoritative file is `masonry/training_data/scored_all.jsonl` (435 records); the stale copy risks being read by downstream scripts that do not use `--base-dir .` flag
**Hypothesis**: The `masonry/masonry/` directory was created when `score_all_agents.py` was invoked from inside `masonry/` as CWD (rather than from repo root with `--base-dir .`). In that case the script resolved its output path as a relative `masonry/training_data/` subfolder, which — from inside `masonry/` — produced `masonry/masonry/training_data/`. The directory is a real directory (not a symlink). It is safe to delete, but the correct invocation path should be documented to prevent recurrence.
**Method**: diagnose-analyst
**Success criterion**: Confirm (a) whether `masonry/masonry/` is a regular directory or a symlink (`ls -la` or `os.path.islink`); (b) trace which script invocation produced it by checking `score_all_agents.py` output path resolution logic; (c) verify no active script or import references `masonry/masonry/training_data/` as its read path; (d) produce a Fix Specification for F21.1 covering the removal command and the prevention note. Verdict: DIAGNOSIS_COMPLETE if safe removal is confirmed with no active references; WARNING if any live reference found.

---

### F21.1: Remove the stale `masonry/masonry/training_data/` directory identified in D21.1

**Status**: DONE
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: D21.1 DIAGNOSIS_COMPLETE (expected) — stale 235-record copy in `masonry/masonry/training_data/` causes ambiguity about authoritative training data path; any script invoked from inside `masonry/` CWD without `--base-dir .` will write a new stale copy here rather than updating the canonical `masonry/training_data/` location
**Hypothesis**: Deleting `masonry/masonry/` (which contains only `training_data/` with three JSONL files) will eliminate the ambiguity. Adding a note to the canonical invocation command in `project-brief.md` or a `README` inside `masonry/training_data/` will prevent recurrence. No code changes required; the fix is purely filesystem cleanup plus documentation.
**Method**: fix-implementer
**Success criterion**: After fix: (a) `masonry/masonry/` directory no longer exists; (b) `masonry/training_data/scored_all.jsonl` (435 records) remains intact and unchanged; (c) `python scripts/score_all_agents.py --base-dir .` from repo root still produces correct output to `masonry/training_data/`; (d) a short note documenting the correct invocation path is added somewhere visible (project-brief.md open issues section or a README). Verdict: FIX_APPLIED.

---

### R21.2: After D21.1 and F21.1, what is the final vigil fleet state — is the "unknown" thorn removable by re-attributing unattributed synthesis findings, or is it structurally unavoidable?

**Status**: DONE
**Operational Mode**: research
**Priority**: LOW
**Motivated by**: R20.1 HEALTHY — vigil reports 1 thorn: `unknown` agent with 0% quality gate pass rate over 13 findings; these are synthesis files written without an `Agent:` field; synthesis_wave20 notes this is "a data-quality issue with unattributed findings, not a fleet regression"; D21.1+F21.1 may alter the findings corpus vigil reads if the stale path contributed unattributed records
**Hypothesis**: The 13 "unknown" findings are synthesis files (`findings/synthesis_wave*.md`, `findings/cascade-map.md`, `findings/audit-report.md`, etc.) that have no `**Agent**:` frontmatter field. Vigil assigns them to the `unknown` bucket. Two resolution paths exist: (a) add `**Agent**: synthesizer-bl2` (or appropriate agent name) to each synthesis file's header — this re-attributes them and removes the unknown thorn; (b) exclude synthesis/meta files from vigil scoring by file-name pattern — this removes them from the count without attribution. After F21.1 removes the stale training_data copy, re-running vigil confirms whether record counts shift (the stale 235-record copy may have contributed unattributed records to vigil's corpus).
**Method**: research-analyst
**Success criterion**: (a) Run vigil after F21.1 and report whether the unknown thorn count changes; (b) inspect the 13 unattributed findings and identify their file names; (c) determine which resolution path (re-attribution vs exclusion) is correct given the finding types; (d) recommend a one-time fix (add Agent: fields or update vigil's exclusion list) that would move the fleet verdict from WARNING to HEALTHY. Verdict: HEALTHY if unknown thorn is provably removable with a concrete one-time action; WARNING if structurally unavoidable (e.g., vigil parses non-finding files by design).

---

## Wave 22

**Generated from findings**: R21.1 (WARNING), synthesis_wave21 open issues
**Mode transitions applied**: R21.1 WARNING (unverified qwen3:14b structured output) → F22.1 Fix (wire 2-line Ollama config specified in R21.1) + R22.1 Research (smoke-test structured output before full run); R22.1 HEALTHY (conditional) → R22.2 Research (full MIPROv2 trial, score delta measurement); synthesis_wave21 open issue #2 (confidence overcalibration limits training volume) → D22.1 Diagnose (characterize impact and design a calibration fix)

---

### F22.1: Wire `configure_dspy()` in `optimizer.py` to accept an Ollama backend using the 2-line config change specified in R21.1

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R21.1 WARNING — `configure_dspy()` (optimizer.py lines 73-76) hardcodes `dspy.LM(f"anthropic/{model}")` with no Ollama path. R21.1 identified this as the sole blocking config change: replace the function body with `dspy.LM("ollama_chat/qwen3:14b", api_base="http://192.168.50.62:11434")`. A caller-site parameter (e.g., `backend: str = "ollama"`) should guard the change so the Anthropic path remains reachable for future use.
**Hypothesis**: Adding a `backend` parameter to `configure_dspy()` with `"ollama"` as the default and conditional logic to select either the Ollama or Anthropic LM will allow the optimizer to run against qwen3:14b without breaking the existing Anthropic path. No changes to `optimize_agent()`, `optimize_all()`, or any DSPy signature are required — the LM is configured globally via `dspy.configure(lm=lm)`.
**Method**: fix-implementer
**Success criterion**: (1) Read `src/dspy_pipeline/optimizer.py` in full. (2) Modify `configure_dspy()` to accept a `backend: str = "ollama"` parameter. When `backend == "ollama"`, configure `dspy.LM("ollama_chat/qwen3:14b", api_base="http://192.168.50.62:11434")`. When `backend == "anthropic"`, keep the existing `dspy.LM(f"anthropic/{model}")` path. (3) Verify `import sys` is already present (it is, line 10 — no addition needed). (4) Confirm no other hardcoded `anthropic/` LM strings remain in the file that would override the configured backend. Verdict: FIX_APPLIED when the Ollama path is wired and the Anthropic path remains intact; FIX_FAILED if `dspy.configure(lm=lm)` is not reached for the Ollama branch.

---

### R22.1: Does a single-prediction smoke-run of `dspy.LM("ollama_chat/qwen3:14b")` against `ResearchAgentSig` produce valid structured output?

**Status**: DONE
**Operational Mode**: research
**Priority**: HIGH
**Motivated by**: R21.1 WARNING — "qwen3:14b structured output reliability under bootstrapping is unverified." R21.1 explicitly states the verdict changes to HEALTHY if "a short smoke-run of dspy.LM('ollama_chat/qwen3:14b') confirms structured output generation works for at least one sample prediction." F22.1 is a prerequisite (must be DONE before this runs).
**Hypothesis**: qwen3:14b is a capable 14B instruction-following model. When prompted with a single `ResearchAgentSig` example via `dspy.ChainOfThought(ResearchAgentSig)`, it will produce parseable output with all required fields populated: `verdict`, `severity`, `confidence`, `summary`, `evidence`, `mitigation`. The primary failure modes are: (a) the model returns free-form prose without field delimiters, (b) it omits one or more output fields, or (c) DSPy's field parser raises a validation error on the response. A single successful prediction is sufficient to unblock the full MIPROv2 trial.
**Method**: research-analyst
**Success criterion**: (1) Confirm F22.1 is DONE (Ollama backend wired). (2) Call `configure_dspy(backend="ollama")` to set the global LM. (3) Load one quantitative-analyst training example via `build_dataset()` from `training_extractor.py`. (4) Instantiate `dspy.ChainOfThought(ResearchAgentSig)` and call it with the example's input fields. (5) Inspect the returned prediction: all six output fields (`verdict`, `severity`, `confidence`, `summary`, `evidence`, `mitigation`) must be non-empty strings or floats. Verdict: HEALTHY if all output fields are populated and parseable; BLOCKED if qwen3:14b systematically returns malformed output (zero valid demos — optimization cannot proceed); WARNING if fields are partially populated (e.g., `mitigation` empty but others valid — optimization may still proceed with degraded quality).

---

### R22.2: Run full MIPROv2 optimization for `quantitative-analyst` using 125 training records via Ollama — what is the pre/post evaluation score delta?

**Status**: DONE
**Finding**: Deferred to R23.1 (carried forward after configure_dspy() bug resolved). R23.1 DONE — WARNING, 68.3% best score vs 59.5% baseline (+8.8pt).
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: R21.1 WARNING + synthesis_wave21 "Next Phase Hypotheses" #2 — once smoke-run confirms qwen3:14b produces valid structured output (R22.1 HEALTHY), run the full MIPROv2 trial. quantitative-analyst has 125 training records — the largest single-agent corpus in the campaign, well above the 5-example minimum in `optimize_all()`. This is the primary validation question for the entire DSPy optimization pipeline.
**Hypothesis**: MIPROv2 will bootstrap 3 demos from the 125-record trainset, run optimization trials, and produce an optimized prompt JSON at `masonry/optimized_prompts/quantitative-analyst.json`. The post-optimization evaluation score will exceed the unoptimized baseline by at least 5 percentage points on the held-out subset. The heuristic metric in `build_metric()` (verdict_match 0.4 + evidence_quality 0.4 + confidence_calibration 0.2) will drive the optimization toward higher-quality verdict and evidence generation.
**Method**: research-analyst
**Success criterion**: (1) Confirm R22.1 is DONE with HEALTHY verdict. (2) Run `optimize_agent("quantitative-analyst", ResearchAgentSig, dataset, output_dir)` with `max_bootstrapped_demos=3, max_labeled_demos=3`. (3) Report the `best_score` field on the returned module and the pre-optimization baseline score (unoptimized module score on the same trainset). (4) Confirm `masonry/optimized_prompts/quantitative-analyst.json` is written and non-empty. (5) Report wall-clock runtime for the optimization run. Verdict: HEALTHY if optimized score > baseline + 0.05 and JSON is written; WARNING if optimization completes but score delta < 0.05 (model converged near baseline); FAILURE if MIPROv2 raises an exception or the output file is not written.

---

### D22.1: Does the `confidence_calibration` component in `build_metric()` systematically penalize correct high-confidence findings, and what recalibration design would stop reducing training data volume?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: LOW
**Motivated by**: synthesis_wave21 open issue #2 — "fix-implementer findings with confidence >= 0.96 score 10/40 on confidence_calibration, suppressing 55% of masonry findings below the 60-point training threshold." The current formula `1 - |predicted - 0.75|` in `build_metric()` (optimizer.py line 29 approx) scores confidence=1.0 as 0.75 (75% of max), while the external scorer in `score_findings.py` awards only 10/40 points to findings with confidence > 0.95. Both systems penalize empirically verified high-confidence findings (e.g., FIX_APPLIED with passing tests where confidence=0.99 is objectively correct). R19.2 flagged this as "Optional Change 4, design decision, not a bug."
**Hypothesis**: The penalty is real and measurable: a fix-implementer finding with confidence=0.99 and correct verdict receives a confidence_calibration component score of ~0.76 in the DSPy metric (instead of the maximum 1.0), reducing its training weight. For the external scorer, confidence > 0.95 receives only 10/40 pts on that rubric dimension — the dominant factor in 55% of masonry findings failing the 60-point threshold. A sigmoid recalibration (or a mode-specific bypass for FIX_APPLIED verdicts) would eliminate the penalty for empirically verified outcomes without affecting uncertainty-bearing research findings where confidence=0.75 is the appropriate prior.
**Method**: diagnose-analyst
**Success criterion**: (1) Read `build_metric()` in `optimizer.py` and the `confidence_calibration` scorer in `score_findings.py`. (2) Quantify the exact score penalty for confidence=0.99 vs confidence=0.75 in both systems. (3) Count how many masonry training records are suppressed by the penalty (records that would pass 60 pts if confidence scoring were neutral). (4) Propose a concrete recalibration: either (a) a sigmoid that scores confidence=0.75 at 0.5 and confidence=0.99 at 0.95 (rescaled), or (b) a verdict-conditional path where FIX_APPLIED findings use `1.0 - 0.1 * max(0, confidence - 0.98)` (near-flat above 0.75). Produce a Fix Specification with the exact line change for each affected file. Verdict: DIAGNOSIS_COMPLETE if the penalty is quantified and a recalibration design is specified with a projected record recovery count; WARNING if multiple recalibration designs are viable and a design decision is needed before fixing.

---

## Wave 23

**Generated from findings**: R22.1 (WARNING), D22.1 (DIAGNOSIS_COMPLETE), R22.2 (PENDING — deferred)
**Mode transitions applied**: R22.1 WARNING (configure_dspy default model wrong for Ollama backend) → F23.1 Fix; D22.1 DIAGNOSIS_COMPLETE (confidence_calibration band cliff confirmed, fix spec complete) → F23.2 Fix; R22.2 PENDING deferred → R23.1 Research (carried forward, blocked on F23.1)

---

### F23.1: Fix `configure_dspy()` default model so that `backend="ollama"` does not silently use "claude-sonnet-4-6"

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R22.1 WARNING — `configure_dspy(backend="ollama")` defaults to `model="claude-sonnet-4-6"` (optimizer.py line 73 signature). Ollama rejects this model with a 404. Confirmed by smoke-test: caller must pass `model="qwen3:14b"` explicitly or the call fails. Every Ollama-backend invocation that omits the `model` argument (including the MCP server default path and `optimize_all()`) will error silently until this default is corrected.
**Hypothesis**: Changing the default value in the `configure_dspy()` signature from `model: str = "claude-sonnet-4-6"` to a backend-conditional default — either by overloading the parameter or by setting `model` to `None` and resolving the default inside the function body (`"qwen3:14b"` when `backend == "ollama"`, `"claude-sonnet-4-6"` when `backend == "anthropic"`) — will make `configure_dspy(backend="ollama")` work correctly without requiring callers to specify the model. No changes to `optimize_agent()`, `optimize_all()`, or the MCP server are required beyond this one fix.
**Method**: fix-implementer
**Success criterion**: (1) Read `masonry/src/dspy_pipeline/optimizer.py` in full to confirm the current signature at line 73. (2) Change the `configure_dspy()` signature so that when `backend="ollama"` and no `model` is provided, the resolved model is `"qwen3:14b"`; when `backend="anthropic"` and no `model` is provided, the resolved model is `"claude-sonnet-4-6"`. (3) Verify the change does not break the existing Anthropic path (`backend="anthropic"` must still resolve to `"claude-sonnet-4-6"` by default). (4) Confirm `optimize_agent()` and `optimize_all()` propagate `backend` correctly to `configure_dspy()` — no caller-side changes should be needed. Verdict: FIX_APPLIED when `configure_dspy(backend="ollama")` resolves to `qwen3:14b` without an explicit `model` argument and `configure_dspy(backend="anthropic")` continues to resolve to `claude-sonnet-4-6`; FIX_FAILED if either path regresses.

---

### F23.2: Widen `confidence_calibration` band in `score_findings.py` from `[0.5, 0.95]` to `[0.5, 1.0]`

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: D22.1 DIAGNOSIS_COMPLETE — `_score_confidence_calibration()` in `score_findings.py` line 183 reads `if 0.5 <= confidence <= 0.95:` and awards 15 points only within that band. Findings with confidence > 0.95 fall outside the band and receive 10 points instead of 15 — a 30-point cliff when scaled (10/40 vs 40/40 on the full rubric). D22.1 quantified the impact: 77 findings affected, 40 training records suppressed below the 60-point threshold (14.4% of total training volume). Fix spec from D22.1 is complete: widen the upper bound from `0.95` to `1.0`. Projected result: +40 training records recoverable, raising training-ready count from 278 to ~318.
**Hypothesis**: A single character change — replacing `0.95` with `1.0` on line 183 — removes the cliff without altering the band's lower behavior (confidence below 0.5 still scores the lower tier). The change is safe because empirically verified high-confidence findings (e.g., FIX_APPLIED with passing tests at confidence=0.99) are objectively correctly calibrated — the existing severity-match logic already penalizes overconfident findings that contradict their evidence, so the confidence band is redundant for that purpose.
**Method**: fix-implementer
**Success criterion**: (1) Read `masonry/scripts/score_findings.py` and locate `_score_confidence_calibration()` (line ~183). (2) Confirm the current condition is `if 0.5 <= confidence <= 0.95:`. (3) Change `0.95` to `1.0`. (4) Re-run `python masonry/scripts/score_findings.py` (or the equivalent scoring invocation) on a sample finding with confidence=0.99 — confirm it now receives 15 points on the calibration component instead of 10. (5) Re-run `python masonry/scripts/score_all_agents.py --base-dir .` from repo root and report the new training-ready count (expected: ~318, up from 278). Verdict: FIX_APPLIED when (a) the line change is confirmed, (b) a confidence=0.99 finding scores 15 pts on calibration, and (c) total training-ready count increases; FIX_FAILED if scoring behavior does not change after the edit.

---

### R23.1: Run full MIPROv2 optimization trial for `quantitative-analyst` via Ollama — measure pre/post evaluation score delta

**Status**: DONE
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: R22.2 PENDING (deferred by user pause) — the full MIPROv2 trial for `quantitative-analyst` was blocked by the `configure_dspy()` default model bug (R22.1 WARNING). F23.1 resolves that blocker. quantitative-analyst has 125 training records — the largest single-agent corpus — and the smoke test (R22.1) confirmed qwen3:14b produces valid structured output. This is the primary validation gate for the entire DSPy optimization pipeline.
**Hypothesis**: With F23.1 DONE, `configure_dspy(backend="ollama")` will correctly resolve to qwen3:14b. MIPROv2 will bootstrap 3 demos from the 125-record trainset and run optimization trials. The optimized prompt JSON will be written to `masonry/optimized_prompts/quantitative-analyst.json`. The post-optimization evaluation score will exceed the unoptimized baseline by at least 5 percentage points on a held-out subset. After F23.2 is also applied, the effective training set for quantitative-analyst may grow (if any of the ~40 recovered records belong to this agent), further improving the optimization.
**Method**: research-analyst
**Success criterion**: (1) Confirm F23.1 is DONE before running. (2) Call `optimize_agent("quantitative-analyst", ResearchAgentSig, dataset, output_dir, backend="ollama")` with `max_bootstrapped_demos=3, max_labeled_demos=3`. (3) Report the `best_score` on the returned optimized module and the unoptimized baseline score (same metric on the same trainset). (4) Confirm `masonry/optimized_prompts/quantitative-analyst.json` is written and non-empty — inspect at least the `instructions` field. (5) Report wall-clock runtime for the full optimization run. Verdict: HEALTHY if optimized score > baseline + 0.05 and the JSON is written; WARNING if optimization completes but score delta < 0.05 (model converged near baseline — inspect demo quality); FAILURE if MIPROv2 raises an exception, times out, or the output file is not produced.

---

## Wave 24

**Generated from findings**: R23.1 (WARNING — 5-7 hour run time), synthesis_wave23 open issues #2 and #3, ROADMAP.md Phase 17 metric plan, training_data/scored_all.jsonl agent distribution (karen 191 records unoptimized), training_data/scored_routing.jsonl (17 records, target_agent field absent)
**Mode transitions applied**: R23.1 WARNING (execution time constraint) → M24.1 Monitor + F24.1 Fix (add --num-trials/--valset-size flags per R23.1 options); synthesis open issue #3 (_build_qid_to_agent_map table-format gap) → D24.1 Diagnose (confirm record loss and fix scope); ROADMAP Phase 17 (metric improvements, assumptions unverified) → R24.1 Research (validate content-signal changes before implementing); karen 191 records + no signature defined → V24.1 Validate (architectural pre-check before committing to multi-agent optimization); routing scored_routing.jsonl target_agent attribution broken → D24.2 Diagnose; onboard_agent.py stale detection missing expanduser (ROADMAP confirmed gap) → D24.3 Diagnose

---

### M24.1: Add MIPROv2 run-time duration to monitor-targets.md with WARNING and FAILURE thresholds

**Status**: DONE
**Operational Mode**: monitor
**Priority**: MEDIUM
**Motivated by**: R23.1 WARNING — full 10-trial MIPROv2 optimization with qwen3:14b requires 4-8 hours per agent. The synthesis identifies this as a blocking constraint for rapid metric iteration. Without a tracked threshold, long-running optimizations will silently exceed acceptable windows for interactive development cycles.
**Hypothesis**: Adding `dspy_optimization_wall_time_minutes` to monitor-targets.md with WARNING at 120 minutes (2-hour threshold for Anthropic API backend) and FAILURE at 480 minutes (8-hour threshold for Ollama overnight run) will make run-time regressions visible before they block the ROADMAP Phase 17 iteration cycle. The Anthropic API path drops from ~5 hours to ~8 minutes per ROADMAP.md line 95, making the WARNING threshold actionable for daytime runs.
**Method**: research-analyst
**Success criterion**: (1) Read or create `masonry/monitor-targets.md`. (2) Add entry for `dspy_optimization_wall_time_minutes`: WARNING threshold = 120 (daytime Anthropic path), FAILURE threshold = 480 (overnight Ollama max). (3) Also add `dspy_bootstrap_failure_rate`: WARNING threshold = 0.1 (>10% of bootstrap sets fail), FAILURE threshold = 0.5 (majority fail — metric arity or LM connectivity issue). (4) Document measurement method: parsed from `opt.log` output lines `"Trial N: score=..."` timestamps. Verdict: HEALTHY if both metrics are added with correct thresholds and measurement method documented; WARNING if monitor-targets.md does not yet exist (create it as part of the fix).

---

### F24.1: Add `--num-trials` and `--valset-size` CLI flags to `run_optimization.py`

**Status**: DONE
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R23.1 WARNING — "Add `--num-trials` / `--valset-size` flags: Reduce to 5 trials × 20 examples → ~1-2 hour run." Without these flags, every optimization run uses the hardcoded constants in `optimizer.py` (`max_bootstrapped_demos=3`, `MIPROv2` defaults for num_trials). ROADMAP.md Phase 17 plans to increase search space (`num_instruct_candidates: 3 → 10`, `max_bootstrapped_demos: 2 → 5`, `num_trials: 10 → 20`), which makes the hardcoded constants an active impediment to iterating on metric design without editing source files.
**Hypothesis**: Adding `--num-trials` (default: 10) and `--valset-size` (default: 100) arguments to `run_optimization.py`'s `argparse` block, and forwarding them into the `optimize_agent()` call (which must in turn pass them to `optimizer.compile()`), will allow short test runs (`--num-trials 3 --valset-size 20` → ~15-30 minutes) without modifying `optimizer.py`. The `optimizer.compile()` call currently passes only `max_bootstrapped_demos` and `max_labeled_demos`; `num_trials` and valset size are MIPROv2 constructor or compile-time parameters that must be verified against the DSPy MIPROv2 API.
**Method**: fix-implementer
**Success criterion**: (1) Read `masonry/scripts/run_optimization.py` in full and `masonry/src/dspy_pipeline/optimizer.py` in full. (2) Add `--num-trials INT` (default 10) and `--valset-size INT` (default 100) to the argparse block. (3) Forward both values through the `run()` function signature into `optimize_agent()`. (4) In `optimize_agent()`, pass `num_trials` to `MIPROv2(...)` constructor or to `optimizer.compile()` — verify the correct parameter name against the DSPy MIPROv2 source or docs. (5) Pass `valset_size` as a slice on the trainset before calling `compile()` (e.g., `trainset[:valset_size]`). (6) Verify with a dry-run invocation: `python masonry/scripts/run_optimization.py quantitative-analyst --backend ollama --num-trials 1 --valset-size 5` should produce a progress line and not raise an error on the parameter signature. Verdict: FIX_APPLIED when the flags are wired end-to-end and the dry-run completes without a TypeError; FIX_FAILED if `optimizer.compile()` raises an unexpected keyword argument error or the flags are not recognized by argparse.

---

### D24.1: How many agent-attributed training records does `_build_qid_to_agent_map()` silently drop from table-format `questions.md` projects, and what is the minimum fix?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: HIGH
**Motivated by**: synthesis_wave23 open issue #3 — "`_build_qid_to_agent_map()` only parses the `### QID:` block format. Projects using the older markdown table format in `questions.md` (e.g. `| ID | Status | Question |`) produce zero agent-attributed records." The ROADMAP.md line 74 confirms this gap. The ADBP project's `questions.md` uses table format. If ~100+ findings from ADBP exist but have no `**Agent**:` field in their finding files, they would have zero agent attribution and be excluded from DSPy training entirely.
**Hypothesis**: `_build_qid_to_agent_map()` in `training_extractor.py` (lines 25-48) uses `re.search(r"###\s+(\w+\d+\.\d+):\s*(.+)", block)` which matches only the `### QID: text` header format. A `questions.md` using markdown table rows (`| D1.1 | DONE | research-analyst | ... |`) produces zero matches. The fallback `**Agent**:` field extraction in the finding file itself (line 152 in `_add()`) would recover records that have the field, but cannot recover records that lack it entirely (older findings pre-Wave 18 backfill). The total record loss is bounded by: (number of ADBP or other table-format findings) × (fraction without `**Agent**:` in the finding file).
**Method**: diagnose-analyst
**Success criterion**: (1) Read `training_extractor.py:_build_qid_to_agent_map()` (lines 25-48) and confirm the regex matches only `### QID:` format. (2) Locate one table-format `questions.md` file in the repo (ADBP or other project). Count rows in it. (3) Run `_build_qid_to_agent_map(path_to_table_format_questions_md)` and confirm it returns an empty dict. (4) Count how many finding files in the same project lack a `**Agent**:` field (these are the unrecoverable records). (5) Specify the minimum fix: either (a) add a table-format regex branch to `_build_qid_to_agent_map()` that parses `| QID | ... | agent-name | ... |` rows, or (b) add a fallback that reads `**Agent**:` from finding files directly (already partially present at line 149-154, but only activates when `qid_map` is non-empty). Produce a Fix Specification with the exact regex and line location. Verdict: DIAGNOSIS_COMPLETE if record loss is quantified and a fix spec is produced; FAILURE if the gap is larger than 50 records (material training data loss warranting immediate fix).

---

### R24.1: Will the four Phase 17 metric improvements in ROADMAP.md actually move the `build_metric()` ceiling from 68.3% to 75-80%?

**Status**: DONE
**Finding**: [R24.1](findings/R24.1.md) — WARNING — Phase 17 changes yield +1-4 pts (reaching 69-73%), not 75-80%; binding constraint is verdict accuracy (~35-40%), not evidence scoring. Fix D24.1 attribution gap first for highest leverage.
**Operational Mode**: research
**Priority**: HIGH
**Motivated by**: synthesis_wave23 milestone #1 — "First MIPROv2 run achieved 68.3% best score vs 59.5% baseline (+8.8pt)." ROADMAP.md Phase 17 proposes four changes to `build_metric()`: (1) replace `len(evidence) > 100` with content signals (`has_numbers`, `has_threshold_language`, `length > 300`), (2) add severity validation component (0.15 weight), (3) verdict-conditioned confidence calibration, (4) filter training records with `score < 0.4`. These are assumptions about what drives metric quality, not verified relationships. The expected gain of "+5-8 points" is a projection, not a measurement.
**Hypothesis**: The evidence length check (current: binary at 100 chars) is the weakest signal because both substantive analysis and verbose filler pass it equally. Content signals (`re.search(r'\d+\.?\d*', evidence)` for numbers, keyword set for threshold language) would better distinguish quality. However, the net gain depends on how often the current metric already gives correct gradient signal — if verdict_match (0.4 weight) already dominates the optimization trajectory, evidence quality changes may have diminishing returns. The claim of 75-80% ceiling requires that at least two of the four changes each contribute >2 points independently.
**Method**: research-analyst
**Success criterion**: (1) Read `masonry/src/dspy_pipeline/optimizer.py:build_metric()` (lines 23-68) in full. (2) For each of the 4 planned changes, estimate the directional impact: does it increase gradient signal quality, reduce noise, or both? Specifically: (a) does replacing length > 100 with `length > 300 AND has_numbers` change the score for at least 30% of the 435 training records? (b) does severity validation add a genuinely independent signal or does it correlate heavily with verdict_match? (c) does verdict-conditioned confidence calibration produce different targets than the fixed 0.75 target for ≥20% of records? (d) how many of the 435 records have `score < 0.4` and would be filtered? (3) Cross-check: compute current `build_metric()` scores on a sample of 20 masonry findings (mix of HEALTHY/WARNING/FAILURE) and identify which records the metric currently scores incorrectly. (4) Verdict: HEALTHY if at least 2 of 4 changes would produce measurable gradient improvement (>10% of records affected with correct directional signal); WARNING if the planned changes are decorative and the real ceiling is already approached; FAILURE if the changes introduce a regression (e.g., severity validation rejects valid severity strings due to case mismatch).

---

### V24.1: Is `karen` (191 training records) a viable next candidate for MIPROv2 optimization, and does `ResearchAgentSig` match karen's actual output structure?

**Status**: DONE
**Operational Mode**: validate
**Priority**: MEDIUM
**Motivated by**: `training_data/scored_all.jsonl` shows karen has 191 training records — the single largest agent corpus, exceeding quantitative-analyst's 125. However, karen has no optimized prompt in `masonry/optimized_prompts/`. The architecture question is whether karen's outputs (roadmaps, changelogs, folder audit reports) fit the `ResearchAgentSig` output schema (`verdict`, `severity`, `confidence`, `evidence`, `mitigation`) or require a new `KarenSig` with different output fields.
**Hypothesis**: karen produces structured organizational outputs (ROADMAP.md updates, CHANGELOG entries, folder audit findings) which do not naturally map to the `verdict`/`severity`/`confidence` schema used in `ResearchAgentSig`. If karen findings lack `**Verdict**:` or `**Severity**:` fields, `extract_finding()` in `training_extractor.py` will return None for those records (line 79: `if not verdict_m: return None`), meaning the 191 records in `scored_all.jsonl` may be sourced from a different extraction path than the standard pipeline. Validating the mismatch before attempting optimization prevents a silent 0-example trainset.
**Method**: research-analyst
**Success criterion**: (1) Read `masonry/src/dspy_pipeline/signatures.py` — confirm `ResearchAgentSig` output fields (`verdict`, `severity`, `confidence`, `evidence`, `mitigation`, `summary`). (2) Sample 5 karen findings from `masonry/findings/` and check which fields are present (`**Verdict**:`, `**Severity**:`, `**Confidence**:`). (3) Read `load_training_data_from_scored_all()` in `run_optimization.py` (lines ~32-65) — confirm what input/output fields it reads from `scored_all.jsonl` records for karen. (4) Determine: can karen's `scored_all.jsonl` records be directly loaded as `ResearchAgentSig` examples, or does a new `KarenSig` need to be defined in `signatures.py`? (5) If ResearchAgentSig is compatible, confirm whether karen's 191 records have sufficient non-empty `verdict` and `evidence` fields to constitute a viable trainset. Verdict: HEALTHY if ResearchAgentSig is compatible and ≥50 karen records have both verdict and evidence; WARNING if compatibility requires a field mapping layer but is achievable without a new signature; FAILURE if karen's output schema is structurally incompatible with ResearchAgentSig and a new KarenSig must be designed before optimization can proceed.

---

### D24.2: Why do all 17 records in `scored_routing.jsonl` have `target_agent = "unknown"`, making them unusable for routing optimization?

**Status**: DONE
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Motivated by**: Inspection of `masonry/training_data/scored_routing.jsonl` (17 records) shows every record has `agent: "mortar"` and `dispatched_agent` populated, but no `target_agent` field. The routing scoring script (`score_routing.py`) assigns `score_breakdown.correct_agent_dispatched = 70` for each record, but without a `target_agent` field, there is no ground-truth label against which to measure routing accuracy. This means the 17 routing records cannot currently train a routing optimizer — they measure dispatch events but not dispatch correctness.
**Hypothesis**: The `score_routing.py` script reads `dispatched_agent` (the agent that was actually called) and writes it as `score_breakdown.correct_agent_dispatched`, but never writes a `target_agent` field (the agent that should have been called, i.e., the ground truth). This is a schema gap: the routing training record schema (`scored_routing.jsonl`) conflates the dispatched agent with the correct agent, awarding 70 points by assumption. If `dispatched_agent == target_agent` is never verified, all 17 records are trivially correct and provide no training signal for the routing optimizer.
**Method**: diagnose-analyst
**Success criterion**: (1) Read `masonry/scripts/score_routing.py` in full. (2) Confirm whether `target_agent` is ever written to the output record. (3) Identify the source of the 70-point `correct_agent_dispatched` score — is it a lookup against a ground-truth label, or a default award? (4) Determine: what data source would provide `target_agent` (ground truth)? Options: (a) the original user request text could be labelled manually, (b) a subset of records where the downstream agent succeeded could be retrospectively labelled as correct. (5) Produce a Fix Specification: the minimum change to `score_routing.py` to either (a) add a `target_agent` column sourced from human-labelled ground truth, or (b) emit a WARNING when writing routing records without ground-truth labels rather than silently writing unusable records. Verdict: DIAGNOSIS_COMPLETE if the schema gap is confirmed with the specific line in `score_routing.py` that omits `target_agent` and a fix spec is produced; WARNING if the gap is structural (ground truth not capturable without human annotation).
**Finding**: [D24.2](findings/D24.2.md) — DIAGNOSIS_COMPLETE — Circular scoring: dispatched agent trivially passes "is known agent?" check at line 112, no ground-truth target_agent exists anywhere in pipeline

---

### D24.3: Does `detect_stale_registry_entries()` in `onboard_agent.py` incorrectly report `~/.claude/agents/*.md` entries as stale on Windows due to missing `expanduser()`?

**Status**: DONE
**Verdict**: DIAGNOSIS_COMPLETE
**Finding**: findings/D24.3.md
**Operational Mode**: diagnose
**Priority**: LOW
**Motivated by**: ROADMAP.md line 110 — "Agents using `~/.claude/agents/` relative paths will always appear stale on Windows unless `~` is expanded before the file existence check. The current code uses `Path(file_val).exists()` without home directory expansion." On Windows, `Path("~/.claude/agents/foo.md").exists()` returns False because `~` is not expanded by the `Path` constructor — `Path.expanduser()` must be called explicitly. The agent_registry.yml contains approximately 20 agents with `file: .claude/agents/` paths (relative), plus global agents with `file: ~/.claude/agents/` paths (tilde-prefixed).
**Hypothesis**: `detect_stale_registry_entries()` at line 106 calls `Path(file_val).exists()` without `.expanduser()`. On Windows, any registry entry with `file: ~/.claude/agents/foo.md` will return `False` from `.exists()` regardless of whether the file actually exists, causing those entries to appear in the stale list. The net effect: `masonry_status` and Kiln's fleet view will show false-positive stale entries for all global agents, potentially triggering unnecessary re-onboarding or incorrect health warnings.
**Method**: diagnose-analyst
**Success criterion**: (1) Read `masonry/scripts/onboard_agent.py:detect_stale_registry_entries()` (lines 85-109). (2) Confirm the exact call site: `Path(file_val).exists()` without `.expanduser()`. (3) Count how many entries in `masonry/agent_registry.yml` use tilde-prefixed paths (`file: ~/.claude/agents/...`) vs relative paths (`file: .claude/agents/...`). (4) Verify on Windows: `Path("~/.claude/agents/quantitative-analyst.md").exists()` should return False (demonstrating the bug), while `Path("~/.claude/agents/quantitative-analyst.md").expanduser().exists()` returns True if the file exists. (5) Produce a Fix Specification: change line 106 to `Path(file_val).expanduser().exists()`. Verdict: DIAGNOSIS_COMPLETE if the bug is confirmed at the specific line and the one-line fix is specified with the count of affected registry entries; HEALTHY if the code already calls expanduser (ROADMAP entry is stale/already fixed).

---

## Wave 25

**Generated from findings**: synthesis_wave24.md open issues #1-6 — routing ground-truth fix (D24.2 deferred), Phase 17 metric selective implementation (R24.1 WARNING), KarenSig prerequisite (V24.1 NOT_VALIDATED), MIPROv2 re-run with enriched data (synthesis open issue #4), next ResearchAgentSig candidate (synthesis open issue #5), verification of end-to-end CLI flag wiring (synthesis open issue #6).
**Mode transitions applied**: D24.2 DIAGNOSIS_COMPLETE (fix spec complete) → F25.1 Fix; R24.1 WARNING (selective Phase 17 implementation needed) → F25.2 Fix; V24.1 NOT_VALIDATED (KarenSig prerequisites) → F25.3 Fix; synthesis issues #4-6 → R25.1, R25.2, V25.1.

---

### F25.1: Implement D24.2 fix — add `request_text` capture to `masonry-subagent-tracker.js` and ground-truth-aware scoring to `score_routing.py`

**Status**: DONE
**Finding**: [F25.1](findings/F25.1.md) — FIX_APPLIED
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: D24.2 DIAGNOSIS_COMPLETE — `score_routing.py` awards 70pts by checking `agent in AGENT_CATEGORIES` (trivially true for any dispatched agent), not by comparing against a ground-truth target. D24.2 fix spec: (A) add `request_text` field to routing log entries in `masonry-subagent-tracker.js`; (B) replace the circular 70-point award in `score_routing.py` with 35pts partial credit when no ground-truth label exists, reserving 70pts for confirmed matches. This unblocks the routing training signal from producing meaningful optimization data.
**Hypothesis**: Adding `request_text` capture (from SubagentStart hook input) to routing log entries enables retrospective labelling. The scoring change (35pts partial credit vs 70pts confirmed) immediately makes routing records usable for training — 35 points is above the `min_training_score` threshold for routing records (65pts with 30pts downstream_success), providing a realistic lower bound on training quality while preserving the full 70pts incentive for future confirmed dispatch events.
**Method**: fix-implementer
**Success criterion**: (1) Read `masonry-subagent-tracker.js` — add `request_text: input.request || input.prompt || ""` to the routing log entry JSON. (2) Read `score_routing.py` and locate the `correct_agent_dispatched` scoring block (line ~112). (3) Replace the trivial check with: if `target_agent` field exists in the raw record AND matches `dispatched_agent`, award 70pts; else award 35pts (no ground truth). (4) Re-run `score_routing.py` on current `routing_log.jsonl` and confirm records now show `correct_agent_dispatched: 35` (partial credit) and include `request_text` in the enriched record. (5) Verify the syntax check passes for the JS change: `node --check masonry-subagent-tracker.js`. Verdict: FIX_APPLIED if both changes are implemented and routing records show partial credit scoring; PARTIAL if only one of the two changes is applied; FAILURE if the changes break existing routing log parsing.

---

### F25.2: Implement Phase 17 change #1 only — replace `len(evidence) > 100` with content signals in `build_metric()`

**Status**: DONE
**Finding**: [F25.2](findings/F25.2.md) — FIX_APPLIED
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: R24.1 WARNING — of the four planned Phase 17 metric changes, only content signal replacement (change #1) provides genuine gradient improvement. Severity validation adds noise (91.1% pass rate, partly redundant with verdict). Verdict-conditioned confidence actively penalizes 39.2% of findings (FAILURE class, mean conf=0.958). Score < 0.4 filter removes 17% of training data without proportional gain. The selective implementation strategy: ship change #1, drop the other three.
**Hypothesis**: Replacing `len(evidence) > 100` with `len(evidence) > 300 AND (has_numbers OR has_threshold_language)` in `build_metric()` will improve gradient signal for ~30% of records where the old binary check was satisfied by verbose filler (>100 chars but no quantitative content). The 16.9% of qualitative findings penalized by the new check represent genuinely weaker evidence; their reduced weight is a feature, not a bug. Net effect: the metric better distinguishes substantive findings from padding, improving MIPROv2's optimization trajectory.
**Method**: fix-implementer
**Success criterion**: (1) Read `masonry/src/dspy_pipeline/optimizer.py:build_metric()` (lines 23-68). (2) Locate the `evidence_quality` scoring block — currently `1.0 if len(example.evidence) > 100 else 0.5`. (3) Replace with: `score = 0.5; evidence = example.evidence or ""; if len(evidence) > 300 and (bool(re.search(r"\d+\.?\d*", evidence)) or any(w in evidence.lower() for w in ["threshold", "baseline", "%", "ms", "pts", "seconds"])): score = 1.0`. (4) Ensure `import re` is present at module top. (5) Run the metric on a sample of 5 known findings (2 with quantitative evidence, 2 without, 1 borderline) and report the score change per finding. Verdict: FIX_APPLIED if the content signal check is implemented and at least 1 finding changes score vs the old threshold; FAILURE if syntax error or the metric function raises an exception on the sample findings.

---

### F25.3: Define `KarenSig` in `signatures.py` and add karen-specific data loader to `training_extractor.py`

**Status**: DONE
**Finding**: [F25.3](findings/F25.3.md) — FIX_APPLIED
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: V24.1 NOT_VALIDATED — karen's 191 training records use ops-domain fields (`commit_subject`, `doc_files_written`, `reverted`, `files_changed`) with zero overlap to `ResearchAgentSig`'s (`verdict`, `severity`, `confidence`, `evidence`, `mitigation`). Attempting optimization with the wrong signature would produce a degenerate prompt. V24.1 identified 5 prerequisite steps; this question implements the first two (signature + data loader) as a precondition for the eventual karen optimization run.
**Hypothesis**: `KarenSig(dspy.Signature)` with input fields `commit_subject: str, files_changed: list[str], doc_context: str` and output fields `action: str, doc_updates: list[str], changelog_entry: str, quality_score: float` captures karen's actual task: given a commit, produce documentation updates and a changelog entry. The ops scorer already grades on `doc_files_written` and `reverted` — `quality_score` maps to `score / max_score` from the ops rubric. A karen-specific data loader reads `scored_all.jsonl` records where `agent == "karen"` and maps `commit_subject → input.commit_subject`, `score → output.quality_score`.
**Method**: fix-implementer
**Success criterion**: (1) Read `masonry/src/dspy_pipeline/signatures.py` in full — confirm `ResearchAgentSig` structure and add `KarenSig` class below it. (2) Read `masonry/scripts/run_optimization.py:load_training_data_from_scored_all()` (lines ~32-65) — understand the data loading pattern. (3) Add `load_karen_training_data(scored_all_path)` function that filters for `agent == "karen"` and returns `dspy.Example` objects with `commit_subject`, `files_changed`, `doc_context` as inputs and `quality_score` as output (computed as `score / 100.0`). (4) Verify at least 50 examples are returned from the 191 karen records (many should have `commit_subject` populated from ops scorer). (5) Add `KarenSig` import to `run_optimization.py` and add a `--signature karen` CLI option that routes to `KarenSig` and `load_karen_training_data()`. Verdict: FIX_APPLIED if `KarenSig` is defined with correct fields, the data loader returns ≥50 examples, and the CLI option is wired; PARTIAL if signature is defined but loader or CLI option is missing; FAILURE if the signature definition causes an import error.

---

### R25.1: Does re-running MIPROv2 for `quantitative-analyst` with D24.1-enriched training data improve verdict accuracy from the Wave 23 ~35-40% baseline?

**Status**: DONE
**Finding**: [R25.1](findings/R25.1.md) — WARNING
**Operational Mode**: research
**Priority**: HIGH
**Motivated by**: synthesis_wave24.md open issue #4 — "The D24.1 attribution fix restores question_text to training records. Re-run MIPROv2 with the enriched dataset to measure whether verdict accuracy improves from the ~35-40% baseline." D24.1 added `_AGENT_RE` extraction so finding files' `**Agent**:` field is now the primary attribution source. If enriched records also carry richer `question_text`, the demo bootstrapping in MIPROv2 should produce more contextually relevant few-shot examples, improving verdict prediction on novel questions.
**Hypothesis**: Before D24.1, quantitative-analyst training records had sparse question_text (derived only from qid_map markdown headers, not the full question body). After D24.1, if `extract_finding()` additionally captures `**Hypothesis**:` or `**Success criterion**:` from the finding file, records would carry richer context. A re-run using `--num-trials 3 --valset-size 20` (F24.1 CLI flags) would take ~15-30 minutes and produce a new `best_score` comparable to the Wave 23 baseline of 68.3%. If verdict accuracy (the sub-component driving the ceiling) improves by ≥3 points, it validates the enrichment hypothesis.
**Method**: research-analyst
**Success criterion**: (1) Read `masonry/src/dspy_pipeline/training_extractor.py:extract_finding()` — confirm what fields are now captured post-D24.1 compared to pre-D24.1. (2) Check whether question_text in training records has become richer (longer, more context) for masonry findings after D24.1. (3) Inspect `scored_all.jsonl` for 5 quantitative-analyst records — compare `question_text` field length pre- and post-D24.1 fix. (4) If question_text is not enriched by D24.1 (only agent attribution was restored), note that the re-run hypothesis may be premature — the enrichment benefit requires a separate change to capture question body text. Verdict: HEALTHY if question_text is measurably richer post-D24.1 and a short re-run is advisable; WARNING if D24.1 only fixed agent attribution without enriching question_text (re-run expected to produce similar scores); FAILURE if training records are still empty or malformed after D24.1.

---

### R25.2: Which Masonry agent (excluding `quantitative-analyst` and `karen`) has the most viable `scored_all.jsonl` records for the next `ResearchAgentSig` optimization run?

**Status**: DONE
**Finding**: [R25.2](findings/R25.2.md) — HEALTHY
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: synthesis_wave24.md open issue #5 — "Identify which agent (after quantitative-analyst) has the most scored_all.jsonl records with populated verdict/evidence/confidence fields for the next optimization run." With quantitative-analyst already optimized (Wave 23) and karen requiring KarenSig (V24.1), the next target should be the ResearchAgentSig-compatible agent with the strongest training corpus. The ROADMAP targets `research-analyst`, `diagnose-analyst`, and `fix-implementer` as secondary candidates.
**Hypothesis**: `research-analyst` has 28+ findings from this campaign and `diagnose-analyst` has 34+ findings. Both produce BL 2.0-format findings with `**Verdict**:`, `**Severity**:`, `**Confidence**:`, and `**Evidence**:` fields. The `fix-implementer` has 43+ findings but uses `FIX_APPLIED`/`FIX_FAILED` verdicts which may not match the `HEALTHY/FAILURE/WARNING/INCONCLUSIVE` vocabulary in `ResearchAgentSig`. The optimal next candidate is whichever agent has ≥5 records in `scored_all.jsonl` with all required ResearchAgentSig output fields populated and non-empty.
**Method**: research-analyst
**Success criterion**: (1) Read `masonry/training_data/scored_all.jsonl` — count records per agent excluding `quantitative-analyst` and `karen`. (2) For the top 3 agents by record count, sample 5 records each and check: are `verdict`, `evidence`, `confidence` fields populated and non-empty? (3) For `fix-implementer` specifically: do `FIX_APPLIED`/`FIX_FAILED` verdicts cause issues in `ResearchAgentSig`, or does the signature accept any string for the `verdict` field? (4) Rank candidates: agent name, total records, records with all 3 fields populated, and verdict vocabulary used. (5) Recommend the strongest candidate with a rationale. Verdict: HEALTHY if a clear next candidate is identified with ≥20 viable records; WARNING if top candidates have <20 records or verdict vocabulary mismatch requires schema changes; INCONCLUSIVE if `scored_all.jsonl` lacks records for any non-karen agent.

---

### V25.1: Are F24.1 CLI flags and D24.1 attribution fix correctly end-to-end for a fresh overnight MIPROv2 run on `quantitative-analyst`?

**Status**: DONE
**Finding**: [V25.1](findings/V25.1.md) — HEALTHY
**Operational Mode**: validate
**Priority**: LOW
**Motivated by**: synthesis_wave24.md open issue #6 — "With F24.1 CLI flags and D24.1 attribution fix both applied, schedule a fresh MIPROv2 run with --num-trials 10 to measure the compound effect on the metric ceiling." Before scheduling an 8-hour overnight run, validate that the two fixes are correctly wired end-to-end (no regressions, no TypeError on CLI flags, training data loads correctly with enriched attribution).
**Hypothesis**: F24.1 added `--num-trials` and `--valset-size` to `run_optimization.py` and wired them into `optimize_agent()`. D24.1 added `_AGENT_RE` extraction to `training_extractor.py`. A dry-run invocation (`python masonry/scripts/run_optimization.py quantitative-analyst --backend ollama --num-trials 1 --valset-size 5`) should complete the CLI parsing, load training data, instantiate MIPROv2 with the specified parameters, and either complete one trial or fail with a recoverable error. This is the minimal end-to-end gate before committing to a full overnight run.
**Method**: research-analyst
**Success criterion**: (1) Read `masonry/scripts/run_optimization.py` in full (post-F24.1) — confirm `--num-trials` and `--valset-size` are in argparse and forwarded to `optimize_agent()`. (2) Read `masonry/src/dspy_pipeline/optimizer.py:optimize_agent()` — confirm `num_trials` is passed to `MIPROv2(num_trials=...)` constructor or `compile()`. (3) Read `masonry/src/dspy_pipeline/training_extractor.py:build_dataset()` — confirm D24.1 `_AGENT_RE` regex is present and agent attribution is extracted from `**Agent**:` field. (4) Count quantitative-analyst records in `scored_all.jsonl` — confirm ≥50 records (sufficient for a valset of 5-20). (5) Verify that `configure_dspy(backend="ollama")` resolves to `qwen3:14b` (F23.1 fix). Verdict: HEALTHY if all five components are correctly wired and the dry-run prerequisites are satisfied; WARNING if one component has a gap that would cause a runtime error; FAILURE if multiple gaps exist that would abort the overnight run before Trial 1 completes.


---

## Wave 26

**Mode transitions applied**: R25.1 WARNING (question_text enrichment missing) -> F26.1 Fix; R25.2 HEALTHY (research-analyst ready) -> R26.1 Research; F25.1 follow-up (request_text available, target_agent labelling needed) -> D26.1 Diagnose; V25.1 HEALTHY (overnight run gate passed) -> V26.1 Validate; F25.3 homogeneity observation (all karen records quality_score=1.0) -> R26.2 Research.

---

### F26.1: Enrich question_text in training_extractor.py to capture the full hypothesis body from questions.md

**Status**: DONE
**Finding**: [F26.1](findings/F26.1.md) — FIX_APPLIED
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R25.1 WARNING -- D24.1 restored agent attribution but question_text is still captured only from the ### QID: <title> header line (_build_qid_to_agent_map line 47). The full Hypothesis paragraph (50-150 words) in each question block is not captured, so training records carry a 5-15 word title where a rich research context should appear. MIPROv2 demo bootstrapping relies on question_text to select contextually similar examples -- sparse titles degrade retrieval quality.
**Hypothesis**: _build_qid_to_agent_map() can be extended to also capture the Hypothesis field from each question block by adding a regex pattern for the Hypothesis section. If the hypothesis is present, concatenate title + hypothesis as question_text (capped at 500 chars). The existing question_text fallback (title-only) should remain for blocks without a Hypothesis field.
**Method**: fix-implementer
**Success criterion**: (1) Read masonry/src/dspy_pipeline/training_extractor.py:_build_qid_to_agent_map() in full -- understand the current regex-split-block approach. (2) Add hypothesis capture: pattern matching the Hypothesis field in each question block. (3) Set question_text = title + ' -- ' + hypothesis[:400] when hypothesis is present, else keep title-only fallback. (4) Verify: run _build_qid_to_agent_map on questions.md -- confirm >= 80% of entries have question_text > 30 chars. (5) Re-run score_all (or verify scored_all.jsonl can be regenerated with enriched question_text). Verdict: FIX_APPLIED if enrichment implemented and >= 80% entries have question_text > 30 chars; PARTIAL if hypothesis capture works but regeneration fails; FAILURE if the regex breaks question block parsing.

---

### D26.1: How can target_agent labels be automatically generated from request_text in routing_log.jsonl for retrospective labelling?

**Status**: DONE
**Finding**: [D26.1](findings/D26.1.md) — WARNING
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Motivated by**: F25.1 follow-up -- request_text is now captured in routing log start events (up to 500 chars), but all 5 records in scored_routing.jsonl have target_agent = "" (no ground-truth labels). Without target_agent, score_routing.py can only award 35 partial points. To reach full 70-point routing training quality, historical routing log entries need retrospective target_agent labels derived from their request_text content.
**Hypothesis**: The four-layer Mortar routing engine classifies requests to target agents. Running request_text values from routing_log.jsonl through the deterministic layer (slash-command detection, autopilot state, Mode field) + semantic layer (Ollama cosine similarity) could retrospectively predict the intended target_agent for each routing event. A script masonry/scripts/label_routing.py could process routing_log.jsonl in batch, invoke masonry/src/routing/router.py:route() for each request_text, and annotate the routing log with predicted target_agent fields.
**Method**: diagnose-analyst
**Success criterion**: (1) Read masonry/scripts/score_routing.py -- understand the target_agent scoring logic (35pts partial vs 70pts confirmed). (2) Read masonry/src/routing/router.py -- confirm whether a batch labelling script can call route() with a text string and get target_agent + confidence. (3) Read 10 sample routing_log.jsonl entries with non-empty request_text -- do they contain enough signal for classification? (4) Estimate what % of entries have request_text long enough (> 50 chars) for reliable classification. (5) Propose a concrete label_routing.py script spec with inputs, output format, confidence threshold. Verdict: DIAGNOSIS_COMPLETE if a viable labelling approach is identified; WARNING if request_text is too sparse for reliable classification; FAILURE if the routing engine cannot be called in batch mode.

---

### R26.1: Does running build_metric() on research-analyst records produce a higher baseline score than the quantitative-analyst baseline of ~68.3%?

**Status**: DONE
**Finding**: [R26.1](findings/R26.1.md) — HEALTHY
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: R25.2 HEALTHY -- research-analyst was identified as the next optimization candidate with 29 strictly viable records (verdict + evidence > 300 chars + confidence != None). quantitative-analyst achieved 68.3% in Wave 23. research-analyst has a better-balanced verdict distribution and longer evidence strings, which may produce a higher baseline metric score.
**Hypothesis**: research-analyst records have average evidence lengths of ~2500 chars vs quantitative-analyst ~1800 chars, so the evidence quality component (0.4 weight) should score higher. Combined with a balanced verdict distribution, the pre-optimization metric baseline could exceed 68.3%. Computing build_metric() on the 29 viable records gives a baseline estimate before scheduling an actual MIPROv2 run.
**Method**: research-analyst
**Success criterion**: (1) Read masonry/training_data/scored_all.jsonl -- pull the 29 research-analyst viable records. (2) Import build_metric() from optimizer.py. (3) For each record, compute metric(example=record_as_example, prediction=record_as_example) to measure the self-consistency score. (4) Compare mean score to the quantitative-analyst baseline of 0.683. (5) Check if confidence type (float vs str) causes issues in build_metric(). Verdict: HEALTHY if mean metric score >= 0.70; WARNING if mean is 0.60-0.70 (similar baseline, re-run may still be worthwhile); FAILURE if mean < 0.60 or type errors occur.

---

### R26.2: Are the 191 karen training records genuinely all quality_score=1.0, and are there recoverable negative examples from git history?

**Status**: DONE
**Finding**: [R26.2](findings/R26.2.md) — WARNING
**Operational Mode**: research
**Priority**: LOW
**Motivated by**: F25.3 finding note -- all 191 karen records have score=100 and reverted=False, producing quality_score="1.0" for every example. This means build_karen_metric()'s quality_score_proximity component (0.5 weight) is trivially maximized for every record, providing no gradient on the most important metric component.
**Hypothesis**: The karen corpus was assembled from post-Wave commit events where the ops scorer always awards full score. Reverted commits in the masonry git history would produce score < 100 and reverted=True records if run through the ops scorer. Even 5 negative examples would break the homogeneity and make quality_score_proximity a meaningful metric component.
**Method**: research-analyst
**Success criterion**: (1) Run git log --oneline --grep=revert (case-insensitive) restricted to masonry/ -- count genuine revert commits. (2) Check CHANGELOG.md for any entries with reverted action from karen. (3) If >= 1 revert commit exists, check whether masonry/scripts/score_ops.py (or equivalent) could produce a score < 100 record for that commit. (4) Estimate how many negative examples are realistically recoverable. Verdict: HEALTHY if >= 5 revert commits found that could produce negative examples; WARNING if 1-4 found; INCONCLUSIVE if no revert commits exist in masonry scope.

---

### V26.1: Does metric_fn=build_karen_metric() in optimize_agent() correctly score KarenSig predictions across edge cases without exception?

**Status**: DONE
**Finding**: [V26.1](findings/V26.1.md) — HEALTHY
**Operational Mode**: validate
**Priority**: MEDIUM
**Motivated by**: F25.3 FIX_APPLIED -- metric_fn parameter was added to optimize_agent() and build_karen_metric() wired in for the karen signature. However, the integration was not tested against actual KarenSig predictions. build_karen_metric() parses quality_score using regex -- if the prediction returns a non-numeric string (e.g. "N/A" or empty), the fallback fires. This validation checks that all three metric components handle edge cases without exception.
**Hypothesis**: build_karen_metric() is defensively written -- each component is wrapped in try/except. A synthetic KarenSig prediction with edge-case values (empty strings, "N/A", None) should produce a score in [0, 1] without exception. The perfect prediction case should score >= 0.9 and the all-empty prediction should score <= 0.25.
**Method**: research-analyst
**Success criterion**: (1) Import build_karen_metric from optimizer.py and KarenSig from signatures.py. (2) Create mock DSPy Example and Prediction objects with KarenSig fields. (3) Test 4 edge cases: (a) perfect prediction (exact quality_score match, correct action, non-empty changelog), (b) wrong action + empty changelog, (c) quality_score = "N/A" (non-numeric), (d) all fields empty. (4) For each case, call metric(example, prediction) and confirm result is float in [0.0, 1.0] with no exception. (5) Verify perfect prediction scores >= 0.9 and all-empty prediction scores <= 0.25. Verdict: HEALTHY if all 4 edge cases produce valid float scores without exception; WARNING if one edge case throws but is caught; FAILURE if exception propagates or perfect prediction scores < 0.8.


---

## Wave 27

**Mode transitions applied**: V26.1 HEALTHY (all-empty floor = 0.70, not calibrated) -> F27.1 Fix; R26.1 HEALTHY (research-analyst optimization recommended) -> V27.1 Validate; R26.2 WARNING (karen needs synthetic negatives) -> F27.2 Fix; F26.1 FIX_APPLIED (enrichment done, scored_all needs regen) -> R27.1 Research; D26.1 WARNING (routing labelling blocked) -> R27.2 Research.

---

### F27.1: Fix build_karen_metric() quality_score_proximity fallback to prevent all-empty predictions scoring 0.5

**Status**: DONE
**Finding**: findings/F27.1.md
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: V26.1 HEALTHY finding -- the all-empty prediction case scores 0.70 because the `or "1.0"` fallback in quality_score_proximity treats empty string as quality_score=1.0 (perfect match). The defensive fallback is too lenient: it should award partial credit (0.25) when quality_score cannot be parsed, not trigger the proximity bonus.
**Hypothesis**: Separate the parse-failure path from the proximity check in quality_score_proximity: when prediction quality_score cannot be parsed to a float (empty or non-numeric), award 0.25 partial credit and skip the proximity check. When parseable, apply existing proximity logic. This makes the all-empty case score ~0.45 (0.25 quality + 0.2 skipped-action) instead of 0.70.
**Method**: fix-implementer
**Success criterion**: (1) Read masonry/src/dspy_pipeline/optimizer.py:build_karen_metric() quality_score_proximity block. (2) Modify so that when regex fails on pred_qs_raw (non-numeric/empty), score += 0.25 and skip proximity check. (3) When prediction IS parseable, apply proximity check as before. (4) Verify: all-empty prediction scores <= 0.50, N/A case scores <= 0.65, perfect prediction scores >= 0.9. Verdict: FIX_APPLIED if all-empty <= 0.50 and perfect >= 0.9; PARTIAL if fix applied but one test fails; FAILURE if perfect score drops below 0.8.

---

### F27.2: Add 5 synthetic negative examples to karen training corpus to break quality_score homogeneity

**Status**: DONE
**Finding**: findings/F27.2.md
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: R26.2 WARNING -- all 191 karen records have quality_score=1.0. The build_karen_metric() quality_score_proximity component (0.5 weight) has zero gradient. Adding 5-10 synthetic negative examples (quality_score=0.0, action=reverted) would break homogeneity and give MIPROv2 calibration signal.
**Hypothesis**: 5 synthetic training examples can be constructed using the single genuine revert commit (1814c08) as a template. Written directly to masonry/training_data/scored_all.jsonl with score=0 and agent=karen. After appending, load_karen_training_data() should return 196 examples with quality_score values including 0.0.
**Method**: fix-implementer
**Success criterion**: (1) Read masonry/training_data/scored_all.jsonl -- understand karen record schema. (2) Construct 5 synthetic records with agent=karen, score=0, reverted=True, action=reverted, quality_score=0.0. (3) Vary commit_subject across 5 different plausible revert scenarios. (4) Append to scored_all.jsonl. (5) Verify: load_karen_training_data() returns 196 examples with quality_score values including 0.0. Verdict: FIX_APPLIED if 5 records appended and loader returns them; PARTIAL if appended but schema mismatch; FAILURE if records corrupt the jsonl file.

---

### R27.1: After F26.1 hypothesis enrichment, how much longer are research-analyst question_text fields vs current scored_all.jsonl values?

**Status**: DONE
**Finding**: findings/R27.1.md
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: F26.1 FIX_APPLIED -- _build_qid_to_agent_map() now enriches question_text with the Hypothesis paragraph (up to 500 chars). But existing scored_all.jsonl records still have the old short question_text. To get the benefit of F26.1, scored_all.jsonl must be regenerated. This research question measures the gap between old and new question_text lengths.
**Hypothesis**: Current scored_all.jsonl research-analyst records have question_text of 5-30 chars (just the title). After F26.1, the same QIDs would map to 200-500 chars (title + hypothesis). The gap is significant enough to meaningfully improve MIPROv2 demo co-variate selection.
**Method**: research-analyst
**Success criterion**: (1) Read 5 research-analyst records from scored_all.jsonl -- measure current question_text field lengths. (2) Run _build_qid_to_agent_map() on questions.md and look up the same QIDs -- compare enriched lengths. (3) Compute median length increase. (4) Confirm QIDs in scored_all.jsonl can be mapped to question blocks in questions.md. (5) Estimate how many of 37 research-analyst records can be enriched. Verdict: HEALTHY if median question_text increases by >= 100 chars; WARNING if increase < 100 chars or < 50% of records can be enriched; INCONCLUSIVE if QID mapping fails for most records.

---

### V27.1: Validate end-to-end pipeline for a research-analyst MIPROv2 run before scheduling the actual run.

**Status**: DONE
**Finding**: findings/V27.1.md
**Operational Mode**: validate
**Priority**: HIGH
**Motivated by**: R26.1 HEALTHY -- research-analyst is the recommended next optimization target (expected MIPROv2 score 0.73-0.87). Before scheduling a 30-60 minute run, validate that all pipeline components are correctly wired: data loading, ResearchAgentSig field alignment, build_metric(), and optimize_agent().
**Hypothesis**: run_optimization.py with --signature research routes to: load_training_data_from_scored_all -> ResearchAgentSig -> build_metric(ResearchAgentSig) -> optimize_agent(metric_fn=None). All components are independently verified -- this validates the assembled pipeline.
**Method**: research-analyst
**Success criterion**: (1) Run load_training_data_from_scored_all(scored_all_path, 'research-analyst') -- confirm 29-37 records with correct field names. (2) Verify ResearchAgentSig.input_fields and output_fields match loaded record keys. (3) Call build_metric(ResearchAgentSig) and score 3 sample records -- confirm scores in [0.6, 1.0]. (4) Confirm optimize_agent() has metric_fn=None default (fallback to build_metric). (5) Verify --signature research routes to metric_fn=None. Verdict: HEALTHY if all 5 checks pass; WARNING if one reveals a non-fatal gap; FAILURE if a gap would abort the optimization run.

---

### R27.2: Can masonry-subagent-tracker.js be modified to populate request_text for autonomous research loop agent spawns?

**Status**: DONE
**Finding**: findings/R27.2.md
**Operational Mode**: research
**Priority**: LOW
**Motivated by**: D26.1 WARNING -- routing labelling is blocked because autonomous research loop agent spawns produce empty request_text. The hook reads input.prompt || input.description, but these are empty for programmatic Agent tool calls.
**Hypothesis**: The SubagentStart hook input object may have additional fields (task, description, or the raw tool input) that could be read. Alternatively, if Agent tool calls pass input.description for some spawn patterns, a simple hook extension could capture it. A 1-3 line change to masonry-subagent-tracker.js could populate request_text for >= 50% of future spawns.
**Method**: research-analyst
**Success criterion**: (1) Read masonry/src/hooks/masonry-subagent-tracker.js lines 185-215 -- identify all input fields currently read. (2) Check what fields are available in SubagentStart hook input for Agent tool calls (docs or existing log inspection). (3) If input.task or additional fields are available, assess whether adding them to the hook read captures request context. (4) Estimate: if modified, what % of future routing_log entries would have non-empty request_text? (5) Assess complexity (1-line vs larger refactor). Verdict: HEALTHY if a simple (1-3 line) change could populate request_text for >= 50% of future spawns; WARNING if fix requires structural changes; INCONCLUSIVE if SubagentStart input does not expose enough context.

---

## Wave 28

**Generated from findings**: F27.1, F27.2, R27.1, V27.1, R27.2
**Mode transitions applied**: R27.1 HEALTHY (regen scored_all.jsonl before MIPROv2) -> F28.1 Fix; V27.1 HEALTHY (pipeline validated, run is ready) -> F28.2 Fix; F27.1+F27.2 FIX_APPLIED (karen corpus now calibrated) -> V28.1 Validate; R27.2 WARNING (PreToolUse:Agent hook not a 1-3 line change) -> F28.3 Fix; F27.1 FIX_APPLIED (metric changed) -> D28.1 Diagnose drift check.

---

### F28.1: Regenerate scored_all.jsonl by running score_all.py so research-analyst MIPROv2 uses enriched question_text from F26.1

**Status**: DONE
**Finding**: findings/F28.1.md
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R27.1 HEALTHY -- F26.1 enrichment adds median +408 chars to research-analyst question_text, but existing scored_all.jsonl still has short pre-enrichment values. R27.1 recommends re-running score_all.py before the MIPROv2 run. Without this, 81% of research-analyst records will have truncated question_text and MIPROv2 demo selection will be degraded.
**Hypothesis**: masonry/scripts/score_all.py (or equivalent) re-extracts all records from questions.md + findings/ and writes a fresh scored_all.jsonl. Running it now will incorporate the F26.1 _build_qid_to_agent_map() enrichment, raising median research-analyst question_text from ~87 chars to ~500 chars across the 30 mappable records.
**Method**: fix-implementer
**Success criterion**: (1) Locate score_all.py -- confirm it exists at masonry/scripts/score_all.py or equivalent path. (2) If it exists, run it and confirm no errors. (3) After run, sample 5 research-analyst records from the new scored_all.jsonl -- confirm question_text length >= 200 chars for mappable QIDs. (4) Confirm total record count is still >= 196 (karen synthetic negatives not lost). (5) Confirm karen records still include quality_score values of 0.0 (F27.2 negatives preserved). Verdict: FIX_APPLIED if score_all.py exists and produces enriched output with all negatives intact; FAILURE if score_all.py does not exist or erases F27.2 synthetic records; PARTIAL if script runs but enrichment not reflected in output.

---

### F28.2: Execute the research-analyst MIPROv2 optimization run and record the resulting score

**Status**: DONE
**Finding**: findings/F28.2.md
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: V27.1 HEALTHY -- all pipeline components validated (37 records, PERFECT field alignment, metric_fn=None confirmed, CLI routing correct). The run has been deferred pending F28.1 scored_all.jsonl regeneration. This fix executes the actual optimization and stores the resulting prompt JSON.
**Hypothesis**: Running run_optimization.py with --signature research will complete in 30-60 minutes and produce an optimized prompt stored in masonry/optimized_prompts/research-analyst.json. The expected MIPROv2 self-consistency score is 0.73-0.87 based on R26.1 projection. The run should complete without error given V27.1 validation.
**Method**: fix-implementer
**Success criterion**: (1) Confirm F28.1 is DONE (scored_all.jsonl regenerated) before starting. (2) Run: python masonry/src/dspy_pipeline/run_optimization.py --signature research. (3) Confirm the run completes without exception. (4) Verify masonry/optimized_prompts/research-analyst.json is written with non-empty instructions field. (5) Record the final MIPROv2 self-consistency score from stdout. (6) Confirm score >= 0.65 (minimum viable threshold). Verdict: FIX_APPLIED if run completes and score >= 0.65; WARNING if score is 0.50-0.65 (marginal); FAILURE if run errors out or score < 0.50.

---

### V28.1: Validate that karen MIPROv2 optimization is viable with 196 records and 2.6% negative rate before scheduling the run

**Status**: DONE
**Finding**: findings/V28.1.md
**Operational Mode**: validate
**Priority**: MEDIUM
**Motivated by**: F27.1 FIX_APPLIED (all-empty floor corrected to 0.45) and F27.2 FIX_APPLIED (5 synthetic negatives added, corpus now 196 records). Karen corpus is now calibrated but 5/196 = 2.6% negative rate is low. Before committing a 30-60 minute optimization run, validate that build_karen_metric() produces useful gradient signal across the full corpus and that the 2.6% negative rate is sufficient for MIPROv2 calibration.
**Hypothesis**: MIPROv2 requires diverse metric scores to select useful few-shot demonstrations. With 191 records scoring ~0.9 and 5 records scoring ~0.2, the score distribution has a bimodal shape. DSPy's MIPROv2 should be able to select the 5 negatives as contrastive examples -- they will be selected with high probability given their distinctive low scores. The 2.6% rate is low but sufficient because MIPROv2 selects ~10-20 demos and the negatives will be overrepresented.
**Method**: research-analyst
**Success criterion**: (1) Load karen training data -- confirm 196 records with quality_score distribution including both 0.0 and 1.0 values. (2) Call build_karen_metric() on the 5 synthetic negative records -- confirm scores <= 0.45. (3) Call build_karen_metric() on 5 positive records -- confirm scores >= 0.85. (4) Compute the score range (max - min across all 196) -- must be >= 0.4 to give MIPROv2 calibration signal. (5) Confirm no exception raised across full corpus pass. Verdict: HEALTHY if score range >= 0.4 and negatives score <= 0.45; WARNING if range is 0.25-0.40 (borderline); FAILURE if range < 0.25 or any negative scores >= 0.70.

---

### F28.3: Implement masonry-preagent-tracker.js PreToolUse:Agent hook to capture request_text for Agent tool spawns

**Status**: DONE
**Finding**: findings/F28.3.md
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: R27.2 WARNING -- SubagentStart event does not expose the Agent tool's prompt parameter. All 66 start entries have empty request_text, blocking routing label extraction. R27.2 confirmed PreToolUse:Agent is the correct fix (new hook script + settings.json registration) and that it is not a 1-3 line change.
**Hypothesis**: A new hook script masonry/src/hooks/masonry-preagent-tracker.js registered under PreToolUse:Agent can read input.prompt (the Agent tool's prompt parameter) before the subagent starts. It should write a transient record to a temp file (e.g., .masonry/pending_agent_prompt.json) keyed by a UUID, which masonry-subagent-tracker.js then reads on SubagentStart to populate request_text. This two-part approach works because PreToolUse fires synchronously before SubagentStart.
**Method**: fix-implementer
**Success criterion**: (1) Write masonry/src/hooks/masonry-preagent-tracker.js -- on PreToolUse:Agent event, read input.prompt (first 300 chars), write to .masonry/pending_agent_prompts/{hookEventId}.json. (2) Modify masonry-subagent-tracker.js -- on SubagentStart, check for pending_agent_prompts/{parentHookEventId}.json and populate request_text if found, then delete the temp file. (3) Register masonry-preagent-tracker.js in .claude/settings.json under hooks.PreToolUse with matcher "Agent". (4) Verify settings.json is valid JSON after edit. (5) In next routing_log entry for an Agent tool spawn, confirm request_text is non-empty. Verdict: FIX_APPLIED if hook fires and at least one future routing_log Agent entry has non-empty request_text; PARTIAL if hook is registered but temp file handoff fails; FAILURE if settings.json is corrupted or hook throws on startup.

---

### D28.1: Has the F27.1 metric change caused any currently-deployed karen optimized prompts to become stale or mis-calibrated?

**Status**: DONE
**Finding**: findings/D28.1.md
**Operational Mode**: diagnose
**Priority**: LOW
**Motivated by**: F27.1 FIX_APPLIED -- build_karen_metric() quality_score_proximity fallback was changed (all-empty now scores 0.25 instead of 0.70). If a karen optimized prompt exists in masonry/optimized_prompts/karen.json, it was selected using the old metric. The selected few-shot demonstrations may now score differently under the new metric, meaning the optimized prompt may be suboptimal or its reported score is stale.
**Hypothesis**: masonry/optimized_prompts/karen.json either does not exist (karen has never been optimized, so no stale prompt problem) or exists but was generated before F27.1. If it exists, running the drift detector against the current metric should report a score delta >= 0.1, triggering a re-optimization recommendation.
**Method**: diagnose-analyst
**Success criterion**: (1) Check if masonry/optimized_prompts/karen.json exists. (2) If it does not exist, verdict is HEALTHY (no stale prompt). (3) If it exists, read the stored score field. (4) Re-score the stored few-shot demonstrations using the current build_karen_metric() -- compare to stored score. (5) If delta >= 0.1, the prompt is stale and needs re-optimization. (6) Check drift_detector.py -- confirm it can be run against karen signature to detect this automatically. Verdict: HEALTHY if no karen.json exists or score delta < 0.05; WARNING if delta is 0.05-0.10; FAILURE if delta >= 0.10 (stale prompt deployed).

---

## Wave 29

**Generated from findings**: F28.1, F28.2, F28.3, D28.1, V28.1
**Mode transitions applied**: F28.1 PARTIAL (root cause #1: score_findings.py missing _build_qid_to_agent_map()) → F29.1 Fix; F28.1 PARTIAL (root cause #2: score_ops_agents.py overwrites synthetic negatives) → F29.2 Fix; F28.2 BLOCKED (Ollama offline) → F29.3 Fix (anthropic backend path); F28.3 FIX_APPLIED → V29.1 Validate; D28.1 HEALTHY + V28.1 HEALTHY (karen MIPROv2 cleared, precondition: re-append synthetics) → F29.4 Fix.

---

### F29.1: Wire _build_qid_to_agent_map() into score_findings.py so enriched question_text reaches scored_all.jsonl

**Status**: DONE
**Finding**: findings/F29.1.md
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: F28.1 PARTIAL -- root cause #1: score_findings.py extracts question_text from finding file header subtitles (median 88 chars) and never reads questions.md or calls _build_qid_to_agent_map(). F26.1 enrichment (500-char hypothesis text) only flows through training_extractor.py, a separate path not touched by score_all_agents.py. The research-analyst MIPROv2 run will train on degraded 88-char question_text until this is fixed.
**Hypothesis**: score_findings.py can be modified to call _build_qid_to_agent_map(questions_md_path) and look up the extracted QID in the returned map; if a match is found, replace the subtitle-extracted question_text with the enriched hypothesis text (up to 500 chars). This is a targeted change at the single point in score_findings.py where question_text is assigned. After the fix, running score_all_agents.py should produce research-analyst records with median question_text >= 200 chars.
**Method**: fix-implementer
**Success criterion**: (1) Read score_findings.py -- locate the exact line where question_text is assigned (currently from _RE_QUESTION regex fallback to header subtitle). (2) Import or inline _build_qid_to_agent_map() in score_findings.py (or call it from a shared utility). (3) Modify question_text assignment: if the QID maps to a questions.md hypothesis block, use that text (capped at 500 chars); otherwise keep the existing header-subtitle fallback. (4) Run score_all_agents.py and sample 5 research-analyst records -- confirm median question_text >= 200 chars. (5) Confirm total records still >= 589 and no records have empty question_text that previously had text. Verdict: FIX_APPLIED if median question_text >= 200 chars after re-run; PARTIAL if some records enriched but median still < 200; FAILURE if score_findings.py errors or record count drops below 500.

---

### F29.2: Create a stable scored_synthetic.jsonl that score_all_agents.py merges so synthetic negatives survive reruns

**Status**: DONE
**Finding**: findings/F29.2.md
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: F28.1 PARTIAL -- root cause #2: score_ops_agents.py regenerates scored_ops_agents.jsonl from git log on every run, overwriting any manually appended synthetic negatives. The 5 karen synthetic negatives added in F27.2 are lost whenever score_all_agents.py runs. V28.1 confirmed this is a precondition blocker for karen MIPROv2: without negatives, score range = 0.0 and MIPROv2 has zero gradient signal.
**Hypothesis**: Creating a new file masonry/training_data/scored_synthetic.jsonl as a stable, committed store for synthetic records, then modifying score_all_agents.py to merge it alongside the four scorer outputs, will permanently preserve synthetic negatives across all future reruns. The 5 F27.2 karen negatives should be written to this file directly. After the fix, score_all_agents.py should produce a scored_all.jsonl with 5 score=0 karen records regardless of how many times it is re-run.
**Method**: fix-implementer
**Success criterion**: (1) Create masonry/training_data/scored_synthetic.jsonl and write the 5 F27.2 synthetic karen negative records into it (recover from git show 56eff3b:masonry/training_data/scored_all.jsonl | tail -5). (2) Modify score_all_agents.py to load scored_synthetic.jsonl and concatenate it onto the merged output after the four scorer outputs. (3) Run score_all_agents.py -- confirm output contains exactly 5 records with agent=karen, score=0, source=synthetic_negative. (4) Run score_all_agents.py a second time -- confirm the 5 synthetic records are still present (idempotency check). (5) Confirm total record count is >= 594 (589 pre-fix + 5 synthetics). Verdict: FIX_APPLIED if synthetics persist across two consecutive runs; PARTIAL if records appear on first run but are deduplicated or lost on second; FAILURE if score_all_agents.py errors or synthetics are absent from output.

---

### F29.3: Validate --backend anthropic path and execute research-analyst MIPROv2 run without Ollama dependency

**Status**: DONE
**Finding**: findings/F29.3.md
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: F28.2 BLOCKED -- Ollama at 192.168.50.62:11434 is unreachable (connection timeout). The research-analyst MIPROv2 run has been deferred since Wave 27. F28.2 notes that run_optimization.py has a --backend anthropic flag that would use the Claude API instead of Ollama, but this path was not validated by V27.1 (which only checked --backend ollama routing). This fix validates the anthropic backend path and, if clear, executes the run -- conditional on F29.1 enrichment being applied first.
**Hypothesis**: run_optimization.py --backend anthropic routes to a different teacher LLM instantiation but uses the same ResearchAgentSig, build_metric(), and scored_all.jsonl loading path validated by V27.1. The anthropic backend should complete the optimization run without requiring Ollama. Preconditions: (1) F29.1 must be DONE (enriched question_text >= 200 chars), (2) scored_all.jsonl must have >= 37 research-analyst records.
**Method**: fix-implementer
**Success criterion**: (1) Check whether F29.1 is DONE before proceeding -- if not, return BLOCKED with note. (2) Read run_optimization.py --backend anthropic code path -- confirm it does not hard-require Ollama for any step. (3) Confirm ANTHROPIC_API_KEY is set in environment (or Claude Code native auth is available). (4) Run: python masonry/scripts/run_optimization.py research-analyst --backend anthropic --num-trials 10 --valset-size 25 --signature research. (5) Confirm masonry/optimized_prompts/research-analyst.json is written with non-empty instructions field and final score >= 0.65. Verdict: FIX_APPLIED if run completes and score >= 0.65; WARNING if score is 0.50-0.65 (marginal); BLOCKED if F29.1 is not yet DONE or API key is unavailable; FAILURE if run errors out or score < 0.50.

---

### V29.1: Verify that masonry-preagent-tracker.js produces non-empty request_text in routing_log.jsonl for real Agent tool spawns in the active session

**Status**: DONE
**Finding**: findings/V29.1.md
**Operational Mode**: validate
**Priority**: MEDIUM
**Motivated by**: F28.3 FIX_APPLIED -- the hook was written, registered in settings.json, and passed a smoke test with a synthetic payload. However, the smoke test used a manually constructed JSON string piped to node, not an actual Agent tool call in a live Claude Code session. The smoke-test pre_spawn entry in routing_log.jsonl was produced by a manual invocation. This validation confirms the hook fires correctly during real campaign execution.
**Hypothesis**: When the masonry research loop spawns an agent (e.g., quantitative-analyst, diagnose-analyst) via the Agent tool, the PreToolUse:Agent hook fires in the parent session and writes a pre_spawn entry to routing_log.jsonl with non-empty request_text. The entry will appear immediately before the corresponding SubagentStart entry (within a few milliseconds). At least one such entry should already exist in routing_log.jsonl from this or recent sessions if any agents were spawned after F28.3 was applied.
**Method**: research-analyst
**Success criterion**: (1) Read routing_log.jsonl -- filter for entries with event=pre_spawn written after the F28.3 fix timestamp (2026-03-23T13:51:16Z). (2) Confirm at least one pre_spawn entry has non-empty request_text that was NOT the smoke-test string ("Act as the research-analyst agent. Question: Is the routing layer working?"). (3) Confirm the request_text value is the actual prompt passed to a real Agent tool call (>= 20 chars, references an agent or question). (4) Cross-reference: confirm a SubagentStart entry with a nearby timestamp exists for the same session_id. (5) Confirm no pre_spawn entries have empty request_text (which would indicate the hook is firing but failing to read input.prompt). Verdict: HEALTHY if >= 1 real pre_spawn entry with non-empty request_text; WARNING if only the smoke-test entry exists (no real spawns captured yet); FAILURE if pre_spawn entries exist but all have empty request_text.

---

### F29.4: Re-append synthetic karen negatives to scored_all.jsonl and execute karen MIPROv2 optimization run

**Status**: DONE
**Finding**: findings/F29.4.md
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: D28.1 HEALTHY (no stale karen prompt, safe to optimize) and V28.1 HEALTHY (score range 0.75 with 5 negatives, MIPROv2 viable) -- both blockers cleared. The only remaining precondition is that the 5 synthetic negatives were wiped from scored_all.jsonl by the F28.1 run. V28.1 recommends: git show 56eff3b:masonry/training_data/scored_all.jsonl | tail -5 >> masonry/training_data/scored_all.jsonl before running. F29.2 provides a permanent fix for future runs; this question handles the immediate pre-run state.
**Hypothesis**: Re-appending the 5 synthetic negatives from git commit 56eff3b restores the 196-record corpus with score range 0.75. Running karen MIPROv2 with --num-trials 10 --valset-size 25 --signature karen should complete in 30-60 minutes and produce masonry/optimized_prompts/karen.json. Expected score: 0.70-0.85 based on the validated gradient signal.
**Method**: fix-implementer
**Success criterion**: (1) Confirm F29.2 is DONE (stable scored_synthetic.jsonl exists) OR manually re-append synthetics from commit 56eff3b if F29.2 is not yet applied. (2) Verify scored_all.jsonl contains exactly 5 records with agent=karen, score=0. (3) Check Ollama at 192.168.50.62:11434 -- if online use --backend ollama; if offline use --backend anthropic. (4) Run: python masonry/scripts/run_optimization.py karen --backend [ollama|anthropic] --num-trials 10 --valset-size 25 --signature karen. (5) Confirm masonry/optimized_prompts/karen.json written with non-empty instructions and final score >= 0.65. Verdict: FIX_APPLIED if run completes and score >= 0.65; WARNING if score is 0.50-0.65; BLOCKED if synthetics cannot be recovered or Ollama offline and anthropic key unavailable; FAILURE if run errors or score < 0.50.

## Fix Status
Updated: 2026-03-23 — BLOCKED by fix-implementer. See masonry/findings/F29.4.md.
All data preconditions confirmed: scored_all.jsonl has 602 records with 5 karen negatives (score=0).
BLOCKED on LLM backends: Ollama unreachable (192.168.50.62:11434 timeout), ANTHROPIC_API_KEY not set.
To unblock: set ANTHROPIC_API_KEY and re-run `python masonry/scripts/run_optimization.py karen --backend anthropic --num-trials 10 --valset-size 25 --signature karen`.

---

## Wave 30

**Generated from findings**: F29.1, F29.2, F29.3, F29.4, V29.1
**Mode transitions applied**: F29.1 FIX_APPLIED -> V30.1 Validate; F29.2 FIX_APPLIED -> V30.1 Validate (merged with F29.1, same corpus gate); F29.3 BLOCKED (external auth, no code fix needed) -> F30.2 Fix (combined with F29.4, user-action preconditioned); F29.4 BLOCKED (same backend blocker) -> F30.2 Fix (merged); V29.1 WARNING (spec-writer slot-miss ~17%, CWD mismatch) -> F30.1 Fix + R30.1 Research (collision side-finding). Additional questions added from synthesis_wave29.md code audit: V30.5 (Mortar injection path gap), F30.5 (optimize_all signature dispatch).

---

### V30.5: Does any code in the Masonry routing or hook layer actually read from optimized_prompts/ and inject those instructions when spawning a specialist agent?

**Status**: DONE
**Finding**: findings/V30.5.md
**Operational Mode**: validate
**Priority**: CRITICAL
**Motivated by**: synthesis_wave29.md open issue #5 (post-optimization validation) and a code audit finding from Wave 30 prep: grepping the entire `masonry/src/` directory for `optimized_prompts`, `inject.*prompt`, or `load.*optimized` returns zero matches in any hook or routing file. The CLAUDE.md project instructions claim "Mortar injects optimized prompts on specialist invocation automatically" but this mechanism has never been validated. `optimized_prompts/` is only read by `mcp_server.py:masonry_optimization_status` (status check) and `run_r23_1.py` (legacy). No routing code, no hook, no Mortar agent file reads from this directory. If the injection path does not exist, running MIPROv2 and producing `optimized_prompts/research-analyst.json` will have zero effect on agent behavior — a critical gap to resolve before the first optimization run.
**Hypothesis**: The Mortar injection path for optimized prompts is not yet implemented in code. The claim in CLAUDE.md describes intended architecture but the concrete mechanism — reading `{agent}.json` from `optimized_prompts/` and prepending the stored `instructions` to the agent's system prompt — does not exist in any hook, router, or MCP server handler. The optimized JSON files are produced but never consumed. If this hypothesis is correct, Wave 30 must build the injection path before investing compute in MIPROv2 runs.
**Method**: research-analyst
**Success criterion**: (1) Grep the full `masonry/src/` directory tree for any reference to `optimized_prompts`, `inject`, `instructions` with context of loading a JSON file and prepending to a prompt. (2) Read `masonry/src/routing/router.py` — check whether `route()` or `dispatch()` loads an optimized JSON. (3) Read `masonry-register.js` and `masonry-session-start.js` — check whether either hook reads from `optimized_prompts/` before composing agent context. (4) Read the mortar.md agent file — check whether Mortar is instructed to read `optimized_prompts/{agent}.json` and inject the `instructions` field into the agent prompt it constructs. (5) Check whether `run_optimization.py`'s `optimize_agent()` stores anything in the format that would be read by a downstream consumer (i.e., what fields does the saved JSON contain?). Verdict: HEALTHY if a complete injection path exists (code reads the JSON and uses it); WARNING if the path exists in documentation/agent instructions but not in code (meaning injection only works if Mortar happens to follow its instructions); FAILURE if no injection path exists anywhere.

---


---

### F30.1: Fix CWD mismatch between masonry-preagent-tracker.js and masonry-subagent-tracker.js that causes spec-writer slot misses

**Status**: DONE
**Finding**: findings/F30.1.md
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: V29.1 WARNING -- spec-writer slot written at 14:08:32.839Z (rt_len=504) but the corresponding SubagentStart start event at 14:08:32.843Z had rt_len=0, slot file unconsumed. Root cause identified: masonry-preagent-tracker.js derives the pending dir from process.cwd() at PreToolUse time (src/hooks line 53), while masonry-subagent-tracker.js derives it from input.cwd from the SubagentStart payload (src/hooks line 155, then builds pendingDir at line 196). When spec-writer or any agent spawns in a CWD that differs from the parent session CWD, the two paths diverge and the slot lookup returns nothing.
**Hypothesis**: Aligning the pending dir derivation in both hooks to use the same canonical base -- preferably resolved from __dirname relative to masonry/src/hooks/ (a stable absolute path independent of session CWD) or an env var MASONRY_ROOT -- will eliminate this class of miss. The slot write, 10-second TTL, and consume-on-read mechanics are otherwise correct and need no changes. After the fix, spec-writer spawns will produce non-empty request_text in routing_log.jsonl start events at the same rate as fix-implementer spawns (currently 100% post-fix yield for non-spec-writer types).
**Method**: fix-implementer
**Success criterion**: (1) Read masonry-preagent-tracker.js lines 53-64 and masonry-subagent-tracker.js lines 155 and 196-197 -- confirm the current path derivation divergence (process.cwd() vs input.cwd). (2) Determine the canonical masonry root by resolving __dirname in each hook (masonry/src/hooks/) relative to the repo root, giving a stable absolute path. (3) Update both hooks to derive pendingDir from the same canonical root, not from runtime CWD. (4) Verify no other hook or script reads from .masonry/pending_agent_prompts/ using the old path assumption. (5) Trigger 5 real agent spawns (including at least one spec-writer if possible, or any two different agent types) and confirm all 5 start events in routing_log.jsonl show request_text length >= 20 chars. Verdict: FIX_APPLIED if 5 consecutive real spawns all yield non-empty request_text; PARTIAL if non-spec-writer agents work but spec-writer still misses; FAILURE if the change introduces a regression where previously working agents now miss.

---

### V30.1: Validate that F29.1 + F29.2 together produce a complete, enriched, and stable training corpus ready for both MIPROv2 runs

**Status**: DONE
**Finding**: findings/V30.1.md
**Operational Mode**: validate
**Priority**: HIGH
**Motivated by**: F29.1 FIX_APPLIED (research-analyst question_text enriched from median 88 to 500 chars via _build_qid_to_agent_map wiring) and F29.2 FIX_APPLIED (scored_synthetic.jsonl created; karen negatives confirmed stable across consecutive reruns). Both fixes interact with the same scored_all.jsonl output file. Neither finding validated joint corpus readiness end-to-end: that a fresh run of score_all_agents.py now satisfies all MIPROv2 preconditions for both agents simultaneously without further data preparation steps.
**Hypothesis**: Running score_all_agents.py now produces a scored_all.jsonl that simultaneously satisfies: (a) research-analyst: >= 37 records, median input.question_text >= 200 chars; (b) karen: >= 10 records with score range >= 0.75 (positives + 5 synthetics at score=0); (c) total records >= 594; (d) idempotency: all counts identical on a second consecutive run. If any criterion fails, the specific failure identifies which fix has a regression or an incomplete interaction.
**Method**: research-analyst
**Success criterion**: (1) Run python masonry/scripts/score_all_agents.py from the repo root and capture summary output. (2) Parse masonry/training_data/scored_all.jsonl -- check research-analyst record count >= 37 and median input.question_text >= 200 chars. (3) Check karen record count >= 10, karen records with score=0 count == 5, karen score range (max_score - min_score) >= 0.75. (4) Check total records >= 594. (5) Run score_all_agents.py a second time and confirm all four counts from steps 2-4 are identical to run 1. (6) Confirm zero records have empty input.question_text. Verdict: HEALTHY if all six criteria pass across both runs; WARNING if any criterion passes on run 1 but drifts on run 2 (idempotency failure); FAILURE if research-analyst median question_text < 200 chars or karen negatives count < 5 after either run.

---

### F30.2: Execute both research-analyst and karen MIPROv2 optimization runs once an LLM backend becomes available

**Status**: DONE
**Finding**: findings/F30.2.md
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: F29.3 BLOCKED (research-analyst MIPROv2 -- ANTHROPIC_API_KEY not set, Ollama offline at 192.168.50.62:11434) and F29.4 BLOCKED (karen MIPROv2 -- identical backend blocker). Both runs share the same external dependency blocker and all data preconditions are confirmed met: research-analyst has 56 records with median question_text 500 chars; karen has 299 records + 5 synthetic negatives with score range 1.0. This question is user-action-gated and must not be executed until a backend check passes.
**Hypothesis**: Once ANTHROPIC_API_KEY is set (or Ollama restored), both optimization runs will complete without error. Expected outcomes: research-analyst final score >= 0.65 (37 training records, enriched question_text); karen final score 0.70-0.85 (299 records + synthetics, score range 1.0). Both runs will write JSON files to masonry/optimized_prompts/ and update agent_registry.yml to dspy_status: optimized for both agents.
**Method**: fix-implementer
**Success criterion**: PRECONDITION CHECK first -- confirm `python -c "import os; print(bool(os.environ.get('ANTHROPIC_API_KEY')))"` prints True, OR `curl -s --connect-timeout 3 http://192.168.50.62:11434/api/tags` returns HTTP 200. If neither passes, return BLOCKED immediately without running either optimization. (1) Determine backend: prefer anthropic if ANTHROPIC_API_KEY is set, else ollama. (2) Run: python masonry/scripts/run_optimization.py research-analyst --backend [ollama|anthropic] --num-trials 10 --valset-size 25 --signature research. Confirm masonry/optimized_prompts/research-analyst.json written with non-empty instructions field and final score >= 0.65. (3) Run: python masonry/scripts/run_optimization.py karen --backend [ollama|anthropic] --num-trials 10 --valset-size 25 --signature karen. Confirm masonry/optimized_prompts/karen.json written with non-empty instructions field and final score >= 0.65. (4) Confirm agent_registry.yml shows dspy_status: optimized for both research-analyst and karen. Verdict: FIX_APPLIED if both runs complete with score >= 0.65; WARNING if one agent scores 0.50-0.65 (marginal but usable); BLOCKED if no backend passes the precondition check; FAILURE if either run errors out or produces score < 0.50.

---

### R30.1: Research whether the one-slot-per-type strategy in masonry-preagent-tracker.js causes prompt collisions when two agents of the same type spawn concurrently

**Status**: DONE
**Finding**: findings/R30.1.md
**Operational Mode**: research
**Priority**: LOW
**Motivated by**: V29.1 WARNING side-finding -- masonry-preagent-tracker.js uses {subagent_type}_latest.json as the slot filename (one slot per agent type). If two fix-implementer agents spawn within the same 10-second TTL window, the second PreToolUse event overwrites the first slot before SubagentStart can consume it, causing the first agent to either capture the wrong prompt or find no slot at all. Wave 29 observed two fix-implementer spawns at 14:03:04Z and 14:03:15Z (11 seconds apart -- just outside the collision window). As campaign parallelism grows (parallel waves, /ultrawork mode), same-type concurrent spawns are likely to become more frequent.
**Hypothesis**: The one-slot-per-type strategy produces a collision rate proportional to how often the same agent type is spawned in parallel within the TTL window. At current serialized campaign throughput the rate is near zero, but a parallel-wave campaign with 3+ simultaneous fix-implementer spawns would produce collisions affecting routing log fidelity. A UUID-keyed or timestamp-keyed slot design would eliminate collisions at the cost of more complex slot matching in SubagentStart.
**Method**: research-analyst
**Success criterion**: (1) Inspect masonry-preagent-tracker.js lines 13-15 (design comment on one-slot-per-type strategy) and lines 63-73 (slot write -- confirm unconditional overwrite of {subagent_type}_latest.json). (2) Scan masonry/routing_log.jsonl for any two consecutive start events of the same agent type (e.g., fix-implementer) with timestamps within 10 seconds of each other -- count such pairs as collision-exposed windows. (3) Estimate observed collision exposure as: (collision-exposed windows) / (total start events). (4) If exposure > 5%: sketch an alternative slot design (e.g., {subagent_type}_{epoch_ms}.json with glob-based oldest-slot matching in SubagentStart) and estimate implementation complexity in lines-of-change. (5) Check whether any start event in the log shows a request_text value that appears to belong to a different question than the agent was assigned (cross-contamination evidence). Verdict: HEALTHY if observed collision exposure < 1% and no cross-contamination evidence found; WARNING if exposure is 1-10% or a plausible collision scenario is found in the log; FAILURE if a confirmed collision has already caused a wrong request_text to be recorded for any agent spawn.

---

### F30.5: Fix optimize_all() to dispatch per-agent signatures and metrics instead of hardcoding ResearchAgentSig for all agents

**Status**: DONE
**Finding**: findings/F30.5.md
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: Wave 25 open issue #6 (never closed) — `optimize_all()` in `masonry/src/dspy_pipeline/optimizer.py` lines 306-312 hardcodes `sig = ResearchAgentSig` for every agent, ignoring agent-specific signature requirements. When karen is optimized via `optimize_all()`, DSPy would receive KarenSig training examples (fields: commit_subject, files_changed, doc_context, quality_score, action, changelog_entry) mapped against a ResearchAgentSig (fields: question_text, project_context, constraints, verdict, severity, evidence, mitigation, confidence) — producing a field mismatch that either crashes or trains the wrong prompt. Note: `run_optimization.py` already dispatches correctly (line 241: `signature_cls = KarenSig if signature == "karen" else ResearchAgentSig`); only `optimize_all()` is broken.
**Hypothesis**: A minimal dispatch table `_SIG_MAP = {"karen": (KarenSig, build_karen_metric())}` with a default fallback to `(ResearchAgentSig, None)` inserted at the top of the `for agent in registry` loop in `optimize_all()` will fix this. The change is ~5 lines and has no external dependencies.
**Method**: fix-implementer
**Success criterion**: (1) Read `optimize_all()` lines 295-316 — confirm hardcoded `sig = ResearchAgentSig` and `metric_fn=None`. (2) Import `KarenSig` and `build_karen_metric` at the top of the function body (lazy import to avoid circular deps). (3) Build `_SIG_MAP = {"karen": (KarenSig, build_karen_metric())}` and replace lines 311-313 with a lookup: `sig, metric_fn = _SIG_MAP.get(agent.name, (ResearchAgentSig, None))`. (4) Run the full test suite — confirm no regressions. (5) Add a unit test: call `optimize_all()` with a registry entry for "karen" and a mock dataset; assert the `signature_cls` argument passed to `optimize_agent` is `KarenSig`, not `ResearchAgentSig`. Verdict: FIX_APPLIED if dispatch table is in place, test confirms KarenSig for karen and ResearchAgentSig for other agents, and full suite passes; PARTIAL if table is present but `metric_fn` is not wired correctly; FAILURE if `optimize_all()` still uses `ResearchAgentSig` for karen after the change.

---

## Wave 31

**Generated from findings**: V30.5, F30.1, F30.2, R30.1, V30.1
**Mode transitions applied**: V30.5 FAILURE (CRITICAL) -> F31.1 Fix (build the missing injection path — highest priority); F30.1 FIX_APPLIED -> V31.1 Validate (confirm slot-miss elimination under real spec-writer spawns); F30.2 BLOCKED (external auth dependency) -> R31.1 Research (investigate whether Claude Code native auth can replace ANTHROPIC_API_KEY for DSPy runs); R30.1 WARNING -> accepted, no new question (zero post-activation collisions, exposure within tolerance at current throughput); V30.1 HEALTHY -> no new question (corpus gate passed, superseded by F31.1 as next unblocking step).

---

### F31.1: Build the optimized prompt injection path so that MIPROv2 output in optimized_prompts/{agent}.json actually affects agent behavior at spawn time

**Status**: DONE
**Finding**: findings/F31.1.md
**Operational Mode**: Fix
**Priority**: CRITICAL
**Motivated by**: V30.5 FAILURE — `optimized_prompts/{agent}.json` files are written by the optimizer but never read at agent spawn time. The `signature.instructions` field is present in every optimized JSON (confirmed in `quantitative-analyst.json` line 40) but zero code in any hook, router, or Mortar agent file reads it. Running MIPROv2 optimization currently produces zero behavioral change in any agent. The CLAUDE.md claim "Mortar injects optimized prompts on specialist invocation automatically" is false — the injection path does not exist. This fix closes that gap before F30.2 optimization runs are worth executing.
**Hypothesis**: The architecturally correct fix is to have `run_optimization.py`'s `optimize_agent()` write the `signature.instructions` content back into the corresponding agent `.md` file in a clearly delimited `## DSPy Optimized Instructions` section, immediately after saving the JSON. This approach is code-enforced (not LLM-honor-based), survives session restarts, requires no new hooks, and makes the injection testable by simply reading the agent `.md`. Option A (updating mortar.md to instruct Mortar to read the JSON) is LLM-honor-based and does not guarantee injection. After this fix, spawning any optimized agent will include the MIPROv2-tuned instructions in its system prompt.
**Method**: fix-implementer
**Success criterion**: (1) Read `masonry/scripts/run_optimization.py` — locate `optimize_agent()` and the post-save block after `dspy.module.save()`. (2) Read `masonry/optimized_prompts/quantitative-analyst.json` — extract the `signature.instructions` string to use as test fixture. (3) Read the agent `.md` file for quantitative-analyst to confirm it currently lacks a `## DSPy Optimized Instructions` section. (4) Implement: after saving the JSON, open the agent `.md` (resolving path via `agent_registry.yml` or a known agents dir), remove any existing `## DSPy Optimized Instructions` section (idempotent), then append the section with the `instructions` text. (5) Run a dry-run test call against the existing `quantitative-analyst.json`: confirm the agent `.md` gains the section with non-empty content matching `signature.instructions`. (6) Run a second call and confirm idempotency — old section removed, new section written, `.md` line count stable. (7) Update the CLAUDE.md "Mortar injects optimized prompts" statement to accurately describe the write-back mechanism. Verdict: FIX_APPLIED if the agent `.md` contains the optimized instructions block matching the JSON, operation is idempotent, and CLAUDE.md is updated; PARTIAL if write-back works but CLAUDE.md is not updated or idempotency fails; FAILURE if the agent `.md` is unchanged after calling `optimize_agent()`.

---

### V31.1: Validate that the F30.1 homedir fix eliminated spec-writer slot misses under real post-fix agent spawns

**Status**: DONE
**Finding**: findings/V31.1.md
**Operational Mode**: Validate
**Priority**: HIGH
**Motivated by**: F30.1 FIX_APPLIED — both tracker hooks now use `os.homedir()` as the base for `pending_agent_prompts/` (verified syntax-clean via `node -c`) but no live spawn validation was performed. V29.1 established the pre-fix baseline: ~17% slot-miss rate for spec-writer spawns (SubagentStart events showing `request_text` length = 0). The fix hypothesis is that this rate drops to 0% for all agent types post-fix. This question validates that hypothesis against routing_log.jsonl entries written after 2026-03-23 (the F30.1 fix date).
**Hypothesis**: Post-fix agent spawns will show 0% slot-miss rate in routing_log.jsonl. The `~/.masonry/pending_agent_prompts/` directory is now the unconditional write and read target in both hooks, so CWD differences between the PreToolUse and SubagentStart events can no longer cause a path divergence. If spec-writer spawns occur in the post-fix log, they will have `request_text` length >= 20, matching the fix-implementer 100% yield observed pre-fix.
**Method**: research-analyst
**Success criterion**: (1) Read `masonry/src/hooks/masonry-preagent-tracker.js` lines near the `pendingDir` assignment — confirm `os.homedir()` is used and no `process.cwd()` or `masonryDir` block remains. (2) Read `masonry/src/hooks/masonry-subagent-tracker.js` lines near the `pendingDir` assignment — confirm `os.homedir()` is used and the old `path.join(cwd, '.masonry', ...)` form is gone. (3) Read `masonry/routing_log.jsonl` — filter to `start` events with `timestamp` >= "2026-03-23". (4) Report: total post-fix start events, count with `request_text` length >= 20, count with `request_text` length = 0. Report spec-writer events separately. (5) Compare post-fix miss rate to V29.1 baseline (~17%). Verdict: HEALTHY if post-fix miss rate = 0% across all agent types (all start events have `request_text` length >= 20) or if no post-fix spawns exist yet (fix unverifiable, need live spawns); WARNING if miss rate dropped below 5% but is non-zero (partial coverage of CWD variants); FAILURE if miss rate is >= 10% (fix had minimal effect) or if either hook still contains a CWD-relative path.

---

### R31.1: Research whether ANTHROPIC_API_KEY can be sourced from Claude Code's native session credentials to unblock MIPROv2 runs without manual key export

**Status**: DONE
**Finding**: findings/R31.1.md
**Operational Mode**: Research
**Priority**: MEDIUM
**Motivated by**: F30.2 BLOCKED — both MIPROv2 optimization runs are blocked because `ANTHROPIC_API_KEY` is absent from the shell environment and Ollama at 192.168.50.62:11434 is offline. The training corpus is fully ready (V30.1 HEALTHY: 606 records). Claude Code is itself an active Anthropic API session — it is plausible that the credentials it uses are accessible to child processes or scripts invoked from within the session, which would allow `run_optimization.py --backend anthropic` to execute without the user manually exporting a key.
**Hypothesis**: Claude Code exposes its Anthropic authentication to subprocess environments via one of: (a) an `ANTHROPIC_API_KEY` env var visible to child processes; (b) a credentials file at a known path such as `~/.config/anthropic/` or `~/.anthropic/`; (c) a `CLAUDE_API_KEY` or similar non-standard var. If any mechanism is confirmed working via a test `anthropic.Anthropic()` call, `run_optimization.py` can be run immediately from within a session Bash call. DSPy's LiteLLM backend reads `ANTHROPIC_API_KEY` by default; if an alternate var is found, a one-line env alias may suffice.
**Method**: research-analyst
**Success criterion**: (1) From within a Bash tool call, run `python -c "import os; print([k for k in os.environ if 'ANTHROPIC' in k.upper() or 'CLAUDE' in k.upper()])"` — report which auth-related env vars are visible to Python subprocesses. (2) Check `ls ~/.config/anthropic/ 2>/dev/null && echo found || echo absent` and `ls ~/.anthropic/ 2>/dev/null && echo found || echo absent`. (3) If any candidate credential is found, test it: `python -c "import anthropic; c = anthropic.Anthropic(); m = c.messages.create(model='claude-haiku-4-5', max_tokens=5, messages=[{'role':'user','content':'hi'}]); print('auth ok')"` — report success or specific error. (4) Check whether DSPy/LiteLLM reads any alternate env var: `python -c "import litellm; print(litellm.utils.get_secret('ANTHROPIC_API_KEY'))"`. (5) Summarize: is a working auth path available without manual key export? If yes, state the exact command to unblock F30.2. If no, confirm manual `export ANTHROPIC_API_KEY=...` remains the only option. Verdict: HEALTHY if a test API call succeeds using session-native credentials; WARNING if credentials are present but the test call fails (wrong scope or format); FAILURE if no Anthropic credential is accessible from within the Claude Code session and manual export is confirmed as the only path.

---

## Wave 32

**Generated from findings**: F31.1, R31.1
**Mode transitions applied**: F31.1 FIX_APPLIED (write-back injection built, but CLAUDE.md line 75 NOT updated — partial success criterion) → F32.1 Fix (correct CLAUDE.md description of injection mechanism); F31.1 FIX_APPLIED → V32.1 Validate (end-to-end confirmation that spawned agents actually receive the injected block in their system prompt); R31.1 WARNING (api_key kwarg identified as the durable unblock path for MIPROv2) → F32.2 Fix (add api_key parameter to configure_dspy() and --api-key CLI flag); R31.1 WARNING (Ollama offline, separate infrastructure issue) → M32.1 Monitor (add Ollama reachability to monitor-targets.md); F31.1 FIX_APPLIED (write-back covers only quantitative-analyst in testing) → V32.2 Validate (confirm write-back handles all agents and edge cases before more JSON files exist).

---

### F32.1: Correct CLAUDE.md line 75 to accurately describe the write-back injection mechanism built in F31.1

**Status**: DONE
**Finding**: findings/F32.1.md
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: F31.1 FIX_APPLIED — the success criterion for F31.1 explicitly required updating the CLAUDE.md "Mortar injects optimized prompts on specialist invocation automatically" claim. Post-fix inspection of `C:/Users/trg16/Dev/Bricklayer2.0/.claude/CLAUDE.md` line 75 confirms it still reads: "Mortar injects optimized prompts on specialist invocation automatically." This is inaccurate — the actual mechanism is a post-optimization write-back that injects a `## DSPy Optimized Instructions` block into the agent `.md` file, not a runtime Mortar injection. F31.1 was PARTIAL by its own success criterion: write-back implemented, CLAUDE.md not updated.
**Hypothesis**: A targeted edit to CLAUDE.md line 75 (and the surrounding DSPy description paragraph) that explains the write-back mechanism will make the documentation accurate. The new text should state that `run_optimization.py` writes the optimized `signature.instructions` back into the agent `.md` file under a `## DSPy Optimized Instructions` delimited section after each MIPROv2 run — and that agents receive these instructions as part of their system prompt on every spawn. The mortar.md line 277 LLM-honor directive remains as a secondary backup path.
**Method**: fix-implementer
**Success criterion**: (1) Read `C:/Users/trg16/Dev/Bricklayer2.0/.claude/CLAUDE.md` lines 69-76 — confirm line 75 reads "Mortar injects optimized prompts on specialist invocation automatically." (2) Replace with accurate text describing the write-back approach: after optimization, `run_optimization.py` appends a `## DSPy Optimized Instructions` section to each agent `.md`; agents receive these instructions in their system prompt on every spawn. (3) Read `C:/Users/trg16/.claude/agents/mortar.md` line 277 — add a clarifying comment that the primary injection mechanism is the write-back; do not remove the LLM-honor directive, it remains a secondary path. (4) Grep the project CLAUDE.md for any other occurrence of "automatically" adjacent to "inject" or "optimized" — update any found. Verdict: FIX_APPLIED if CLAUDE.md line 75 no longer says "automatically" and instead describes the write-back mechanism; PARTIAL if only CLAUDE.md is updated but mortar.md line 277 comment is not added; FAILURE if CLAUDE.md is unchanged.

---

### V32.1: Validate end-to-end that a spawned agent receives the DSPy Optimized Instructions block in its active system prompt

**Status**: DONE
**Finding**: findings/V32.1.md
**Operational Mode**: validate
**Priority**: HIGH
**Motivated by**: F31.1 FIX_APPLIED — `writeback_optimized_instructions()` was verified to write the `## DSPy Optimized Instructions` block to disk in all candidate agent `.md` files. However, the finding only confirmed the write step. The injection path's last mile — whether Claude Code reads the full `.md` file (including appended body content) when spawning a subagent — was assumed but not confirmed. If Claude Code reads only frontmatter metadata and ignores body text, the entire F31.1 injection mechanism is silently ineffective.
**Hypothesis**: Claude Code reads the full content of an agent `.md` file when constructing a subagent's system prompt, including content appended after the original frontmatter body. The `## DSPy Optimized Instructions` block written by `writeback_optimized_instructions()` will therefore be present in the subagent's system context on every spawn, completing the optimization loop: MIPROv2 run → JSON saved → write-back to .md → Claude reads .md at spawn → optimized instructions active.
**Method**: research-analyst
**Success criterion**: (1) Read `C:/Users/trg16/Dev/Bricklayer2.0/.claude/agents/quantitative-analyst.md` — confirm the `## DSPy Optimized Instructions` block is present and non-empty at the end of the file. (2) Determine how Claude Code loads agent `.md` files: check Claude Code documentation or inspect how the agents directory is processed — specifically whether the full file body is included in the system prompt or only the frontmatter. (3) If the full body is included: classify the F31.1 injection as code-enforced and active; verdict HEALTHY. (4) If Claude Code reads only frontmatter metadata and ignores body text: the write-back approach does NOT inject into the system prompt and F31.1's injection is ineffective — this would be FAILURE requiring a different mechanism (e.g., writing instructions into a frontmatter `instructions:` or `system_prompt:` field). (5) Cross-check by inspecting a routing_log.jsonl `start` event for a quantitative-analyst spawn post-F31.1 — does the `request_text` field contain any text from the `## DSPy Optimized Instructions` block? Verdict: HEALTHY if the block is present on disk AND evidence confirms Claude Code reads the full .md body at spawn time; WARNING if the block is present but evidence is ambiguous about whether Claude Code includes appended body content; FAILURE if Claude Code only reads frontmatter and the injection block is silently ignored.

---

### F32.2: Add api_key parameter to configure_dspy() in optimizer.py so MIPROv2 runs are triggerable without manual ANTHROPIC_API_KEY env export

**Status**: DONE
**Finding**: findings/F32.2.md
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R31.1 WARNING — E4 confirmed that `configure_dspy()` currently calls `dspy.LM("anthropic/claude-sonnet-4-6")` with no credential argument, relying entirely on `ANTHROPIC_API_KEY` env var (E5: not present in subprocess). E2 confirmed that `dspy.LM()` accepts `api_key` as a kwargs pass-through to `litellm.completion()`. R31.1 Path 2 (add api_key parameter to configure_dspy) is the recommended durable unblock — it makes the credential injection explicit and allows Kiln or CLI callers to supply the key without requiring the user to export an env var before each session.
**Hypothesis**: Adding `api_key: str | None = None` to `configure_dspy()` and passing it to `dspy.LM()` only when non-None (4-line change) will make optimization runs invokable as `python masonry/scripts/run_optimization.py research-analyst --api-key sk-ant-...` without any env setup. A companion `--api-key` flag in `run_optimization.py`'s argparse block (defaulting to `os.environ.get("ANTHROPIC_API_KEY")`) makes the CLI ergonomic while preserving backward compatibility for callers that rely on the env var.
**Method**: fix-implementer
**Success criterion**: (1) Read `masonry/src/dspy_pipeline/optimizer.py` `configure_dspy()` — confirm current signature lacks api_key and the dspy.LM call is bare. (2) Add `api_key: str | None = None` to the signature. (3) Update the `dspy.LM()` call: pass `api_key=api_key` only when non-None using `**{"api_key": api_key} if api_key else {}`. (4) Read `masonry/scripts/run_optimization.py` argparse block — add `--api-key` argument (optional, default = `os.environ.get("ANTHROPIC_API_KEY")`), thread it through to the `configure_dspy()` call. (5) Run `python -m pytest masonry/tests/dspy_pipeline/test_optimizer.py -v` — confirm all 6 existing tests pass. (6) Add 1 new test: mock `dspy.LM` and call `configure_dspy(api_key="test-key-123")`; assert dspy.LM was called with `api_key="test-key-123"`. Verdict: FIX_APPLIED if configure_dspy accepts api_key, dspy.LM receives it when non-None, run_optimization.py accepts --api-key, and all 7 tests pass; PARTIAL if only optimizer.py is updated but run_optimization.py CLI is not changed; FAILURE if any of the 6 existing tests regress.

---

### M32.1: Add Ollama reachability at 192.168.50.62:11434 to monitor-targets.md as a fallback-backend health check

**Status**: DONE
**Finding**: findings/M32.1.md
**Operational Mode**: monitor
**Priority**: LOW
**Motivated by**: R31.1 WARNING — E8 confirmed `http://192.168.50.62:11434` is unreachable (timeout) and no local `ollama` binary exists on PATH, making the `--backend ollama` flag in `run_optimization.py` non-functional. Ollama is the zero-credential fallback optimization backend (no API key required). Its persistent unavailability means there is no alternative when ANTHROPIC_API_KEY is not set. Adding Ollama reachability to the monitor-targets produces a visible signal when the CasaOS container recovers, at which point `--backend ollama` becomes immediately viable.
**Hypothesis**: Adding a reachability check for `http://192.168.50.62:11434/api/tags` to `monitor-targets.md` with appropriate thresholds will surface Ollama recovery events to the campaign without requiring a dedicated research question each time. Current state: OFFLINE. Expected recovery signal: HTTP 200 from `/api/tags` listing available models including `qwen3:14b`.
**Method**: research-analyst
**Success criterion**: (1) Read `C:/Users/trg16/Dev/Bricklayer2.0/masonry/monitor-targets.md` — determine if it exists and what format existing entries use. (2) Add an entry: metric name `ollama_backend_reachable`, check command `curl -s --connect-timeout 3 http://192.168.50.62:11434/api/tags`, WARNING threshold = unreachable (any non-200 or timeout), FAILURE threshold = unreachable for > 7 consecutive campaign days (blocks the no-credential fallback path), current status = OFFLINE (confirmed R31.1 2026-03-23). (3) Note that local `ollama` binary absence means localhost fallback is also unavailable. (4) Confirm the file is written and the new entry follows the same format as existing entries. Verdict: DONE if the monitor entry is written with check command and thresholds; INCONCLUSIVE if `monitor-targets.md` does not exist and the correct creation path is unclear.

---

### V32.2: Validate that `writeback_optimized_instructions()` gracefully skips missing `.md` paths and is truly idempotent under changed instruction text

**Status**: DONE
**Finding**: findings/V32.2.md
**Operational Mode**: validate
**Priority**: MEDIUM
**Motivated by**: F31.1 FIX_APPLIED — `writeback_optimized_instructions()` was built and tested against the existing `quantitative-analyst.json` fixture (6 files updated, idempotency confirmed with identical instruction text). Two edge cases were not exercised in the F31.1 verification: (a) the `continue` guard at line 176-177 when none of the three candidate paths resolve to an existing file — must return `[]` silently without raising; (b) true idempotency when `instructions` text changes between consecutive calls — the regex `section_pattern.sub()` path must fully replace the old section without appending, so `.md` line count stabilizes after repeated runs with new content.
**Hypothesis**: (a) Calling `writeback_optimized_instructions(base_dir, "nonexistent-agent", "...", "...")` for an agent with no `.md` file on any of the three candidate paths returns `[]` without raising. (b) Calling `writeback_optimized_instructions()` twice with different `instructions` values on the same `.md` file results in exactly one `## DSPy Optimized Instructions` section containing the second call's text — `.md` line count after call 2 equals line count after call 1 (no growth).
**Method**: research-analyst
**Success criterion**: (1) Read `masonry/scripts/run_optimization.py` lines 175-187 — confirm `if not md_path.exists(): continue` covers all three candidate paths (project-level, sub-project, and user-global). (2) Identify an agent name guaranteed to have no `.md` on disk (e.g., `"ghost-agent"`); invoke `writeback_optimized_instructions()` with that name and confirm the return value is `[]` with no exception raised. (3) Take a `.md` that F31.1 already patched (e.g., `C:/Users/trg16/Dev/Bricklayer2.0/.claude/agents/quantitative-analyst.md`). Record current line count. Call `writeback_optimized_instructions()` with a different instruction string. Confirm: (a) `grep -c "## DSPy Optimized Instructions"` = 1, (b) section body contains the new text, (c) line count equals the pre-call line count ± 3. (4) Repeat with a third instruction string — confirm line count is still stable and section count = 1. Verdict: HEALTHY if missing-path returns `[]` silently AND changed-text idempotency holds for 2 consecutive calls with stable line count; WARNING if graceful skip works but line count grows by > 3 lines per call (slow accumulation that would corrupt `.md` over many runs); FAILURE if any call raises on a missing path or if two sections appear after two calls with different text.

---

### R32.1: Estimate the expected MIPROv2 score improvement for `research-analyst` given 500-char vs 88-char `question_text` input fields

**Status**: DONE
**Finding**: findings/R32.1.md
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: V31.1 HEALTHY (slot injection clean) + F31.1 FIX_APPLIED (writeback path operational) + F30.2 still BLOCKED on API key — the corpus is fully ready (V30.1 HEALTHY: 606 records, research-analyst median `question_text` approximately 500 chars post-F26.1/F29.1 enrichment). Before Tim exports an API key and runs the first real `research-analyst` MIPROv2 optimization, this question estimates whether the richer input context is likely to produce a meaningfully better prompt than the pre-enrichment 88-char baseline, informing the "is this API call worth the cost" decision.
**Hypothesis**: MIPROv2 selects few-shot demonstrations by co-variate similarity — longer, semantically richer `question_text` fields give the optimizer more signal to cluster demos by question type, domain, and difficulty. Based on the `quantitative-analyst` empirical data point (R23.1: 125 records, 88-char `question_text`, +8.8 pt score delta via Ollama qwen3:14b), the `research-analyst` run with 500-char `question_text` and 37 records should achieve a delta of at least comparable magnitude, offset by the smaller corpus (37 vs 125 records). If the projected delta is < 3 pts, the run is marginal given API cost; if >= 5 pts, it is clearly worth proceeding.
**Method**: research-analyst
**Success criterion**: (1) Sample 10 research-analyst records from `masonry/training_data/scored_all.jsonl` and report actual median `question_text` length (must confirm >= 200 chars, expected approximately 500 after F29.1 enrichment). (2) Review R23.1 as the pre-enrichment analogue (125 records, 88-char `question_text`, +8.8 pt delta). (3) Assess how DSPy MIPROv2 demonstration selection uses input-field similarity — does richer `question_text` improve demo diversity and metric coverage? Cite DSPy source or documentation. (4) Estimate the expected score delta for `research-analyst` with 500-char `question_text` and 37 records: weigh enrichment ratio (approximately 5.7x), corpus-size penalty (37 vs 125), and the R23.1 empirical anchor. (5) Report a projected score delta range (e.g., "+6 to +14 pts") with a confidence level and the top two uncertainty factors. Verdict: HEALTHY if projected delta >= 5 pts (API run is clearly worth it); WARNING if projected delta is 2-5 pts (marginal — run but set expectations low); INCONCLUSIVE if available data cannot distinguish >= 5 pts from < 2 pts (need empirical run to resolve).

---

## Wave 33

**Generated from findings**: V32.1, F32.2, R32.1, V32.2, F30.2
**Mode transitions applied**: V32.1 HEALTHY (injection confirmed) + F32.2 FIX_APPLIED (api_key param) + R32.1 HEALTHY (run worth it) → R33.1 Research (document and validate full end-to-end optimization run procedure now that all prerequisites are met); V32.1 HEALTHY (injection structural) → R33.2 Research (evaluate content quality of injected instructions vs base prompt — structural confirmation does not imply quality); F30.2 BLOCKED (third recurrence across Waves 29-30) → D33.1 Diagnose (audit the BLOCKED pattern history and assess whether F32.2 durably resolves it or a systematic infrastructure gap remains); V32.2 HEALTHY (writeback scope limited to one-level scan) → V33.1 Validate (enumerate all agents with optimized JSONs and confirm every reachable .md received the DSPy block — only quantitative-analyst currently has a JSON); R32.1 HEALTHY (run justified) → F33.1 Fix (add a runbook for triggering research-analyst and karen optimization runs to CLAUDE.md so the procedure is documented and repeatable).

---

### R33.1: Is there a complete, tested end-to-end procedure for triggering a research-analyst MIPROv2 optimization run and verifying its output?

**Status**: DONE
**Finding**: findings/R33.1.md
**Operational Mode**: research
**Priority**: HIGH
**Motivated by**: F32.2 FIX_APPLIED + R32.1 HEALTHY — F32.2 added `--api-key` to the CLI, making the run triggerable without environment setup. R32.1 confirmed the corpus is ready (57 records, 500-char median `question_text`) and the expected delta (+8 to +12 pts) justifies the API cost. However, no verified end-to-end procedure exists: what preconditions must pass before the run, what exact command should be issued, what files are written, and what post-run verification confirms success? Without a verified procedure, a first run attempt risks silent failure (wrong working directory, wrong signature name, JSON written to wrong path) with no clear diagnostic path.
**Hypothesis**: A complete, correct invocation of `run_optimization.py` for `research-analyst` requires: (1) CWD set to `C:/Users/trg16/Dev/Bricklayer2.0`, (2) `--signature research` flag matching the `ResearchAgentSig` class in `masonry/src/dspy_pipeline/signatures.py`, (3) either `--api-key sk-ant-...` or `ANTHROPIC_API_KEY` set in environment, (4) `--backend anthropic` (since Ollama is offline per M32.1). Post-run success can be confirmed by checking: `masonry/optimized_prompts/research-analyst.json` exists with non-empty `predict.signature.instructions`, `agent_registry.yml` shows `dspy_status: optimized` for research-analyst, and `.claude/agents/research-analyst.md` contains a `## DSPy Optimized Instructions` block.
**Method**: research-analyst
**Success criterion**: (1) Read `masonry/scripts/run_optimization.py` `--help` output and verify `--signature`, `--backend`, `--api-key`, `--num-trials`, `--valset-size` flags all exist with expected defaults. (2) Read `masonry/src/dspy_pipeline/signatures.py` — confirm `ResearchAgentSig` is the correct class name for `--signature research`. (3) Trace the post-run output path: confirm `optimize_agent()` saves to `masonry/optimized_prompts/{agent}.json`, that `writeback_optimized_instructions()` is called, and that `update_registry_dspy_status()` updates `agent_registry.yml`. (4) Produce a verified runbook: exact command, expected runtime estimate, three post-run verification checks. (5) Identify the top two failure modes that would cause a silent or misleading failure (e.g., wrong CWD produces empty registry, wrong signature name raises KeyError). Verdict: HEALTHY if a complete, verified runbook can be produced with all three post-run checks specified; WARNING if one post-run check cannot be confirmed from code inspection alone; INCONCLUSIVE if a code path ambiguity prevents confirming the JSON output location without a live test run.

---

### R33.2: Does the injected `quantitative-analyst` DSPy instruction text represent a meaningful behavioral improvement over the base agent prompt?

**Status**: DONE
**Finding**: findings/R33.2.md
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: V32.1 HEALTHY — confirmed that the `## DSPy Optimized Instructions` block is present on disk and that Claude Code delivers it in the system prompt. The structural injection loop is closed. However, V32.1 did not evaluate the *quality* of the instruction text itself. The block reads: "Analyze the research question within the project context, applying domain-specific reasoning and numerical modeling..." (~270 chars). This is the only MIPROv2-generated instruction in production. Whether it adds signal beyond the base quantitative-analyst.md system prompt — or is essentially a restatement of it — has never been assessed.
**Hypothesis**: The MIPROv2-generated instruction text for `quantitative-analyst` differs from the base system prompt in at least one measurable way: it either (a) introduces specificity absent from the base prompt (e.g., explicit mention of thresholds, step-by-step structure, or quantitative content requirements), (b) reorders or emphasizes elements in a way that aligns with the metric's scoring rubric, or (c) is substantially redundant with the base prompt (in which case the optimization produced negligible behavioral delta despite the +8.8 pt score gain, and the score gain reflects the few-shot demonstrations rather than the instruction rewrite).
**Method**: research-analyst
**Success criterion**: (1) Read `C:/Users/trg16/Dev/Bricklayer2.0/.claude/agents/quantitative-analyst.md` — extract the base system prompt (everything before the `## DSPy Optimized Instructions` section) and the injected instruction block. (2) Compare: does the injected block introduce any element not present in the base prompt? Specifically check for: structured output format (numbered steps), explicit confidence score requirement, evidence table requirement, and actionable mitigation requirement. (3) Read `masonry/optimized_prompts/quantitative-analyst.json` — check `predict.signature.instructions` against what was written to the `.md` (confirm no truncation or encoding artifact). (4) Read `masonry/src/dspy_pipeline/signatures.py` `QuantAnalystSig` — does the MIPROv2-generated instruction align with the signature's `output_fields`? (5) Assess: is the injected text additive (new behavioral signal), redundant (restatement of existing prompt), or contradictory (conflicts with base prompt directives). Verdict: HEALTHY if the injected text introduces at least two behavioral elements absent from the base prompt; WARNING if the injected text is largely redundant (< 1 new element); FAILURE if the injected text contradicts a directive in the base prompt (e.g., instructs a different output format than what the base prompt specifies).

---

### D33.1: Is the recurring "no LLM backend" BLOCKED state a systematic infrastructure gap, or does F32.2 durably resolve it?

**Status**: DONE
**Finding**: findings/D33.1.md
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Motivated by**: F30.2 BLOCKED — this is the third BLOCKED verdict on MIPROv2 runs across consecutive waves (F29.3 BLOCKED Wave 29, F29.4 BLOCKED Wave 29, F30.2 BLOCKED Wave 30). All three cite the same root: `ANTHROPIC_API_KEY` not in environment and Ollama at `192.168.50.62:11434` offline. F32.2 (Wave 32) added `--api-key` to the CLI to allow key injection at invocation time. However, the fix addresses the ergonomics of key passing, not the underlying question: why does the ANTHROPIC_API_KEY not persist in the shell environment across sessions, and is the Ollama offline state persistent or transient? Without understanding the root cause, BLOCKED states will recur whenever optimization runs are attempted.
**Hypothesis**: The ANTHROPIC_API_KEY absence is a Windows shell environment issue — the key is not set in the user's persistent environment (System Properties > Environment Variables) and must be manually exported each session. The Ollama offline state is a CasaOS container issue unrelated to the Windows shell. F32.2 durably resolves the Anthropic path by moving key injection from environment lookup to CLI argument. The Ollama path remains blocked until M32.1's monitor target signals recovery. Together, these represent two independent infrastructure gaps, not one systematic issue, and F32.2 resolves the one that matters most for near-term optimization runs.
**Method**: diagnose-analyst
**Success criterion**: (1) Check whether `ANTHROPIC_API_KEY` appears in Windows persistent environment: `[System.Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY", "User")` — if NULL, confirm the "manual export required each session" hypothesis. (2) Check Ollama host reachability: `curl -s --connect-timeout 3 http://192.168.50.62:11434/api/tags` — confirm current status (OFFLINE per M32.1 or recovered). (3) Verify F32.2 fix coverage: confirm `python masonry/scripts/run_optimization.py --help` includes `--api-key` and that the argparse default is `os.environ.get("ANTHROPIC_API_KEY")` (so env var still works if set). (4) Assess whether any other code path in `run_optimization.py` or `optimizer.py` still hard-requires the env var (i.e., any call to `os.environ["ANTHROPIC_API_KEY"]` rather than `os.environ.get(...)`). Verdict: DIAGNOSIS_COMPLETE if root causes for both blockers are identified and F32.2 is confirmed to durably resolve the Anthropic path; WARNING if F32.2 resolves the CLI path but a secondary code location still hard-requires the env var; FAILURE if F32.2 contains a regression that breaks the env-var fallback for callers that do set the key.

---

### V33.1: Confirm that all agents with an `optimized_prompts/*.json` file have a corresponding `## DSPy Optimized Instructions` block in their `.md` file

**Status**: DONE
**Finding**: findings/V33.1.md
**Operational Mode**: validate
**Priority**: MEDIUM
**Motivated by**: V32.2 HEALTHY (writeback scope) — V32.2 confirmed that `writeback_optimized_instructions()` correctly handles edge cases (missing paths, changed text, empty instructions). However, the function's one-level scan covers `{base_dir}/.claude/agents/` and one-level sub-projects. V32.2 observation #3 explicitly flagged that `projects/bl2/.claude/agents/quantitative-analyst.md` did NOT receive the DSPy block because it is two levels deep from the BL root. As optimization runs expand to cover more agents (research-analyst, karen), this gap will compound: any agent `.md` file outside the one-level scan range will silently miss the writeback, running without optimization despite a valid JSON existing.
**Hypothesis**: Currently only `quantitative-analyst.json` exists in `masonry/optimized_prompts/`. Exactly two `.md` files received the writeback block: `.claude/agents/quantitative-analyst.md` and `adbp/.claude/agents/quantitative-analyst.md`. A third candidate — `projects/bl2/.claude/agents/quantitative-analyst.md` (if it exists) — is outside scan range and lacks the block. When `research-analyst.json` and `karen.json` are eventually written, the same gap will apply to any `research-analyst.md` or `karen.md` deeper than one sub-project level.
**Method**: research-analyst
**Success criterion**: (1) List all files in `masonry/optimized_prompts/` — confirm the current set of optimized agents. (2) For each optimized agent, enumerate all `.md` candidate paths (project-level, one-level sub-projects, user-global) using the same logic as `writeback_optimized_instructions()`. (3) For each found `.md`, grep for `## DSPy Optimized Instructions` — report which files have it and which do not. (4) Identify any `.md` files at two or more levels deep that are missing the block. (5) If gaps exist: assess whether the current one-level scan limit is the intended design (acceptable trade-off) or an unintentional coverage gap that should be widened (e.g., to two levels). Verdict: HEALTHY if all reachable `.md` files within the one-level scan have the block, and any misses are only at two+ levels deep (documented acceptable gap); WARNING if a reachable `.md` within the one-level scan is missing the block (unexpected miss); FAILURE if a `.md` file was scanned but the block was not written due to a regex or path-resolution bug.

---

### F33.1: Add a MIPROv2 optimization runbook to CLAUDE.md documenting the exact procedure for triggering research-analyst and karen optimization runs

**Status**: DONE
**Finding**: findings/F33.1.md
**Operational Mode**: fix
**Priority**: LOW
**Motivated by**: R32.1 HEALTHY (run justified) + F32.2 FIX_APPLIED (api_key param added) — the optimization infrastructure is complete and the corpus is ready, but no procedure document exists that tells Tim (or a future session) exactly what to run. The CLAUDE.md DSPy section was updated in F32.1 to correct the injection mechanism description, but it does not include the specific commands needed to trigger an optimization run. Without a runbook, each attempt requires re-reading `run_optimization.py --help`, re-checking the signature class names, and reconstructing the correct flags from scratch — as evidenced by F30.2 and R32.1 spending substantial tokens rediscovering what command to issue.
**Hypothesis**: A 10-15 line runbook block in the CLAUDE.md DSPy section — covering precondition checks (backend availability, API key), exact command for each pending agent (research-analyst, karen), expected runtime, and three post-run verification commands — will reduce the per-run rediscovery overhead to near zero and eliminate the risk of silent misconfiguration (wrong CWD, wrong signature name).
**Method**: fix-implementer
**Success criterion**: (1) Read `C:/Users/trg16/Dev/Bricklayer2.0/.claude/CLAUDE.md` — locate the DSPy Optimization section (updated by F32.1). (2) Insert a "Running an Optimization" subsection containing: (a) precondition check command (`curl` for Ollama, `python -c "import os; print(...)"` for env key), (b) exact `run_optimization.py` command for research-analyst with correct flags (`--signature research --backend anthropic --num-trials 10 --valset-size 25`), (c) same for karen (`--signature karen`), (d) expected runtime per agent (4-8 hours), (e) three post-run verification commands (check JSON exists, grep .md for block, check registry). (3) Do not change any other section of CLAUDE.md. Verdict: FIX_APPLIED if the runbook subsection is present with at least the two agent commands and three verification checks; PARTIAL if only one agent is documented; FAILURE if CLAUDE.md is not modified.

---

### E33.1: Execute MIPROv2 optimization run for `research-analyst` (user provides `--api-key`)

**Status**: BLOCKED
**Operational Mode**: fix
**Priority**: CRITICAL
**Motivated by**: synthesis_wave32 OPEN ISSUE #1 — all code blockers resolved (F32.2 FIX_APPLIED: `--api-key` CLI arg live). Corpus confirmed ready: 57 records, 500-char median `question_text`, projected +8 to +12 pts delta (R32.1 HEALTHY). Ollama is OFFLINE (M32.1) so the run must target `--backend anthropic`. This is the single highest-priority action gated only on Tim supplying an API key.
**Hypothesis**: Running `python masonry/scripts/run_optimization.py research-analyst --api-key sk-ant-... --backend anthropic --num-trials 10 --valset-size 25 --signature research` from `C:/Users/trg16/Dev/Bricklayer2.0` will complete without error, write `masonry/optimized_prompts/research-analyst.json` with a non-empty `predict.signature.instructions` field, trigger `writeback_optimized_instructions()` to inject a `## DSPy Optimized Instructions` block into `.claude/agents/research-analyst.md`, and update `agent_registry.yml` with `dspy_status: optimized`. Best score is expected >= 70% based on R32.1 projection (current quantitative-analyst baseline: 68.3%).
**Method**: fix-implementer
**Success criterion**: (1) **User action required**: Tim runs the command with a valid Anthropic API key. (2) Run completes without `Exception` or `BLOCKED` in stdout. (3) `masonry/optimized_prompts/research-analyst.json` exists and `cat research-analyst.json | python -c "import json,sys; d=json.load(sys.stdin); print(d['predict']['signature']['instructions'])"` returns non-empty text. (4) `.claude/agents/research-analyst.md` contains a `## DSPy Optimized Instructions` section with the same instruction text. (5) `masonry/agent_registry.yml` shows `dspy_status: optimized` for `research-analyst`. (6) Report the best trial score and compare to the 68.3% quantitative-analyst baseline and the R32.1 projected range (70-80%). Verdict: FIX_APPLIED if all 5 post-run checks pass and best score >= 68%; WARNING if run completes but score < 68% or writeback has partial failures; BLOCKED if Tim has not yet provided an API key (do not attempt to run without key).

---

### R33.3: Would adding more training examples to the research-analyst corpus improve MIPROv2 scores beyond the projected 70-80% ceiling, or is 57 records adequate?

**Status**: DONE
**Finding**: findings/R33.3.md
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: R32.1 HEALTHY — R32.1 projected +8 to +12 pts delta and assessed the 57-record corpus as "adequate" for a 25-example valset split. However, the self-consistency ceiling for research-analyst was estimated at 0.9666 (R26.1), and the achievable range was 0.73-0.87 — the upper end of that range requires high-quality demonstrations that may not be fully represented in 57 records. The wave 32 synthesis flags `project_context` as empty for all 57 records, which is a known ceiling constraint. This question asks: post-E33.1, if the actual score falls below 0.80, what is the cost-benefit of adding 30-50 more training examples vs running more trials with the existing corpus?
**Hypothesis**: The 57-record corpus is near the minimum viable size for MIPROv2 with `valset_size=25` (32 training examples left). Diminishing returns set in quickly above 60-80 records for the research-analyst task type. The primary ceiling constraint is not corpus size but `project_context` emptiness (100% of records) — adding records without fixing `project_context` will produce marginal gains. If the E33.1 best score falls below 0.75, the recommended action is to enrich `project_context` in existing records (using the F29.1 enrichment pattern), not to add more records.
**Method**: research-analyst
**Success criterion**: (1) Review DSPy MIPROv2 documentation on bootstrap sample size effects — what is the documented minimum record count for reliable optimization, and at what size do returns diminish? (2) Assess the `project_context` gap: how many of the 57 records have non-empty `project_context`? What is the score distribution for records with vs without `project_context`? (3) Estimate the incremental score gain from adding 30 more records vs from enriching `project_context` in existing records. (4) If E33.1 has completed, report the actual best score and compare to the 70-80% projection — if actual < 70%, diagnose which corpus gap (size, context, verdict balance) is most likely responsible. Verdict: HEALTHY if 57 records is sufficient (actual score >= 70% or analysis shows corpus size is not the binding constraint); WARNING if corpus size is the binding constraint and adding 30+ records would likely push score above 75%; INCONCLUSIVE if the question cannot be resolved without the E33.1 actual score result.

---

### F33.2: Fix MCP masonry_optimize_agent tool to forward api_key to configure_dspy() (D33.1 DIAGNOSIS_COMPLETE)

**Status**: DONE
**Finding**: findings/F33.2.md
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: D33.1 PARTIAL — CLI path (run_optimization.py) was fixed by F32.2, but the MCP tool entry point (`_tool_masonry_optimize_agent` in server.py) calls `configure_dspy(model=model, backend=backend)` without api_key. Kiln "OPTIMIZE" button remains BLOCKED without env var.
**Method**: fix-implementer
**Success criterion**: `configure_dspy(model=model, backend=backend, api_key=api_key)` in server.py; api_key in inputSchema; no test regressions.

---

### F33.3: Correct --valset-size from 50 to 27 in CLAUDE.md runbook and run_optimization.py defaults (R33.3 WARNING)

**Status**: DONE
**Finding**: findings/F33.3.md
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R33.3 WARNING — effective bootstrap training set = 57 - 50 = 7 examples when using --valset-size 50. DSPy requires 30 training examples for reliable optimization. With 57 total records, --valset-size 27 leaves 30 training examples (crosses threshold). F33.1 wrote CLAUDE.md runbook with --valset-size 50 — this must be corrected to --valset-size 27 for research-analyst. Karen has 301 records, so --valset-size 25 is fine (276 training examples).
**Hypothesis**: Changing --valset-size from 50 to 27 in the research-analyst command in CLAUDE.md and in any default or comment in run_optimization.py will ensure 30 bootstrap training examples are available when the actual optimization run executes.
**Method**: fix-implementer
**Success criterion**: (1) Read CLAUDE.md DSPy optimization runbook — confirm research-analyst command uses --valset-size 50. (2) Change to --valset-size 27 with a comment explaining 57 total - 27 valset = 30 training examples (DSPy minimum). (3) Check run_optimization.py for any comment or default suggesting 25 or 50 for research-analyst — update if found. (4) Confirm karen command stays at --valset-size 25. Verdict: FIX_APPLIED if CLAUDE.md research-analyst command uses --valset-size 27; PARTIAL if comment added but valset-size unchanged; FAILURE if CLAUDE.md is not modified.

---

### M33.1: Establish a restoration path for the Ollama backend at `192.168.50.62:11434` and update monitor-targets.md with a recovery procedure

**Status**: DONE
**Finding**: findings/M33.1.md
**Operational Mode**: monitor
**Priority**: MEDIUM
**Motivated by**: M32.1 DONE (monitor entry added, current status OFFLINE) — the monitor entry records the OFFLINE state but provides no recovery procedure. Ollama is the designated zero-credential backend for DSPy optimization (no API key required) and the embedding source for semantic routing. With Ollama offline, semantic routing falls through to the LLM layer on every dispatch (additional latency and cost), and future optimization runs are locked to `--backend anthropic` (API key required). Restoring Ollama would remove the API key dependency for future runs.
**Hypothesis**: The Ollama backend at `192.168.50.62:11434` is a CasaOS Docker container that may have stopped or failed. The restoration path is: (1) check CasaOS Docker container status for Ollama, (2) if stopped, `docker compose up -d` or restart from CasaOS UI, (3) confirm `qwen3:14b` model is still loaded (or re-pull if needed), (4) re-run `curl -s http://192.168.50.62:11434/api/tags` to confirm availability. The semantic routing threshold and embedding model configuration in `masonry/src/routing/semantic.py` do not need changes — the backend URL is already correct.
**Method**: research-analyst
**Success criterion**: (1) Run `curl -s --connect-timeout 3 http://192.168.50.62:11434/api/tags` — report current status (ONLINE or OFFLINE). (2) If OFFLINE: identify the Docker container name or CasaOS app hosting Ollama. Provide the exact command(s) Tim should run to restart it. (3) Confirm whether `qwen3:14b` model would still be available after restart (check if models persist across container restarts in the Docker volume). (4) Update `masonry/monitor-targets.md` `ollama_backend_reachable` entry: add a "Recovery procedure" subsection with the identified restart commands. (5) If ONLINE: record the recovery date, update the monitor entry status to ONLINE, and recommend running a test embedding query to confirm the semantic routing can use the backend. Verdict: DONE if monitor-targets.md is updated with a concrete recovery procedure (even if Ollama remains OFFLINE — the procedure itself is the deliverable); WARNING if the recovery procedure cannot be determined without physical access to the CasaOS host.

---

## Wave 34

**Generated from findings**: R33.3, R33.2, D33.1, F33.2, F33.3, V33.1
**Mode transitions applied**: R33.3 WARNING → F34.1 Fix (populate project_context in load_training_data_from_scored_all); R33.3 WARNING → R34.1 Research (score 30+ new findings to grow corpus above 87-record threshold); R33.2 HEALTHY with latent inconsistency → D34.1 Diagnose (does build_metric score "CONCERNS" correctly or as 0); F33.2 FIX_APPLIED (D33.1 PARTIAL) → V34.1 Validate (confirm server.py api_key change works end-to-end with mock key); F33.3 FIX_APPLIED → R34.2 Research (given valset=27 and corpus=57, is 30 bootstrap examples at the threshold boundary sufficient for a reliable run or should we wait for corpus growth first)

---

### F34.1: Fix `load_training_data_from_scored_all()` to populate `project_context` from `project-brief.md` instead of hardcoding `""`

**Status**: DONE
**Finding**: findings/F34.1.md
**Operational Mode**: fix
**Priority**: MEDIUM
**Motivated by**: R33.3 WARNING — all 57 research-analyst records in `scored_all.jsonl` have `project_context = ""`. `ResearchAgentSig` defines `project_context` as a named `InputField`. Bootstrapped few-shot demos always show the agent operating with no project context, meaning MIPROv2 cannot learn from context-aware reasoning patterns. The fix is to populate `project_context` using `_load_project_brief()` (already implemented in `build_dataset()` at optimizer.py line ~183) when loading records from `scored_all.jsonl`.
**Hypothesis**: `load_training_data_from_scored_all()` in `masonry/src/dspy_pipeline/optimizer.py` hardcodes `project_context: ""` for all records. Calling `_load_project_brief(base_dir)` and injecting the result into each Example object when constructing the training set will enrich the bootstrap demos without requiring new findings to be scored.
**Method**: fix-implementer
**Success criterion**: (1) Read `masonry/src/dspy_pipeline/optimizer.py` — locate `load_training_data_from_scored_all()` and confirm `project_context` is hardcoded to `""`. (2) Confirm `_load_project_brief()` is defined and returns the content of `project-brief.md` given a `base_dir` path. (3) Add a `base_dir: Path | None = None` parameter to `load_training_data_from_scored_all()`. (4) When `base_dir` is provided and `_load_project_brief(base_dir)` returns non-empty text, set `project_context` to that value for each Example; otherwise keep `""` as fallback. (5) Update the call site in `optimize_agent()` to pass `base_dir` through. (6) Run `python -m pytest masonry/tests/dspy_pipeline/test_optimizer.py -v` — confirm all existing tests pass. (7) Add 1 new test: call `load_training_data_from_scored_all(scored_path, base_dir=tmp_path_with_brief)` and assert `examples[0].project_context` is non-empty. Verdict: FIX_APPLIED if `project_context` is populated from `project-brief.md` in the returned Examples and all tests pass; PARTIAL if `base_dir` parameter is added but not wired to the call site; FAILURE if any existing test regresses.

---

### R34.1: How many unscored findings in `findings/` could be processed by `build_dataset()` to grow the research-analyst corpus from 57 to 87+ records?

**Status**: DONE
**Finding**: findings/R34.1.md
**Operational Mode**: research
**Priority**: HIGH
**Motivated by**: R33.3 WARNING — 57 research-analyst records leaves only 30 bootstrap training examples at the corrected --valset-size 27 (exactly at the DSPy 30-example threshold). Adding 30 more records (to 87 total) would raise the effective bootstrap pool to 60 and move the expected score above the 75% WARNING boundary. The question is whether enough unscored findings exist to reach 87 without running a new campaign.
**Hypothesis**: Findings from Waves 24-33 that have not been processed into `scored_all.jsonl` could be scored by `build_dataset()` to grow the corpus. If 30+ unscored research-analyst findings exist in `masonry/findings/`, the corpus can cross the 87-record threshold without any API key or new campaign run.
**Method**: research-analyst
**Success criterion**: (1) Count the total number of `*.md` files in `masonry/findings/` that are research-analyst findings (identify by `**Agent**: research-analyst` header or question IDs matching `R{wave}.{n}` pattern). (2) Read `masonry/training_data/scored_all.jsonl` — count distinct `question_id` values where agent = "research-analyst". (3) Compute unscored = total research-analyst findings − already-scored findings. (4) If unscored >= 30: confirm that `build_dataset()` would process these (check whether `scored_all.jsonl` uses `question_id` deduplication to skip already-scored records, or if it would re-score them). (5) Provide the exact `python` command Tim should run to rebuild the corpus. (6) If unscored < 30: report the current gap and recommend the minimum number of new research questions that would need to be answered to reach 87. Verdict: HEALTHY if 30+ unscored research-analyst findings exist and the rebuild command is confirmed valid; WARNING if fewer than 30 exist but a concrete path to 87 is specified; FAILURE if `build_dataset()` would not incorporate existing findings without re-running the full campaign.

---

### D34.1: Does `build_metric()` score a "CONCERNS" verdict correctly, or does it always produce 0 on the verdict component when ground truth is "CONCERNS"?

**Status**: DONE
**Finding**: findings/D34.1.md
**Operational Mode**: diagnose
**Priority**: MEDIUM
**Motivated by**: R33.2 HEALTHY — the finding noted a latent inconsistency: some findings in `findings/` use the verdict "CONCERNS" (non-standard; not in the HEALTHY/WARNING/FAILURE/DIAGNOSIS_COMPLETE/PARTIAL/FIX_APPLIED canonical set). `build_metric()` uses exact string match (`ex_verdict == pred_verdict`). If 3 out of 57 training records have `verdict = "CONCERNS"` and the agent predicts "WARNING" (the semantically equivalent standard verdict), those records score 0.0 on the 0.4-weight verdict component — effectively penalizing correct near-miss predictions and reducing the achievable optimization score ceiling.
**Hypothesis**: `scored_all.jsonl` contains records with `verdict = "CONCERNS"` (the non-standard 3 records noted in R33.3). The exact-match metric will score these 0 even when the agent predicts the correct semantic equivalent. Additionally, the `build_dataset()` scoring pipeline may be labeling new records with "CONCERNS" from raw finding files, compounding the issue as the corpus grows.
**Method**: diagnose-analyst
**Success criterion**: (1) Read `masonry/training_data/scored_all.jsonl` — count records where `verdict` is not in `{"HEALTHY", "WARNING", "FAILURE", "DIAGNOSIS_COMPLETE", "PARTIAL", "FIX_APPLIED", "BLOCKED", "PROMISING", "PROBABLE", "IMMINENT", "NON_COMPLIANT", "INCONCLUSIVE"}`. Report the count and the distinct non-standard verdict strings found. (2) Read `masonry/src/dspy_pipeline/optimizer.py` `build_metric()` (lines 24-75) — confirm whether exact string match is used for verdict scoring or if a normalization/synonym map exists. (3) If non-standard verdicts exist AND no normalization is present: produce a DIAGNOSIS_COMPLETE verdict with a Fix Specification: add a `_VERDICT_ALIASES` dict that maps non-standard strings to canonical equivalents (`"CONCERNS" → "WARNING"`) applied to `ex_verdict` before the comparison. (4) If no non-standard verdicts exist in `scored_all.jsonl`: produce a HEALTHY verdict confirming the inconsistency is limited to the findings prose and does not affect the metric. Verdict: DIAGNOSIS_COMPLETE if non-standard verdicts exist and a fix specification is written; HEALTHY if the metric is unaffected; FAILURE if the scoring pipeline actively imports non-standard verdicts into future corpus records.

---

### V34.1: Validate that the `server.py` `masonry_optimize_agent` MCP tool correctly forwards `api_key` to `configure_dspy()` without breaking existing tool behavior

**Status**: DONE
**Finding**: findings/V34.1.md
**Operational Mode**: validate
**Priority**: MEDIUM
**Motivated by**: F33.2 FIX_APPLIED (D33.1 PARTIAL) — F33.2 added `api_key` to the MCP tool inputSchema and threaded it to `configure_dspy()`. The fix was applied with confidence 0.97 but was not validated with a live or mock end-to-end call. The concern is that the MCP inputSchema change could break Kiln's schema introspection if the new optional field is not correctly typed, or that `args.get("api_key")` silently returns `None` in cases where Kiln omits the field, which would regress to the original blocked state.
**Hypothesis**: The three-point change in `server.py` (inputSchema addition + `args.get("api_key")` extraction + `configure_dspy(api_key=api_key)` call) is complete and correct. When `api_key` is omitted from the MCP call, `args.get("api_key")` returns `None` and `configure_dspy` falls back to env var — preserving the original behavior. When `api_key` is provided, it is forwarded correctly.
**Method**: research-analyst
**Success criterion**: (1) Read `masonry/mcp_server/server.py` — find `_tool_masonry_optimize_agent` function and the `masonry_optimize_agent` inputSchema block. (2) Confirm `api_key` is listed in `inputSchema["properties"]` with `"type": "string"` and `"required"` does NOT include `"api_key"` (it must be optional). (3) Confirm the function body contains `api_key = args.get("api_key")` (or equivalent). (4) Confirm `configure_dspy(model=model, backend=backend, api_key=api_key)` is the call — all three keyword arguments present. (5) Read `masonry/tests/` — check whether a test for `_tool_masonry_optimize_agent` with an explicit `api_key` argument exists. If not, note the test gap. (6) Run `python -m pytest masonry/tests/ -k "optimize" -v` — confirm all optimization-related tests pass. Verdict: HEALTHY if all 4 code checks pass and tests pass; WARNING if the test for explicit api_key does not exist (functional but undertested); FAILURE if `api_key` is in `"required"` (breaking change for callers that omit it) or if any test regresses.

---

### R34.2: Given the corrected `--valset-size 27` and corpus of 57, should we attempt the research-analyst optimization run now or wait until corpus reaches 87+?

**Status**: DONE
**Finding**: findings/R34.2.md
**Operational Mode**: research
**Priority**: HIGH
**Motivated by**: F33.3 FIX_APPLIED — the runbook now uses `--valset-size 27`, leaving exactly 30 bootstrap training examples. R33.3 WARNING noted that 30 examples is the DSPy minimum threshold ("substantial value") but the recommended target is 87+ (37 effective bootstrap examples). E33.1 is BLOCKED pending API key. The question is whether to unblock E33.1 immediately (accepting the 30-example floor risk) or wait until R34.1 confirms corpus can grow to 87+ first.
**Hypothesis**: Running optimization at the 30-example threshold will produce a usable but potentially suboptimal result. The expected score range at 30 examples is 65-75% (touching but not reliably above the 75% WARNING boundary). If corpus can be grown to 87+ with minimal effort (unscored findings exist), waiting 1-2 campaign waves before running is the better risk-adjusted choice. If corpus growth requires new findings, the 30-example run should proceed now to establish a baseline.
**Method**: research-analyst
**Success criterion**: (1) Reference R34.1 findings (or estimate from the question): how many unscored research-analyst findings exist? (2) Estimate the score improvement between a 30-example run vs. a 37-example run using DSPy's documented performance curves. (3) Estimate the time cost of running `build_dataset()` to grow the corpus vs. the time cost of a 10-trial MIPROv2 run at 30 examples. (4) Produce a clear recommendation: "Run now at 30 examples" (if corpus growth is blocked or the expected score at 30 crosses 75%) OR "Wait for corpus growth" (if R34.1 confirms 30+ unscored findings exist and can be processed in < 30 minutes). (5) If "Run now": confirm E33.1 should be re-enabled as the next executable question once an API key is available. Verdict: HEALTHY if a clear, evidence-backed recommendation is produced with a decision threshold; WARNING if the recommendation is ambiguous or conditional on data not yet available.

---

## Wave 35

**Generated from findings**: R34.1, R34.2, F34.1, M33.1
**Mode transitions applied**: R34.1 WARNING → F35.1 Fix (section name mismatch in score_findings.py blocks 10 findings); R34.1 WARNING → F35.2 Fix (agent field regex corrupted by backtick H1 titles blocks 2 findings); R34.2 HEALTHY (clear recommendation: apply fixes, re-run score_all_agents.py) → V35.1 Validate (confirm 13 Group A findings score cleanly after both fixes applied); F34.1 FIX_APPLIED (applied to run_optimization.py, not optimizer.py — original hypothesis named optimizer.py) → R35.1 Research (verify optimizer.py has no independent training data load path with hardcoded project_context); M33.1 DONE (Ollama offline, recovery procedure documented) → M35.1 Monitor (probe whether Ollama has come back online since M33.1)

---

### F35.1: Fix `_extract_section()` in `score_findings.py` to accept non-standard evidence section names used in Waves 11-13 findings

**Status**: DONE
**Finding**: findings/F35.1.md
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R34.1 WARNING — `score_findings.py:_extract_section()` performs an exact match on `"Evidence"`. Findings from Waves 11-13 used `Analysis`, `Verification Results`, and `Code Trace` as their evidence section headers. This blocks 10 findings from receiving any evidence quality points (0 of 40), causing them to fail the 60-point TRAINING_THRESHOLD. Fixing the match to accept a list of known section names would unlock these 10 records, growing the corpus from 70 to 82 after score_all_agents.py is re-run.
**Hypothesis**: The `_extract_section(text, "Evidence")` call on line 139 of `score_findings.py` can be extended with a fallback list: try `"Evidence"` first, then `"Analysis"`, then `"Verification Results"`, then `"Code Trace"`. The first non-empty match wins. This change is additive — findings that already have `## Evidence` are unaffected. The 10 blocked findings gain evidence quality points and cross the 60-point threshold.
**Method**: fix-implementer
**Success criterion**: (1) Read `masonry/scripts/score_findings.py` — confirm that `extract_finding_fields()` calls `_extract_section(text, "Evidence")` with a single hardcoded section name on line ~139. (2) Confirm `_extract_section()` uses `re.escape(section_name)` in its regex, meaning only exact matches succeed. (3) Modify `extract_finding_fields()` to attempt extraction in priority order: `["Evidence", "Analysis", "Verification Results", "Code Trace"]` — return the first non-empty result. Keep `_extract_section()` itself unchanged (single-name interface). (4) Run `python -m pytest masonry/tests/ -k "score" -v` — confirm no test regressions. (5) Run `python masonry/scripts/score_findings.py --base-dir C:/Users/trg16/Dev/Bricklayer2.0 --output masonry/training_data/scored_findings_test.jsonl` and confirm the count of research-analyst records increases relative to the pre-fix baseline. Verdict: FIX_APPLIED if the fallback list is in place and at least 8 of the 10 previously-blocked findings now produce non-zero evidence quality scores when scored individually; PARTIAL if the code change is correct but the count increase cannot be confirmed; FAILURE if any existing test regresses.

---

### F35.2: Fix `_RE_AGENT` regex in `score_findings.py` to prevent multi-line corruption when the H1 title contains backtick-delimited spans

**Status**: DONE
**Finding**: findings/F35.2.md
**Operational Mode**: fix
**Priority**: HIGH
**Motivated by**: R34.1 WARNING — Two findings (R14.1, R17.2) have H1 titles containing backtick spans. R34.1 reports that the `**Agent**:` field extraction produces a corrupted multi-part string for these files, preventing them from being attributed to `research-analyst`. The current `_RE_AGENT` pattern `r"\*\*Agent\*\*\s*:\s*([^\n]+)"` with a trailing `.strip()` may capture unexpected content depending on the file's parsed structure.
**Hypothesis**: The fix is to tighten the agent capture group from `[^\n]+` (any non-newline chars) to `([\w-]+)` (word chars and hyphens only, matching `research-analyst` exactly). This eliminates any trailing artifacts, backtick rendering leftovers, or whitespace continuation issues. The change is safe because all valid agent names in the registry consist only of word characters and hyphens.
**Method**: fix-implementer
**Success criterion**: (1) Read `masonry/scripts/score_findings.py` line 49 — confirm `_RE_AGENT = re.compile(r"\*\*Agent\*\*\s*:\s*([^\n]+)", re.IGNORECASE)`. (2) Read the raw bytes of `masonry/findings/R14.1.md` and `masonry/findings/R17.2.md` — extract the `**Agent**:` line and run the current pattern against it. Record what `group(1).strip()` produces. If it already returns `"research-analyst"` cleanly, record HEALTHY for this defect (corruption may be a different mechanism). (3) If corruption is confirmed: change the capture group to `([\w-]+)` so the pattern is `r"\*\*Agent\*\*\s*:\s*([\w-]+)"`. (4) Verify by calling `score_finding(Path("masonry/findings/R14.1.md"))` and `score_finding(Path("masonry/findings/R17.2.md"))` — confirm `fields["agent"] == "research-analyst"` for both. (5) Run `python -m pytest masonry/tests/ -k "score" -v` — confirm no regressions. Verdict: FIX_APPLIED if both files return `agent="research-analyst"` from `score_finding()` and all tests pass; HEALTHY if the corruption cannot be reproduced (R34.1 diagnosis was incorrect about the mechanism); FAILURE if any test regresses.

---

### V35.1: Validate that re-running `score_all_agents.py` after F35.1 and F35.2 grows the research-analyst corpus to at least 70 records

**Status**: DONE
**Finding**: findings/V35.1.md
**Operational Mode**: validate
**Priority**: HIGH
**Motivated by**: R34.2 HEALTHY — R34.2 recommended running `score_all_agents.py` after applying both pipeline fixes to grow the research-analyst corpus from 57 to 70 (13 Group A findings qualify as-is) and potentially 82 (fixes unlock 12 more). This question validates that the re-run produces the expected growth and that no deduplication or filtering issue silently blocks the increase.
**Hypothesis**: After F35.1 and F35.2 are applied, running `score_all_agents.py` will produce a `scored_all.jsonl` with at least 70 research-analyst records (57 existing + 13 Group A). If both fixes fully succeed, the count may reach 82. The deduplication logic uses `question_id` as key — existing 57 records are not re-added, only new records are appended.
**Method**: research-analyst
**Success criterion**: (1) Gate check: confirm F35.1 status is DONE and F35.2 status is DONE before proceeding. If either is PENDING or FAILURE, mark this question BLOCKED and report which fix is incomplete. (2) Read `masonry/scripts/score_all_agents.py` — confirm the deduplication strategy (does it skip already-scored `question_id` values, or rebuild from scratch?). (3) Run `python masonry/scripts/score_all_agents.py` (or the equivalent command from R34.2). (4) Count research-analyst records in the updated `masonry/training_data/scored_all.jsonl`. Report: baseline (57), net-new added, total. (5) If total >= 70: confirm bootstrap pool for `--valset-size 27` is now 43+ examples and recommend immediately running MIPROv2 optimization once ANTHROPIC_API_KEY is available. If total 63-69: diagnose which Group A findings failed to score and why. If total <= 57: FAILURE — fixes did not take effect. Verdict: HEALTHY if research-analyst corpus reaches >= 70 records after the re-run; WARNING if corpus reaches 63-69 (partial improvement, some Group A findings still blocked); FAILURE if corpus stays at 57.

---

### R35.1: Does `optimizer.py:optimize_agent()` independently load training data from disk, or does it always receive the dataset from its caller?

**Status**: DONE
**Finding**: findings/R35.1.md
**Operational Mode**: research
**Priority**: MEDIUM
**Motivated by**: F34.1 FIX_APPLIED — F34.1 fixed `load_training_data_from_scored_all()` in `run_optimization.py` to populate `project_context` from `project-brief.md`. The pre-flight check in F34.1 confirmed the function lives in `run_optimization.py`, not `optimizer.py`. However, the original F34.1 hypothesis named `optimizer.py` as the target, suggesting a belief that `optimizer.py` had its own loading path. If `optimizer.py:optimize_agent()` has a default or fallback that reloads from `scored_all.jsonl` with a hardcoded `project_context: ""`, the F34.1 fix is silently bypassed in any code path that calls `optimize_agent()` directly without going through `run_optimization.py`.
**Hypothesis**: `optimizer.py:optimize_agent()` takes a `dataset: list[dict]` parameter that is always provided by the caller. It does not load from disk. The `project_context` enrichment in F34.1 flows correctly from `run_optimization.py:load_training_data_from_scored_all()` through the `dataset` argument into `optimize_agent()`. No second hardcoding point exists in `optimizer.py`.
**Method**: research-analyst
**Success criterion**: (1) Read `masonry/src/dspy_pipeline/optimizer.py` in full — locate `optimize_agent()` and `optimize_all_agents()`. Confirm whether either function contains any file I/O call (`open(`, `Path(`, `.read_text`, `.jsonl`, reference to `scored_all`). (2) Confirm the signature of `optimize_agent()`: does the `dataset` parameter have a default value that would trigger an internal load if omitted? (3) Check whether any other script or test in the repo calls `optimize_agent()` or `optimize_all_agents()` directly with an un-enriched dataset (grep for `optimize_agent(` outside of `run_optimization.py`). (4) Confirm the end-to-end call chain: `run_optimization.py:run()` → `load_training_data_from_scored_all(base_dir=base_dir)` → `optimize_agent(dataset=examples)`. Verdict: HEALTHY if `optimizer.py` has no independent loading path and the F34.1 fix is the sole injection point; WARNING if a secondary path exists but is not the default (latent risk — recommend adding a guard or test); FAILURE if `optimize_agent()` has a fallback load with `project_context: ""` that can bypass the F34.1 fix.

---

### M35.1: Probe Ollama at `192.168.50.62:11434` for current online status and update `monitor-targets.md`

**Status**: DONE
**Finding**: findings/M35.1.md
**Operational Mode**: monitor
**Priority**: LOW
**Motivated by**: M33.1 DONE — M33.1 confirmed Ollama OFFLINE as of 2026-03-23 with a documented CasaOS recovery procedure. Ollama is the zero-credential backend for DSPy optimization (no ANTHROPIC_API_KEY required) and the embedding source for semantic routing Layer 2. If Ollama has been restored, future MIPROv2 runs can use `--backend ollama` instead of `--backend anthropic`, removing the API key dependency. Semantic routing would also regain embedding-based dispatch.
**Hypothesis**: Ollama may have been restarted since M33.1 (2026-03-23). A connectivity probe will determine current status. If ONLINE, the CLAUDE.md optimization runbook should note that `--backend ollama` is available. If still OFFLINE, the monitor entry is updated with a new timestamp and no other action is needed.
**Method**: research-analyst
**Success criterion**: (1) Run `curl -s --connect-timeout 5 http://192.168.50.62:11434/api/tags` — capture exit code and response body. Exit code 0 with JSON response = ONLINE; exit code 7 (connection refused) or 28 (timeout) = OFFLINE. (2) If ONLINE: confirm which models are available. If `qwen3:14b` is listed, note that `--backend ollama --model qwen3:14b` is now viable. Run a test embedding query (`curl -s -X POST http://192.168.50.62:11434/api/embeddings -d '{"model":"nomic-embed-text","prompt":"test"}'`) to confirm the semantic routing endpoint is functional. Update `masonry/monitor-targets.md` `ollama_backend_reachable` entry to ONLINE with today's date. (3) If OFFLINE: update `masonry/monitor-targets.md` `ollama_backend_reachable` entry with today's date and the exit code (to confirm the probe ran). No other action required. Verdict: HEALTHY if Ollama is ONLINE and the embedding endpoint responds correctly; WARNING if Ollama is ONLINE but embedding endpoint fails or required model is missing; DONE if Ollama is still OFFLINE and monitor-targets.md is updated with the current probe timestamp.

---

## Wave 36

**Generated from findings**: V35.1, R35.1, M35.1
**Mode transitions applied**: V35.1 HEALTHY (corpus unblocked, 77 records) → V36.1 Validate (writeback target structure); V35.1 HEALTHY (corpus unblocked) → V36.2 Validate (karen corpus readiness at 321 records); M35.1 DONE with escalation recommendation → D36.1 Diagnose (Ollama host vs. container unreachable — 3 consecutive OFFLINE checks); V35.1 HEALTHY + E33.1 BLOCKED → V36.3 Validate (--api-key CLI arg wiring before run); V35.1 HEALTHY → R36.1 Research (project_context fill rate in 77-record corpus)

---

## Wave 37 — Predict Mode (cascade-analyst)

**Generated from findings**: M32.1/M33.1/M35.1 (Ollama persistent OFFLINE), E33.1 BLOCKED (MIPROv2 never run), V36.2 (karen corpus score concentration), R30.1 WARNING (slot collision dormant), D3.2 WARNING (interrupted-build resume broken), F12.1 deferred (drift metric confusion), V36.1/V36.3 HEALTHY (write-back structure confirmed)
**Mode**: predict
**Agent**: cascade-analyst
**Purpose**: Map downstream failure cascades from unresolved open issues — what breaks next and when if these issues are not addressed?

---

### P1: If Ollama remains OFFLINE beyond 7 consecutive campaign days, what is the downstream cascade on routing quality and DSPy optimization costs?

**Status**: DONE
**Operational Mode**: predict
**Agent**: cascade-analyst
**Priority**: HIGH
**Motivated by**: M32.1/M33.1/M35.1 — Ollama at `192.168.50.62:11434` has been OFFLINE for all 3 health checks on 2026-03-23, crossing into WARNING range. The 7-day FAILURE threshold in `monitor-targets.md` has not been crossed yet.
**Hypothesis**: If Ollama is not restored within 7 campaign days, two cascades will materialize: (1) Layer 2 (semantic routing) will be permanently non-functional — every request will fall through to Layer 3 (one LLM call per route), increasing latency by ~200ms and API cost by ~0.001 USD/route. At campaign loop velocity (~50 routes/wave), this compounds to ~$0.05/wave in unnecessary cost. (2) The zero-credential DSPy optimization path (`--backend ollama`) becomes permanently unavailable — all MIPROv2 runs will require a live Anthropic API key, eliminating the fallback for credential-free optimization. The cascade terminates when Ollama is restored or the infrastructure is formally decommissioned.
**Success criterion**: (1) Probe `http://192.168.50.62:11434/api/tags` — record exit code and timestamp. (2) Query `masonry/monitor-targets.md` for consecutive OFFLINE day count. (3) If count >= 7: classify as FAILURE cascade — quantify wave-level API cost delta between L2-functional and L2-degraded routing (extract from routing log hit rates). (4) Project when the API cost delta exceeds the cost of a single MIPROv2 optimization run (~$2-5). (5) Confirm whether `--backend ollama` is documented in the CLAUDE.md runbook as the only zero-cost path. Verdict: CASCADE_IMMINENT if OFFLINE count is 5-6 days (2 days before threshold); CASCADE_ACTIVE if 7+ days (cost accumulation confirmed); DORMANT if OFFLINE count < 5 days (threshold not yet in sight).

---

### P2: If E33.1 (MIPROv2 execution) remains BLOCKED indefinitely, what is the compounding quality debt on agent outputs over subsequent campaign waves?

**Status**: DONE
**Operational Mode**: predict
**Agent**: cascade-analyst
**Priority**: HIGH
**Motivated by**: E33.1 BLOCKED — all code-side blockers were resolved by Wave 32 (F32.2 api_key parameter, F31.1 write-back, V36.3 HEALTHY wiring confirmed). The optimization run has never executed. Agents are running on unoptimized instructions since the campaign began.
**Hypothesis**: Each wave run by an unoptimized research-analyst or karen produces findings scored at the pre-optimization baseline (68.3% — Trial 3, Wave 23, quantitative-analyst analog). The projected post-optimization score is 70-80% (R32.1 +8 to +12 pts). Every wave executed without optimization represents a compounding quality debt: findings that would pass a 75% quality gate instead produce at 68%, creating a false floor in the training corpus. By Wave 40, if E33.1 remains BLOCKED, the 77-record corpus will contain approximately 20-25 Wave 36-40 findings scored at the pre-optimization ceiling, potentially anchoring the next MIPROv2 run to a degraded baseline rather than improving from it.
**Success criterion**: (1) Count the number of research-analyst findings generated in Waves 33-36 that are present in `scored_all.jsonl` with scores below 75%. (2) Project the corpus composition at Wave 40 if E33.1 remains BLOCKED (estimate net-new records per wave). (3) Determine whether sub-75% records are excluded from MIPROv2 training or included — if included, they dilute the signal; if excluded by a score gate, the corpus may shrink. (4) Estimate the "score floor anchoring" risk: will a MIPROv2 run at Wave 40 produce a lower score than Wave 37 because the training corpus degraded? Verdict: CASCADE_ACTIVE if sub-75% records are being included in the training corpus and diluting signal; CASCADE_IMMINENT if the corpus is shrinking due to exclusion; DORMANT if training corpus quality is stable regardless of E33.1 status.

---

### P3: If the karen corpus score concentration (98.4% records scoring 90-100) is not corrected before the first MIPROv2 karen run, what optimization failure cascade results?

**Status**: DONE
**Operational Mode**: predict
**Agent**: cascade-analyst
**Priority**: MEDIUM
**Motivated by**: V36.2 HEALTHY — karen corpus contains 321 records with mean 98.44 and median 100.0. Only 5 records score below 60. This near-zero variance is structurally problematic for MIPROv2 because the optimizer cannot distinguish good examples from mediocre ones when all scores are 90-100.
**Hypothesis**: MIPROv2 requires score variance to identify which prompt instructions produce better outputs. If 98.4% of the 321 karen records score 90-100, the optimizer's bootstrap phase will treat nearly all examples as equally high-quality and will be unable to identify which few-shot examples actually improve performance. The result is one of two failure modes: (1) MIPROv2 produces an "optimized" karen that scores the same or lower than baseline because the training signal has insufficient variance; (2) The optimization run succeeds superficially but the resulting instructions overfit to the degenerate scoring distribution, producing a prompt that is confidently wrong in novel situations. The cascade terminus is that the karen optimization run produces a regression, and `writeback_optimized_instructions()` writes degraded instructions into `karen.md`, silently lowering karen's performance on every subsequent spawn.
**Success criterion**: (1) Read `masonry/src/metrics.py` — confirm whether the karen scoring function uses a different quality rubric than research-analyst (if karen scoring is trivially easy to pass, the 98.4% concentration is a scorer defect, not a corpus defect). (2) Check MIPROv2 bootstrap minimum variance requirements — does DSPy require a minimum score spread to produce meaningful optimization? (3) Identify how many records would be labeled "negative examples" (score < 70) under the current scoring — if only 5 of 321, the bootstrap phase cannot construct meaningful contrastive pairs. (4) Estimate the probability of optimization regression given the current score distribution. Verdict: CASCADE_ACTIVE if scorer confirms karen rubric is trivially easy (structural corpus defect); CASCADE_IMMINENT if DSPy bootstrap minimums require score spread that the current corpus cannot provide; DORMANT if MIPROv2 can extract useful signal from a high-concentration corpus.

---

### P4: If the one-slot-per-type collision in masonry-preagent-tracker.js triggers during a parallel campaign wave, what training signal corruption cascade results?

**Status**: DONE
**Operational Mode**: predict
**Agent**: cascade-analyst
**Priority**: MEDIUM
**Motivated by**: R30.1 WARNING — code confirms one-slot-per-type overwrite strategy; 0% collision rate post-activation in Waves 30-36 because the campaign loop dispatches agents sequentially. The risk is dormant but the code defect is live.
**Hypothesis**: If two agents of the same type (e.g., two `research-analyst` spawns) are dispatched within the 10-second TTL window, the second agent's prompt will overwrite the first agent's slot. The first agent's training record will then be attributed with the wrong `question_text` (the second question instead of the first). Over multiple collision events, the training corpus accumulates mislabeled examples: findings from Question A are paired with the question_text from Question B. MIPROv2 trains on these corrupted pairs, learning an instruction set that is optimized for question-finding mismatch — the resulting optimized prompt may produce correct verdicts for wrong reasons (coincidental alignment) or systematically wrong verdicts when the mismatch pattern reverses. The cascade is silent: no error is raised, the collision is not logged, and the corpus appears valid.
**Success criterion**: (1) Confirm the collision window: read `masonry-preagent-tracker.js` TTL value — if still 10 seconds, confirm whether parallel `/ultrawork` or multi-agent dispatches could realistically fire within this window. (2) Estimate the blast radius: how many records in the current 77-record research-analyst corpus could be corrupted if 5% of spawns collided? (3) Determine whether any existing detection mechanism (e.g., question_id cross-reference in scorer) would surface the corruption. (4) Model the MIPROv2 score impact of 5 corrupted records in an 77-record corpus (6.5% contamination rate). Verdict: CASCADE_ACTIVE if parallel dispatch is used and the TTL makes collisions near-certain; CASCADE_IMMINENT if parallel dispatch is used occasionally and the TTL creates a race window; DORMANT if dispatch is strictly sequential and no mechanism produces parallel same-type spawns.

---

### P5: If the D3.2 WARNING (session-start interrupted-build resume silently broken) is not fixed before the next /build campaign, what failure cascade results when a build is interrupted mid-task?

**Status**: DONE
**Operational Mode**: predict
**Agent**: cascade-analyst
**Priority**: MEDIUM
**Motivated by**: D3.2 WARNING — the session-start hook's interrupted-build resume logic is broken: when a build is interrupted mid-task, the next session start silently fails to resume it. The user sees no error but the in-progress task is abandoned without a BLOCKED or PAUSED status.
**Hypothesis**: If a `/build` campaign is interrupted (context overflow, session stop, network drop) and the user starts a new session, the masonry-session-start hook attempts to detect and resume the interrupted build. D3.2 confirms this detection is broken. The cascade: (1) The interrupted build's `.autopilot/progress.json` retains status `IN_PROGRESS` for the abandoned task. (2) The next session start does not surface this state. (3) The user runs a new `/build` or `/plan` without knowing a prior build was interrupted. (4) If the new run creates a conflicting spec or overwrites `progress.json`, the interrupted build's task history is permanently lost. (5) Any code changes from the partial task are now uncommitted orphans — present in the working tree but never verified or committed. This cascade is invisible until the user notices unexpected working-tree changes or duplicate task work.
**Success criterion**: (1) Read `masonry/src/hooks/masonry-session-start.js` — identify the exact detection mechanism for interrupted builds (does it read `.autopilot/mode` or `progress.json`?). (2) Reproduce the failure: manually set `.autopilot/mode = "build"` and `progress.json` task to `IN_PROGRESS`, then simulate a session start — confirm whether the hook surfaces the state or silently skips. (3) Determine whether `masonry-stop-guard.js` provides a partial mitigation (blocks Stop on uncommitted changes), which would surface the abandoned partial task indirectly. (4) Assess the probability that an in-progress build task leaves uncommitted code in the working tree. Verdict: CASCADE_ACTIVE if the broken resume creates silent orphan code changes that are never committed or surfaced; CASCADE_IMMINENT if the broken resume causes task deduplication or spec overwrite; DORMANT if the stop-guard hook provides sufficient mitigation by catching uncommitted changes before session end.

---

### P6: If the drift scoring metric (F12.1 deferred — FAILURE treated as bad agent performance) is never corrected, what quality signal inversion cascade accumulates in agent_db.json over future campaign waves?

**Status**: DONE
**Operational Mode**: predict
**Agent**: cascade-analyst
**Priority**: LOW
**Motivated by**: F12.1 deferred from Wave 12 — verdict-based drift scoring treats FAILURE verdict as evidence of bad agent performance, but for research agents FAILURE means "correctly found a problem." The confidence-based metric replacement was proposed but not implemented.
**Hypothesis**: As the campaign continues, agents that correctly identify failures (the campaign's primary purpose) will accumulate negative drift scores in `agent_db.json`. Research agents with high TRUE-FAILURE detection rates will appear as "drifting" or "degraded" while agents that return only HEALTHY or FIX_APPLIED will appear "stable." This inversion means: (1) Kiln's fleet health view will flag the most accurate research agents as underperforming; (2) Any auto-retirement logic triggered by drift score thresholds would preferentially retire the most useful agents; (3) MIPROv2 training data constructed from "high drift" agents (actually high-accuracy agents) would be deprioritized or excluded; (4) The campaign may reflexively generate "fix" questions to "restore" high-FAILURE agents that are actually working correctly. The cascade compounds silently across waves until a human audits `agent_db.json` verdict distributions.
**Success criterion**: (1) Read `masonry/src/dspy_pipeline/drift_detector.py` — confirm the current scoring logic: does a FAILURE verdict decrease an agent's drift score? (2) Count research-analyst FAILURE verdicts in `agent_db.json` — if the count is high (>10), compute the implied drift score and compare to the FAILURE threshold. (3) Determine whether any auto-retirement threshold in the registry or Kiln would trigger on the current research-analyst drift score. (4) Verify whether the `sync_verdicts_to_agent_db.py` integration (F11.3) currently runs with the broken metric or the correct one. Verdict: CASCADE_ACTIVE if research-analyst drift score is at or near the auto-retirement threshold; CASCADE_IMMINENT if any downstream system acts on drift scores (Kiln display, training data filtering, auto-retirement); DORMANT if drift scores are computed but nothing consumes them yet.

---

### P7: If the `AgentRegistryEntry.optimized_prompt` schema field remains an unpopulated placeholder, what downstream cascade affects any system that reads it to determine optimization status?

**Status**: DONE
**Operational Mode**: predict
**Agent**: cascade-analyst
**Priority**: LOW
**Motivated by**: V30.5 investigation — `AgentRegistryEntry.optimized_prompt` was identified as a schema field that is "never populated or read by code." The field exists in `masonry/src/schemas/payloads.py` but write-back via `run_optimization.py` does not update the registry entry.
**Hypothesis**: If MIPROv2 optimization runs succeed (E33.1 eventually executes) and `writeback_optimized_instructions()` writes optimized text into agent `.md` files, the `AgentRegistryEntry.optimized_prompt` field in `agent_registry.yml` will still be empty/null. Any code that reads this field to determine whether an agent has been optimized will incorrectly report all agents as unoptimized — even after successful optimization. Cascades: (1) Kiln's "Not optimized" badge will persist for agents that actually have optimized instructions in their `.md` files, causing false-negative displays; (2) Any routing logic that checks `optimized_prompt` before selecting between base and optimized agent behavior will always fall back to unoptimized behavior; (3) The `masonry_drift_check` MCP tool, if it reads `optimized_prompt` to assess optimization coverage, will report 0% coverage indefinitely. The cascade is cosmetic unless code begins acting on the field.
**Success criterion**: (1) Read `masonry/src/schemas/payloads.py` — confirm the `AgentRegistryEntry` schema definition for `optimized_prompt` (type, default, required). (2) Grep the entire codebase for reads of `optimized_prompt` from registry entries — confirm whether any code path currently consumes this field. (3) Check Kiln source (`masonry/kiln/` or `BrickLayerHub/`) for any UI component that reads `optimized_prompt` to render the "Not optimized" badge. (4) Determine whether `writeback_optimized_instructions()` in `run_optimization.py` updates `agent_registry.yml` after writing to `.md` files. Verdict: CASCADE_ACTIVE if any executed code path reads `optimized_prompt` and makes decisions based on it; CASCADE_IMMINENT if Kiln reads the field for display (false-negative badge is user-visible); DORMANT if the field is defined but truly unread by any current code path.

---

## Wave Mid — Fix + Validate Questions (Generated 2026-03-24)

### F-mid.1: Clear contaminated karen.md DSPy section and fix `_build_prompt()` rubric injection

**Status**: DONE
**Operational Mode**: fix
**Agent**: fix-implementer
**Priority**: HIGH
**Motivated by**: P3 (CASCADE_ACTIVE) — karen.md contaminated with research-analyst rubric from `optimize_with_claude.py` `_build_prompt()` hardcoding; `karen.json` `optimized_at: 2026-03-24T23:17:33Z` confirms live contamination. P3 peer review quality score 0.95 — all claims verified.
**Hypothesis**: Fix requires two changes: (A) strip the contaminated DSPy Optimized Instructions section from `karen.md` (and `~/.claude/agents/karen.md` on all machines) using `strip_optimized_instructions()`; (B) fix `_build_prompt()` in `optimize_with_claude.py` to inject the correct karen rubric when `--signature karen` is passed — weight distribution: `quality_score_proximity 0.5`, `action_match 0.3`, `changelog_quality 0.2`. Without fix (A), every karen invocation runs against research-analyst criteria. Without fix (B), the next optimization run will re-contaminate karen.md.
**Success criterion**: (1) Grep `karen.md` and `~/.claude/agents/karen.md` for `## DSPy Optimized Instructions` — confirm section absent post-fix. (2) Read `_build_prompt()` in `optimize_with_claude.py` — confirm signature-conditional rubric injection present. (3) Run `improve_agent.py karen --signature karen --dry-run` — confirm `before_score` reflects karen-specific metric, not research-analyst metric. Verdict: FIX_APPLIED if all three checks pass; PARTIAL if only strip is done without `_build_prompt()` fix.

---

### F-mid.2: Remove 15 mock_campaign records from `scored_all.jsonl` and add source-exclusion guard

**Status**: DONE
**Operational Mode**: fix
**Agent**: fix-implementer
**Priority**: HIGH
**Motivated by**: P2 (WARNING/High) — 15 records with `source: mock_campaign` in `scored_all.jsonl` are degrading `before_score` from 0.35 → 0.25 → 0.15 across optimization loops, effectively freezing the loop. P2 peer review CONFIRMED all 7 evidence points.
**Hypothesis**: Remove all records where `source == "mock_campaign"` from `scored_all.jsonl`. Add a filter in `_load_records()` in `optimize_with_claude.py` (line 44) to exclude records with `source` in a configurable exclusion list (`["mock_campaign", "test_campaign"]`). After cleanup, `before_score` should recover to ≥0.45 on next eval cycle.
**Success criterion**: (1) Count records in `scored_all.jsonl` before and after — confirm 15 fewer records. (2) Grep `scored_all.jsonl` for `mock_campaign` — confirm zero hits post-fix. (3) Read `_load_records()` in `optimize_with_claude.py` — confirm source-exclusion filter present. (4) Run `improve_agent.py research-analyst --dry-run` — confirm `before_score` ≥ 0.45. Verdict: FIX_APPLIED if all checks pass; PARTIAL if records removed but guard not added.

---

### V-mid.1: Verify F12.1 (confidence-based drift metric) is active end-to-end

**Status**: DONE
**Operational Mode**: validate
**Agent**: design-reviewer
**Priority**: HIGH
**Motivated by**: P6 (CONFIRMED/Critical) — drift scoring inversion is cascade-active. Four agents at CRITICAL drift (45–100%) because FAILURE=0.0. P6 mitigation recommends confidence-based `_score_verdicts()` as fix. V-mid.1 checks whether F12.1 was actually implemented. P6 peer review also flagged that `masonry/src/drift_detector.py` may differ from `masonry/src/dspy_pipeline/drift_detector.py`.
**Hypothesis**: F12.1 was tracked as a queued fix in prior synthesis. If implemented, `drift_detector.py` should contain a `confidences` parameter in `_score_verdicts()` and a confidence-weighted mean path. If NOT implemented, the four CRITICAL agents remain at inversion risk and `masonry_drift_check(auto_trigger=true)` must stay prohibited.
**Success criterion**: (1) Read `masonry/src/drift_detector.py` AND `masonry/src/dspy_pipeline/drift_detector.py` — determine which is canonical (imported by `mcp_server/server.py`). (2) Check `_score_verdicts()` signature — does it accept a `confidences` parameter? (3) Check whether `run_drift_check()` passes `confidences` from `agent_db.json` entries. (4) If confidence path exists, compute research-analyst's score with actual confidence values — confirm it flips from CRITICAL to ok. Verdict: PASS if F12.1 is fully active; FAIL if not implemented; PARTIAL if code exists but confidence data not plumbed through.

---

### F-mid.3: Add MIN_VERDICTS guard before auto_trigger fires in `masonry_drift_check`

**Status**: DONE
**Operational Mode**: fix
**Agent**: fix-implementer
**Priority**: MEDIUM
**Motivated by**: P6 (CONFIRMED/Critical) — benchmark-engineer at 100% drift from only 2 verdicts. A 2-sample statistical basis is insufficient to trigger `improve_agent.py`. P6 mitigation recommends a minimum sample threshold of ≥10 verdicts.
**Hypothesis**: Add `MIN_VERDICTS_FOR_AUTO_OPTIMIZE = 10` constant and gate the `auto_trigger` spawning block in `mcp_server/server.py` `_tool_masonry_drift_check()` (lines 438-497) — only spawn `improve_agent.py` if `len(agent_db_entry["verdicts"]) >= MIN_VERDICTS_FOR_AUTO_OPTIMIZE`. This prevents benchmark-engineer (2 verdicts) from triggering unnecessary optimization while the statistical basis is too small to be meaningful.
**Success criterion**: (1) Read `mcp_server/server.py` `_tool_masonry_drift_check()` — confirm MIN_VERDICTS guard present in `auto_trigger` block. (2) Verify benchmark-engineer's 2-verdict entry would be excluded by the guard. (3) Confirm research-analyst (29 verdicts) and diagnose-analyst (34 verdicts) would still pass the guard. Verdict: FIX_APPLIED if guard present and logic correct; PARTIAL if constant added but guard not wired in.

---

### V-mid.2: Verify F3.1 resolves interrupted-build resume output collision end-to-end

**Status**: DONE
**Operational Mode**: validate
**Agent**: design-reviewer
**Priority**: MEDIUM
**Motivated by**: P5 (CONFIRMED/High) — session-start interrupted-build cascade. P5 peer review found that F3.1 (empty hooks.json) has already been applied — `hooks/hooks.json` contains `{"hooks": {}}`. V-mid.2 validates this end-to-end: confirms the double-fire path is closed AND that cross-session build-guard gating remains the residual risk.
**Hypothesis**: With `hooks/hooks.json` empty, SessionStart fires only once (from `~/.claude/settings.json` registration). The interrupted-build fast path in `masonry-session-start.js` lines 67-78 should produce valid single-JSON output that Claude's hook framework can parse. The residual risk is `masonry-build-guard.js` session-ID gating (line 82-97: exits 0 on session mismatch), which remains unaddressed.
**Success criterion**: (1) Read `hooks/hooks.json` — confirm `{"hooks": {}}` or equivalent empty-hooks structure. (2) Read `~/.claude/settings.json` hook registrations — confirm SessionStart registered once (not twice). (3) Trace `masonry-session-start.js` interrupted-build fast path — confirm single JSON output would be valid. (4) Read `masonry-build-guard.js` lines 82-97 — confirm cross-session gating behavior and whether it surfaces any warning. Verdict: PASS if F3.1 effective and residual risk documented; FAIL if double-fire still possible; PARTIAL if F3.1 applied but stop-guard/build-guard residuals not assessed.

---

## Wave Next — Validation + Optimization Queue (Generated 2026-03-24)

### F-next.1: Implement F12.1 — confidence-based drift metric in drift_detector.py

**Status**: DONE
**Operational Mode**: fix
**Agent**: fix-implementer
**Priority**: HIGH
**Motivated by**: V-mid.1 (FAIL) — F12.1 not implemented; P6 (CONFIRMED/Critical) — drift scoring inversion CASCADE_ACTIVE. V-mid.1 confirmed `_score_verdicts()` has no confidence parameter; research-analyst at 45.2% CRITICAL drift.
**Hypothesis**: Add `confidences: list[float] | None = None` parameter to `_score_verdicts()` with confidence-weighted mean path; thread through `detect_drift()` and `run_drift_check()` which reads `entry.get("confidences", [])` from `agent_db.json`. Apply to both `masonry/src/drift_detector.py` (canonical) and `masonry/src/dspy_pipeline/drift_detector.py`.
**Success criterion**: `grep -n "confidences" masonry/src/drift_detector.py` returns 3+ hits; research-analyst drift computes to −7.4% (ok/improvement) from mean confidence 0.9131. Verdict: FIX_APPLIED if all checks pass.

---

### V-next.1: Verify F12.1 end-to-end — masonry_drift_check returns correct alert levels

**Status**: DONE
**Operational Mode**: validate
**Agent**: design-reviewer
**Priority**: HIGH
**Motivated by**: F-next.1 (FIX_APPLIED) — F12.1 implemented. V-next.1 validates the fix end-to-end by checking that research-analyst and diagnose-analyst flip from CRITICAL to ok/improvement, and that the MIN_VERDICTS guard (F-mid.3) correctly gates benchmark-engineer (2 verdicts).
**Hypothesis**: With F12.1 live in `masonry/src/drift_detector.py`, calling `run_drift_check()` should compute research-analyst current_score ≈ 0.9131 (mean confidence), drift ≈ −7.4%, alert = ok. Diagnose-analyst and design-reviewer should similarly show ok/WARNING based on their confidence means. Benchmark-engineer (2 verdicts) should be excluded by MIN_VERDICTS guard from auto_trigger path.
**Success criterion**: (1) Read `masonry/src/drift_detector.py` — confirm `_score_verdicts()` has confidence path (grep for "confidences"). (2) Read `agent_db.json` — get research-analyst confidence mean. (3) Compute expected drift with confidence-weighted score vs. baseline. (4) Verify MIN_VERDICTS guard present in `mcp_server/server.py`. Verdict: PASS if all four agents compute correctly; FAIL if confidence path missing; PARTIAL if path exists but wrong data plumbed.

---

### R-next.1: Does `improve_agent.py --dry-run` show before_score ≥ 0.50 for research-analyst after corpus cleanup?

**Status**: DONE
**Operational Mode**: research
**Agent**: research-analyst
**Priority**: HIGH
**Motivated by**: F-mid.2 (FIX_APPLIED, 135 mock records removed) + P2 (WARNING/High, before_score degraded 0.35 → 0.25 → 0.15). With the corpus clean and F12.1 active, the eval pipeline should now produce a meaningful before_score that enables improvement detection.
**Hypothesis**: After removing 135 mock_campaign records from `scored_all.jsonl`, the remaining 527 real records should produce a before_score ≥ 0.45 (P2 cap estimate) or possibly ≥ 0.50 if the contamination was the primary drag. If before_score is still < 0.45, additional corpus issues may exist (sparse low-scoring examples, mislabeled records, or rubric misalignment).
**Success criterion**: (1) Read `masonry/training_data/scored_all.jsonl` — confirm mock_campaign records absent (grep for "mock_campaign"). (2) Read `masonry/scripts/eval_agent.py` to understand eval sampling. (3) Compute expected before_score from remaining records using `_score_verdicts()` logic. (4) Determine if the eval would produce a score ≥ 0.45 or ≥ 0.50. Verdict: HEALTHY if ≥ 0.50; WARNING if 0.35–0.50; FAILURE if < 0.35 (still degraded despite cleanup).

---

### F-next.2: Fix build-guard cross-session warning visibility (V-mid.2 residual risk 1)

**Status**: DONE
**Operational Mode**: fix
**Agent**: fix-implementer
**Priority**: MEDIUM
**Motivated by**: V-mid.2 (WARNING) — `masonry-build-guard.js` exits 0 on session mismatch with stderr-only message not visible in Claude's conversation context. If user dismisses session-start resume directive, there is no Stop-time enforcement.
**Hypothesis**: Modify `masonry-build-guard.js` lines 86-91: add a `hookSpecificOutput` to the cross-session mismatch path alongside the existing stderr write. The hookSpecificOutput should name the orphaned build's project and task count, making the warning visible in Claude's conversation context at Stop time as a non-blocking second safety net. The `process.exit(0)` should remain — this is a warning, not a block.
**Success criterion**: (1) Read `masonry-build-guard.js` lines 82-97. (2) Add hookSpecificOutput to the `buildSessionId !== currentSessionId` branch. (3) Verify the exit code remains 0 (non-blocking). (4) Verify the hookSpecificOutput includes project name and orphaned task count. Verdict: FIX_APPLIED if hookSpecificOutput added; PARTIAL if message modified but not surfaced in-conversation.

---

### F-next.3: Add IN_PROGRESS task gate to stop-guard auto-commit (V-mid.2 residual risk 2)

**Status**: DONE
**Operational Mode**: fix
**Agent**: fix-implementer
**Priority**: MEDIUM
**Motivated by**: V-mid.2 (WARNING) — `masonry-stop-guard.js` auto-commits all session-touched files unconditionally with no test-pass gate, no IN_PROGRESS task guard, generic commit message. Partial interrupted-build implementations can enter git history without verification.
**Hypothesis**: Add a guard before the auto-commit block (line 296 in masonry-stop-guard.js): if `.autopilot/mode` is `"build"` or `"fix"` AND `progress.json` has any tasks with `status: "IN_PROGRESS"`, skip the auto-commit and emit a blocking message explaining that mid-task partial code will not be auto-committed. Also add the build task ID to the auto-commit message for traceability.
**Success criterion**: (1) Read `masonry-stop-guard.js` lines 280-320. (2) Add IN_PROGRESS task check before auto-commit. (3) Verify the check reads `.autopilot/progress.json` and inspects task statuses. (4) Verify the blocking message names the in-progress task. Verdict: FIX_APPLIED if guard present and logic correct; PARTIAL if guard added but message lacks task context.

---

## Wave 40 — Post-Fix Validation and Open Risk Closure

### V-w40.1: Verify karen corpus score distribution — is bimodal cliff still present after F-mid.1/F-mid.2?

**Status**: DONE
**Operational Mode**: validate
**Agent**: design-reviewer
**Priority**: HIGH
**Motivated by**: P3 (CONFIRMED) identified a 98.7%-at-100 bimodal cliff with 5 synthetic_negative records at score=0 using mismatched schema. F-mid.1 fixed the rubric injection but did NOT replace the 5 synthetic negatives or diversify the score distribution. P3 Fix 3 ("replace synthetic negatives with real organic examples") was listed as a precondition but not implemented.
**Hypothesis**: `scored_all.jsonl` still has the bimodal distribution for karen records: 374 records near score=100, 5 synthetic_negative records at score=0, zero records in the 10-89 range. This means the optimization contrast for karen is still derived from structurally mislabeled negatives, and `_tier_examples()` still selects arbitrary records from an undifferentiated high tier. The F-mid.1 rubric fix improves the *direction* of optimization but not the *gradient quality*.
**Success criterion**: (1) Count karen records in `scored_all.jsonl` by score band: score=100, 90-99, 50-89, 10-49, 0-9. (2) Check if any `synthetic_negative` records remain. (3) Verify whether `build_karen_metric` produces scores in the 10-89 range for any real records. (4) Assess whether the low-tier records are structurally valid contrast examples. Verdict: HEALTHY if ≥ 10 real records below score 50 with valid schema; WARNING if only synthetic_negative records remain as low tier; FAIL if distribution is still bimodal cliff.

---

### R-w40.1: Does karen.md DSPy section contain any research-analyst behavioral patterns on this machine?

**Status**: DONE
**Operational Mode**: research
**Agent**: research-analyst
**Priority**: HIGH
**Motivated by**: P3 (CONFIRMED) identified that `writeback_optimized_instructions()` propagates to ALL karen.md copies including `~/.claude/agents/karen.md`. F-mid.1 cleared the global copy on casaclaude. However: (a) the fix may not have reached proxyclaude's ~/.claude/agents/karen.md, and (b) project-level copies in bricklayer-v2, bl-audit, and template directories were explicitly preserved. The research-analyst behavioral patterns (verdict calibration, evidence length, confidence targeting) may still be active in project-level karen.md copies used by agents spawned from those directories.
**Hypothesis**: At least one of the project-level karen.md copies (`.claude/agents/karen.md` in bricklayer-v2/, bl-audit/, template/) contains a DSPy Optimized Instructions section with research-analyst behavioral patterns. These are not the global copy but would affect karen agents spawned from those project contexts.
**Success criterion**: (1) `grep -rn "DSPy Optimized Instructions" C:/Users/trg16/Dev/Bricklayer2.0/` — count hits. (2) For any hits, check if content references "verdict match", "evidence quality", or "confidence calibration" (research-analyst rubric markers). (3) Verify the global `~/.claude/agents/karen.md` is clean. Verdict: HEALTHY if only global copy is present and clean; WARNING if project-level copies contain research-analyst DSPy content; FAIL if global copy was re-contaminated.

---

### F-w40.1: Add circuit breaker to semantic.py for Ollama timeout (P1 residual)

**Status**: DONE
**Operational Mode**: fix
**Agent**: fix-implementer
**Priority**: MEDIUM
**Motivated by**: P1 (CONFIRMED) identified that when Ollama is offline, Layer 2 (semantic routing) hangs for the full HTTP timeout before propagating to Layer 3 (LLM fallback). The cascade: Layer 2 timeout → blocking wait → all routes stall → deterministic Layer 1 handles only slash commands; everything else waits. P1 recommended a circuit breaker with configurable timeout and failure tracking.
**Hypothesis**: `masonry/src/routing/semantic.py` has no circuit breaker — it makes a direct HTTP call to Ollama's embedding endpoint with no per-call timeout guard, no failure counter, and no fast-fail path. Adding a 2-second per-call timeout with a circuit breaker (e.g., after 3 consecutive failures, skip Layer 2 for 60 seconds) would eliminate the cascade.
**Success criterion**: (1) Read `masonry/src/routing/semantic.py` — identify the Ollama HTTP call. (2) Add a per-call timeout (≤ 2 seconds). (3) Add a circuit breaker state (failure_count, last_failure_time, OPEN/CLOSED state). (4) When OPEN, skip Layer 2 and fall through to Layer 3 immediately. (5) Reset after 60 seconds or on next success. Verdict: FIX_APPLIED if circuit breaker present with correct timeout and state machine; PARTIAL if timeout added but no circuit state.

---

### R-w40.2: P4 subagent tracker slot collision — what records are actually lost or corrupted?

**Status**: DONE
**Operational Mode**: research
**Agent**: research-analyst
**Priority**: LOW
**Motivated by**: P4 (peer review: CONCERNS) — the 16.7% near-collision rate in `masonry-subagent-tracker.js` was flagged but the actual downstream impact was unquantified. Each slot overwrites `${subagentType}_latest.json` when two agents of the same type start within the 10-second window. The question is: does this affect any downstream consumer that reads these files, and is the corruption observable in agent_db.json or training data?
**Hypothesis**: The `${subagentType}_latest.json` files are read by analytics or onboarding scripts that use the data for training record attribution. If a collision overwrites a record, the earlier agent's data may be attributed to the wrong session or lost entirely. However, if the files are only used for in-session tracking with no durable read-back, the 16.7% collision rate is a logging gap with no functional impact.
**Success criterion**: (1) Read `masonry-subagent-tracker.js` — identify what `${subagentType}_latest.json` contains and who reads it. (2) Search for any script that reads from `agent_snapshots/*/` or `latest.json` files. (3) Determine if lost slots produce missing records in `agent_db.json` or `scored_all.jsonl`. (4) Assess actual vs. theoretical damage. Verdict: HEALTHY if collision has no downstream data impact; WARNING if records are lost but not corrupted; FAIL if agent_db.json attribution errors are traceable to P4 collisions.

---

### F-w40.2: Fix dead `optimized_prompt` field in improve_agent.py comparison report (P7)

**Status**: DONE
**Operational Mode**: fix
**Agent**: fix-implementer
**Priority**: LOW
**Motivated by**: P7 (CONFIRMED/DORMANT) — `improve_agent.py` reads `optimized_prompt` from the optimization output JSON but `optimize_with_claude.py` no longer writes this field (the field was removed in an earlier refactor). The comparison report logs an empty or missing field. This is a cosmetic bug — the optimization loop works correctly — but the before/after report is misleading.
**Hypothesis**: `improve_agent.py` has a line like `optimized = result.get("optimized_prompt", "")` or similar that reads a field no longer written by `optimize_with_claude.py`. The fix is to either (a) remove the field read and display `instructions_applied: true/false` instead, or (b) restore the field write in `optimize_with_claude.py`. Option (a) is simpler.
**Success criterion**: (1) Read `masonry/scripts/improve_agent.py` — find all references to `optimized_prompt`. (2) Read `masonry/scripts/optimize_with_claude.py` output schema — confirm `optimized_prompt` is absent. (3) Remove or replace the dead field read in `improve_agent.py`. (4) Verify the before/after comparison report still shows meaningful diff (before_score, after_score, delta, instructions excerpt). Verdict: FIX_APPLIED if dead field removed and report still meaningful; PARTIAL if removed but report loses information.

---

### P-w40.1: If improve_agent.py runs now (all cascades fixed), what new failure modes could the optimization loop introduce?

**Status**: DONE
**Operational Mode**: predict
**Agent**: cascade-analyst
**Priority**: MEDIUM
**Motivated by**: R-next.1 (HEALTHY) confirmed before_score=0.5333 and the optimization pipeline is unblocked. The cascades that previously corrupted optimization (P2 corpus, P3 rubric, P6 drift) are resolved. However, the optimization loop introduces its own risks: LLM-generated instruction changes may degrade agent behavior in ways not captured by the eval metric, the revert gate may have edge cases, and the write-back mechanism may overwrite content beyond the DSPy section boundaries.
**Hypothesis**: The optimization loop has at least three residual risks now that it's unblocked: (1) The held-out eval metric only measures verdict/evidence/confidence quality — it cannot detect degradation in agent reasoning style, context handling, or edge-case behavior. (2) The revert gate (compare before_score vs. after_score) has a ±0.05 noise band — small degradations below this band will not trigger a revert. (3) `writeback_optimized_instructions()` uses delimiter-based replacement that could corrupt agent instructions if the delimiter appears in the generated content.
**Success criterion**: Identify the specific failure modes that remain possible after the three cascades are resolved, with evidence from code inspection of `improve_agent.py`, `optimize_with_claude.py`, and `writeback.py`. Assess severity and probability. Predict which agents are at highest risk for silent degradation after optimization. Verdict: CONFIRMED if failure modes are real and code-evidenced; INCONCLUSIVE if risks are theoretical without code support.

---

## Wave 41 — Optimization Safety Gates + Karen Corpus Unblock

### F-w41.1: Enforce train/eval split in scored_all.jsonl to close P-w40.1 convergence trap

**Status**: PENDING
**Operational Mode**: fix
**Agent**: fix-implementer
**Priority**: HIGH
**Motivated by**: P-w40.1 (CONFIRMED/IMMINENT) — E5 convergence trap: `eval_agent.py` uses `records[-eval_size:]` and `_tier_examples()` uses all records sorted by score — these overlap when corpus is small, causing the optimizer to see its own eval examples.
**Hypothesis**: Add a `held_out_ids` exclusion: mark the last N record IDs as held-out in `eval_agent.py`, pass those IDs to `optimize_with_claude.py` so `_tier_examples()` excludes them from the optimization pool. Add guard: if remaining records after exclusion < 10 per tier, warn and skip optimization.
**Success criterion**: (1) Read `eval_agent.py` — how held-out records are selected. (2) Read `_tier_examples()` — confirm overlap possible. (3) Implement held-out exclusion. (4) Add low-record guard. Verdict: FIX_APPLIED if split enforced + guard present; PARTIAL if split enforced but no guard.

---

### F-w41.2: Increase eval size to N=50 and add minimum improvement threshold to revert gate

**Status**: PENDING
**Operational Mode**: fix
**Agent**: fix-implementer
**Priority**: HIGH
**Motivated by**: P-w40.1 (CONFIRMED/IMMINENT) — E1 revert gate dead zone: N=20 minimum delta 0.05, stochasticity ~11% stddev. Sub-5% real regressions pass silently.
**Hypothesis**: Change default `--eval-size` from 20 to 50. Add `MIN_IMPROVEMENT = 0.02` constant and update gate from `after_score > before_score` to `after_score >= before_score + MIN_IMPROVEMENT`. Ties and marginal changes revert rather than lock in.
**Success criterion**: (1) Read `improve_agent.py` — find eval_size default and revert gate line (~151). (2) Change default to 50. (3) Add MIN_IMPROVEMENT=0.02 and update gate condition. (4) Report logs the threshold. Verdict: FIX_APPLIED if both changes applied; PARTIAL if only one.

---

### F-w41.3: Sanitize DSPy delimiters in writeback to prevent E3 corruption

**Status**: PENDING
**Operational Mode**: fix
**Agent**: fix-implementer
**Priority**: MEDIUM
**Motivated by**: P-w40.1 (CONFIRMED/POSSIBLE) — E3 delimiter corruption: `writeback.py` uses delimiter strings as regex anchors with no sanitization. If LLM-generated instructions contain the delimiter, the section replacement breaks.
**Hypothesis**: Before writing instructions, check if content contains `_SECTION_HEADER` or `_SECTION_END` strings — if found, strip or escape them. After writeback, validate by re-parsing the DSPy section and confirming it matches what was written.
**Success criterion**: (1) Read `masonry/src/writeback.py` — find delimiter constants and regex replacement. (2) Add pre-write sanitization. (3) Add post-write validation. Verdict: FIX_APPLIED if both present; PARTIAL if only sanitization added.

---

### F-w41.4: Fix karen corpus — add synthetic_negative to exclusions + generate organic low-quality records

**Status**: PENDING
**Operational Mode**: fix
**Agent**: fix-implementer
**Priority**: HIGH
**Motivated by**: V-w40.1 (FAIL, High) — Karen corpus bimodal cliff: 5 synthetic_negative records at score=0 not in `_EXCLUDED_SOURCES`. Karen optimization blocked until fixed.
**Hypothesis**: (1) Add `"synthetic_negative"` to `_EXCLUDED_SOURCES` in `optimize_with_claude.py`. (2) Add guard when low tier is empty — warn and exit rather than optimize with no contrast. (3) Generate 5-10 synthetic organic karen records with genuine low scores (ambiguous commit types, no doc targets), score with `build_karen_metric`, add as `"source": "organic_low"` to `scored_all.jsonl`.
**Success criterion**: (1) `"synthetic_negative"` in `_EXCLUDED_SOURCES`. (2) Empty-low-tier guard present. (3) ≥ 5 new organic_low records with score < 50. (4) `_tier_examples()` for karen produces valid high + low tiers. Verdict: FIX_APPLIED if all four; PARTIAL if exclusion added but no organic records.

---

### V-w41.1: Verify F-w40.1 circuit breaker — does semantic.py fall through to Layer 3 when OPEN?

**Status**: PENDING
**Operational Mode**: validate
**Agent**: design-reviewer
**Priority**: MEDIUM
**Motivated by**: F-w40.1 (FIX_APPLIED) — circuit breaker added to `semantic.py`. Validates the fall-through contract: OPEN → None → router activates Layer 3.
**Hypothesis**: `route_semantic()` returns None when OPEN (not raises). `router.py` treats None from Layer 2 as a miss and falls through to Layer 3. Timeout is on the HTTP call parameter. Circuit state is module-level.
**Success criterion**: (1) semantic.py OPEN path returns None. (2) router.py handles None from Layer 2 → Layer 3. (3) Timeout on HTTP call not a sleep/thread. (4) `_cb_failures`, `_cb_opened_at` are module-level. Verdict: PASS if all four; PARTIAL if OPEN returns None but router doesn't handle it.
