#!/usr/bin/env bash
# Install git pre-commit hook for this repo.
# Run once after cloning: bash scripts/install-hooks.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GIT_DIR="$(git -C "$REPO_ROOT" rev-parse --git-dir)"
HOOKS_DIR="$GIT_DIR/hooks"
HOOK_FILE="$HOOKS_DIR/pre-commit"

mkdir -p "$HOOKS_DIR"

cat > "$HOOK_FILE" << HOOK
#!/usr/bin/env bash
# Auto-installed by scripts/install-hooks.sh
python "\$(git rev-parse --show-toplevel)/scripts/pre-commit.py"
HOOK

chmod +x "$HOOK_FILE"

echo "Pre-commit hook installed: $HOOK_FILE"
echo "Runs: scripts/pre-commit.py (lint-guard + commit-reviewer)"
echo ""
echo "To skip for a single commit: git commit --no-verify"
echo "To uninstall:                rm $HOOK_FILE"
