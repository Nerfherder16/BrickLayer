#!/usr/bin/env bash
set -euo pipefail

PID_FILE="/tmp/hud-server.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "HUD is not running (no PID file found)"
  exit 0
fi

PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
  kill -TERM "$PID"
  # Wait briefly for the process to clean up
  sleep 0.3
fi

rm -f "$PID_FILE"
echo "HUD stopped"
