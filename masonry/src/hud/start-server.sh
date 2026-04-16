#!/usr/bin/env bash
set -euo pipefail

PID_FILE="/tmp/hud-server.pid"
SERVER="/home/nerfherder/Dev/Bricklayer2.0/masonry/src/hud/server.cjs"
PORT="${HUD_PORT:-7824}"

# Check if already running
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "HUD already running (PID $OLD_PID) at http://localhost:$PORT"
    exit 0
  else
    echo "Removing stale PID file"
    rm -f "$PID_FILE"
  fi
fi

cd /home/nerfherder/Dev/Bricklayer2.0

# Start server in background
node "$SERVER" >> /tmp/hud-server.log 2>&1 &

# Poll /health up to 3 seconds
DEADLINE=$((SECONDS + 3))
until curl -sf "http://localhost:$PORT/health" > /dev/null 2>&1; do
  if [ "$SECONDS" -ge "$DEADLINE" ]; then
    echo "HUD server failed to start — check /tmp/hud-server.log" >&2
    exit 1
  fi
  sleep 0.2
done

echo "HUD running at http://localhost:$PORT"
