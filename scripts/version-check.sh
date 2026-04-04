#!/usr/bin/env bash
# version-check.sh — BrickLayer + Masonry daily version check
# Runs on VS Code folder open, fires at most once per day.

STAMP_FILE="$HOME/.bricklayer-last-check"
TODAY=$(date +%Y-%m-%d)

# Only run once per day
if [[ -f "$STAMP_FILE" ]] && [[ "$(cat "$STAMP_FILE")" == "$TODAY" ]]; then
  exit 0
fi

echo "$TODAY" > "$STAMP_FILE"

BL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BL_VERSION=$(cat "$BL_ROOT/VERSION" 2>/dev/null || echo "unknown")
MASONRY_VERSION=$(cat "$BL_ROOT/masonry/VERSION" 2>/dev/null || echo "unknown")
GIT_BRANCH=$(git -C "$BL_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_COMMIT=$(git -C "$BL_ROOT" log --oneline -1 2>/dev/null || echo "unknown")
GIT_DIRTY=$(git -C "$BL_ROOT" status --short 2>/dev/null | wc -l | tr -d ' ')

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║        BrickLayer 2.0  Daily Check           ║"
echo "╠══════════════════════════════════════════════╣"
printf  "║  BrickLayer  : %-29s ║\n" "v$BL_VERSION"
printf  "║  Masonry     : %-29s ║\n" "v$MASONRY_VERSION"
printf  "║  Branch      : %-29s ║\n" "$GIT_BRANCH"
printf  "║  Last commit : %-29s ║\n" "${GIT_COMMIT:0:29}"
printf  "║  Uncommitted : %-29s ║\n" "$GIT_DIRTY files"
echo "╚══════════════════════════════════════════════╝"
echo ""
