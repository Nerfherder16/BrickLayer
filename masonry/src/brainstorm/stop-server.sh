#!/bin/bash
PID_FILE=/tmp/brainstorm-server.pid
if [ ! -f "$PID_FILE" ]; then
  echo "Brainstorm server not running"
  exit 0
fi
PID=$(cat "$PID_FILE")
kill "$PID" 2>/dev/null
sleep 0.5
rm -f "$PID_FILE"
echo "Brainstorm server stopped"
