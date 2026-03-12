#!/bin/bash
# Start the autosearch dashboard
# Usage: ./start.sh [project-path]
# Example: ./start.sh C:/Users/trg16/Dev/autosearch/adbp

PROJECT=${1:-"C:/Users/trg16/Dev/autosearch/adbp"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting autosearch dashboard..."
echo "Project: $PROJECT"
echo "Backend:  http://localhost:8100"
echo "Frontend: http://localhost:3100"
echo ""

# Start backend
cd "$SCRIPT_DIR/backend" && AUTOSEARCH_PROJECT="$PROJECT" uvicorn main:app --host 0.0.0.0 --port 8100 --reload &
BACKEND_PID=$!

# Start frontend
cd "$SCRIPT_DIR/frontend" && npm run dev &
FRONTEND_PID=$!

echo "PIDs: backend=$BACKEND_PID frontend=$FRONTEND_PID"
echo "Press Ctrl+C to stop both."

trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT INT TERM
wait
