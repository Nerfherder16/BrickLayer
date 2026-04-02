# CodeVV OS — Architecture

**Authority: Tier 1 — Human Only**
Last updated: 2026-04-02

---

## System Layers

```
┌─────────────────────────────────────────────────┐
│  User Browser (any device on network)           │
│  → https://codevv.local                         │
├─────────────────────────────────────────────────┤
│  Nginx (reverse proxy, SSL termination)         │
│  :443 only — sole externally-exposed port       │
├──────────┬──────────┬──────────┬────────────────┤
│ React 19 │ FastAPI  │ Yjs      │ LiveKit        │
│ Frontend │ Backend  │ Server   │ (video collab) │
│ (Vite)   │ (Python) │ (Node)   │                │
├──────────┴──────────┴──────────┴────────────────┤
│  PostgreSQL 16  │  Redis 7  │  (no pgvector)   │
├─────────────────┴───────────┴───────────────────┤
│  Docker Compose (service orchestration)         │
├─────────────────────────────────────────────────┤
│  Alpine Linux (minimal base OS)                 │
├─────────────────────────────────────────────────┤
│  Proxmox VM  (or bare metal)                    │
└─────────────────────────────────────────────────┘
```

**Note:** pgvector has been removed — no vector use case in CodeVV. Recall uses Qdrant (on GPU VM).

## Kiosk Boot Chain (local console only)

```
BIOS/UEFI → [Phase 1 PoC: GRUB] → Alpine Linux kernel
  → OpenRC init
    → docker compose up -d (all services)
    → service healthchecks (depends_on: service_healthy)
    → cage -- chromium --kiosk https://localhost
```

**Boot note:** GRUB is used for Phase 1 proof-of-concept. Phase 5 target is `systemd-boot` (UEFI direct, no GRUB, faster boot). Do not build Phase 5 ISO pipeline assuming GRUB.

The kiosk boot chain is only for the local console (e.g., a monitor plugged into the server). Remote users simply open a browser to the server's IP/hostname.

## Network Architecture

```
┌──────────────────────────────┐
│  Office LAN / Tailscale VPN  │
│                              │
│  ┌─────────┐  ┌─────────┐   │
│  │ Laptop  │  │ Tablet  │   │     ┌──────────────────────────┐
│  │ Browser │  │ Browser │   │────▶│  CodeVV-OS VM            │
│  └─────────┘  └─────────┘   │     │  :443 (Nginx) ← LAN only │
│                              │     │                          │
│  ┌─────────┐  ┌─────────┐   │     │  All other ports are     │
│  │ Phone   │  │ Desktop │   │     │  Docker-internal only    │
│  │ Browser │  │ Browser │   │────▶│  (expose:, not ports:)   │
│  └─────────┘  └─────────┘   │     └────────┬─────────────────┘
│                              │              │ Recall API call
└──────────────────────────────┘              │ (not Ollama directly)
                                    ┌────────▼─────────────────┐
                                    │  GPU VM                  │
                                    │  Recall :8200            │
                                    │  Ollama :11434 (internal)│
                                    │  2x RTX 3090 (48GB)      │
                                    └──────────────────────────┘
```

**Port isolation rule:** Only Nginx `:443` is published to the LAN (`ports:`). Postgres `:5432`, Redis `:6379`, Yjs `:1234`, FastAPI `:8000`, and all other internal services use Docker `expose:` only — reachable within the Docker network, not from the host or LAN.

**Recall:** Fresh Recall instance deployed from scratch on the GPU VM as part of this build (not the existing personal Recall). CodeVV backend calls it at `http://gpu-vm:8200`. API key auth configured at deployment time — `RECALL_API_KEY` stored as Docker secret in CodeVV's compose stack.

## Storage Layout (Proxmox Host)

```
Boot ZFS Mirror (2x Samsung 990 PRO 4TB)
├── rpool/ROOT           → Proxmox OS
├── rpool/data           → VM disks (CodeVV-OS, GPU VM)
└── rpool/iso            → ISO images, VM templates

AI ZFS Mirror (2x Samsung 990 PRO 4TB)
├── aipool/models        → LLM weights (mounted into GPU VM)
└── aipool/datasets      → Embeddings, training data

Data Pool (WD Black SN850X 8TB)
├── datapool/users       → User home directories
├── datapool/projects    → CodeVV project files
├── datapool/backups     → Proxmox Backup Server
└── datapool/shared      → Team shared storage
```

## Docker Compose Services

All internal services use `expose:` (Docker-internal only). Only Nginx uses `ports:` (LAN-accessible).

| Service | Image | Expose | Purpose |
|---------|-------|--------|---------|
| `nginx` | nginx:alpine | `ports: 443:443` | Reverse proxy, SSL — **sole LAN port** |
| `frontend` | Custom (Vite build) | `expose: 3000` | React 19 UI (served via Nginx) |
| `backend` | Custom (FastAPI) | `expose: 8000` | API, AI tools, Recall integration |
| `postgres` | postgres:16 | `expose: 5432` | Primary database |
| `redis` | redis:7-alpine | `expose: 6379` | Session cache, pub/sub, ARQ queue |
| `yjs` | Custom (Node.js) | `expose: 1234` | Real-time document sync (Yjs) |
| `tldraw-sync` | Custom (Node.js) | `expose: 1235` | tldraw v2 native sync |
| `livekit` | livekit/livekit-server | `expose: 7880`, `ports: 50000-60000/udp` | Video/audio SFU |
| `livekit-agents` | Custom (Python 3.12-slim) | `expose: 8081` | LiveKit AI agent runner |
| `ptyhost` | Custom (Node.js) | `expose: 3001` | Terminal PTY WebSocket bridge |
| `sandbox-manager` | Custom | `expose: 3002` | Docker sandbox orchestration (owns docker.sock via socket-proxy) |
| `worker` | Custom (same as backend) | — | ARQ background job worker |
| `bricklayer` | Custom (Python) | `expose: 8300` | BrickLayer research engine sidecar |
| `masonry-mcp` | Custom (Node.js) | `expose: 3003` | Masonry MCP server |

**LiveKit UDP note:** UDP `50000-60000` must be published (`ports:`) for WebRTC media. Without this, media falls back to TURN relay and video quality degrades significantly.

**livekit-agents base image:** Must use `python:3.12-slim-bookworm` (glibc-based). Do NOT use Alpine — `opuslib` and audio codec dependencies fail to compile against musl libc.

**sandbox-manager docker.sock:** Accessed only via `tecnativa/docker-socket-proxy` scoped to `exec` operations. No other service mounts docker.sock.

## Authentication Flow

```
User opens browser → https://codevv.local
  → Nginx serves React app
  → Login screen (OS-style full-screen)
  → FastAPI /auth/login → JWT issued
  → WebSocket established (Yjs sync, ptyHost, tldraw-sync)
  → User enters collaborative workspace
```

**Claude AI authentication:** Per-user API keys stored encrypted via `pgcrypto` (`pgp_sym_encrypt`) with key from Docker secret. No OAuth PKCE — Anthropic banned third-party OAuth PKCE for non-Console apps in Jan 2026.

**JWT shared library:** Single `auth.py` (backend) and `auth.js` (Node services) used by all services. No service implements its own JWT parse logic.

## GPU Access Pattern

CodeVV-OS VM does NOT have direct GPU access. Instead:

1. User triggers AI action in CodeVV UI
2. FastAPI backend calls **Recall API** (`http://gpu-vm:8200`)
3. Recall routes to Ollama (`http://localhost:11434`) on the GPU VM
4. GPU VM processes with RTX 3090s
5. Response streamed back via SSE to frontend

**CodeVV backend does NOT call Ollama directly.** All LLM inference goes through Recall's API. This keeps Ollama an implementation detail of the GPU VM, not a direct CodeVV dependency.

## Resource Allocation (Proxmox)

| VM | vCPU | RAM | Storage | GPU |
|----|------|-----|---------|-----|
| CodeVV-OS | 16 threads | 64GB | 100GB (boot) + NFS mounts | None |
| GPU / Ollama + Recall | 8 threads | 32GB | 50GB + AI pool mount | 2x RTX 3090 |
| Remaining | 8 threads | 160GB | — | For future VMs/LXCs |
