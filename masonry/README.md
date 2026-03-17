# Masonry

Research-first orchestration framework for Claude Code, built on BrickLayer 2.0.

> A mason works with the same raw material as a bricklayer but with greater precision, scope, and craft.

## What It Is

Masonry is the platform that BrickLayer 2.0 deserves:
- **Research loop as the engine** — not bolted on
- **Parallel team execution** — multiple agents per wave
- **Recall-native memory** — every session fully hydrated, every finding auto-stored
- **Zero-friction onboarding** — `/masonry-init` wizard
- **Domain-agnostic** — research, coding, audit, science, legal, anything
- **Self-managing agent fleet** — forge-check, agent-auditor, peer-reviewer built in

## Status

🚧 **Pre-alpha — spec phase**

See [MASONRY-SPEC.md](./MASONRY-SPEC.md) for the full design.

## Structure

```
masonry/
  bin/              ← CLI entry points (masonry-setup.js, masonry-mcp.js)
  src/
    core/           ← loop engine, team composer, registry, session manager
    hooks/          ← Claude Code hook scripts
  skills/           ← /masonry-* skill definitions
  packs/
    masonry-core/   ← BL2 template agents + mode instructions
    masonry-frontier/ ← Frontier discovery agents
```

## Quick Start (once released)

```bash
npm install -g masonry-mcp
masonry-setup
```

Then in any Claude Code session:
```
/masonry-init
/masonry-run
```

## Relationship to BrickLayer 2.0

Masonry does not replace BrickLayer 2.0's core evaluation logic — it provides the platform:
- All BL2 Python modules (`campaign.py`, `findings.py`, etc.) are unchanged
- Existing BL2 projects migrate with `masonry migrate {project-path}`
- `DISABLE_OMC=1` requirement eliminated — Masonry IS the platform

## Built On

- **BrickLayer 2.0** — research loop engine, verdict system, agent fleet
- **Mnemonics** (System-Recall) — onboarding wizard, hook architecture
- **Recall** — memory foundation (`http://100.70.195.84:8200`)
