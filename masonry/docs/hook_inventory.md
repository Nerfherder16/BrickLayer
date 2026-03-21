# Masonry Hook Inventory

All hook scripts live in `src/hooks/`. The project-scoped `hooks.json` (at the masonry project root) activates a subset of these hooks. The full fleet is activated in the user's global `~/.claude/settings.json`.

---

## Project-Scoped Hooks (hooks.json at masonry root)

These are the hooks active when working inside the masonry project directory itself.

| Hook | Event | File | Async | Timeout | Purpose |
|------|-------|------|-------|---------|---------|
| masonry-register | UserPromptSubmit | src/hooks/masonry-register.js | No | 8s | Registers the session against campaign state at the start of every user prompt |
| masonry-observe | PostToolUse | src/hooks/masonry-observe.js | Yes | 5s | Detects findings written to findings/*.md, stores to Recall, logs file activity |
| masonry-guard | PostToolUse | src/hooks/masonry-guard.js | Yes | 3s | Fingerprints error patterns in tool responses; triggers 3-strike warning |
| masonry-agent-onboard | PostToolUse | src/hooks/masonry-agent-onboard.js | Yes | 5s | Detects new agent .md files; extracts frontmatter; appends to agent_registry.yml |
| masonry-stop | Stop | src/hooks/masonry-stop.js | No | 15s | Blocks session stop if there are uncommitted git changes from this session |

---

## Full Fleet (global ~/.claude/settings.json)

These hooks are active in all Claude Code sessions on this machine.

| Hook | Event | File | Async | Purpose | Known Interactions |
|------|-------|------|-------|---------|-------------------|
| masonry-session-start | SessionStart | src/hooks/masonry-session-start.js | No | Restores autopilot/UI/campaign context; snapshots pre-existing dirty files | Writes session snapshot used by masonry-stop-guard |
| masonry-approver | PreToolUse (Write/Edit/Bash) | src/hooks/masonry-approver.js | No | Auto-approves tool calls when build or UI compose mode is active | Runs before masonry-guard; can approve calls that masonry-guard later flags |
| masonry-context-safety | PreToolUse (ExitPlanMode) | src/hooks/masonry-context-safety.js | No | Blocks plan-mode exit during active build or high context usage | — |
| masonry-lint-check | PostToolUse (Write/Edit) | src/hooks/masonry-lint-check.js | No | Runs ruff + prettier + eslint after every write; blocks on lint errors | Runs after masonry-observe and masonry-guard (which are async) |
| masonry-design-token-enforcer | PostToolUse (Write/Edit) | src/hooks/masonry-design-token-enforcer.js | No | Warns on hardcoded hex values or banned fonts in UI files | — |
| masonry-observe | PostToolUse (Write/Edit) | src/hooks/masonry-observe.js | Yes | Campaign state observation; finding detection; Recall storage | May race with masonry-guard on same tool call |
| masonry-guard | PostToolUse (Write/Edit) | src/hooks/masonry-guard.js | Yes | Error pattern detection; 3-strike escalation | May race with masonry-observe on same tool call |
| masonry-tool-failure | PostToolUseFailure | src/hooks/masonry-tool-failure.js | No | Error tracking; 3-strike escalation on tool failures | — |
| masonry-subagent-tracker | SubagentStart | src/hooks/masonry-subagent-tracker.js | Yes | Tracks active agent spawns | — |
| masonry-stop-guard | Stop | src/hooks/masonry-stop-guard.js | No | Blocks stop on uncommitted git changes from this session | Reads session snapshot written by masonry-session-start |
| masonry-build-guard | Stop | src/hooks/masonry-build-guard.js | No | Blocks stop if .autopilot/ has pending tasks | Both stop hooks fire on every Stop event |
| masonry-ui-compose-guard | Stop | src/hooks/masonry-ui-compose-guard.js | No | Blocks stop if .ui/ compose has pending tasks | Both stop hooks fire on every Stop event |
| masonry-context-monitor | Stop | src/hooks/masonry-context-monitor.js | Yes | Warns when context exceeds 150K tokens | — |
| masonry-agent-onboard | PostToolUse (Write/Edit) | src/hooks/masonry-agent-onboard.js | Yes | Auto-onboards new agents to registry | May race with masonry-observe |

---

## Known Interaction Concerns

### masonry-approver vs masonry-guard

These hooks operate on opposite sides of the same tool call:
- `masonry-approver` (PreToolUse, synchronous): approves the call before it runs
- `masonry-guard` (PostToolUse, async): checks the response for error patterns after it runs

A tool call can be approved by masonry-approver and still trigger a strike in masonry-guard. The two hooks do not share state — masonry-guard does not know that masonry-approver already blessed the call. This is by design but means a high-error-rate approved build could accumulate guard strikes.

### masonry-observe vs masonry-guard (PostToolUse race)

Both are PostToolUse async hooks. Claude Code fires async hooks in parallel (or in registration order without waiting). There is no documented guarantee of which completes first. If both read and write to the same session state file simultaneously, the last writer wins. The risk: masonry-observe writes a finding to Recall, while masonry-guard writes a strike for the same file operation if the response contained any error signal. This is not inherently wrong but could produce conflicting state entries.

### masonry-stop-guard vs masonry-build-guard (Stop race)

Both are Stop hooks but synchronous. They fire in the order listed in settings.json. If masonry-stop-guard exits with code 2 (block), masonry-build-guard may or may not run depending on Claude Code's hook sequencing behavior. If masonry-build-guard runs first and exits 2, masonry-stop-guard may not run, meaning different block reasons on each stop attempt.

### Async hook timeout behavior

masonry-observe (5s timeout) and masonry-guard (3s timeout) are async. If the hooks exceed their timeout, Claude Code kills the process. Any state written partially before timeout is left dirty. masonry-guard uses a file-based queue (`GUARD_THRESHOLD` strikes) — a partial write mid-timeout could corrupt the strike counter.

### Project-scoped hooks.json vs global settings.json duplication

Both the project hooks.json and the global settings.json register masonry-observe, masonry-guard, and masonry-agent-onboard for PostToolUse events. When working inside the masonry project, these hooks may fire twice per tool call — once from the project hooks.json and once from the global settings.json.

---

## hooks.json Active Hook Summary (masonry project)

Source: `hooks.json` at masonry project root.

```
UserPromptSubmit  → masonry-register (sync, 8s)
PostToolUse       → masonry-observe (async, 5s)
                  → masonry-guard (async, 3s)
                  → masonry-agent-onboard (async, 5s)
Stop              → masonry-stop (sync, 15s)
statusLine        → masonry-statusline (read-only display)
```
