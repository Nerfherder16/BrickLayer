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
import json, sys, os, tempfile

src_file, dst_file = sys.argv[1], sys.argv[2]

with open(src_file) as f:
    src = json.load(f)

dst = {}
if os.path.exists(dst_file):
    with open(dst_file) as f:
        try:
            dst = json.load(f)
        except Exception as e:
            print(f"WARNING: {dst_file} is invalid JSON ({e}), skipping merge to avoid data loss", file=sys.stderr)
            sys.exit(1)

src_mcps = src.get('mcpServers', {})

# On non-WSL Linux, remap Windows paths (/mnt/c/Users/trg16/...) to ~/Dev/...
import platform, subprocess
is_wsl = False
if platform.system() == 'Linux':
    try:
        with open('/proc/version') as pv:
            is_wsl = 'microsoft' in pv.read().lower()
    except Exception:
        pass

if not is_wsl and platform.system() == 'Linux':
    home = os.path.expanduser('~')
    win_prefix = '/mnt/c/Users/trg16/Dev/'
    linux_prefix = os.path.join(home, 'Dev/')
    for name, server in src_mcps.items():
        new_args = [a.replace(win_prefix, linux_prefix) for a in server.get('args', [])]
        # Fix capitalization: Bricklayer2.0 -> BrickLayer2.0 (ubuntu-claude repo path)
        new_args = [a.replace('/Dev/Bricklayer2.0/', '/Dev/BrickLayer2.0/') for a in new_args]
        if new_args != server.get('args', []):
            server = dict(server, args=new_args)
            src_mcps[name] = server

dst.setdefault('mcpServers', {}).update(src_mcps)

# Atomic write: write to temp file first, then rename
dst_dir = os.path.dirname(os.path.abspath(dst_file))
fd, tmp_path = tempfile.mkstemp(dir=dst_dir, suffix='.tmp')
try:
    with os.fdopen(fd, 'w') as f:
        json.dump(dst, f, indent=2)
    os.replace(tmp_path, dst_file)
except Exception:
    os.unlink(tmp_path)
    raise
PYEOF
  if [[ $? -eq 0 ]]; then
    echo "[$TIMESTAMP] deploy-claude: mcp-servers merged into ~/.claude.json" >> "$LOG"
  else
    echo "[$TIMESTAMP] deploy-claude: mcp-servers merge SKIPPED (invalid target JSON)" >> "$LOG"
  fi
fi

echo "[$TIMESTAMP] deploy-claude: done" >> "$LOG"
