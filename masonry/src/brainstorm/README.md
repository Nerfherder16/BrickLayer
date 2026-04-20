# BrickLayer Brainstorm Canvas

Zero-dependency Node.js HTTP server for visual brainstorming sessions.

## Start / Stop

```bash
./start-server.sh    # starts on port 7823 (or $BRAINSTORM_PORT)
./stop-server.sh     # sends SIGTERM, removes PID file
```

Open http://localhost:7823 in a browser.

## API

| Method | Path       | Description                                  |
|--------|------------|----------------------------------------------|
| GET    | /          | Serve the brainstorm canvas HTML              |
| GET    | /health    | `{ ok: true, port }`                         |
| GET    | /state     | `{ sections: [...], last_updated: ISO }`     |
| POST   | /section   | Add/update a section                         |
| POST   | /click     | Record approve/flag/expand action            |
| GET    | /events    | JSONL stream of all events (keep-alive)      |

### POST /section body

```json
{ "id": "intro", "title": "Introduction", "content": "...", "status": "draft" }
```

`status` must be `draft` | `approved` | `flagged`. Defaults to `draft`.

### POST /click body

```json
{ "section_id": "intro", "action": "approve" }
```

`action` must be `approve` | `flag` | `expand`.

## Tests

```bash
cd masonry && npm test -- brainstorm
```
