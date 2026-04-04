# CodeVV OS — Project Brief

**Authority: Tier 1 — Human Only**
Last updated: 2026-04-01

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
- **Database:** PostgreSQL + pgvector
- **Cache:** Redis
- **Real-time collaboration:** Yjs (multi-user document sync)
- **Video collaboration:** LiveKit
- **AI integration:** Claude via OAuth PKCE with SSE streaming
- **Semantic memory:** Recall integration
- **8 project-aware AI tools**
- **Deployment:** Docker Compose (already containerized)

---

## What Needs to Be Added

| Feature | Priority | Description |
|---------|----------|-------------|
| Built-in terminal | P0 | xterm.js component with WebSocket to backend shell |
| System file browser | P0 | Extend existing file browser to show system files |
| Login screen | P0 | Leverage existing auth — add OS-style login UI |
| App launcher / dock | P1 | React component to launch tools as panels/tabs |
| System settings panel | P1 | User management, network, display settings |
| Boot-to-CodeVV ISO | P1 | Alpine Linux + Docker Compose + Chromium kiosk |
| Notification system | P2 | System-level notifications (build status, collab, AI) |
| Peripheral management | P2 | Printer, display, audio routing |

---

## Architecture

```
Boot → Alpine Linux (minimal, ~50MB)
  → Docker Compose (auto-start on boot)
    → PostgreSQL + pgvector
    → Redis
    → Yjs server (real-time collab)
    → FastAPI backend (+ Recall + Claude AI)
    → Nginx (reverse proxy + SSL)
  → Cage/Sway (Wayland kiosk compositor)
    → Chromium --kiosk → https://localhost
      → CodeVV React frontend IS the desktop
```

### Multi-User on Proxmox

```
Proxmox (Threadripper PRO 9975WX)
├── CodeVV-OS VM (runs all Docker services)
│   ├── PostgreSQL (shared state)
│   ├── Redis (sessions)
│   ├── Yjs (real-time sync)
│   ├── FastAPI + Recall + Ollama API
│   └── Nginx
├── GPU VM (Ollama + 2x RTX 3090, 48GB VRAM)
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

### Phase 1: Proof of Concept (1-2 weeks)
- Boot Alpine Linux → Docker Compose → CodeVV
- Chromium kiosk mode as sole UI
- Validate multi-user access from external browsers
- Package as bootable ISO

### Phase 2: OS Features (2-3 weeks)
- xterm.js integrated terminal
- System file browser
- App launcher / dock UI
- OS-style login screen
- System settings panel

### Phase 3: Production Deployment (1 week)
- Deploy on Proxmox Threadripper server
- GPU passthrough for Ollama LLM inference
- ZFS storage pools configured
- Apache Guacamole for remote access fallback
- Monitoring (Grafana/Prometheus)

### Phase 4: Polish & Distribution
- Custom branding / boot splash
- Auto-update mechanism
- Installer for bare-metal deployment
- Documentation

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
