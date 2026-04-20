#!/bin/bash
PID_FILE=/tmp/brainstorm-server.pid
PORT=${BRAINSTORM_PORT:-7823}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    echo "Brainstorm server already running (PID $PID) at http://localhost:$PORT"
    exit 0
  fi
fi

node "$SCRIPT_DIR/server.cjs" &
# Wait up to 3s for /health to respond
for i in $(seq 1 6); do
  sleep 0.5
  if curl -sf "http://localhost:$PORT/health" > /dev/null 2>&1; then
    echo "Brainstorm server running at http://localhost:$PORT"
    exit 0
  fi
done
echo "ERROR: server did not start within 3 seconds"
exit 1
