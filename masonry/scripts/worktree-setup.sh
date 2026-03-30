#!/usr/bin/env bash
# worktree-setup.sh — Create isolated git worktree for a BrickLayer campaign
#
# Usage: bash masonry/scripts/worktree-setup.sh <project-name>
# Example: bash masonry/scripts/worktree-setup.sh adbp
#
# Creates:
#   ../worktrees/<project>-<date>/  — isolated working directory
#   Branch: <project>/<monthday>    — auto-named campaign branch
#
# Benefits:
#   - Multiple campaigns can run simultaneously in separate directories
#   - No branch switching conflicts between parallel Claude sessions
#   - Each worktree has its own index and working tree
#   - Changes in one worktree don't affect others until merged

set -euo pipefail

PROJECT="${1:?Usage: worktree-setup.sh <project-name>}"
DATE=$(date +%b%d | tr '[:upper:]' '[:lower:]')
BRANCH="${PROJECT}/${DATE}"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || { echo "Error: not in a git repo"; exit 1; })
WORKTREE_BASE="${REPO_ROOT}/../worktrees"
WORKTREE_DIR="${WORKTREE_BASE}/${PROJECT}-${DATE}"

# Ensure worktrees base directory exists
mkdir -p "${WORKTREE_BASE}"

# Check if worktree already exists
if [ -d "${WORKTREE_DIR}" ]; then
    echo "Worktree already exists: ${WORKTREE_DIR}"
    echo "To use it: cd ${WORKTREE_DIR}"
    echo "To remove it: git worktree remove ${WORKTREE_DIR}"
    exit 0
fi

# Check if branch already exists
if git rev-parse --verify "${BRANCH}" >/dev/null 2>&1; then
    echo "Branch '${BRANCH}' already exists — creating worktree from it"
    git worktree add "${WORKTREE_DIR}" "${BRANCH}"
else
    echo "Creating new branch '${BRANCH}' and worktree"
    git worktree add -b "${BRANCH}" "${WORKTREE_DIR}"
fi

echo ""
echo "=== Worktree created ==="
echo "  Directory: ${WORKTREE_DIR}"
echo "  Branch:    ${BRANCH}"
echo ""
echo "To start a campaign in this worktree:"
echo "  cd ${WORKTREE_DIR}/${PROJECT}"
echo "  claude --dangerously-skip-permissions \"Read program.md and questions.md. Begin the research loop.\""
echo ""
echo "To list all worktrees:"
echo "  git worktree list"
echo ""
echo "To clean up when done:"
echo "  git worktree remove ${WORKTREE_DIR}"
