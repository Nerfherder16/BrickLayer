#!/usr/bin/env bash
# git-sync.sh — auto-sync BrickLayer repo between machines
# Runs on cron, pulls remote changes then pushes local ones.
# Uses --autostash to handle dirty working trees safely.

REPO="/home/nerfherder/Dev/Bricklayer2.0"
LOG="$HOME/.bricklayer-sync.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

cd "$REPO" || exit 1

# Skip if inside an active rebase/merge
if [[ -d "$REPO/.git/rebase-merge" || -d "$REPO/.git/rebase-apply" || -f "$REPO/.git/MERGE_HEAD" ]]; then
  echo "[$TIMESTAMP] SKIP — rebase/merge in progress" >> "$LOG"
  exit 0
fi

# Pull with autostash (handles dirty working tree)
PULL_OUT=$(git pull --rebase --autostash 2>&1)
PULL_EXIT=$?

if [[ $PULL_EXIT -ne 0 ]]; then
  echo "[$TIMESTAMP] PULL FAILED: $PULL_OUT" >> "$LOG"
  exit 1
fi

# Push local commits
PUSH_OUT=$(git push 2>&1)
PUSH_EXIT=$?

if [[ $PUSH_EXIT -ne 0 ]]; then
  echo "[$TIMESTAMP] PUSH FAILED: $PUSH_OUT" >> "$LOG"
  exit 1
fi

echo "[$TIMESTAMP] OK — $(git log --oneline -1)" >> "$LOG"
