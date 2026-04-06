# Adding a New Hook or Engine Module

**Hooks → Node.js. Campaign runners → Python. When in doubt, see `docs/hook-creation-guide.md`.**

---

## Decision Table

| Factor | Node.js | Python |
|-----------------------------|----------------------|----------------------|
| Cold-start latency | 50-100ms | 300-400ms |
| Claude Code hook system | Native | Not available |
| MCP tool integration | Via CLI wrapper | Native (FastMCP) |
| DSPy / ML optimization | Not available | Required |
| tmux agent spawn | Not available | Required |
| File I/O (YAML, JSON, MD) | Fast | Fine |
| GPU / Ollama inference | Via HTTP only | Preferred |

---

## New file in this directory?

If you create a new `.js` file here, register it in `~/.claude/settings.json` under the appropriate hook event. The `masonry-hook-watch.js` PostToolUse hook will detect the new file and remind you of this guide.

If you think the logic belongs in Python, it almost certainly belongs in `bl/` instead — not here. See `docs/hook-creation-guide.md` for the migration checklist if you need to bridge JS hooks to Python MCP capabilities.
