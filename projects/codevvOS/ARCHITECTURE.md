# CodeVV OS — Architecture

**Authority: Tier 1 — Human Only**
Last updated: 2026-04-01

---

## System Layers

```
┌─────────────────────────────────────────────────┐
│  User Browser (any device on network)           │
│  → https://codevv.local                         │
├─────────────────────────────────────────────────┤
│  Nginx (reverse proxy, SSL termination)         │
├──────────┬──────────┬──────────┬────────────────┤
│ React 19 │ FastAPI  │ Yjs      │ LiveKit        │
│ Frontend │ Backend  │ Server   │ (video collab) │
│ (Vite)   │ (Python) │ (Node)   │                │
├──────────┴──────────┴──────────┴────────────────┤
│  PostgreSQL + pgvector  │  Redis  │  Ollama API │
├─────────────────────────┴─────────┴─────────────┤
│  Docker Compose (service orchestration)         │
├─────────────────────────────────────────────────┤
│  Alpine Linux (minimal base OS)                 │
├─────────────────────────────────────────────────┤
│  Proxmox VM  (or bare metal)                    │
└─────────────────────────────────────────────────┘
```

## Kiosk Boot Chain (local console only)

```
BIOS/UEFI → GRUB → Alpine Linux kernel
  → OpenRC init
    → docker-compose up -d (all services)
    → wait-for-healthy.sh (poll service health)
    → cage -- chromium --kiosk https://localhost
```

The kiosk boot chain is only for the local console (e.g., a monitor plugged into the server). Remote users simply open a browser to the server's IP/hostname.

## Network Architecture

```
┌──────────────────────────────┐
│  Office LAN / VPN            │
│                              │
│  ┌─────────┐  ┌─────────┐   │
│  │ Laptop  │  │ Tablet  │   │     ┌─────────────────────┐
│  │ Browser │  │ Browser │   │────▶│  CodeVV-OS VM       │
│  └─────────┘  └─────────┘   │     │  :443 (Nginx)       │
│                              │     │  :5432 (Postgres)   │
│  ┌─────────┐  ┌─────────┐   │     │  :6379 (Redis)      │
│  │ Phone   │  │ Desktop │   │     │  :1234 (Yjs)        │
│  │ Browser │  │ Browser │   │────▶│  :8000 (FastAPI)    │
│  └─────────┘  └─────────┘   │     └────────┬────────────┘
│                              │              │
└──────────────────────────────┘              │ API call
                                    ┌────────▼────────────┐
                                    │  GPU VM             │
                                    │  Ollama :11434      │
                                    │  2x RTX 3090 (48GB) │
                                    └─────────────────────┘
```

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

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `frontend` | Custom (Vite build) | 3000 | React 19 UI |
| `backend` | Custom (FastAPI) | 8000 | API, AI tools, Recall |
| `postgres` | postgres:16 + pgvector | 5432 | Primary database |
| `redis` | redis:7-alpine | 6379 | Session cache, pub/sub |
| `yjs` | Custom (Node) | 1234 | Real-time document sync |
| `livekit` | livekit/livekit-server | 7880 | Video collaboration |
| `nginx` | nginx:alpine | 443 | Reverse proxy, SSL |

## Authentication Flow

```
User opens browser → https://codevv.local
  → Nginx serves React app
  → Login screen (OS-style)
  → FastAPI /auth/login → JWT issued
  → WebSocket established (Yjs sync)
  → User enters collaborative workspace
```

## GPU Access Pattern

CodeVV-OS VM does NOT have direct GPU access. Instead:

1. User triggers AI action in CodeVV UI
2. FastAPI backend calls Ollama API (`http://gpu-vm:11434`)
3. GPU VM processes with RTX 3090s
4. Response streamed back via SSE to frontend

This keeps GPU resources shared across all users without passthrough complexity in the CodeVV VM.

## Resource Allocation (Proxmox)

| VM | vCPU | RAM | Storage | GPU |
|----|------|-----|---------|-----|
| CodeVV-OS | 16 threads | 64GB | 100GB (boot) + NFS mounts | None |
| GPU / Ollama | 8 threads | 32GB | 50GB + AI pool mount | 2x RTX 3090 |
| Remaining | 8 threads | 160GB | — | For future VMs/LXCs |
