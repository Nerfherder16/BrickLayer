# BrickLayer 2.0 — Claude Plugin

AI research campaign + autonomous build framework for Claude Code.

## Install

```bash
claude install bricklayer
```

Or manually:

```bash
git clone https://github.com/your-org/bricklayer2
cd bricklayer2
cp -r template/.claude/agents/ ~/.claude/agents/
# Merge masonry/hooks/hooks.json into ~/.claude/settings.json
# Add masonry MCP server: node masonry/bin/masonry-mcp.js
```

## What Gets Installed

| Component | Destination | Count |
|-----------|-------------|-------|
| Agents | `~/.claude/agents/` | 20+ specialist agents |
| Skills | `~/.claude/skills/` | 15+ slash commands |
| Hooks | `~/.claude/settings.json` | 14 lifecycle hooks |
| MCP Server | Claude settings | `masonry` (20+ tools) |

## Quick Start

### Research Campaign
```
/teach-bricklayer     # one-time project setup (reads your codebase)
/masonry-init         # create a new research project
/masonry-run          # start the autonomous research loop
```

### Autonomous Build
```
/teach-bricklayer     # one-time project setup
/plan                 # spec-writer explores codebase, writes .autopilot/spec.md
# review and approve the spec, then:
/build                # TDD pipeline — test-writer → developer → code-reviewer per task
/verify               # independent compliance check
```

## Commands

| Command | Description |
|---------|-------------|
| `/teach-bricklayer` | Context Gathering Protocol — indexes your project for all agents |
| `/plan` | Write a buildable spec from a one-line task description |
| `/build` | Autonomous TDD build — commits after every passing task |
| `/verify` | Independent spec compliance verification (never modifies source) |
| `/fix` | Targeted fix cycle — max 3 attempts, then escalates |
| `/ultrawork` | High-throughput parallel build for independent tasks |
| `/masonry-run` | Start or resume a BrickLayer research campaign |
| `/masonry-status` | Campaign progress, question counts, findings summary |
| `/masonry-fleet` | Agent fleet health — scores, add/retire agents |
| `/ui-init` | Initialize dark-first UI design system with token extraction |
| `/ui-compose` | Agent-mode UI build from design brief or Figma URL |
| `/visual-report` | Convert synthesis.md findings into a navigable HTML report |

## Full Documentation

- Architecture: `docs/architecture.md`
- Campaign workflow: `docs/campaign-workflow.md`
- Build workflow: `docs/build-workflow.md`
- Agent registry: `masonry/agent_registry.yml`
