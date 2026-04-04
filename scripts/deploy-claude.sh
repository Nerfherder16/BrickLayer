#!/usr/bin/env bash
# deploy-claude.sh — sync .claude/ from BrickLayer repo to ~/.claude/
# Safe to run repeatedly — skips settings.json if secrets not filled in.

BL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$BL_ROOT/.claude"
DST="$HOME/.claude"
LOG="$HOME/.bricklayer-sync.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] deploy-claude: syncing .claude/" >> "$LOG"

# Skills
if [[ -d "$SRC/skills" ]]; then
  mkdir -p "$DST/skills"
  rsync -a --delete "$SRC/skills/" "$DST/skills/"
  echo "[$TIMESTAMP] deploy-claude: skills synced" >> "$LOG"
fi

# Plugins
if [[ -d "$SRC/plugins" ]]; then
  mkdir -p "$DST/plugins"
  rsync -a --delete "$SRC/plugins/" "$DST/plugins/"
  echo "[$TIMESTAMP] deploy-claude: plugins synced" >> "$LOG"
fi

# Monitors
if [[ -d "$SRC/monitors" ]]; then
  mkdir -p "$DST/monitors"
  rsync -a --delete "$SRC/monitors/" "$DST/monitors/"
  echo "[$TIMESTAMP] deploy-claude: monitors synced" >> "$LOG"
fi

# Rules (merge — don't delete local-only rules)
if [[ -d "$SRC/rules" ]]; then
  mkdir -p "$DST/rules"
  rsync -a "$SRC/rules/" "$DST/rules/"
  echo "[$TIMESTAMP] deploy-claude: rules synced" >> "$LOG"
fi

# Commands (merge)
if [[ -d "$SRC/commands" ]]; then
  mkdir -p "$DST/commands"
  rsync -a "$SRC/commands/" "$DST/commands/"
  echo "[$TIMESTAMP] deploy-claude: commands synced" >> "$LOG"
fi

# Agents (merge)
if [[ -d "$SRC/agents" ]]; then
  mkdir -p "$DST/agents"
  rsync -a "$SRC/agents/" "$DST/agents/"
  echo "[$TIMESTAMP] deploy-claude: agents synced" >> "$LOG"
fi

# settings.json — only deploy template if no settings.json exists yet
# Never overwrite an existing settings.json (it has machine-specific secrets)
if [[ ! -f "$DST/settings.json" ]] && [[ -f "$SRC/settings.template.json" ]]; then
  cp "$SRC/settings.template.json" "$DST/settings.json"
  echo "[$TIMESTAMP] deploy-claude: settings.json created from template — fill in REPLACE_ME values" >> "$LOG"
  echo ""
  echo "⚠️  ~/.claude/settings.json created from template."
  echo "    Open it and replace REPLACE_ME values with your API keys."
  echo ""
fi

# MCP servers — merge into ~/.claude.json (preserves user-specific fields)
if [[ -f "$SRC/mcp-servers.json" ]] && command -v python3 &>/dev/null; then
  python3 - "$SRC/mcp-servers.json" "$HOME/.claude.json" <<'PYEOF'
import json, sys, os

src_file, dst_file = sys.argv[1], sys.argv[2]
with open(src_file) as f:
    src = json.load(f)

dst = {}
if os.path.exists(dst_file):
    with open(dst_file) as f:
        try:
            dst = json.load(f)
        except Exception:
            dst = {}

dst.setdefault('mcpServers', {}).update(src.get('mcpServers', {}))

with open(dst_file, 'w') as f:
    json.dump(dst, f, indent=2)
PYEOF
  echo "[$TIMESTAMP] deploy-claude: mcp-servers merged into ~/.claude.json" >> "$LOG"
fi

echo "[$TIMESTAMP] deploy-claude: done" >> "$LOG"
