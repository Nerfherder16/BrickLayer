# Spec: Agent Performance HUD Widget
Date: 2026-04-16
Status: DRAFT

## Problem Statement
During /build runs, there is no live visibility into which agents are performing well or struggling. Confidence scores exist in `pattern-confidence.json` and run results exist in `telemetry.jsonl`, but nothing surfaces them in real time. This means Tim has no signal about agent health until a build completes or fails.

## Chosen Approach
**Approach B — Separate server on port 7824.** Keeps the HUD completely independent from the brainstorm canvas. Can be started/stopped independently, survives brainstorm server restarts, and avoids coupling two unrelated concerns into one process.

## Data Model

**Source files read:**

`pattern-confidence.json` — per agent record:
```json
"developer": {
  "confidence": 0.9999,
  "last_used": "2026-04-16T02:08:43Z",
  "uses": 142
}
```

`.autopilot/telemetry.jsonl` — per task event (one JSON per line):
```json
{
  "task_id": "t-1776305100172",
  "phase": "post",
  "timestamp": "2026-04-16T02:08:43Z",
  "duration_ms": 223581,
  "success": true,
  "agent": "general-purpose"
}
```

**In-memory AgentRecord** (merged from both sources, keyed by agent name):
```
AgentRecord {
  name: string           // agent identifier
  confidence: number     // 0.0–1.0 from pattern-confidence.json
  uses: number           // total invocations all-time
  lastResult: "pass" | "fail" | "unknown"  // from telemetry success field
  lastDurationMs: number // most recent completed task duration
  lastUsed: string       // ISO timestamp
}
```

Server polls both source files every 2 seconds. No database — all state lives in memory, rebuilt from disk on each poll cycle.

## API / Interface Contract

Server runs on port 7824 (configurable via `HUD_PORT` env var). Four read-only endpoints:

```
GET /health
Response: { ok: true, port: 7824, agentCount: N }

GET /agents
Response: AgentRecord[]  (sorted by confidence descending)

GET /events
Response: text/plain keep-alive JSONL stream
Each line: { "type": "update", "agents": AgentRecord[] }
Pushed whenever in-memory state changes (every 2s poll cycle if data changed)

GET /
Response: HUD HTML page (self-contained, zero build step, dark theme)
```

No write endpoints. The HUD is read-only.

## User / System Flow

1. User runs: `cd masonry/src/hud && bash start-server.sh`
   - Server starts on port 7824, writes PID to `/tmp/hud-server.pid`
   - Immediately reads `pattern-confidence.json` + `telemetry.jsonl`
   - Builds initial AgentRecord map in memory
2. User opens `http://localhost:7824`
   - Receives self-contained HUD HTML page
   - Page subscribes to `GET /events` stream
   - Table renders immediately with current agent data
3. Every 2 seconds:
   - Server re-reads both source files from disk
   - Diffs against current in-memory state
   - If anything changed, pushes `{ type: "update", agents: [...] }` to all open `/events` connections
   - Page receives update, re-renders affected rows (confidence bar animates)
4. During a `/build`:
   - `telemetry.jsonl` gets new entries as tasks complete
   - HUD picks up new `duration_ms` + `success` values on next 2s poll
   - User sees agent rows update live: confidence %, pass/fail badge, duration
5. User runs: `bash stop-server.sh`
   - SIGTERM sent to PID, server closes `/events` connections gracefully
   - PID file removed

## Error Handling

| Failure | Detection | Response |
|---|---|---|
| `pattern-confidence.json` missing | `fs.existsSync` on each poll | Skip file, keep last known values, no crash |
| `telemetry.jsonl` missing or empty | `fs.existsSync` | All agents show `lastResult: "unknown"` |
| Malformed JSON line in telemetry | `try/catch` per line | Skip that line, log to stderr, continue |
| Port 7824 already in use | `EADDRINUSE` on server start | Print "port 7824 in use — is another HUD running?" and exit 1 |
| `/events` client disconnects | `res.on('close')` | Remove from active connections set, no error |
| Server killed mid-poll | stale PID file | `start-server.sh` detects stale PID on next start, clears it |

## Out of Scope
- Persisting HUD data to disk or database
- Historical graphs or trend lines
- Alerting or notifications when confidence drops
- Any write operations (the HUD never modifies source files)
- Integration with the brainstorm canvas (separate server, separate concern)

## Open Questions
_(none)_
