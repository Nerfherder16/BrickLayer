# CodeVV OS — Project Brief

**Authority: Tier 1 — Human Only**
Last updated: 2026-04-02

---

## What CodeVV OS Is

CodeVV OS is a boot-to-browser operating system experience built on top of CodeVV (https://github.com/Nerfherder16/Codevv). Instead of a traditional desktop environment, users boot into CodeVV — a collaborative AI-assisted software design platform — as their entire workspace.

It is not a kernel-level OS. It is a minimal Linux distribution that boots directly into CodeVV's web interface via a kiosk-mode browser. Multiple users access the same deployment through any web browser, collaborating in real-time via Yjs.

**The one-sentence pitch:** A bootable, multi-user development OS where CodeVV IS the desktop — AI-assisted planning, real-time editing, visual design, and deployment orchestration, all in the browser.

---

## Core Thesis

Developers don't need a general-purpose desktop. They need an editor, a terminal, a file browser, and AI assistance. CodeVV already provides all of these as a web app. Wrapping it in a minimal Linux boot image eliminates the overhead of a traditional OS and delivers a focused, collaborative development environment.

The target deployment is a Threadripper PRO 9975WX server running Proxmox, where CodeVV OS runs as a VM serving multiple simultaneous users via browser.

---

## What CodeVV Already Has

- **Frontend:** React 19, TypeScript, Tailwind v4, Vite
- **Backend:** FastAPI, SQLAlchemy (async), Pydantic
- **Database:** PostgreSQL 16 (no pgvector — removed, no use case)
- **Cache:** Redis 7
- **Real-time collaboration:** Yjs (multi-user document sync)
- **Video collaboration:** LiveKit
- **AI integration:** Claude via Console API key with SSE streaming (OAuth PKCE removed — banned by Anthropic Jan 2026)
- **Semantic memory:** Recall integration (on GPU VM at `http://gpu-vm:8200`)
- **8 project-aware AI tools**
- **Deployment:** Docker Compose (already containerized)

---

## What Needs to Be Added

| Feature | Priority | Description |
|---------|----------|-------------|
| dockview shell | P0 | Replace sidebar with dockview-react v5.2.0 tiling panel manager |
| Built-in terminal | P0 | xterm.js v6 + WebSocket to ptyHost Node.js service |
| System file browser | P0 | @headless-tree/react + @tanstack/react-virtual v3 |
| OS-style login screen | P0 | Full-screen login wrapping existing JWT auth |
| Multi-tenant schema + RLS | P0 | New PostgreSQL schema with codevv_app non-superuser role |
| Claude API key auth | P0 | Per-user encrypted key (pgcrypto) replacing OAuth PKCE |
| App dock | P1 | React component to launch tools as dockview panels |
| System settings panel | P1 | JSONForms auto-rendered from Pydantic settings schema |
| Notification system | P1 | PostgreSQL-backed, SSE-delivered notification center |
| tldraw native sync | P1 | @tldraw/sync-core + tldraw-sync Docker service |
| BrickLayer sidecar | P1 | bl/server.py FastAPI wrapper at http://bricklayer:8300 |
| Personal AI assistant | P2 | Per-user persistent Recall-scoped assistant |
| Knowledge graph | P2 | AI-maintained via Claude + Recall Neo4j |
| Sandbox | P2 | Three modes: scratchpad, environment clone, artifact execution |
| Boot-to-CodeVV ISO | P2 | Alpine Linux + Docker Compose + Chromium kiosk (Phase 5) |
| Notification system | P2 | System-level notifications (build status, collab, AI) |

---

## Architecture

```
Boot → Alpine Linux (minimal, ~50MB)
  → Docker Compose (auto-start on boot)
    → PostgreSQL 16 (multi-tenant, RLS)
    → Redis 7
    → Yjs server (real-time collab)
    → tldraw-sync (canvas sync)
    → FastAPI backend (+ Recall + Claude AI)
    → ptyHost (terminal WebSocket bridge)
    → sandbox-manager (Docker sandbox orchestration)
    → BrickLayer sidecar (research engine)
    → Nginx (reverse proxy + SSL) ← sole LAN-exposed port
  → Cage/Sway (Wayland kiosk compositor)
    → Chromium --kiosk → https://localhost
      → CodeVV React frontend IS the desktop
```

### Multi-User on Proxmox

```
Proxmox (Threadripper PRO 9975WX)
├── CodeVV-OS VM (runs all Docker services)
│   ├── PostgreSQL 16 (multi-tenant, RLS)
│   ├── Redis 7 (sessions, ARQ queue)
│   ├── Yjs + tldraw-sync (real-time sync)
│   ├── FastAPI backend (Claude AI via API key)
│   └── Nginx (:443 only)
├── GPU VM (Recall :8200 + Ollama :11434 + 2x RTX 3090)
│   └── CodeVV backend calls Recall API → Recall calls Ollama
└── Users open browser → https://codevv.local
    → Login → Full collaborative IDE
    → Multiple users, same project, real-time
```

No per-user VMs needed. CodeVV already supports multi-user via Yjs. Everyone hits one deployment.

---

## Target Hardware

| Component | Model |
|-----------|-------|
| CPU | AMD TR PRO 9975WX 32C/64T |
| Motherboard | ASUS WRX90E-SAGE SE |
| RAM | 256GB DDR5-6400 ECC RDIMM |
| GPU | 2x RTX 3090 24GB (48GB total) |
| Storage | 4TB mirror (boot) + 4TB mirror (AI) + 8TB (data) |
| Hypervisor | Proxmox VE |

---

## Phases

### Phase 0: Pre-Build Gate (before any code)
- Resolve all security and architecture decisions
- Update Tier 1 docs to match ROADMAP decisions
- Confirm Recall API auth status
- Author baseline docker-compose.yml

### Phase 1: Infrastructure (1 week)
- Docker hardening (security, secrets, healthchecks)
- ptyHost terminal service
- Nginx configuration
- Backend API extensions
- Full multi-tenant PostgreSQL schema with RLS
- Claude API key auth (replace OAuth PKCE)

### Phase 2: OS Shell (1 week)
- dockview tiling shell
- OS-style dock
- OS-style login screen

### Phase 3: Core Features (1-2 weeks)
- File browser, terminal upgrade, settings panel
- Notification center
- Inline AI editing (Cmd+K)
- Live preview panel

### Phase 3.5: Product Features (2-3 weeks)
- Workspace templates, theming
- Collaborative canvas (tldraw + projector mode)
- BrickLayer sidecar integration
- Personal AI assistant + custom agents
- Knowledge graph
- File viewers (Univer spreadsheet, docx, PDF)
- Artifact panel + sandbox
- GitHub integration + branch auto-environments

### Phase 4: Integration & Polish
- Full E2E validation, audit campaign
- Performance optimization

### Phase 5: Boot-to-Browser ISO
- Alpine Linux ISO build (systemd-boot, not GRUB)
- Cage/Wayland kiosk setup
- CI ISO build pipeline

### Phase 6: Production Deployment
- Proxmox deployment
- ZFS storage pools
- Monitoring (Grafana/Prometheus)

### Phase 7: Polish & Distribution
- Custom branding, auto-update, installer docs

---

## Source Repository

- **CodeVV:** https://github.com/Nerfherder16/Codevv
- **CodeVV OS:** This project (build system, ISO generation, OS configs)

---

## Non-Goals

- Not a general-purpose Linux distribution
- Not a kernel fork
- Not replacing Proxmox — runs as a VM or bare-metal appliance
- Not supporting arbitrary desktop applications (CodeVV IS the app)
- Not using pgvector (no vector use case — Recall handles embeddings via Qdrant)
- Not using OAuth PKCE for Claude (banned by Anthropic Jan 2026)
