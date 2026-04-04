#!/usr/bin/env bash
# Hook timing wrapper. Logs actual execution time of every hook.
# Usage: hook-timer.sh <hook-name> <actual-command...>
# Logs to ~/.claude/monitors/hook-times.log
#
# To view slow hooks:  grep -E '[0-9]{4,}ms' ~/.claude/monitors/hook-times.log
# To view recent:      tail -30 ~/.claude/monitors/hook-times.log
# To view by hook:     grep style-checker ~/.claude/monitors/hook-times.log

LOG="/home/nerfherder/.claude/monitors/hook-times.log"
NAME="$1"
shift

START_MS=$(($(date +%s%N) / 1000000))

# Pass stdin through to the actual command
"$@"
EXIT_CODE=$?

END_MS=$(($(date +%s%N) / 1000000))
ELAPSED=$((END_MS - START_MS))

echo "$(date -Iseconds) ${NAME} ${ELAPSED}ms exit=${EXIT_CODE}" >> "$LOG"

# Flag slow hooks (>2s) to stderr so they show in masonry error logs
if [ "$ELAPSED" -gt 2000 ]; then
  echo "[SLOW HOOK] ${NAME}: ${ELAPSED}ms" >> "$LOG"
fi

exit $EXIT_CODE
