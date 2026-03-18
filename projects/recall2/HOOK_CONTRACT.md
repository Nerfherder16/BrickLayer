# Recall 2.0 — Hook Contract

**Status: LOCKED**
Derived from: Wave 34 (Q261-Q266), Wave 31-33 (Q214, Q231, Q247), architecture synthesis
Do not modify without research justification.

---

## Overview

Three hooks. Each fires as a Claude Code hook via `settings.json`. All communicate with Recall 2.0
over HTTP to `RECALL2_HOST` (default: `http://localhost:8201` — parallel to Recall 1.0 at :8200).

| Hook | Event | Purpose |
|------|-------|---------|
| `recall2-retrieve.js` | UserPromptSubmit | Inject relevant memories before prompt |
| `recall2-observe.js` | PostToolUse (Write, Edit, Bash) | Extract facts from tool output and store |
| `recall2-summary.js` | Stop | Store session narrative summary |

**Kill switch**: `DISABLE_RECALL2=1` disables all three hooks. Required when running BrickLayer
loops to prevent hook interference with research agents.

---

## 1. recall2-retrieve.js — UserPromptSubmit

### Contract

**Trigger**: Every UserPromptSubmit
**Latency budget**: 200ms p95 (enforced by hook timeout)
**Output**: Injects two labeled blocks into the prompt via `injectedContext`

### Payload Sent to Server

```json
POST /retrieve
{
  "query": "<user prompt text>",
  "session_id": "uuid-abc123",
  "machine_id": "casaclaude",
  "k_semantic": 5,
  "k_spreading": 3
}
```

### Server Response

```json
{
  "semantic": [
    { "id": "uuid", "content": "...", "score": 0.84, "tags": ["python", "recall"] }
  ],
  "spreading": [
    { "id": "uuid", "content": "...", "score": 0.71, "tags": ["config"] }
  ]
}
```

### Injected Output Format

```
[Recalled — relevant to your query]
• {content} ({score:.2f})
• {content} ({score:.2f})
...up to K=5

[Recalled — session context]
• {content} ({score:.2f})
...up to K=3
```

Total cap: **K=10** across both blocks. If semantic returns 5 and spreading returns 3, total = 8.
If semantic returns 7 (server may return more), truncate to 5. Never exceed 10 total items.

### Retrieval Strategy (server-side)

- **Semantic block** (K=5): BM25 + dense hybrid with RRF fusion (k=60). Queries all stored memories.
- **Spreading activation block** (K=3): Pull CO_RETRIEVED neighbors of the last 3 retrieved memory IDs
  for this session. Surfaces memories behaviorally associated with recent context without requiring
  query similarity. Uses `session_id` to track which memories were retrieved this session.

### Failure Behavior

On timeout or server unreachable: inject nothing, continue silently. Never block the prompt.

---

## 2. recall2-observe.js — PostToolUse

**Trigger**: PostToolUse for `Write`, `Edit`, `Bash`
**Latency budget**: Sync path ≤ 5ms; async LLM path is fire-and-forget (non-blocking)

### Routing Decision

```
tool_type == "Write" or "Edit"  →  C+ path (structural chunking)
tool_type == "Bash"             →  Bash routing (see below)
```

### C+ Path — Write/Edit

**Step 1: Chunk the content**

Split file content at structural boundaries by file type:

| Extension | Boundary pattern | Max chunk tokens |
|-----------|-----------------|-----------------|
| `.py` | `def`/`async def`/`class` at column 0 | 400 |
| `.ts`, `.tsx`, `.js` | `export function`/`class`/`const` at top level | 400 |
| `.rs` | `pub fn`/`pub struct`/`pub impl`/`pub enum` at top level | 400 |
| `.yml`, `.yaml` | Top-level key at column 0 | 300 |
| `.json` | Top-level key (depth=1) | 300 |
| `.env`, `.toml` | Entire file is atomic | 400 |
| `.md` | H1/H2/H3 section headers | 500 |
| `.sh`, `.bash` | Function definitions or blank-separated blocks | 300 |
| `*` (unknown) | Blank-line paragraph boundaries | 200 |

Token bounds:
- Minimum: 50 tokens. Below threshold → append to preceding chunk.
- Maximum: per table above. Split at nearest available boundary.
- Overlap: 20 tokens between adjacent chunks. No overlap for atomic types (`.env`, `.toml`).

**Step 2: Scope context injection**

For source code chunks, prefix with enclosing class/module header:
```
[class MemoryStore]
async def retrieve(self, query: str, k: int = 10) -> list[Memory]:
    ...
```

**Step 3: Entity extraction (8 regex patterns)**

```
IP_PORT:   \b(?:\d{1,3}\.){3}\d{1,3}(?::\d{2,5})?\b
VERSION:   \bv?\d+\.\d+(?:\.\d+)?(?:[a-zA-Z]\w*)?\b
KEY_VALUE: (?m)^[\w_-]+\s*[=:]\s*\S+
FUNCTION:  (?:def|fn|function|func)\s+(\w+)\s*\(
CLASS:     (?:class|struct|interface|impl)\s+(\w+)
PORT_NUM:  \b(?:port|PORT|listen|bind|expose)\s*[=:]\s*(\d{2,5})\b
ERROR:     \b(?:[A-Z][A-Z_]+ERROR|E[A-Z_]+|HTTP \d{3})\b
SERVICE:   \b(qdrant|neo4j|redis|ollama|fastapi|nginx|docker|postgres|recall)\b
```

**Step 4: Tag inference**

```javascript
const EXT_TAGS = {
  py: ['python'], ts: ['typescript'], tsx: ['react', 'typescript'],
  js: ['javascript'], rs: ['rust'], yml: ['config', 'yaml'],
  yaml: ['config', 'yaml'], json: ['config', 'json'],
  env: ['config', 'dotenv'], toml: ['config', 'toml'],
  md: ['markdown', 'documentation'], sh: ['shell'],
};

function inferTags(filePath, toolType) {
  const tags = [toolType.toLowerCase()];
  const ext = filePath.includes('.') ? filePath.split('.').pop().toLowerCase() : 'unknown';
  tags.push(...(EXT_TAGS[ext] || [ext]));
  const parts = filePath.replace(/\\/g, '/').split('/');
  if (parts.length >= 2) tags.push(parts[0].toLowerCase()); // top-level dir = project tag
  return [...new Set(tags)];
}
```

**Step 5: Anchor block**

Extracted entities are stored as a separate anchor field in the memory document with 3× BM25
field weight boost. This ensures exact entity matches (IPs, ports, service names, function names)
surface in hybrid retrieval regardless of semantic score.

```json
"anchor": {
  "entities": ["100.70.195.84:8200", "store_memory", "qdrant"],
  "boost": 3.0
}
```

### Bash Routing

**Stage 1: Command prefix check**

```javascript
const STRUCTURED_PREFIXES = new Set([
  'docker', 'git', 'npm', 'pip', 'pip3', 'cargo', 'curl', 'wget',
  'kubectl', 'helm', 'python', 'python3', 'node', 'npx', 'uvicorn',
  'pytest', 'rustfmt', 'clippy', 'ansible', 'terraform',
]);

function routeBash(command, output) {
  const cmdPrefix = command.trim().split(/\s+/)[0].split('/').pop().toLowerCase();
  const tokenCount = output.split(/\s+/).length;

  if (tokenCount < 20) return 'skip';           // trivial output
  if (STRUCTURED_PREFIXES.has(cmdPrefix)) return 'c_plus';  // known schema → C+

  // Identifier density for unknown commands
  const identifierMatches = (output.match(/\b[A-Za-z_]\w{2,}\b/g) || []).length;
  const density = identifierMatches / tokenCount;

  if (density >= 0.30) return 'c_plus';         // dense identifiers → C+ sufficient
  if (density < 0.10 && tokenCount > 200) return 'llm_async'; // opaque long output → LLM
  return 'c_plus';                               // default → C+
}
```

**Stage 2: Schema parsers (structured commands)**

Top parsers by frequency:
- `docker ps`: container names, image names, exposed port bindings, status
- `git log --oneline`: commit hashes (7-char), commit messages
- `git status`: modified/added/deleted file paths
- `npm install` / `pip install`: package names + versions
- `pytest` / `cargo test`: test file names, pass/fail counts

Each parser returns entities + summary string via pure regex/text parsing. No LLM call.

**Stage 3: Async LLM extraction (unstructured)**

For `llm_async` routed output:
- Fire-and-forget: hook ACKs immediately after sync storage, LLM call is queued
- Model: `qwen3:14b` at `http://192.168.50.62:11434`
- Timeout: 8 seconds (hard kill)
- Budget: max 50 LLM calls per session (budget guard; excess falls back to C+)
- Output: 1-2 sentence description of output significance (~400 token cap)
- Result stored as `description` field update on the already-stored memory document

**LLM extraction prompt template:**

```
You are a memory extraction assistant. Given a bash command and its output,
write 1-2 sentences describing what significant information this output contains
for future reference. Focus on: IPs, ports, errors, service states, file paths,
version numbers, configuration values. Be specific and factual.

Command: {command}
Output (truncated to 500 tokens): {output}

Description:
```

### Payload Sent to Server (both paths)

```json
POST /store
{
  "content": "<chunked text, 50-500 tokens>",
  "entities": ["100.70.195.84:8200", "store_memory", "qdrant"],
  "anchor": { "entities": [...], "boost": 3.0 },
  "tags": ["python", "services", "recall", "write"],
  "provenance": {
    "tool_type": "Write",
    "file_path": "app/services/memory_store.py",
    "session_id": "uuid-abc123",
    "timestamp": "2026-03-17T14:22:00Z",
    "machine_id": "casaclaude"
  },
  "chunk_index": 2,
  "parent_hash": "sha256:abc123...",
  "description": null
}
```

`description` is `null` for C+ writes. Filled asynchronously for qualifying Bash output.

### CO_RETRIEVED Edge Weights

| Provenance tier | W_min threshold | Edge weight |
|----------------|-----------------|-------------|
| UserDirect (Tier 1) | 3 | 1.0 |
| AgentToolUse (Tier 2) | 3 | 0.8 |
| ToolOutput (Tier 3) | 1 | 0.5 |
| Inferred (Tier 4) | 3 | 0.4 |
| Background (Tier 5) | 3 | 0.3 |

ToolOutput W_min=1 prevents cold-start starvation: Bash output memories can form CO_RETRIEVED
edges after a single co-retrieval rather than requiring 3 co-retrievals like higher-tier memories.

### Failure Behavior

On server unreachable: log to stderr, continue silently. Never block tool use.
On LLM async timeout: memory stored without description. No retry.

---

## 3. recall2-summary.js — Stop

**Trigger**: Stop event
**Latency budget**: Sync, but user is already done — 2-5 seconds acceptable

### What Claude Sends

Claude generates a 2-4 sentence plain-text summary of the session at stop time:
- What problem was being solved
- What decisions were made (the *why*, not just *what*)
- What was explicitly abandoned or deferred
- Current state / where to resume

This captures narrative context that server logs cannot reconstruct.

### Payload Sent to Server

```json
POST /store
{
  "content": "<2-4 sentence session summary>",
  "entities": [],
  "anchor": { "entities": [], "boost": 1.0 },
  "tags": ["session-summary", "stop"],
  "provenance": {
    "tool_type": "Stop",
    "session_id": "uuid-abc123",
    "timestamp": "2026-03-17T18:45:00Z",
    "machine_id": "casaclaude"
  },
  "chunk_index": 0,
  "parent_hash": null,
  "description": null
}
```

### Server-Side Session Reconstruction

On receiving a Stop payload, server:
1. Looks up all `store` events for `session_id` → what was written this session
2. Looks up all `retrieve` events for `session_id` → what was accessed
3. Updates CO_RETRIEVED edges for retrieve co-occurrences (already done live, this is a final flush)
4. Tags the summary memory with the union of tags from all session store events (adds topical context)
5. Stores summary with `provenance: UserDirect` (0.9 multiplier) — highest trust tier

### Why Claude Generates the Summary

Server logs capture *what happened* (store/retrieve events). Claude's summary captures *why* —
the intent, the reasoning, what was considered and rejected. These are not derivable from event logs.

### Failure Behavior

On server unreachable: log to stderr. Session ends normally. Summary is lost but non-blocking.
No retry — Stop fires exactly once and the user is gone.

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RECALL2_HOST` | `http://localhost:8201` | Recall 2.0 server address |
| `RECALL2_API_KEY` | `""` | Bearer token (empty = no auth during dev) |
| `RECALL2_TIMEOUT_MS` | `200` | Retrieve timeout; `5000` for store |
| `DISABLE_RECALL2` | unset | Set to `1` to disable all three hooks |

---

## Hook File Locations

```
~/.claude/hooks/
  recall2-retrieve.js    — UserPromptSubmit
  recall2-observe.js     — PostToolUse (Write, Edit, Bash)
  recall2-summary.js     — Stop
```

These are new files. The existing Recall 1.0 hooks (`recall-retrieve.js`, `observe-edit.js`,
`recall-session-summary.js`) remain untouched and continue pointing at `:8200`.

## settings.json Registration (parallel dev config)

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "command": "node ~/.claude/hooks/recall2-retrieve.js" }
    ],
    "PostToolUse": [
      { "command": "node ~/.claude/hooks/recall2-observe.js", "tools": ["Write", "Edit", "Bash"] }
    ],
    "Stop": [
      { "command": "node ~/.claude/hooks/recall2-summary.js" }
    ]
  }
}
```

Hooks are added to settings.json only when Recall 2.0 server is running. Until then, only
Recall 1.0 hooks are active.

---

## Decisions Log

| Decision | Rationale | Research |
|----------|-----------|----------|
| K=10 hard cap on retrieve | Attention degradation binding constraint | Q214 |
| Pull + push two-block retrieve | Session context without polluting semantic results | Architecture synthesis |
| C+ for Write/Edit (no LLM) | 2ms vs 100ms; ≤6% MRR gap closed by BM25+CO_RETRIEVED | Q261-Q266 |
| Function-level chunking (80-200 tokens) | Cosine 0.75-0.85 vs 0.35-0.42 for file blobs | Q262 |
| Identifier density routing for Bash | Separates structured/unstructured without LLM at route time | Q265 |
| W_min=1 for ToolOutput edges | Prevents cold-start starvation on Bash-sourced memories | Q263 |
| Anchor block 3× BM25 boost | Identifier queries win on exact match regardless of semantic | Q261 |
| qwen3:14b for async LLM extraction | Instruction-following at reasonable latency; already deployed | Q266 |
| Server reconstructs session from logs | Server already has complete event picture; Claude adds narrative | Architecture |
| Claude generates stop summary | Captures *why* (intent, reasoning, rejections) — not in logs | Architecture |
