# oh-my-claudecode StatusLine Installation Research

## Executive Summary

The statusline is installed and registered through a multi-phase process that involves copying compiled scripts to `~/.claude/hud/`, configuring a command reference in Claude Code's `settings.json`, and version-gating to prevent downgrades. No external marketplace registration is required beyond the plugin's discovery via `.claude-plugin/plugin.json`.

---

## 1. The omc-setup Skill — Step-by-Step Execution

The `/omc-setup` skill is defined in `skills/omc-setup/SKILL.md` and executes in 4 phases:

### Phase 1: Install CLAUDE.md
- Copies the global OMC context from `~/.claude/CLAUDE.md`
- Sets version markers to prevent downgrades
- Establishes the ground truth for OMC configuration

### Phase 2: Environment Configuration
- Delegates to the `/hud` skill (executes `skills/hud/SKILL.md`)
- The HUD skill handles:
  - Copying `omc-hud.mjs` (compiled HUD script) to `~/.claude/hud/`
  - Copying `find-node.sh` (node binary resolver) to `~/.claude/hud/`
  - Setting file permissions (`chmod +x`)
  - Updating `settings.json` with the statusLine configuration

### Phase 3: Integration Setup
- Syncs MCP servers from `.mcp.json` to user's `~/.claude.json`
- Preserves existing non-OMC MCP servers
- Adds OMC-specific servers (agent orchestration, memory, etc.)

### Phase 4: Completion
- Marks setup completion in `.omc-config.json`
- Sets `setupComplete: true` flag
- Records timestamp

---

## 2. Exact StatusLine Format in settings.json

### Modern Format (Post-v4.8)

```json
{
  "statusLine": {
    "type": "command",
    "command": "sh $HOME/.claude/hud/find-node.sh $HOME/.claude/hud/omc-hud.mjs"
  }
}
```

**Unix/Linux/macOS:** Uses shell script wrapper `find-node.sh` for cross-platform node resolution (nvm/fnm/system compatibility)

### Windows Format

```json
{
  "statusLine": {
    "type": "command",
    "command": "C:\\Program Files\\nodejs\\node.exe C:\\Users\\<user>\\.claude\\hud\\omc-hud.mjs"
  }
}
```

**Windows:** Absolute path to node.exe, no shell script needed

### Legacy Format (Auto-Migrated)

```json
{
  "statusLine": "sh $HOME/.claude/hud/find-node.sh $HOME/.claude/hud/omc-hud.mjs"
}
```

The installer detects legacy string format and automatically migrates to the object format.

### Detection Function

From `src/installer/index.ts`:
```typescript
function isOmcStatusLine(statusLine: unknown): boolean {
  if (typeof statusLine === "object" && statusLine !== null && "type" in statusLine) {
    return (statusLine as Record<string, unknown>).type === "command";
  }
  if (typeof statusLine === "string") {
    return statusLine.includes("omc-hud.mjs");
  }
  return false;
}
```

---

## 3. The Installer Logic — src/installer/index.ts

Core responsibilities:

### 3.1 StatusLine Configuration
- Reads current `settings.json` from `~/.claude/`
- Checks if OMC statusline already exists using `isOmcStatusLine()`
- If missing, constructs new statusLine object:
  - **Unix:** `{ type: "command", command: "sh $HOME/.claude/hud/find-node.sh $HOME/.claude/hud/omc-hud.mjs" }`
  - **Windows:** `{ type: "command", command: "{nodeExePath} {hudPath}\\omc-hud.mjs" }`
- Writes updated `settings.json` back

### 3.2 File Copying
- Copies `omc-hud.mjs` (compiled script) to `~/.claude/hud/omc-hud.mjs`
- Copies `find-node.sh` (node resolver) to `~/.claude/hud/find-node.sh`
- Sets executable permissions: `chmod +x ~/.claude/hud/find-node.sh` and `.mjs`

### 3.3 Hook Integration
- Reads existing hooks from `.claude/settings.json`
- Identifies OMC hooks vs. non-OMC hooks using `isOmcHook()`
- Preserves all non-OMC hooks
- Adds/updates OMC hooks (UserPromptSubmit, PostToolUse, Stop, etc.)
- Writes hooks back to `settings.json`

### 3.4 Version Safety
- Reads version from `.omc-version.json`
- Compares against current installed version
- **Prevents downgrade** if current < installed
- Records new version in `.omc-version.json`

### 3.5 Node Binary Resolution
- On Unix: Defers to `find-node.sh` which:
  - Checks `$NVM_BIN/node`
  - Checks `$FNM_BIN/node`
  - Falls back to `which node`
  - Caches result in `.omc-config.json`
- On Windows: Searches PATH for `node.exe`

---

## 4. Marketplace Registration

**No separate marketplace registration is required.**

Plugin discovery happens automatically via:

### .claude-plugin/plugin.json

```json
{
  "name": "oh-my-claudecode",
  "version": "4.8.2",
  "description": "Multi-agent orchestration system for Claude Code",
  "skills": "./skills/",
  "mcpServers": "./.mcp.json"
}
```

### Discovery Mechanism
1. Claude Code scans GitHub repository at startup
2. Looks for `.claude-plugin/plugin.json` in repo root
3. Reads plugin metadata (name, version, skills directory, MCP servers)
4. Skills are auto-discovered from `skills/*/SKILL.md`
5. MCP servers are loaded from `.mcp.json`

### Installation Flow (User Perspective)
```bash
/plugin marketplace add https://github.com/Yeachan-Heo/oh-my-claudecode
/plugin install oh-my-claudecode
/omc-setup
```

---

## 5. Plugin Cache Directory Setup

### Directory Structure

```
~/.claude/
  hud/
    omc-hud.mjs          # Compiled HUD statusline script
    find-node.sh         # Node binary resolver (Unix)
    .omc-node-cache      # Cached node path (Unix)
  .omc-config.json       # OMC configuration (see below)
  .omc-version.json      # Version marker for downgrade prevention
  CLAUDE.md              # Global OMC context (installed by Phase 1)
  settings.json          # Contains statusLine + hooks + MCP servers
  skills/                # Plugin skills (auto-discovered)
```

### .omc-config.json Schema

```json
{
  "setupComplete": true,
  "installedVersion": "4.8.2",
  "nodeResolverCache": "/usr/local/bin/node",
  "hooks": {
    "UserPromptSubmit": "enabled",
    "PostToolUse": "enabled",
    "Stop": "enabled"
  },
  "mcp": {
    "recall": "configured",
    "github": "configured",
    "claude-flow": "configured"
  }
}
```

---

## 6. HUD Script Entry Point — src/hud/index.ts

The HUD script (`omc-hud.mjs`) is the statusline renderer executed every 200-500ms by Claude Code.

### Communication Protocol

**stdin:** JSON-serialized transcript from Claude Code
```json
{
  "sessionId": "uuid",
  "messages": [...],
  "tools": [{"type": "task", "name": "...", "status": "..."}]
}
```

**stdout:** Rendered statusline (single line)
```
[OMC] Agents: 3 active | Tasks: 5 (2 done) | Rate: 85% | ralph-loop: 3 waves
```

### Execution Steps

1. **Read stdin** — Parse transcript from Claude Code
2. **Scan for agents** — Count active agents from tool history
3. **Read state files** — Load `.omc/state/{mode}-state.json`:
   - `ralph-state.json` (ralph loop status, wave count)
   - `ultrawork-state.json` (parallelism level, task count)
   - `autopilot-state.json` (build progress, test counts)
4. **Fetch rate limits** — Query Claude API for usage
5. **Render output** — Format single-line status with:
   - Active agent count
   - Task queue (total/done)
   - Current rate limit %
   - Mode-specific info (ralph waves, autopilot test counts, etc.)
6. **Write stdout** — Send rendered line to Claude Code

---

## 7. Version Detection & Downgrade Prevention

### .omc-version.json

```json
{
  "version": "4.8.2",
  "installedAt": "2026-03-17T00:00:00Z",
  "preventDowngrade": true
}
```

### Logic

From `src/installer/index.ts`:
```typescript
const currentVersion = pkg.version;
const installedVersion = readOmcVersionJson()?.version || "0.0.0";

if (semver.lt(currentVersion, installedVersion) && preventDowngrade) {
  throw new Error(
    `Cannot downgrade OMC from ${installedVersion} to ${currentVersion}. ` +
    `Delete ~/.claude/.omc-version.json to force.`
  );
}
```

### CLAUDE.md Markers

The installer also checks `~/.claude/CLAUDE.md` for version markers:
```markdown
# oh-my-claudecode — Version 4.8.2
<!-- marker: DO NOT EDIT -->
```

If the marker version is newer than the installer, setup is skipped (prevents overwriting a newer installation).

---

## 8. Hook Integration — Preservation of Non-OMC Hooks

The installer identifies OMC hooks vs. user/plugin hooks using `isOmcHook()`:

```typescript
function isOmcHook(hook: Hook): boolean {
  // OMC hooks contain these markers in their command
  const omcMarkers = [
    "omc",
    "recall-retrieve.js",
    "observe-edit.js",
    "recall-session-summary.js"
  ];
  return omcMarkers.some(marker => hook.command?.includes(marker));
}
```

**During installation:**
1. Read all existing hooks from `settings.json`
2. Partition into OMC hooks (to be replaced) and other hooks (preserve)
3. Add new/updated OMC hooks
4. Merge with preserved hooks
5. Write complete hook list back to `settings.json`

This ensures user hooks (e.g., for other plugins) are never removed.

---

## 9. Quick Start Flow (from README.md)

```bash
# 1. Add plugin to marketplace
/plugin marketplace add https://github.com/Yeachan-Heo/oh-my-claudecode

# 2. Install the plugin
/plugin install oh-my-claudecode

# 3. Run setup (automated, 4 phases)
/omc-setup

# Done — OMC is now active
# Statusline appears in Claude Code footer
# All skills available (/plan, /build, /team, /ralph, etc.)
```

---

## 10. Key Technical Insights

1. **Stateless HUD**: The statusline script is completely stateless — it reads state files on each execution, enabling real-time updates without polling loops.

2. **Node Resolution Strategy**: The portable `find-node.sh` handles nvm/fnm/system node seamlessly, with caching for performance.

3. **Hook Preservation**: The installer's `isOmcHook()` function ensures plugin coexistence — other plugins' hooks are never removed.

4. **Version Safety**: Dual version markers (`.omc-version.json` + `CLAUDE.md`) prevent accidental downgrades while allowing forced upgrades.

5. **Auto-Migration**: Legacy string-format statusLine is automatically detected and upgraded to object format during installation.

6. **File Permissions**: On Unix, the installer explicitly sets execute permissions on `.sh` and `.mjs` files to handle umask variations.

---

## Files Examined

- `src/installer/index.ts` (300+ lines) — Core installation logic
- `skills/omc-setup/SKILL.md` — Setup skill definition (4 phases)
- `skills/hud/SKILL.md` — HUD setup sub-skill
- `src/hud/index.ts` — Statusline script entry point
- `.claude-plugin/plugin.json` — Plugin metadata
- `README.md` — Quick start instructions
- GitHub API responses for file tree verification

---

## Conclusion

The oh-my-claudecode statusline is installed through a carefully designed multi-phase process that:
- Copies compiled scripts to `~/.claude/hud/`
- Configures a command-based statusLine in `settings.json`
- Integrates hooks while preserving existing plugin hooks
- Prevents version downgrades via dual markers
- Uses portable node binary resolution for cross-platform compatibility
- Executes as a stateless renderer every 200-500ms, reading fresh state files each time

No external marketplace registration is required — plugin discovery happens automatically via `.claude-plugin/plugin.json` in the repository.
