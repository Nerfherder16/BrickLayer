# Research Questions — CodeVV OS

Status values: PENDING | IN_PROGRESS | DONE | INCONCLUSIVE

---

## Domain 1 — Boot & ISO Engineering

| ID | Status | Question | Finding |
|----|--------|---------|---------|
| 1.1 | DONE | What is the minimum Alpine Linux configuration needed to boot into Docker Compose + Chromium kiosk? Target image size? | ~235MB with Chromium kiosk stack. Alpine is one of only two distros (with NixOS) that support Docker Compose + kiosk. |
| 1.2 | DONE | What is the correct Cage/Sway compositor configuration for a single-app kiosk that auto-restarts on crash? | Cage is the clear winner — purpose-built single-app Wayland kiosk compositor. Wrap in systemd service with `Restart=always`. Sway is overkill. VT switching blocked by default (don't pass `-s` flag). |
| 1.3 | DONE | How should `wait-for-healthy.sh` poll Docker service health before launching the kiosk browser? Timeout strategy? | Replace with native Docker HEALTHCHECK + `depends_on: condition: service_healthy`. wait-for-it/dockerize are obsolete. Cage service should `After=docker.service` with a startup script that waits for HTTP 200. |
| 1.4 | DONE | What is the optimal ISO build pipeline (Alpine `mkimage` vs custom)? Can it be fully automated in CI? | Alpine mkimage is most maintainable for small team. Containerize build in Dockerfile (alpine-sdk + squashfs-tools + xorriso). Packer can't produce ISOs. Buildroot lacks Docker support. |
| 1.5 | DONE | What boot time is achievable from GRUB to usable CodeVV UI? Where are the bottlenecks? | 8-15 seconds on modern x86 with SSD. Biggest bottleneck: Docker image loading. Use systemd-boot (skip GRUB), pre-load Docker images on persistent partition, lz4 initramfs compression. |

---

## Domain 2 — Multi-User & Networking

| ID | Status | Question | Finding |
|----|--------|---------|---------|
| 2.1 | DONE | How many concurrent Yjs users can a single CodeVV deployment handle before performance degrades? | Hundreds of concurrent WebSocket connections per y-websocket instance. 5-20 users is well within safe territory. Bottleneck is memory (document state), not connections. |
| 2.2 | DONE | What is the correct Nginx configuration for WebSocket proxying (Yjs + LiveKit) with SSL termination? | Per-service location blocks with `proxy_http_version 1.1`, `Upgrade` headers, `proxy_read_timeout 3600s`. `proxy_buffering off` for WS/SSE. Nginx does NOT support WebSocket over HTTP/2. mkcert for LAN SSL. |
| 2.3 | DONE | How should user sessions be isolated? Per-user PostgreSQL schemas, shared tables, or namespace separation? | Row-Level Security (RLS) on shared tables. DB-enforced isolation, simpler than schema-per-user. Requires non-superuser application role (superusers bypass RLS). |
| 2.4 | DONE | What happens when multiple users edit the same file simultaneously? Conflict resolution strategy? | Yjs YATA algorithm resolves deterministically via client IDs. Character interleaving is a known edge case (Fugue paper, 2023) but rare in practice — presence cursors prevent most conflicts. Hybrid approach: code-server for individual work + shared CodeMirror 6 for pair sessions. |
| 2.5 | DONE | What is the network latency impact of routing all AI inference through a separate GPU VM vs local? | AI inference is a separate request/response flow via FastAPI SSE, not through Yjs. No impact on collaboration. Both Ollama and vLLM expose OpenAI-compatible SSE streaming — same format CodeVV uses for Claude. |

---

## Domain 3 — Proxmox & Hardware Integration

| ID | Status | Question | Finding |
|----|--------|---------|---------|
| 3.1 | DONE | What is the correct IOMMU group configuration for GPU passthrough on the WRX90E-SAGE SE? | Expect clean IOMMU groups per CPU-direct PCIe slot, but no published dump exists for this board. Must verify with enumeration script on actual hardware. Do NOT use `pcie_acs_override`. Disable ReBAR in BIOS. RTX 3090 has Ampere reset bug — may need VBIOS ROM dump. |
| 3.2 | DONE | How should ZFS pools be configured for optimal performance across boot, AI, and data workloads? | ashift=12 (10-22% faster on 990 PRO), lz4 compression, limit ARC to 16GB (default claims 50% of RAM). AI pool: recordsize=1M, primarycache=metadata. No SLOG/L2ARC needed for all-NVMe. WARNING: Samsung 990 PRO 4TB has documented reliability issues. |
| 3.3 | DONE | What Proxmox resource limits prevent the CodeVV-OS VM from starving the GPU VM (or vice versa)? | Host reserves ~24GB (2GB OS + 16GB ARC + 4GB KVM overhead). CodeVV-OS: 16 threads, 64GB. GPU VM: 8 threads, 48GB (bumped from 32GB for 70B models). Disable memory ballooning on passthrough VMs. ~120GB headroom remains. |
| 3.4 | DONE | How should Proxmox backups be configured for CodeVV user data and project files? | PBS for VM snapshots (incremental, deduplicated, encrypted). pgBackRest for PostgreSQL PITR. Sanoid for automated ZFS snapshots with pre-snapshot PostgreSQL CHECKPOINT hook. ZFS rollback RTO < 30 seconds. |
| 3.5 | DONE | What is the thermal profile of 2x RTX 3090 + TR PRO 9975WX in a 12U rack enclosure? Cooling adequacy? | Total ~1100-1180W. 360mm AIO works for CPU but MUST have full-coverage sTR5 rectangular cold plate (SilverStone XE360-TR5 or Enermax LIQTECH XTR). Water-cool GPUs — 700W open-air heat in 12U is the biggest thermal challenge. Blower RTX 3090s are scarce. Buy NVLink bridge ($30-50). |

---

## Domain 4 — OS Features (Phase 2)

| ID | Status | Question | Finding |
|----|--------|---------|---------|
| 4.1 | DONE | What is the security model for xterm.js terminal access? Per-user sandboxing, or shared shell with RBAC? | Node.js + node-pty ptyHost service (production standard: VS Code, Theia, Gitpod). Per-user container sandboxing via Docker exec. ReconnectingPTY pattern with replay buffer for session persistence. WebSocket auth via JWT in first message. |
| 4.2 | DONE | How should the system file browser handle permissions when multiple users access the same filesystem? | Docker volume per user for workspace isolation. `os.path.realpath()` + workspace root prefix check for path traversal prevention. Symlink target validation. `@headless-tree/react` for tree component. `watchfiles` (Rust-backed) for file watching, SSE for change notifications. |
| 4.3 | DONE | What app launcher model works best for a single-page React app? Tabs, panels, or virtual desktops? | dockview-react — tiling-first with floating escape hatch. Dock/taskbar lives outside dockview layout tree. Panels inherit React context (portals, not separate roots). `renderer: 'always'` for terminals, `onlyWhenVisible` for everything else. Singleton pattern for Settings, multi-instance for Terminal. |
| 4.4 | DONE | How should OS-level settings (network, display, users) be exposed without giving users root access? | `@jsonforms/react` auto-rendered from Pydantic-generated JSON Schema. Network info via `/proc/net/`, system metrics via `psutil`, display via browser `window.screen` API. FastAPI RBAC via `Depends(require_role("admin"))`. |
| 4.5 | DONE | What notification transport works for system events (build status, collab invites, AI completion)? | SSE (separate from Yjs WebSocket) — auto-reconnect, one-way, simpler than WebSocket. Sonner for toast UI (zero deps). PostgreSQL-backed notification persistence with read/unread tracking. Do NOT multiplex on Yjs WebSocket. |

---

## Domain 5 — Security & Operations

| ID | Status | Question | Finding |
|----|--------|---------|---------|
| 5.1 | DONE | What is the attack surface of a kiosk browser pointed at localhost? How to harden? | Chromium kiosk needs: `--disable-dev-tools`, `--url-blocklist='file://*,chrome://*'`, `--url-allowlist='https://localhost/*'`, `--incognito`. Cage blocks VT switching by default. Disable getty on other TTYs, remove SSH, disable USB storage via udev. |
| 5.2 | DONE | How should auto-updates work for a Docker Compose-based OS? Rolling updates vs full ISO replacement? | Container-based updates: OS stays immutable, `docker compose pull && docker compose up -d`. OS-level updates via full ISO replacement (rare). Rollback via pinned Docker image tags. This is the Torizon OS production pattern. |
| 5.3 | DONE | What monitoring metrics matter most? Resource usage, user sessions, AI inference latency? | GPU metrics via `dcgm-exporter` from inside GPU VM. PostgreSQL metrics via pg_stat. Docker stats for container resource usage. Expose metrics endpoint for Grafana/Prometheus. |
| 5.4 | DONE | How should secrets (JWT keys, API tokens, SSL certs) be managed in a bootable ISO context? | Docker Compose file-based secrets (mounted at `/run/secrets/`). Pydantic `SecretsSettingsSource` reads from `/run/secrets/` natively with env var fallback. PostgreSQL supports `_FILE` suffix. Redis needs custom entrypoint. mkcert for LAN SSL certs. |
| 5.5 | DONE | What is the disaster recovery plan? Time-to-restore from backup to working system? | ZFS snapshot rollback: < 30 seconds. PBS VM restore: 5-30 minutes. pgBackRest: 10-30 minutes. Sanoid for automated ZFS snapshots with pre-snapshot CHECKPOINT hook. Syncoid for offsite replication. |

---

## Domain 6 — AI Inference (NEW — from research)

| ID | Status | Question | Finding |
|----|--------|---------|---------|
| 6.1 | DONE | What inference server should serve 5-20 concurrent users? | Hybrid: Ollama for FIM autocomplete (low concurrency) + vLLM for chat (continuous batching, 3-19x more throughput). Both expose OpenAI-compatible APIs. |
| 6.2 | DONE | What models fit in 48GB VRAM and are best for coding? | Qwen 2.5 Coder 32B Q4 (~20GB) for autocomplete. Qwen 3.5 27B Q4 (~16GB) for chat. Or Qwen3-Coder-Next 80B Q4 (~35-40GB) across both GPUs. Qwen dominates local coding models 2025-2026. CodeLlama is superseded. |
| 6.3 | DONE | Does RTX 3090 support NVLink for multi-GPU inference? | Yes — last consumer GPU with NVLink. Bridge costs $30-50. 50% inference improvement with vLLM tensor parallelism. Verify slot spacing on WRX90E-SAGE SE supports NVLink bridge. |

---

## Domain 7 — Frontend Architecture (NEW — from research)

| ID | Status | Question | Finding |
|----|--------|---------|---------|
| 7.1 | DONE | How to migrate from React Router page navigation to dockview panels? | Keep React Router for full-screen pages (login, onboarding) and deep links. `/app/*` route renders DockviewShell. Migrate pages to panels incrementally. Panel state in `toJSON()`/`fromJSON()`, NOT in URLs. |
| 7.2 | DONE | Do dockview panels inherit React context providers? | Yes — dockview uses React portals, not separate roots. All 5 CodeVV contexts work as-is. Disable popout windows (context breaks in separate browser windows). |
| 7.3 | DONE | What collaborative code editor approach works with existing Yjs? | Hybrid: code-server for individual work + shared CodeMirror 6 (`y-codemirror.next`) for pair sessions. y-monaco binding is ~200 lines. Do NOT try to make code-server itself collaborative. |

---

## Domain 8 — Claude AI Integration (NEW — from research)

| ID | Status | Question | Finding |
|----|--------|---------|---------|
| 8.1 | DONE | Can CodeVV use Claude subscription OAuth tokens (Pro/Max/Teams) for its AI features? | **NO.** Anthropic bans third-party apps from using subscription OAuth tokens. Server-side enforced since Jan 2026. CodeVV's current OAuth PKCE flow must be removed. |
| 8.2 | DONE | What authentication method should CodeVV use for Claude AI? | Anthropic Console API keys (`sk-ant-api03-*`). Either org-level shared key (`ANTHROPIC_API_KEY` env var — already works) or per-user keys stored encrypted in PostgreSQL. |
| 8.3 | DONE | Should CodeVV use the Claude Agent SDK instead of raw Anthropic SDK? | Strong candidate. Agent SDK (`claude-agent-sdk`) gives Claude Code's full tool suite (Read, Write, Edit, Bash, Grep, Glob) built-in, plus session management, subagents, and MCP support. Native Python async, streaming via async iterators. Auth via API key (compliant). |
| 8.4 | DONE | How do Claude Code Teams accounts relate to API access? | Teams is a subscription plan (claude.ai) — separate from Console/API billing. Teams Premium ($100/seat/mo) includes Claude Code CLI access but the OAuth tokens are restricted to Claude Code only. For third-party apps, use Console API keys with per-token billing. |
| 8.5 | DONE | What changes in CodeVV's SSE streaming when switching from OAuth to API key? | Nothing. The `anthropic` Python SDK streaming works identically with API keys. Just change `AsyncAnthropic(auth_token=...)` to `AsyncAnthropic(api_key=...)`. |
