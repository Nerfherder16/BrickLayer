# Hook Injection Audit
**Date:** 2026-04-06
**Scope:** UserPromptSubmit and lifecycle hooks in `masonry/src/hooks/` + `~/.claude/recall-hooks/recall-retrieve.js`
**Method:** Read-only static analysis of hook source files

---

## Summary Table

| Hook | Event | Output Key | Fires | Est. Max Tokens | Flag |
|------|-------|-----------|-------|-----------------|------|
| `masonry-register.js` | UserPromptSubmit | `additionalContext` | Every prompt | 200–700 | YES (first call w/ handoff) |
| `masonry-prompt-router.js` | UserPromptSubmit | `additionalContext` | Prompts > 20 chars, non-slash | 100–250 | No |
| `masonry-prompt-inject.js` | UserPromptSubmit | `additionalContext` | Every prompt (Recall available) | 100–200 | No |
| `masonry-guard-flush.js` | UserPromptSubmit | `systemMessage` | Only when guard queue file exists | 50–200 | No |
| `masonry-bash-trim.js` | PreToolUse (Bash) | `systemMessage` | Per Bash call matching patterns | 50–100 | No |
| `masonry-session-start.js` | SessionStart | `systemMessage` | Once per session | 500–2500+ | **YES** |
| `masonry-pre-compact.js` | PreCompact | `systemMessage` | On context compaction | 200–600 | YES |
| `masonry-post-compact.js` | PostCompact | `systemMessage` | After context compaction | 200–600 | YES |
| `recall-retrieve.js` | UserPromptSubmit | `additionalContext` | Every prompt (Recall available) | 200–600 | YES |

---

## Per-Hook Analysis

### 1. `masonry-register.js` — Mortar Routing Directive

**Event:** UserPromptSubmit (every prompt)
**Output key:** `additionalContext`

**What it injects:**

On every subsequent call (session already seen):
```
[MASONRY] Route this prompt through Mortar (.claude/agents/mortar.md).
Mortar is the executive layer — it decides how to handle every request.
[optional: Active campaign: <project>, wave N, M questions pending.]
[optional: Active build: <project>, N/M tasks complete.]
```
Estimated ~50–100 tokens for the base directive + campaign/build state lines.

On first call with a valid handoff document from Recall (< 24h old), it additionally injects:
```
[MASONRY] Resuming campaign for "<project>"
<resume_prompt text from handoff>
Recent findings:
  Q123 — WARNING (high): <summary>
  ...
```
The `resume_prompt` in a handoff document has no enforced length cap. In practice handoff summaries are 200–500 words, making this path **400–900 tokens**. With 5 recent findings each truncated to 150 chars, add ~100 tokens.

On first call without a handoff but with findings from Recall (up to 5, truncated to 150 chars each):
```
[MASONRY] Context for "<project>" — recent findings:
  • <snippet up to 150 chars>
  ...
```
Estimated 100–200 tokens.

**Flag:** First-call-with-handoff path can exceed 500 tokens. Normal path is well under.

---

### 2. `masonry-prompt-router.js` — Intent Routing Hint

**Event:** UserPromptSubmit (fires when prompt > 20 chars, not a slash command, not inside a BL research project, no active campaign)
**Output key:** `additionalContext`

**What it injects:**

For dev tasks (most common path), the hint text is:
```
[MASONRY ROUTING — DO NOT SKIP]
Route to: <agent> [effort:<level>]

You are an orchestrator. Do NOT read files and write code directly.
Spawn rough-in DIRECTLY for this dev task:

  Task tool: subagent_type="rough-in", prompt="<first 200 chars of prompt>"

WHY: Rough-in reads the codebase, selects from 100+ specialist agents, builds a wave plan,
and hands parallel dispatch to Queen Coordinator (up to 8 workers). Direct inline work
skips code review, skips TDD, and uses your main context for implementation instead of
preserving it for orchestration.
```
The fixed frame is ~110 tokens. The prompt echo is capped at 200 chars (~50 tokens). Total: **~160–200 tokens** for dev routing.

Self-invoke bypass (`@agent-name: ...`) injects a shorter message (~80 tokens).

Low-effort classification: ~10 tokens ("Answer inline — no agent needed for simple lookups").

No injection when `hasSignal` is false (medium effort + no route matched).

**Flag:** None. Peak is ~200 tokens, always conditional.

---

### 3. `masonry-prompt-inject.js` — Recall Memory Context

**Event:** UserPromptSubmit (every prompt where Recall is available and returns results)
**Output key:** `additionalContext`

**What it injects:**
```
[RECALL] Relevant context from memory:
- <up to 200 chars of content>
- <up to 200 chars of content>
- <up to 200 chars of content>
```
Capped at `MAX_RESULTS = 3` entries × 200 chars each = 600 chars = **~150 tokens** maximum.

Uses threshold `min_importance = 0.15` (low bar — most memories qualify).

**Note:** This is a different file from `recall-retrieve.js`. This is the simpler in-repo version at `masonry/src/hooks/masonry-prompt-inject.js`. See also recall-retrieve.js below for the more complex global hook.

**Flag:** None. Hard-capped and modest.

---

### 4. `masonry-guard-flush.js` — 3-Strike Warnings

**Event:** UserPromptSubmit (only fires when `masonry-guard-<sessionId>.ndjson` exists in `/tmp`)
**Output key:** `systemMessage`

**What it injects:**
```
[Masonry Guard] N 3-strike warning(s) from prior tool calls:
  • <message from JSON entry>
  • <message from JSON entry>
Investigate root cause before retrying these patterns.
```
One entry per strike. Messages are free-form strings from `masonry-mistake-monitor.js`. No enforced cap on message length.

Typical warning message: "Repeated linting failure on same file" (~8 words). With the header/footer, **3 warnings ≈ 50–80 tokens**.

**Flag:** None in typical use. Could spike if warning messages are verbose, but this is rare/edge-case.

---

### 5. `masonry-bash-trim.js` — Output Limiter Advisory

**Event:** PreToolUse (Bash calls only)
**Output key:** `systemMessage`

**What it injects (only when a pattern matches):**
```
[Token Trim] This command may produce large output:
  - <hint text, one per matched pattern>
```
Hints are short hardcoded strings like "Pipe to | head -50 or | tail -20 to limit output". Maximum ~3 hints at 10 tokens each + 10 token header = **~40–60 tokens**.

**Flag:** None. Small and conditional.

---

### 6. `masonry-session-start.js` — Session Context Injection

**Event:** SessionStart (once per session, synchronous)
**Output key:** `systemMessage`

**What it injects:**

Phase 0 (always): Orchestrator role priming line (~35 tokens):
```
[Masonry] You are an orchestrator. For any task requiring Write, Edit, or Bash,
route through Mortar first (subagent_type: "mortar"). Mortar dispatches specialist
agents (developer, test-writer, code-reviewer) in parallel. Direct inline coding
skips code review and TDD enforcement. Exception: single-sentence factual lookups
and clarification questions.
```

Phase 1 (`build-state.js`): Interrupted build path — if detected, **writes to stdout directly and returns early** with:
```
[Masonry] Interrupted build detected: project "X", N/M tasks done.
  Next: #N — <description>
  Auto-resuming — run /build to continue.
Resume the interrupted build now. Invoke the /build skill to continue.
```
Estimated ~80 tokens. Then exits — no further phases run.

Phase 1 normal path: Up to 3 additional status lines for autopilot mode, UI mode, campaign state, or Karen maintenance flag. Karen flag is the largest:
```
[Masonry] Doc maintenance needed. Spawn karen: Act as the karen agent in ~/.claude/agents/karen.md.
Update and commit these stale project docs: <file list>. Do this before any other work.
```
~50 tokens per line, 3 lines max = ~150 tokens.

Phase 2 (`project-detect.js`): BL project detection, worker status, context.md injection. The `context.md` from a project is read and injected without a size cap. If this file is large, it can be hundreds to thousands of tokens.

Phase 3 (`context-data.js`): Multiple contributors:
- Swarm resume warning: ~100 tokens if inflight tasks present
- Top agents by confidence: ~50 tokens (5 agents × ~10 tokens each)
- Build patterns from Recall: ~50 tokens summary
- Codebase map (`map.md`): ~100 tokens (stack + entry points + key dirs)
- ReasoningBank patterns: up to 5 patterns × ~30 tokens = ~150 tokens
- Relevant skills from Recall: 3 skills × ~30 tokens = ~90 tokens
- Auto-safeguards: up to 10 lines × ~15 tokens = ~150 tokens

Phase 4 (hotpaths): Hot file list — typically short ~50 tokens.

**Conservative total (idle project, no build):** ~600–900 tokens
**Active build with context.md + swarm resume + all phases:** **1500–2500+ tokens**

**Flag: YES — session-start is the largest single injection. The `context.md` path has no size cap and is the primary risk for token bloat.**

---

### 7. `masonry-pre-compact.js` — Pre-Compaction State Snapshot

**Event:** PreCompact (on context compaction)
**Output key:** `systemMessage`

**What it injects:**

Active build mode path:
```
[Masonry] COMPACTING — BUILD mode preserved.
  Project: <name>, N/M tasks done.
  After compact, resume from task #N: <description>
  Run /masonry-build to continue.
PRE_COMPACT BUILD: snapshot saved to .autopilot/pre-compact-snapshot.json
  task-ids.json backed up to pre-compact-task-ids.json
```
~80 tokens.

UI compose path: ~50 tokens.

Swarm inflight tasks (N tasks × ~20 tokens each): up to ~200 tokens.

Campaign state: ~50 tokens.

Session breadcrumb (last 6 edit summaries, each ~30 chars):
```
[Masonry] Session work (N edits this session): file1.py → file2.js → ...
```
~100 tokens.

**Total typical:** **200–400 tokens**. Peaks at ~600 tokens with many inflight tasks.

**Flag:** Borderline. Unlikely to hit 500 tokens in typical use but possible in a large swarm.

---

### 8. `masonry-post-compact.js` — Post-Compaction Resume Context

**Event:** PostCompact (after context compaction)
**Output key:** `systemMessage`

**What it injects:**

Active build path:
```
[Masonry] RESUMED after compaction — BUILD mode.
  Project: <name>, N/M tasks done.
  Next task #N: <description>
  Run /masonry-build to continue.
Resume the interrupted build now. Invoke the /build skill to continue from where it left off.
```
~80 tokens.

UI compose path: ~60 tokens.

Swarm inflight task warnings (N tasks × ~20 tokens): ~100–200 tokens.

Campaign state: ~60 tokens.

Session breadcrumb (last 8 edit paths):
```
[Masonry] Resuming after compaction — last session edited N file(s).
  Recent: file1 → file2 → ...
```
~100 tokens.

**Total typical:** **200–500 tokens**. With many inflight tasks, could reach 600.

**Flag:** Borderline. Same profile as pre-compact.

---

### 9. `recall-retrieve.js` (global) — Full Recall Memory Injection

**File:** `~/.claude/recall-hooks/recall-retrieve.js`
**Event:** UserPromptSubmit (every prompt, fired before masonry hooks)
**Output key:** `additionalContext`

This is the full-featured recall hook (11KB vs the simpler 3.5KB `masonry-prompt-inject.js`). Key behaviors:

**Rehydrate context** (first prompt of session, prompt > 80 chars, domain known): fetches up to 5 domain memories, no per-entry length cap in this code path. The `formatRehydrate()` function (from `recall-retrieve-results.js`) controls the output.

**Browse search results**: `queryType.maxResults + 2` results (typically 5–7). Each result passed to `formatContext()` which controls truncation.

**Profile proposals** (first prompt only): appends up to 3 pending profile proposals, each with `proposed_value.slice(0, 120)` (~30 tokens each).

**Based on the simpler `masonry-prompt-inject.js` pattern** (200 chars/entry, 3 results = ~150 tokens) this hook does the same but with up to 7 results and an additional rehydrate block. Estimated max:
- Rehydrate block (5 entries × ~60 tokens): ~300 tokens
- Search results (7 entries × ~60 tokens): ~420 tokens  
- Profile proposals: ~100 tokens
- Headers/framing: ~50 tokens

**Estimated max: ~600–870 tokens on first prompt with domain match and many results.**

**Flag: YES — this hook has the highest per-prompt token cost, particularly on session-opening prompts where both rehydrate and browse paths fire.**

---

## Cumulative Worst-Case Analysis

A single "first prompt of session" in an active build project with Recall running could trigger:

| Hook | Max Tokens |
|------|-----------|
| `recall-retrieve.js` (rehydrate + search + proposals) | ~870 |
| `masonry-register.js` (handoff from Recall) | ~700 |
| `masonry-prompt-router.js` (dev task route) | ~200 |
| `masonry-prompt-inject.js` (3 memories) | ~150 |
| Total first-prompt injection | **~1,920 tokens** |

Note: `masonry-session-start.js` fires at SessionStart, not UserPromptSubmit — it adds separately (600–2500 tokens).

**Grand total for session open in active project: 2,500–4,400+ tokens of injected context.**

---

## Recommendations

1. **`masonry-session-start.js` context.md path** — add a hard size cap (e.g., 4000 chars / ~1000 tokens) on injected `context.md` content. Currently uncapped.

2. **`recall-retrieve.js` rehydrate path** — the first-prompt rehydrate block can return verbose entries. Consider capping entry length at 150 chars (matching `masonry-prompt-inject.js`).

3. **`masonry-register.js` handoff path** — the `resume_prompt` field from Recall handoff documents has no enforced length cap. The handoff writer should truncate to ~300 tokens max.

4. **Double-injection risk** — both `recall-retrieve.js` and `masonry-prompt-inject.js` query Recall on every prompt. They use different endpoints (`/search/browse` + `/search/rehydrate` vs just `/search/browse`) but may return overlapping memories. Consider consolidating to one Recall hook.

5. **`masonry-pre-compact.js` and `masonry-post-compact.js`** — these are appropriately sized. No action needed.
