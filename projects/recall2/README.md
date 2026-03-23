# Recall 2.0

Self-hosted AI memory system. Single Rust binary replacing a 6-service Docker stack
(Qdrant + Neo4j + PostgreSQL + Redis + Ollama + ARQ).

Derived from 256 questions of frontier research in `../../recall-arch-frontier/`.

## Install

```bash
cargo build --release
```

Binary outputs to `target/release/recall2`.

## Configure

Copy and edit `config/default.toml`:

```toml
[server]
port = 8200

[storage]
data_dir = "/data/recall2"
```

Set `RECALL2_CONFIG` environment variable to override config path.

## Run

```bash
# Create data directory
mkdir -p /data/recall2

# Run
./target/release/recall2
```

The server starts on port 8200 (same as Recall 1.0 for drop-in replacement).

## Architecture

See `ARCHITECTURE.md` for the full component map and data flow.
See `BUILD_PLAN.md` for the 5-phase, 35-day construction schedule.

## Migration from Recall 1.0

```bash
curl -X POST http://localhost:8200/admin/migrate \
  -H "Content-Type: application/json" \
  -d '{"source_url": "postgresql://..."}'
```

Existing hooks (recall-retrieve.js, observe-edit.js, recall-session-summary.js)
work without modification against the Recall 2.0 API.
