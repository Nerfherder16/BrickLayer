# Hook Output Schemas

Valid stdout JSON schemas per Claude Code hook event type. This is the single source of truth for what each hook should output.

## Event Type Reference

| Event Type | Valid Output | Purpose |
|------------|-------------|---------|
| **SessionStart** | `{ systemMessage: "..." }` | Inject context at session open |
| **UserPromptSubmit** | `{ additionalContext: "..." }` | Inject context before Claude processes the prompt |
| **PreToolUse** | `{ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow"\|"deny"\|"block", permissionDecisionReason: "..." } }` | Allow/deny/block a tool call |
| **PostToolUse** | No stdout (async) | Side effects only |
| **Stop** | `{ decision: "block", reason: "..." }` | Block the stop; omit stdout to allow |
| **PreCompact** | `{ systemMessage: "..." }` | Inject context that survives compaction |
| **SubagentStart** | No stdout (async) | Side effects only |
| **PostToolUseFailure** | No stdout (async) | Side effects only |
| **TeammateIdle** | `{ systemMessage: "..." }` | Inject task assignment for idle agent |
| **TaskCompleted** | `{ systemMessage: "..." }` | Inject next task assignment |
| **SessionEnd** | No stdout | Cleanup only |

## Key Rules

1. **`hookSpecificOutput` is ONLY for PreToolUse** permission hooks. No other event type uses it.

2. **`systemMessage`** is the standard output for content-injection hooks: SessionStart, PreCompact, TeammateIdle, TaskCompleted.

3. **`additionalContext`** is the standard output for UserPromptSubmit hooks. It is a top-level field, NOT wrapped in hookSpecificOutput.

4. **Stop hooks** use `{ decision: "block", reason: "..." }` to block. Output nothing (or return silently) to allow the stop.

5. **Async hooks** (PostToolUse, SubagentStart, PostToolUseFailure) should not write to stdout. They run for side effects only (logging, state updates, tracking).

6. Unrecognized output fields are silently discarded by Claude Code — bugs in output schema produce no error, just missing behavior.

## Hook Inventory

### Masonry Hooks

| Hook | Event | Output Schema | Notes |
|------|-------|---------------|-------|
| masonry-session-start.js | SessionStart | `{ systemMessage }` | Delegates to session/*.js modules |
| masonry-prompt-router.js | UserPromptSubmit | `{ additionalContext }` | Routing hint injection |
| masonry-pre-compact.js | PreCompact | `{ systemMessage }` | State preservation across compaction |
| masonry-teammate-idle.js | TeammateIdle, TaskCompleted | `{ systemMessage }` | Auto-assigns next build task |
| masonry-approver.js | PreToolUse | `{ hookSpecificOutput: { permissionDecision } }` | Auto-approve in build/fix mode |
| masonry-content-guard.js | PreToolUse | `{ hookSpecificOutput: { permissionDecision } }` | Config protection + secret scanning |
| masonry-context-safety.js | PreToolUse | `{ hookSpecificOutput: { permissionDecision } }` | Block plan-mode exit during build |
| masonry-context-monitor.js | Stop | `{ decision, reason }` | Block stop on large context + uncommitted |
| masonry-stop-guard.js | Stop | `{ decision, reason }` | Block stop on uncommitted changes |
| masonry-build-guard.js | Stop | `{ decision, reason }` | Block stop with pending autopilot tasks |
| masonry-ui-compose-guard.js | Stop | `{ decision, reason }` | Block stop with pending UI tasks |
| masonry-observe.js | PostToolUse | None (async) | Activity tracking |
| masonry-style-checker.js | PostToolUse | None (async) | Lint enforcement |
| masonry-tool-failure.js | PostToolUseFailure | None (async) | Error tracking |
| masonry-subagent-tracker.js | SubagentStart | None (async) | Agent spawn tracking |
| masonry-agent-onboard.js | PostToolUse | None (async) | Agent registry auto-onboard |
| masonry-tdd-enforcer.js | PostToolUse | None (async) | TDD compliance check |

### Recall Hooks

| Hook | Event | Output Schema | Notes |
|------|-------|---------------|-------|
| recall-retrieve.js | UserPromptSubmit | `{ additionalContext }` | Memory retrieval |
| context-monitor.js | PostToolUse | `{ additionalContext }` | Context window warning |
| observe-edit.js | PostToolUse | None (async) | Memory observation |
| recall-session-summary.js | Stop | None (stderr only) | Session summary to Recall |
| session-save.js | Stop | None (async) | Session state persistence |
| autopilot-approver.js | PreToolUse | `{ hookSpecificOutput: { permissionDecision } }` | Auto-approve |

## Termination Pattern

Hooks should use natural event loop drain, not `process.exit(0)`:

```javascript
// Correct
async function main() {
  // ... hook logic ...
  if (output) process.stdout.write(JSON.stringify(output));
}
main().catch(() => {});

// Avoid
async function main() {
  process.stdout.write(JSON.stringify(output));
  process.exit(0); // Can truncate stdout on Windows pipes
}
```

For module functions called by a parent hook (e.g., `build-state.js` called by `session-start.js`), use a flag pattern instead of `process.exit(0)`:

```javascript
// In module:
state.earlyExit = true;
return;

// In parent:
if (state.earlyExit) return;
```
