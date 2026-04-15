# Hook Enforcement Audit — BrickLayer 2.0 / Masonry
**Date:** 2026-04-15  
**Reviewer:** Claude Code (hook-enforcement-audit skill)  
**Scope:** All hooks registered in `~/.claude/settings.json` + all files in `masonry/src/hooks/`  
**Method:** Read-only. No hook files modified.  
**Note:** Writing this file was blocked by `masonry-routing-gate.js` until the gate was manually cleared — live confirmation that Track A enforcement is working correctly.

---

## 1. Hook Inventory

63 hook files found in `masonry/src/hooks/`. Registered event coverage:

| Event | Hook Count | Notes |
|-------|-----------|-------|
| SessionStart | 2 | masonry-session-start + cozempic guard/digest |
| UserPromptSubmit | 6 | guard-flush, recall-retrieve, register, prompt-router, prompt-inject, better-hook |
| PreToolUse | 13 registered entries | 8 distinct matcher groups |
| PostToolUse | 12 registered entries | 6 distinct matcher groups |
| PostToolUseFailure | 1 | masonry-tool-failure |
| SubagentStart | 1 | masonry-subagent-tracker |
| SubagentStop | 2 | masonry-agent-complete, masonry-auto-pr |
| TeammateIdle / TaskCompleted | 1 each | masonry-teammate-idle (shared) |
| Stop | 3 entries | masonry-token-logger, masonry-stop-checker (→4 guards), masonry-stop-runner (→11 background tasks) |
| SessionEnd | 1 | masonry-session-end |
| PreCompact / PostCompact | 2 each | masonry-pre-compact / masonry-post-compact + cozempic |
| Notification | 1 | better-hook |

---

## 2. Hook Authority Classification

### 2a. PreToolUse Enforcement Hooks

| Hook | Matcher | Authority | Mechanism |
|------|---------|-----------|-----------|
| masonry-routing-gate.js | Write\|Edit | **HARD BLOCK** | `process.exit(2)` |
| masonry-pre-protect.js (Phase 1) | Write\|Edit | **HARD BLOCK** | `{ decision: "block", reason }` via stdout |
| masonry-pre-protect.js (Phase 1.5) | Write\|Edit | **ADVISORY** | `process.stderr.write(...)` then exit 0 |
| masonry-block-no-verify.js | Bash | **HARD BLOCK** | `{ decision: "block", reason }` + exit 2 |
| masonry-dangerous-cmd.js | Bash | **HARD BLOCK** | `{ decision: "block", reason }` + exit 2 |
| masonry-bash-trim.js | Bash | **INJECT** | `{ systemMessage: ... }` advisory only |
| masonry-approver.js (Mortar gate) | Write\|Edit\|Bash | **ADVISORY** (default) / **HARD DENY** (flag) | stderr advisory; `permissionDecision: "deny"` behind `MASONRY_ENFORCE_ROUTING=1` |
| masonry-dep-audit.js | Write\|Edit | **ADVISORY** | stderr only, exit 0 always |
| masonry-content-guard.js | Write\|Edit | **HARD BLOCK** | exit 2 (secrets + lint config + .env) |
| masonry-context-safety.js | ExitPlanMode | **HARD BLOCK** | `permissionDecision: "block"` + exit 2 |
| masonry-mortar-enforcer.js | Agent | **HARD BLOCK** | `{ decision: "block", reason }` |
| masonry-read-dedup.js | Read | **HARD BLOCK** | `permissionDecision: "block"` + exit 2 |
| masonry-jcodemunch-nudge.js | Read | **ADVISORY** (<8KB) / **HARD BLOCK** (≥8KB) | stderr nudge / exit 2 |

### 2b. PostToolUse Enforcement Hooks

| Hook | Matcher | Authority | Mechanism |
|------|---------|-----------|-----------|
| masonry-tdd-enforcer.js | Write\|Edit | **ADVISORY** (default) / **HARD BLOCK** (/build mode) | stderr / exit 2 |
| masonry-file-size-guard.js | Write\|Edit | **ADVISORY** (>400 lines) / **HARD BLOCK** (>600 lines) | stderr / exit 2 |
| masonry-hook-watch.js | Write\|Edit | Async validator | exit 0 always (async) |
| masonry-agent-complete.js | Agent | Tracker | async, advisory |
| masonry-auto-pr.js | Agent | PR creation | async, advisory |
| masonry-guard.js | (all) | 3-strike error monitor | advisory |
| masonry-mistake-monitor.js | Bash | Error recorder | advisory |
| masonry-read-tracker.js | Read | Activity tracking | advisory |

### 2c. Stop Guards (via masonry-stop-checker.js orchestrator)

| Guard | Authority | Notes |
|-------|-----------|-------|
| masonry-stop-guard.js | **HARD BLOCK** (exit 2) | Auto-commits session files; blocks if commit fails |
| masonry-build-guard.js | **HARD BLOCK** (exit 2) | Blocks if build IN_PROGRESS for this session |
| masonry-ui-compose-guard.js | **HARD BLOCK** (exit 2) | Blocks if UI compose IN_PROGRESS |
| masonry-context-monitor.js | **HARD BLOCK** (>750K tokens + dirty) / **ADVISORY** (clean) | Semantic checks advisory |

---

## 3. State File Analysis

Two separate state stores are used for Mortar gating:

| Store | Path | Writer | Reader |
|-------|------|--------|--------|
| Gate file | `/tmp/masonry-mortar-gate.json` | `masonry-prompt-router.js` (→false) + `masonry-subagent-tracker.js` (→true) | `masonry-routing-gate.js`, `masonry-pre-protect.js` Phase 1.5 |
| Masonry state | `masonry/masonry-state.json` | `masonry-prompt-router.js` (last_route only, not mortar_consulted) | `masonry-approver-helpers.js::isMortarConsulted()` |

**Live state of `/tmp/masonry-mortar-gate.json` at audit start:**
```json
{"mortar_consulted":false,"timestamp":"2026-04-15T19:08:22.893Z","prompt_summary":"can we do a full audit..."}
```
Written by masonry-prompt-router.js at turn start — working correctly.

**Live state of `masonry/masonry-state.json`:**
```json
{
  "mortar_consulted": true,
  "mortar_session_id": "2026-04-04T15:45:35.687Z",
  ...
}
```
`mortar_session_id` is **11 days stale**. MORTAR_SESSION_FRESHNESS_MS = 4 hours → `isMortarConsulted()` always returns **false**.

---

## 4. Enforcement Gap Analysis

### CRITICAL — Orphaned checker: `isMortarConsulted()` reads wrong state store

**Hook:** `masonry-approver.js`  
**File:** `masonry/src/hooks/masonry-approver-helpers.js:96–107`

```js
function isMortarConsulted() {
  const state = JSON.parse(readFileSync(MASONRY_STATE_PATH, "utf8"));
  if (!state.mortar_consulted) return false;        // always false — never freshly updated
  if (!state.mortar_session_id) return false;
  return Date.now() - sessionTime < MORTAR_SESSION_FRESHNESS_MS;  // 4 hour TTL
}
```

**MASONRY_STATE_PATH** = `masonry/masonry-state.json`  
**What writes `mortar_consulted` to masonry-state.json?** → **Nothing currently active.**

`masonry-subagent-tracker.js` (line 76–83) writes `mortar_consulted: true` to `/tmp/masonry-mortar-gate.json` — a **different file** from what `isMortarConsulted()` reads. The fields `mortar_consulted` and `mortar_session_id` in `masonry-state.json` are vestigial from an earlier architecture and are never updated at runtime.

**Impact:**
- `isMortarConsulted()` always returns false → advisory fires on every Write/Edit (harmless noise)
- **If `MASONRY_ENFORCE_ROUTING=1` is ever set**, it would cause a hard deny on **every** Write/Edit regardless of whether routing was actually performed, because the writer is missing
- The actual routing gate (masonry-routing-gate.js via /tmp gate file) works correctly — these are two separate, conflicting systems

**Severity: CRITICAL** (not immediately harmful, but makes MASONRY_ENFORCE_ROUTING unusable)

---

### HIGH — Two-track Mortar gate: parallel systems with conflicting state

**Hooks affected:** `masonry-routing-gate.js` (Track A) vs `masonry-approver.js` (Track B)

| | Track A | Track B |
|-|---------|---------|
| State file | `/tmp/masonry-mortar-gate.json` | `masonry/masonry-state.json` |
| Writer | prompt-router + subagent-tracker | **missing** |
| Reader | masonry-routing-gate.js | masonry-approver.js (isMortarConsulted) |
| Authority | HARD BLOCK (exit 2) | ADVISORY (stderr) / flag-gated deny |
| Status | **Correctly wired** | **Orphaned checker** |

Track A is the real enforcement system and works. Track B is dead infrastructure. They should be unified — Track B should either be removed or updated to read from the same `/tmp` gate file.

**Severity: HIGH**

---

### HIGH — Context safety check: unreachable threshold via primary code path

**Hook:** `masonry-context-safety.js` (PreToolUse:ExitPlanMode)  
**File:** `masonry/src/hooks/masonry-context-safety.js:44–50`

```js
if (obj.context_window?.used_percentage != null) {
  // CC reports % against 200K; Sonnet/Opus 4.6 have 1M window — rescale
  return Math.round(obj.context_window.used_percentage * 0.2);
}
```

The 0.2 scaling factor is applied to a value that is already a percentage (0–100). To reach `HIGH_CONTEXT_PCT = 80`, `used_percentage` would need to equal 400 — impossible. This code path never produces a block.

The fallback path (`usage.input_tokens / usage.context_window * 100`) would work correctly, but it depends on transcript event structure that may not always appear. In practice, `estimateContextPct()` returns 0 most of the time → the ExitPlanMode context check is functionally disabled.

**Note:** `masonry-context-monitor.js` (Stop hook) uses a separate size-based estimate that works correctly, so context protection at Stop time is intact.

**Fix:** Remove the `* 0.2` multiplier, or adjust threshold to `HIGH_CONTEXT_PCT = 16`:
```js
// Remove the rescaling — trust CC's reported %
return Math.round(obj.context_window.used_percentage);
```

**Severity: HIGH** (ExitPlanMode context guard is dead; can exit plan mode at any context level)

---

### MEDIUM — masonry-pre-protect.js Phase 1.5 is a soft duplicate of masonry-routing-gate.js

**Hook:** `masonry-pre-protect.js` (PreToolUse:Write|Edit, lines 110–151)

Phase 1.5 checks the same `/tmp/masonry-mortar-gate.json` as `masonry-routing-gate.js` but only emits a stderr advisory instead of blocking. Both hooks fire on Write|Edit in series. The routing-gate does real enforcement; Phase 1.5 adds advisory noise after an already-blocked attempt would never reach it.

Also: Phase 1.5 uses a **5-minute** freshness window; routing-gate uses **10 minutes** — inconsistency with no clear rationale.

**Recommendation:** Remove Phase 1.5 from masonry-pre-protect.js. Routing-gate handles the enforcement.

**Severity: MEDIUM** (functional duplicate, not dangerous)

---

### MEDIUM — masonry-dep-audit.js audits pre-write state

**Hook:** `masonry-dep-audit.js` (PreToolUse:Write|Edit)

Runs npm/pip audit before the file is written, meaning it audits the **current** package.json/requirements.txt, not the one about to be written. A Write that adds a vulnerable dependency won't be caught at this point.

Since the hook is advisory-only (exits 0 always), there's no blocking issue — but it's misregistered. Should be PostToolUse to catch newly-added vulnerabilities.

**Severity: MEDIUM** (advisory only, not harmful)

---

### LOW — masonry-jcodemunch-nudge.js: hard block at 8KB is too aggressive

**Hook:** `masonry-jcodemunch-nudge.js` (PreToolUse:Read)

Hard blocks full reads of source files ≥8KB. The 8KB threshold is low — many legitimate source files exceed this and sometimes need to be read whole (first read on an unfamiliar codebase section, refactoring context). The bypass requires adding `offset=0` which abuses offset semantics.

The read-dedup hook already prevents redundant re-reads. The nudge's hard block adds friction on legitimate first reads.

**Recommendation:** Raise `BLOCK_THRESHOLD` from 8KB to 20KB, or make the hook advisory-only throughout.

**Severity: LOW**

---

### LOW — masonry-guard.js: broad error regex patterns

**Hook:** `masonry-guard.js` (PostToolUse, no matcher)

Uses patterns like `/\bError\b/`, `/\bnot found\b/i`, `/\bundefined\b/i` across tool responses. Very broad — any response containing these words (including in code output, doc strings, variable names) matches. The hook is advisory and async, so no blocking issue, but 3-strike accumulation from false positives generates confusing noise.

**Severity: LOW**

---

## 5. Summary Table

| # | Hook | Event | Gap Type | Severity | Blocks Today? |
|---|------|-------|----------|----------|---------------|
| 1 | masonry-approver.js (isMortarConsulted) | PreToolUse | **Orphaned checker** — writer missing for masonry-state.json | **CRITICAL** | No (only if MASONRY_ENFORCE_ROUTING=1) |
| 2 | masonry-routing-gate.js vs masonry-approver.js | PreToolUse | **Two-track confusion** — parallel systems, Track B dead | **HIGH** | No (Track A works) |
| 3 | masonry-context-safety.js | PreToolUse:ExitPlanMode | **Dead code path** — `* 0.2` makes threshold unreachable | **HIGH** | No (context guard functionally disabled for ExitPlanMode) |
| 4 | masonry-pre-protect.js Phase 1.5 | PreToolUse | **Soft duplicate** advisory, redundant noise | **MEDIUM** | No |
| 5 | masonry-dep-audit.js | PreToolUse (wrong event) | Audits pre-write state instead of post-write | **MEDIUM** | No (advisory only) |
| 6 | masonry-jcodemunch-nudge.js | PreToolUse:Read | Hard block threshold too low (8KB) | **LOW** | Yes for large first-reads |
| 7 | masonry-guard.js | PostToolUse | Broad regex, false positive risk | **LOW** | No |

**Hard-blocking hooks (fully working):** 9  
**Advisory-only hooks:** 6  
**Advisory-with-flag (safe pin):** 1 (masonry-approver Mortar gate)  
**Orphaned checkers (writer missing):** 1 (isMortarConsulted in masonry-approver-helpers)

---

## 6. Fully Functional Gates (No Gaps)

- **masonry-routing-gate.js** — Track A Mortar gate, correctly wired via /tmp gate file ✓
- **masonry-block-no-verify.js** — Blocks `--no-verify` and `git push --force` ✓
- **masonry-dangerous-cmd.js** — Blocks `git stash drop`, `git reset --hard` (dirty), force-push to main ✓
- **masonry-content-guard.js** — Secret scanner + lint config + .env protection ✓
- **masonry-mortar-enforcer.js** — Agent hierarchy enforcement ✓
- **masonry-read-dedup.js** — Read deduplication with per-turn cache clear ✓
- **masonry-tdd-enforcer.js** — TDD enforcement in /build mode ✓
- **masonry-file-size-guard.js** — 600-line hard limit ✓
- **masonry-stop-guard.js** — Auto-commit + hard block on uncommitted session files ✓
- **masonry-build-guard.js** — IN_PROGRESS build protection ✓
- **masonry-ui-compose-guard.js** — IN_PROGRESS UI compose protection ✓
- **masonry-pre-protect.js Phase 1** — Cross-session session lock ✓
- **masonry-context-monitor.js** — 750K token + dirty state hard block ✓

---

## 7. Recommendations (Prioritized)

### P1 — Fix isMortarConsulted() state store mismatch ⚠️ BEFORE enabling MASONRY_ENFORCE_ROUTING

In `masonry/src/hooks/masonry-approver-helpers.js`, update `isMortarConsulted()` to read from `/tmp/masonry-mortar-gate.json`:

```js
function isMortarConsulted() {
  try {
    const os = require('os');
    const gateFile = process.env.BL_GATE_FILE || require('path').join(os.tmpdir(), 'masonry-mortar-gate.json');
    const gate = JSON.parse(readFileSync(gateFile, 'utf8'));
    if (!gate.mortar_consulted) return false;
    const gateAge = Date.now() - new Date(gate.timestamp || 0).getTime();
    return gateAge < 10 * 60 * 1000; // match routing-gate's 10-minute window
  } catch {
    return false;
  }
}
```

Then clean up stale `mortar_consulted` / `mortar_session_id` from `masonry/masonry-state.json`.

### P2 — Fix context safety scaling bug

In `masonry/src/hooks/masonry-context-safety.js:47`, remove the `* 0.2` multiplier:

```js
// Remove rescaling — report raw percentage
return Math.round(obj.context_window.used_percentage);
```

### P3 — Move masonry-dep-audit.js to PostToolUse

In `settings.json`, move the dep-audit entry from PreToolUse to PostToolUse so it audits the actual written state.

### P4 — Remove masonry-pre-protect.js Phase 1.5

Delete lines 110–151 (the mortar routing advisory block) from `masonry-pre-protect.js`. masonry-routing-gate.js handles real enforcement.

### P5 — Raise jcodemunch-nudge hard block threshold

In `masonry/src/hooks/masonry-jcodemunch-nudge.js`, change:
```js
const BLOCK_THRESHOLD = 20 * 1024;  // raise from 8KB to 20KB
```

---

## 8. Deployment Prerequisites for MASONRY_ENFORCE_ROUTING=1

**Current status: NOT SAFE to enable.**

| Prerequisite | Status |
|-------------|--------|
| Track A (routing-gate via /tmp gate file) working | ✅ PRESENT |
| Per-turn gate reset (prompt-router writes false at turn start) | ✅ PRESENT |
| Gate writer for Track A (subagent-tracker writes true) | ✅ PRESENT |
| **isMortarConsulted() reading correct store** | ❌ **MISSING — fix P1 first** |

Once P1 is fixed, enable with:
```bash
# In ~/.claude/settings.json env block:
"MASONRY_ENFORCE_ROUTING": "1"
```
