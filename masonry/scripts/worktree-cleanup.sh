#!/usr/bin/env bash
# worktree-cleanup.sh — Clean up completed campaign worktrees
#
# Usage: bash masonry/scripts/worktree-cleanup.sh [--all | <project-name>]
# Example: bash masonry/scripts/worktree-cleanup.sh adbp
#          bash masonry/scripts/worktree-cleanup.sh --all

set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || { echo "Error: not in a git repo"; exit 1; })
WORKTREE_BASE="${REPO_ROOT}/../worktrees"

if [ "${1:-}" = "--all" ]; then
    echo "Removing all campaign worktrees..."
    git worktree list | grep "${WORKTREE_BASE}" | while read -r line; do
        dir=$(echo "$line" | awk '{print $1}')
        branch=$(echo "$line" | awk '{print $3}' | tr -d '[]')
        echo "  Removing: ${dir} (${branch})"
        git worktree remove "${dir}" --force 2>/dev/null || true
    done
    git worktree prune
    echo "Done. Remaining worktrees:"
    git worktree list
elif [ -n "${1:-}" ]; then
    PROJECT="$1"
    git worktree list | grep "${PROJECT}" | while read -r line; do
        dir=$(echo "$line" | awk '{print $1}')
        echo "  Removing: ${dir}"
        git worktree remove "${dir}" --force 2>/dev/null || true
    done
    git worktree prune
    echo "Remaining worktrees:"
    git worktree list
else
    echo "Usage: worktree-cleanup.sh [--all | <project-name>]"
    echo ""
    echo "Current worktrees:"
    git worktree list
fi
