#!/usr/bin/env bash
# Masonry Background Daemon Manager
# Manages long-running background workers for BrickLayer quality analysis.
#
# Usage:
#   ./daemon-manager.sh start [worker]   # start all workers, or a specific one
#   ./daemon-manager.sh stop [worker]    # stop all workers, or a specific one
#   ./daemon-manager.sh status           # show worker status
#   ./daemon-manager.sh restart [worker] # restart worker(s)
#
# Workers:
#   testgaps   — 30min: scan for files without tests, write .autopilot/testgaps.md
#   optimize   — 30min: linter + typecheck, write .autopilot/quality.md
#   consolidate — 2h: deduplicate Recall build patterns via similarity
#   deepdive   — 4h: code complexity + dead code + duplication audit
#   ultralearn  — 60min: deep session pattern extraction, store to Recall
#   map         — 30min: codebase structure map, write .autopilot/map.md
#   document    — 60min: docstring gap analysis, store to Recall
#   refactor    — 2h: god files + duplicate blocks + deep nesting → .autopilot/refactor-candidates.md
#   benchmark   — 4h: test suite timing, regression detection → .autopilot/benchmark.md

set -euo pipefail

DAEMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${DAEMON_DIR}/logs"
PID_DIR="${DAEMON_DIR}/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

# Worker definitions: name -> script -> interval_seconds
declare -A WORKER_SCRIPTS=(
  [testgaps]="${DAEMON_DIR}/worker-testgaps.js"
  [optimize]="${DAEMON_DIR}/worker-optimize.js"
  [consolidate]="${DAEMON_DIR}/worker-consolidate.js"
  [deepdive]="${DAEMON_DIR}/worker-deepdive.js"
  [ultralearn]="${DAEMON_DIR}/worker-ultralearn.js"
  [map]="${DAEMON_DIR}/worker-map.js"
  [document]="${DAEMON_DIR}/worker-document.js"
  [refactor]="${DAEMON_DIR}/worker-refactor.js"
  [benchmark]="${DAEMON_DIR}/worker-benchmark.js"
)

declare -A WORKER_INTERVALS=(
  [testgaps]=1800      # 30 minutes
  [optimize]=1800      # 30 minutes
  [consolidate]=7200   # 2 hours
  [deepdive]=14400     # 4 hours
  [ultralearn]=3600    # 60 minutes
  [map]=1800           # 30 minutes
  [document]=3600      # 60 minutes
  [refactor]=7200      # 2 hours
  [benchmark]=14400    # 4 hours
)

pid_file() { echo "${PID_DIR}/${1}.pid"; }
log_file() { echo "${LOG_DIR}/${1}.log"; }

is_running() {
  local name=$1
  local pidfile; pidfile=$(pid_file "$name")
  if [[ -f "$pidfile" ]]; then
    local pid; pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

start_worker() {
  local name=$1
  local script="${WORKER_SCRIPTS[$name]}"
  local interval="${WORKER_INTERVALS[$name]}"
  local pidfile; pidfile=$(pid_file "$name")
  local logfile; logfile=$(log_file "$name")

  if is_running "$name"; then
    echo "[daemon-manager] $name already running (PID $(cat "$pidfile"))"
    return 0
  fi

  if [[ ! -f "$script" ]]; then
    echo "[daemon-manager] ERROR: Script not found: $script"
    return 1
  fi

  # Start in background with nohup + sleep loop
  nohup bash -c "
    while true; do
      echo \"[\$(date -Iseconds)] $name: starting\" >> '$logfile'
      node '$script' >> '$logfile' 2>&1
      echo \"[\$(date -Iseconds)] $name: done, sleeping ${interval}s\" >> '$logfile'
      sleep $interval
    done
  " > /dev/null 2>&1 &

  local pid=$!
  echo $pid > "$pidfile"
  echo "[daemon-manager] Started $name (PID $pid, interval ${interval}s)"
}

stop_worker() {
  local name=$1
  local pidfile; pidfile=$(pid_file "$name")

  if ! is_running "$name"; then
    echo "[daemon-manager] $name not running"
    rm -f "$pidfile"
    return 0
  fi

  local pid; pid=$(cat "$pidfile")

  # Kill the process group (catches the nohup + bash + node chain)
  kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
  sleep 1
  kill -KILL "$pid" 2>/dev/null || true

  rm -f "$pidfile"
  echo "[daemon-manager] Stopped $name (was PID $pid)"
}

show_status() {
  echo "Masonry Daemon Workers"
  echo "====================="
  for name in testgaps optimize consolidate deepdive ultralearn map document refactor benchmark; do
    local pidfile; pidfile=$(pid_file "$name")
    local logfile; logfile=$(log_file "$name")
    local interval="${WORKER_INTERVALS[$name]}"

    if is_running "$name"; then
      local pid; pid=$(cat "$pidfile")
      local last_run=""
      if [[ -f "$logfile" ]]; then
        last_run=$(grep "starting" "$logfile" 2>/dev/null | tail -1 | cut -d']' -f1 | tr -d '[' || echo "unknown")
      fi
      printf "  %-15s RUNNING  PID=%-8s interval=%ds  last=%s\n" "$name" "$pid" "$interval" "$last_run"
    else
      printf "  %-15s STOPPED  interval=%ds\n" "$name" "$interval"
    fi
  done

  echo ""
  echo "Output files:"
  local cwd; cwd=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  for f in testgaps quality; do
    local fp="${cwd}/.autopilot/${f}.md"
    if [[ -f "$fp" ]]; then
      echo "  .autopilot/${f}.md — $(wc -l < "$fp") lines, $(date -r "$fp" '+%Y-%m-%d %H:%M')"
    else
      echo "  .autopilot/${f}.md — not yet generated"
    fi
  done
}

# --- Main ---

COMMAND="${1:-status}"
WORKER="${2:-all}"

case "$COMMAND" in
  start)
    if [[ "$WORKER" == "all" ]]; then
      for name in testgaps optimize consolidate deepdive ultralearn map document refactor benchmark; do start_worker "$name"; done
    else
      start_worker "$WORKER"
    fi
    ;;
  stop)
    if [[ "$WORKER" == "all" ]]; then
      for name in testgaps optimize consolidate deepdive ultralearn map document refactor benchmark; do stop_worker "$name"; done
    else
      stop_worker "$WORKER"
    fi
    ;;
  restart)
    if [[ "$WORKER" == "all" ]]; then
      for name in testgaps optimize consolidate deepdive ultralearn map document refactor benchmark; do
        stop_worker "$name"
        sleep 0.5
        start_worker "$name"
      done
    else
      stop_worker "$WORKER"
      sleep 0.5
      start_worker "$WORKER"
    fi
    ;;
  status)
    show_status
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status} [worker|all]"
    exit 1
    ;;
esac
