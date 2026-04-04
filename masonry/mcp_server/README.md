# Masonry MCP Server

Exposes BrickLayer 2.0 campaign and fleet operations via the Model Context Protocol.

## Tools

| Tool | Description |
|------|-------------|
| `masonry_status` | Current campaign state, question counts, wave number |
| `masonry_questions` | List questions filtered by status (PENDING, DONE, etc.) |
| `masonry_nl_generate` | Generate questions from natural language description |
| `masonry_weights` | Question weight report — priority, prunable, retry |
| `masonry_git_hypothesis` | Generate questions from recent git diffs |
| `masonry_run_question` | Run a question by ID, get verdict envelope |
| `masonry_fleet` | List fleet agents with performance scores |
| `masonry_recall_search` | Search Recall for relevant memories |

## Setup

Add to `~/.claude.json` (MCP servers section):

```json
"masonry": {
  "command": "python",
  "args": ["-m", "masonry.mcp_server.server"],
  "cwd": "C:/Users/trg16/Dev/Bricklayer2.0"
}
```

## Transport

- **Primary**: MCP Python SDK (`pip install mcp`) — stdio transport
- **Fallback**: Raw JSON-RPC 2.0 over stdio — no dependencies, always available

The server auto-detects which transport to use at startup.
