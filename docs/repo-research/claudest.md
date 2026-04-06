# Repo Research: gupsammy/Claudest

**Repo**: https://github.com/gupsammy/Claudest
**Researched**: 2026-04-06
**Researcher**: repo-researcher agent
**Purpose**: Focused gap analysis on the claude-memory plugin, token tracking implementation, and session context injection patterns vs. BrickLayer 2.0

---

## Verdict Summary

Claudest is a polished Claude Code plugin marketplace (128 stars, 8 plugins) built by one developer. Its `claude-memory` plugin is doing something fundamentally different from BrickLayer's `masonry-token-logger.js` + `masonry-read-tracker.js` + `/token-dashboard` skill: it reads the raw `~/.claude/projects/**/*.jsonl` conversation files that Claude Code writes natively, parses every turn's usage fields, and builds a structured SQLite analytics database — no hook-time token capture required. BrickLayer's approach captures a single summary per Stop event; Claudest's `ingest_token_data.py` retroactively ingests the full per-turn token stream from every existing session, including sessions that predate the plugin installation. BrickLayer beats Claudest on routing complexity, multi-agent orchestration, campaign infrastructure, and full build lifecycle; Claudest beats BrickLayer on per-turn token analytics depth, cache cliff detection, and session memory continuity across context clears.

---

## File Inventory

```
.claude-plugin/
  marketplace.json          — Plugin registry: name, version, source path for 8 plugins

plugins/
  claude-memory/            — Conversation memory + token analytics plugin
    .claude-plugin/
      plugin.json           — Plugin metadata: name, version, keywords
    agents/
      memory-auditor.md     — Subagent: audits existing MEMORY.md for stale entries
      signal-discoverer.md  — Subagent: discovers learnings from raw conversation text
      claude-code-guide.md  — Subagent: interprets token insights for Claude Code context
      skill-lint.md         — Subagent: validates skill structure post-creation
    commands/
      manage-memory.md      — Slash command: DB management (sync, search, stats, import)
    hooks/
      hooks.json            — Hook registration: SessionStart (3), SessionEnd (1), Stop (1)
      memory-setup.py       — SessionStart: create ~/.claude-memory/, trigger initial import
      memory-context.py     — SessionStart: inject prev session context via hookSpecificOutput
      consolidation-check.py — SessionStart: nudge when memory consolidation is due
      clear-handoff.py      — SessionEnd (matcher: "clear"): write handoff.json for /clear continuity
      memory-sync.py        — Stop: write stdin to tempfile, spawn sync_current.py async
      sync_current.py       — Background: parse JSONL, store messages+branches to SQLite
      import_conversations.py — Bulk import all ~/.claude/projects/**/*.jsonl to SQLite
      backfill_summaries.py — Background: compute context_summary for all existing branches
    skills/
      get-token-insights/
        SKILL.md            — Skill definition: 3-step workflow (ingest → enrich → analyze)
        scripts/
          ingest_token_data.py — Reads JSONL files, populates token_snapshots + analytics tables
          __init__.py
        templates/
          dashboard.html    — Pre-built self-contained HTML dashboard (embed JS, no deps)
      extract-learnings/
        SKILL.md            — Distill session learnings into 5-layer memory hierarchy
      recall-conversations/
        SKILL.md            — FTS5/BM25 keyword search + chronological browsing
        scripts/
          memory_lib/
            __init__.py
            db.py           — SQLite connection, schema migration, DEFAULT_SETTINGS
            content.py      — Text extraction, sanitize_fts_term, notification filter
            parsing.py      — JSONL parser, branch detection via UUID parent chain
            formatting.py   — project key derivation, time formatting, cwd normalization
            summarizer.py   — DECIDED/OPEN/NEXT/REJECTED marker extraction, context_summary build
          search_conversations.py — CLI: search by keyword
          recent_chats.py   — CLI: list recent sessions
    .gitignore
    CHANGELOG.md            — 269 commits of history
    README.md

  claude-research/          — Multi-source research (Reddit, X, YouTube, web)
  claude-skills/            — Skill/agent authoring and repair
  claude-coding/            — Git workflows, CLAUDE.md maintenance, changelog generation
  claude-thinking/          — council (6 parallel agent personas), brainstorm
  claude-content/           — Gemini image gen, ffmpeg video/audio pipeline
  claude-utilities/         — convert-to-markdown via ezycopy
  claude-claw/              — OpenClaw advisory

docs/
  session-context-injection-spec.md — Design spec: DECIDED/OPEN/NEXT/REJECTED markers

scripts/
  auto-version.py           — pre-commit hook: auto-bump patch versions, sync README badges

tests/                      — pytest + hypothesis tests for claude-memory hooks

.github/workflows/          — CI: claude-review workflow (skips when actor is claude[bot])
.pre-commit-config.yaml     — pre-commit framework config
CHANGELOG.md
CLAUDE.md                   — Project instructions: architecture, dev commands, conventions
README.md                   — Marketplace listing with install instructions
pyproject.toml
```

---

## Architecture Overview

Claudest is a Claude Code plugin marketplace where the `/plugin` command fetches plugin definitions from `.claude-plugin/marketplace.json` and installs hooks, skills, agents, and commands into the user's global Claude Code config. No build system — pure Python 3.7+ stdlib and SQLite.

The `claude-memory` plugin operates across three phases:

**Write path (Stop hook):** `memory-sync.py` receives the Stop event stdin, writes it to a `tempfile.mkstemp()` with 0o600 permissions (TOCTOU prevention), then spawns `sync_current.py --input-file` as a detached background process. `sync_current.py` locates the session's JSONL file under `~/.claude/projects/{project_hash}/{session_uuid}.jsonl`, parses the full conversation into branches (using UUID parent-chain analysis to detect rewinds), stores messages with dedup by UUID, and computes a `context_summary` (pre-rendered markdown) + `context_summary_json` (structured data) for each branch. Everything goes to `~/.claude-memory/conversations.db` (SQLite, WAL mode, 5s busy_timeout).

**Read path (SessionStart hook):** `memory-context.py` queries the DB for the most recent substantive session (>2 exchanges) for the current project, reads its cached `context_summary`, and injects it via `hookSpecificOutput.additionalContext`. On `/clear`, `clear-handoff.py` writes the dying session's UUID to `clear-handoff.json` at SessionEnd, and the SessionStart hook reads it to hard-link to the exact cleared-from session — enabling seamless `/clear` continuation.

**Analytics path (on-demand skill):** `ingest_token_data.py` is not a hook — it runs on demand when the user invokes `/get-token-insights`. It scans all JSONL files under `~/.claude/projects/`, parses every `assistant` turn's `usage` object (input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens), and upserts into a `token_snapshots` table in `conversations.db`. It also extracts tool usage counts, hook execution times, skill invocations, agent spawns, and response times. Output: a slim JSON blob to stdout (consumed by the skill's Step 2 analysis) + a self-contained `dashboard.html` written to `~/.claude-memory/dashboard.html`.

---

## Detailed Analysis: claude-memory Plugin

### 1. Token Tracking Mechanism

**What it tracks:** NOT a hook that captures at Stop time. Instead, `ingest_token_data.py` reads the raw JSONL conversation files that Claude Code writes natively to `~/.claude/projects/{project_hash}/{session_uuid}.jsonl`. Every assistant message in these files contains a `usage` object with per-turn token counts. The script parses every turn across all historical sessions.

**Per-turn fields extracted:**
- `input_tokens` — context window tokens consumed
- `output_tokens` — response tokens generated
- `cache_read_tokens` — tokens served from prompt cache
- `cache_creation_tokens` — tokens spent writing to cache
- `ephemeral_5m_tokens` / `ephemeral_1h_tokens` — cache tier classification for cliff detection

**Session-level fields stored in `token_snapshots` table:**
```sql
CREATE TABLE IF NOT EXISTS token_snapshots (
  id INTEGER PRIMARY KEY,
  session_uuid TEXT UNIQUE NOT NULL,
  project_path TEXT,
  start_time DATETIME,
  duration_minutes INTEGER,
  user_message_count INTEGER,
  assistant_message_count INTEGER,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  cache_read_tokens INTEGER DEFAULT 0,
  cache_creation_tokens INTEGER DEFAULT 0,
  tool_counts TEXT,            -- JSON: {tool_name: count}
  tool_errors INTEGER DEFAULT 0,
  uses_task_agent INTEGER DEFAULT 0,
  uses_web_search INTEGER DEFAULT 0,
  uses_web_fetch INTEGER DEFAULT 0,
  user_response_times TEXT,    -- JSON: [seconds between turns]
  lines_added INTEGER DEFAULT 0,
  lines_removed INTEGER DEFAULT 0,
  goal_categories TEXT,        -- JSON: inferred session goals
  outcome TEXT,
  session_type TEXT,
  friction_counts TEXT,        -- JSON: friction event counts
  brief_summary TEXT,
  imported_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Cache cliff detection:** Detects when `cache_read_tokens` drops >50% between turns after an idle period. Reads `ephem_5m` vs `ephem_1h` per session to auto-detect whether the active cache TTL tier is 5 minutes or 1 hour (empirically confirmed as 1h for Claude Code). Counts cliffs per session and per project, reports total across all sessions.

**Data source:** `~/.claude/projects/**/*.jsonl` — this is Claude Code's native storage, not something the plugin writes. The plugin is a reader of data that already exists. First run processes all files (~100s for ~2500 files), incremental runs complete under 5s (tracks `imported_at` per file).

### 2. What `/get-token-insights` Outputs

**Step 1 (ingest_token_data.py stdout):** A JSON blob containing:
```json
{
  "total_sessions": N,
  "date_range": {"start": "...", "end": "..."},
  "total_spend_usd": X.XX,
  "avg_cost_per_session": X.XX,
  "insights": [
    {
      "waste_usd": 12.50,
      "finding": "meta-ads-cli: 75 cache cliffs across 53 sessions",
      "root_cause": "Idle periods > 1h cause cache to expire, forcing re-ingestion on next turn",
      "solution": {
        "action": "Add to CLAUDE.md",
        "detail": "exact rule text"
      }
    }
  ],
  "trends": {
    "current_window": {...},
    "prior_window": {...},
    "improved": [...],
    "regressed": [...],
    "hook_trends": [...]
  },
  "workflow_analytics": {
    "skills": {...},
    "agents": {...},
    "hooks": {...}
  }
}
```

**Step 1.5 (claude-code-guide subagent):** Spawned in foreground with the top 3 insights verbatim. Interprets the findings in the context of Claude Code features the user may not be exploiting — e.g., "cache cliff from idle periods: consider /compact to preserve cache across breaks."

**Step 2 (skill analysis):** Six-part markdown analysis: top-line summary, priority insights by dollar waste, model economics, project cost ranking, workflow analytics (skill/agent/hook patterns), week-on-week trends.

**Step 3:** Opens `~/.claude-memory/dashboard.html` — a self-contained HTML file with 20+ interactive charts: sessions by day, token composition by day, cache trajectory per session, ephemeral cache tiers by project, tool efficiency (bash antipatterns, redundant reads, edit retry chains), behavioral patterns (turn complexity, user response times, hook overhead), project intelligence, and a "Claude Code Ecosystem" section (skill usage, agent delegation, hook performance).

### 3. Hooks Registered

```json
{
  "hooks": {
    "SessionStart": [
      {"matcher": "*",             "command": "memory-setup.py"},
      {"matcher": "startup|clear", "command": "memory-context.py"},
      {"matcher": "startup|clear", "command": "consolidation-check.py"}
    ],
    "SessionEnd": [
      {"matcher": "clear",         "command": "clear-handoff.py"}
    ],
    "Stop": [
      {"matcher": "*",             "command": "memory-sync.py"}
    ]
  }
}
```

No PostToolUse hooks. No PreToolUse hooks. Token data is extracted from existing JSONL files, not captured at write/read time.

### 4. DECIDED/OPEN/NEXT/REJECTED Context Injection Pattern

This is the most architecturally interesting part. Documented in `docs/session-context-injection-spec.md`. Implemented in `memory_lib/summarizer.py`.

**The problem it solves:** BrickLayer's session handoff (masonry-handoff.js) writes a handoff document at Stop. Claudest's approach is different: at every Stop, `sync_current.py` computes a `context_summary` (pre-rendered markdown) and `context_summary_json` (structured data) for each conversation branch. On the next SessionStart, `memory-context.py` reads the cached summary from DB — a fast DB lookup, not re-reading the full conversation.

**The marker extraction heuristics (in summarizer.py):**

The `extract_markers()` function runs 6 layers over stored messages to produce structured markers:
1. **Keyword matching** — scans for: "decided", "let's go with", "chose", "next step", "blocked on", "TODO", "skip", "instead of", "we should", "the plan is", "need to fix"
2. **Positional extraction** — last sentence of final assistant response + bullet/numbered lists from it
3. **Question detection** — user messages ending with `?` in last exchange mapping to unanswered intents
4. **User intent prefixes** — "let's", "can you", "I want", "we need to"
5. **Negation tracking** — "don't", "skip", "not X", "instead of" (captures explicit rejections as REJECTED markers)
6. **Code reference extraction** — file path regex + function name extraction from last few exchanges

**The injected template:**
```markdown
## Previous Session Context

### Session: {start_time} -> {end_time} (branch: {git_branch})
Modified: `file1`, `file2`, ...
Commits: commit message 1; ...
Tools: {tool_counts_summary}

### Key Signals
- [DECIDED] switched to SQLite over PostgreSQL for zero-dep constraint
- [OPEN] token dashboard needs week-on-week comparison chart
- [NEXT] implement cache cliff detection
- [REJECTED] skip LLM-based summarization — all extraction deterministic Python

### First Exchange
**[09:23] User:**
{first_user_message_verbatim}

**[09:23] Assistant:**
{first_300_chars}...[truncated]...{last_600_chars}

[... 8 exchanges ...]

### Where We Left Off
**[11:45] User:**
{last_3_user_messages_verbatim}

**[11:45] Assistant:**
{truncated_last_3_assistant_responses}

[12 total exchanges — proactively use /recall-conversations to retrieve relevant 
context from past conversations when the user references prior work...]
```

**Stored as:** `branches.context_summary` (pre-rendered markdown) + `branches.context_summary_json` (structured JSON with version field). JSON is source of truth; markdown is derived. Version field (`summary_version = 2`) enables background backfill when algorithm improves.

**Token budget:** Median ~3k tokens. Short sessions (<=8 exchanges) inject everything verbatim. Long sessions inject first 2 + last 6 exchanges with mid-truncation (300 front + 600 back chars per assistant response).

### 5. Plugin Marketplace System

The `/plugin` command (Claude Code built-in) fetches `marketplace.json` from the GitHub repo's `.claude-plugin/` directory. Each plugin has a `plugin.json` with `name`, `version`, `source` pointing to a relative path. The plugin system installs:
- `hooks/hooks.json` — registers hooks into Claude Code's settings
- `skills/*.md` — SKILL.md files with YAML frontmatter
- `agents/*.md` — agent files with YAML frontmatter
- `commands/*.md` — slash commands

Plugin scripts use `${CLAUDE_PLUGIN_ROOT}` env var (injected by the plugin system) to find their sibling scripts at runtime. No npm, no pip, no build step. All Python uses stdlib only.

---

## BrickLayer 2.0 vs. Claudest: Token Tracking Comparison

### BrickLayer's Current Implementation

**masonry-token-logger.js (Stop hook):**
- Event: Stop (async)
- Captures from Stop event stdin: `session_id`, `context_window.used_percentage`, `usage.input_tokens`, `usage.context_window`
- Writes one record per session to `~/.mas/token-log.jsonl`
- Record fields: `ts`, `session_id`, `input_tokens`, `context_window`, `pct`, `cwd`
- Cap: 500 lines (trims oldest)
- What it misses: output_tokens, cache_read_tokens, cache_creation_tokens, per-turn data, model identity, tool usage

**masonry-read-tracker.js (PostToolUse/Read hook):**
- Event: PostToolUse, matcher: Read (async)
- Captures: file path, estimated byte size from tool result
- Writes to `~/.mas/read-log.jsonl`
- Record fields: `ts`, `session_id`, `file`, `bytes`, `cwd`
- Cap: 2000 lines

**/token-dashboard skill (SKILL.md):**
- Reads both log files
- Produces a markdown table: recent sessions with token counts and context%, top files by read frequency, top files by byte volume, reduction opportunities
- No HTML output, no charts, no cost calculation, no cache analysis

### Claudest's Implementation

**ingest_token_data.py (on-demand, not a hook):**
- Event: Invoked by skill, not by any hook
- Data source: `~/.claude/projects/**/*.jsonl` (Claude Code native storage)
- Extracts per-turn token data from every historical session
- Computes: cache hit rate, cache cliff count, cost by model (using known pricing), tool usage patterns, hook execution times, skill/agent invocation counts, user response times, lines added/removed
- Stores to SQLite `token_snapshots` table
- First run: ~100s for ~2500 files. Incremental: <5s.
- Outputs: slim JSON blob + self-contained HTML dashboard with 20+ charts

### The Fundamental Architectural Difference

BrickLayer captures token data **at hook-fire time** from the Stop event payload. Claudest reads token data **retroactively** from Claude Code's native JSONL storage.

The consequence: Claudest can report on sessions that predate the plugin installation. It can analyze every turn's cache hit, not just the session aggregate. It knows which model was used per turn. It knows tool-level costs (how many tokens does a single Bash call add to context?). It detects cache cliffs with per-session resolution.

BrickLayer's approach is not wrong — it's simpler and lower overhead. But it captures ~20% of the available signal from the same Stop event.

---

## Feature Gap Analysis

| Feature | In Claudest | In BrickLayer 2.0 | Gap Level | Notes |
|---------|-------------|-------------------|-----------|-------|
| Per-turn token capture (input, output, cache_read, cache_creation) | Yes — ingest_token_data.py reads JSONL | No — only session-level input_tokens + context% | HIGH | BL captures from Stop payload; Claudest reads native JSONL for per-turn breakdown |
| Cache hit rate analytics | Yes — cache_read / (cache_read + input) per turn | No | HIGH | BL can compute this from existing JSONL but doesn't |
| Cache cliff detection | Yes — detects cache_read drop >50% after idle | No | HIGH | Novel pattern; requires per-turn data |
| Dollar cost calculation | Yes — models pricing applied to token counts | No | HIGH | BL has no USD cost output |
| Interactive HTML dashboard | Yes — self-contained dashboard.html, 20+ charts | No — markdown table only | HIGH | SKILL.md produces markdown; Claudest produces bookmarkable HTML |
| Historical data ingestion (pre-install) | Yes — scans all existing JSONL | No — only captures going forward | MEDIUM | Retroactive coverage vs. forward-only |
| Hook execution time tracking | Yes — hook overhead chart in dashboard | No | MEDIUM | BL hooks are async but their runtime isn't tracked |
| Skill/agent invocation analytics | Yes — skill usage, agent delegation patterns | No | MEDIUM | Useful for BL given 50+ agent fleet |
| Week-on-week trend comparison | Yes — current vs prior 7-day window | No | MEDIUM | Requires historical data, which JSONL ingestion provides |
| Model mix analytics | Yes — cost split by model per project | No | MEDIUM | BL uses multiple models; knowing cost per model matters |
| Tool context footprint | Yes — avg tokens each tool adds per call | No | MEDIUM | Measures single-tool turns to isolate tool overhead |
| Redundant read detection | Yes — files read 3+ times in same session | Partial — masonry-read-tracker.js captures reads but no dedup analysis | MEDIUM | BL has the raw data; just needs the analysis |
| SQLite persistence (token data) | Yes — token_snapshots table | No — JSONL flat file only | MEDIUM | SQLite enables aggregation queries; JSONL requires full file scan |
| Session memory continuity across /clear | Yes — SessionEnd + clear-handoff.json pattern | No | MEDIUM | BL has masonry-post-compact.js for compaction but not /clear handoff |
| DECIDED/OPEN/NEXT/REJECTED injection markers | Yes — heuristic extraction in summarizer.py | Partial — masonry-handoff.js writes handoff doc but no structured markers | MEDIUM | BL's handoff is free-text; Claudest's is structured with marker types |
| Context injection token budget control | Yes — ~3k median, adaptive by exchange count, mid-truncation | No — masonry-context-monitor.js warns but doesn't compress injected context | MEDIUM | BL warns at 150K; Claudest pre-computes compact summaries |
| FTS5/BM25 search over conversation history | Yes — full-text search with BM25 ranking | Partial — Recall (Qdrant) provides semantic search | LOW | BL uses Qdrant vector search; Claudest uses keyword FTS. Different tradeoffs |
| Session branch tracking (rewind detection) | Yes — UUID parent-chain analysis | No | LOW | BL doesn't expose conversation rewind recovery |
| Extract-learnings → memory hierarchy | Yes — 5-layer hierarchy (L0-L3 + Meta) | Partial — masonry-agent-onboard.js, but no structured memory layers | LOW | BL uses CLAUDE.md; Claudest adds MEMORY.md + topic files |
| Consolidation nudge (memory pruning) | Yes — consolidation-check.py SessionStart | No | LOW | BL has no memory pruning workflow |
| Bash antipattern detection | Yes — cat/grep/find/ls usage by project | No | LOW | Flags "should use dedicated tools" patterns |
| Edit retry chain analysis | Yes — failed edit + retry to same file | No — masonry-tool-failure.js does 3-strike escalation | LOW | Different: BL escalates, Claudest measures the pattern |

---

## Top 5 Recommendations

### 1. Read from JSONL natively to get per-turn token data [8h, HIGH]

BrickLayer has a Stop hook that captures session-aggregate token counts from the Stop event payload. Claudest's insight is that the raw `~/.claude/projects/**/*.jsonl` files contain per-turn `usage` objects with full cache breakdowns. A one-time Python script (not a hook) can scan these files and populate a richer `token_snapshots` table in `.mas/token-analytics.db`.

What to build: `masonry/scripts/ingest_token_data.py` modeled on Claudest's approach. Run it from the `/token-dashboard` skill as Step 1. This immediately unlocks cache hit rate, cache cliff detection, dollar cost calculation, and model mix analytics from data BrickLayer already has but isn't reading.

This is not a replacement for `masonry-token-logger.js` — the Stop hook capture is a good complement for real-time pct tracking. The JSONL reader is a retroactive enrichment pass.

### 2. Add cache hit rate and dollar cost to `/token-dashboard` output [4h, HIGH]

The existing SKILL.md at `~/.claude/skills/token-dashboard/SKILL.md` outputs a markdown table. Extend it:
- Run `ingest_token_data.py` first (from Rec #1)
- Add cache reuse ratio: `cache_read / (cache_read + input)` — this is the single most actionable cost metric
- Add USD cost estimate using `input_tokens * $3/MTok + output_tokens * $15/MTok + cache_read * $0.30/MTok + cache_creation * $3.75/MTok` (Sonnet pricing)
- Add "cache cliff count" — sessions where cache_read dropped >50% — flagged as idle-break waste
- Keep markdown output (no need for interactive HTML initially)

### 3. Implement DECIDED/OPEN/NEXT/REJECTED markers in masonry-handoff.js [6h, MEDIUM]

The existing `masonry-handoff.js` (Stop runner) writes a free-text handoff document. BrickLayer could adopt Claudest's structured marker extraction from `summarizer.py`:
- Keyword scan for "decided", "let's go with", "next step", "blocked on", "TODO"
- Positional extraction: last sentence of final assistant response + bullet lists
- Negation tracking: "skip", "don't", "instead of" → REJECTED markers
- Render as structured `[DECIDED]` / `[OPEN]` / `[NEXT]` / `[REJECTED]` markers

These markers would appear in the handoff doc and could also be injected via `masonry-prompt-inject.js` on the next session start. Key advantage: the agent immediately knows what decisions were locked in (no re-litigation) and what threads are unfinished (proactive pickup) without reading the entire handoff file.

### 4. Add hook execution time tracking [3h, MEDIUM]

Claudest's dashboard includes "Hook Performance" — total runtime (ms) per hook command, with week-on-week deltas. BrickLayer has 30+ hooks registered; some are slow (Ollama embedding calls, PageRank computation, score triggers). A lightweight timer in `masonry-stop-runner.js` that records start/end time per background hook and appends to `~/.mas/hook-perf.jsonl` would give visibility into which hooks are adding latency. The `/token-dashboard` skill could then surface the slowest hooks.

### 5. Add SQLite aggregation layer to token data [3h, MEDIUM]

`~/.mas/token-log.jsonl` and `~/.mas/read-log.jsonl` are capped flat files. This makes multi-session aggregation slow (full file scan) and limits query complexity. A SQLite DB at `~/.mas/analytics.db` with sessions and file_reads tables (populated by the JSONL ingest from Rec #1) enables: project-level cost rollups, cache hit rate time series, cross-session file read frequency analysis. The existing JSONL files can remain as the write target (they're fast); SQLite becomes the read target for the dashboard skill.

---

## Novel Patterns to Incorporate (Future)

**Cache TTL tier auto-detection:** Claudest empirically confirmed Claude Code uses a 1-hour cache TTL (not 5 minutes). The detection method — reading `ephem_5m` vs `ephem_1h` fields and computing which predicts actual cache drops — is worth porting. This changes the cache cliff detection threshold from 5 min to 1 hour.

**Session selection algorithm for context injection:** Claudest's `select_sessions()` in `memory-context.py` uses an exchange-count filter: skip sessions with <=1 exchange, collect sessions with exactly 2 exchanges as "short sessions" (recent noise), take the first session with >2 exchanges as the primary. This prevents the agent from injecting context from a 1-turn throwaway session. BrickLayer's `masonry-session-summary.js` writes a summary but doesn't apply this filtering on read. Worth adopting.

**`/clear` handoff pattern:** When a user runs `/clear` to reset context mid-work, Claudest writes the session UUID to `~/.claude-memory/clear-handoff.json` at SessionEnd (matcher: "clear"), then reads it at the next SessionStart to inject the exact cleared-from session's context. BrickLayer has `masonry-post-compact.js` for compaction but no equivalent for `/clear`. This enables seamless mid-session memory continuity — the agent knows it's continuing from the cleared session, not starting fresh.

**5-layer memory hierarchy:** Claudest's `extract-learnings` skill writes persistent knowledge to: L0 (`~/.claude/CLAUDE.md`, global), L1 (`/CLAUDE.md`, project), L2 (`memory/MEMORY.md`, working notes), L3 (`memory/*.md`, topic files), Meta (suggest new skill). This explicit tiering prevents over-loading CLAUDE.md with session-specific state. BrickLayer currently dumps everything into CLAUDE.md or the project CLAUDE.md. A `memory/MEMORY.md` layer for working notes that don't warrant a permanent CLAUDE.md entry would reduce context bloat.

**Background summary backfill:** When Claudest's summarizer algorithm improves (tracked by `summary_version`), `memory-setup.py` checks at SessionStart if any branches have `summary_version < 2` and spawns a background `backfill_summaries.py`. BrickLayer could adopt this pattern for its own context summaries — any time the handoff generation algorithm changes, mark existing summaries for recompute.

**`suppressOutput` on sync hooks:** `sync_current.py` returns `{"continue": true, "suppressOutput": true}` when it successfully writes messages. This prevents the async background sync from writing anything to the transcript. BrickLayer's async hooks (masonry-stop-runner.js batch) should check if any background hook is writing to stdout and apply the same suppression.
