#!/bin/sh
# TIME_BOMB mitigation: bricklayer entrypoint MUST start tmux before uvicorn.
# See ROADMAP.md 0d — if tmux is not started first, spawn_agent() will fail
# because it tries to create tmux sessions but the server isn't running.
set -e

# Start tmux server in background (required for BrickLayer agent spawning)
tmux new-session -d -s main 2>/dev/null || true

# Launch uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8300
