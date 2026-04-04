# CodeVV OS — Roadmap

Tracks planned work across project phases. Derived from `project-brief.md` and validated by research (2026-04-01).

---

## Phase 1: Infrastructure & Backend (no frontend dependency)

### 1a. Docker Compose Hardening
- [ ] Add native Docker HEALTHCHECK per service (`pg_isready`, `redis-cli ping`, `curl /health`)
- [ ] Replace `wait-for-healthy.sh` with `depends_on: condition: service_healthy`
- [ ] Add Docker network isolation: `frontend` (exposed) + `backend` (internal)
- [ ] Add log rotation on all services (`max-size: 10m`, `max-file: 3`)
- [ ] Add resource limits (memory + CPU) per service
- [ ] Add Docker secrets for passwords/keys (replace env vars)
- [ ] Remove docker.sock mount from backend container (security fix)
- [ ] Add `restart: unless-stopped` on all long-running services

### 1b. Node.js ptyHost Service (NEW)
- [ ] Dedicated Node.js + `node-pty` microservice for per-user terminal PTY
- [ ] WebSocket transport with ACK-based flow control
- [ ] ReconnectingPTY pattern: session persistence via replay buffer per session
- [ ] Per-user container sandboxing (Docker exec into user container)
- [ ] Shell cleanup on disconnect: SIGHUP -> timeout -> SIGKILL -> waitpid -> close FDs
- [ ] Heartbeat monitoring with crash recovery (VS Code ptyHost pattern)

### 1c. Nginx Reverse Proxy (NEW)
- [ ] Per-service WebSocket location blocks (Yjs, terminal, LiveKit, SSE)
- [ ] `proxy_read_timeout 3600s` + ping/pong every 30s for long-lived WebSocket
- [ ] SSL termination (self-signed for LAN; Let's Encrypt optional)
- [ ] `proxy_buffering off` for WebSocket and SSE paths
- [ ] HTTP/2 for static assets (WebSocket falls back to HTTP/1.1 automatically)

### 1d. Backend API Extensions (FastAPI)
- [ ] `GET /api/files/tree?path=` — Lazy-load directory listing with `os.path.realpath()` path traversal prevention
- [ ] `PATCH /api/files/{path}` — File operations (rename, delete, move) scoped to user workspace
- [ ] File watch via `watchfiles` (Rust-backed) pushing changes over SSE
- [ ] `GET /api/settings/schema` — JSON Schema auto-generated from Pydantic models
- [ ] `GET/PUT /api/settings/user` — Per-user settings CRUD
- [ ] `GET/PUT /api/admin/settings` — Admin-only settings with `require_role("admin")` dependency
- [ ] `GET /api/notifications` — Notification history with read/unread tracking (PostgreSQL-backed)
- [ ] `PATCH /api/notifications/{id}/read` — Mark notification read

### 1e. PostgreSQL Multi-Tenant
- [ ] Enable Row-Level Security (RLS) on shared tables
- [ ] Add `tenant_id` column + B-tree index on tenant-scoped tables
- [ ] Create non-superuser application role (superusers bypass RLS)
- [ ] Add admin role to user model

---

## Phase 2: Frontend Shell (depends on Phase 1)

### 2a. Desktop Shell — dockview
- [ ] Replace sidebar+page navigation with `dockview-react` panel manager
- [ ] Tiling-first layout with floating escape hatch for transient panels
- [ ] JSON-serializable layout state: `api.toJSON()` / `api.fromJSON()`
- [ ] Layout persistence per user in PostgreSQL
- [ ] Wrap `fromJSON()` in try/catch with default layout fallback
- [ ] Store schema version alongside layout JSON for migration

### 2b. Dock / Taskbar
- [ ] Persistent bar (outside dockview layout tree) with app launcher icons
- [ ] App registry: `{ id, label, icon, componentFactory }` per launchable app
- [ ] Click icon -> `api.addPanel()` or focus if already open
- [ ] Active panel indicator via `onDidActivePanelChange` subscription
- [ ] Built with React + Tailwind + Framer Motion

### 2c. OS-Style Login Screen
- [ ] Full-screen login UI replacing default app entry
- [ ] Connects to existing FastAPI `/auth/login` -> JWT
- [ ] Session management via Redis with TTL matching JWT expiry

---

## Phase 3: Frontend Features (depends on Phase 2)

### 3a. Code File Browser
- [ ] `@headless-tree/react` + `react-window` for virtualized tree
- [ ] Lazy-load children on directory expand (never full tree fetch)
- [ ] Connected to `GET /api/files/tree?path=` backend API
- [ ] Real-time updates via SSE file watch channel
- [ ] Inline rename, drag-and-drop, context menus, keyboard navigation
- [ ] Exclude `.git/` from file watching
- [ ] Debounce file events 100-300ms

### 3b. Terminal Upgrade
- [ ] Connect `SharedTerminal.tsx` to new ptyHost WebSocket service
- [ ] Add xterm.js addons: `@xterm/addon-webgl` (primary renderer), `@xterm/addon-fit`, `@xterm/addon-serialize`, `@xterm/addon-web-links`, `@xterm/addon-search`
- [ ] Remove deprecated canvas addon (deprecated in xterm.js v6)
- [ ] Debounce `fitAddon.fit()` 150-200ms with `ResizeObserver`
- [ ] Per-user terminal sessions with reconnection (session ID-based)
- [ ] Multiple terminal tabs within dockview panel
- [ ] WebGL context loss fallback to DOM renderer
- [ ] Always call `terminal.dispose()` on unmount

### 3c. Settings Panel
- [ ] `@jsonforms/react` auto-rendered from Pydantic-generated JSON Schema
- [ ] Layered: user settings override system defaults
- [ ] Admin-only section for user management, network info, system metrics
- [ ] Network info via `/proc/net/`, system metrics via `psutil`
- [ ] Display/resolution via browser `window.screen` API

### 3d. Notification Center Upgrade
- [ ] Swap toast implementation to Sonner (zero deps, simplest API)
- [ ] Notification center dropdown with history (PostgreSQL-backed)
- [ ] Read/unread tracking with `PATCH /api/notifications/{id}/read`
- [ ] SSE push for real-time delivery + `GET /api/notifications` for missed on page load

---

## Phase 4: Integration & Polish

- [ ] End-to-end testing across all panel types
- [ ] Admin panel: user management, system settings, resource monitoring
- [ ] Layout persistence stress testing (10+ panels, page refresh, reconnection)
- [ ] Performance profiling: memory per terminal, panel mount/unmount leaks
- [ ] Security audit: path traversal, RLS bypass, WebSocket auth, RBAC enforcement

---

## Phase 5: Boot-to-Browser ISO (DEFERRED — after Phases 1-4 validated)

### 5a. Alpine Linux Base
- [ ] Minimal Alpine Linux rootfs (~235MB with Chromium kiosk stack)
- [ ] systemd-boot (UEFI direct, skip GRUB for faster boot)
- [ ] Read-only root filesystem (overlayroot or `mount -o ro`)
- [ ] Persistent partition for `/var/lib/docker` (overlay2 incompatible with overlayroot)
- [ ] Partition layout: EFI (256MB) + rootfs (2-4GB, ro) + docker (8-20GB) + data (remaining)

### 5b. Kiosk Compositor
- [ ] Cage (single-app Wayland kiosk compositor) + Chromium `--kiosk --ozone-platform=wayland`
- [ ] systemd service with `Restart=always` for crash recovery
- [ ] Disable DPMS/screen blanking: `consoleblank=0`, `IdleAction=ignore`
- [ ] Scheduled Chromium restart every 6-12h (memory leak mitigation)

### 5c. Boot Chain
- [ ] Docker Compose auto-start on boot via systemd/OpenRC
- [ ] Native health checks gate browser launch (don't start Cage until services healthy)
- [ ] Loading splash page that auto-refreshes until app responds
- [ ] Target boot time: 8-15 seconds to browser on SSD

### 5d. ISO Build Pipeline
- [ ] Alpine `mkimage` with custom `mkimg.profile.sh`
- [ ] Docker images pre-loaded on persistent partition (not pulled on first boot)
- [ ] CI/CD: containerized build in GitHub Actions

### 5e. Update Mechanism
- [ ] Container-based updates: OS immutable, `docker compose pull && docker compose up -d`
- [ ] OS-level updates via full ISO replacement (rare)
- [ ] Rollback via pinned Docker image tags

---

## Phase 6: Production Deployment

- [ ] Deploy on Proxmox Threadripper PRO server
- [ ] GPU passthrough for Ollama LLM inference (2x RTX 3090)
- [ ] ZFS storage pools configured (boot mirror, AI mirror, data)
- [ ] Apache Guacamole for remote access fallback
- [ ] Monitoring stack (Grafana + Prometheus)

---

## Phase 7: Polish & Distribution

- [ ] Custom branding and boot splash
- [ ] Bare-metal installer
- [ ] End-user documentation

---

## Technology Decisions (Research-Validated)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Panel manager | `dockview-react` | Zero deps, React 19, tabs+dock+float+serialize, most actively maintained |
| File tree | `@headless-tree/react` | 9.5kB, virtualized, accessible, successor to react-complex-tree |
| Terminal PTY | Node.js + `node-pty` | Production standard (VS Code, Theia, Gitpod). Python pty lacks flow control |
| Terminal frontend | xterm.js v6 + WebGL addon | Production standard, GPU-accelerated rendering |
| File watching | `watchfiles` (Rust-backed) | Faster, lower memory than Python watchdog |
| Settings UI | `@jsonforms/react` | Auto-rendered from Pydantic JSON Schema |
| Toast notifications | Sonner | Zero deps, simplest API, smallest footprint |
| Notification transport | SSE (separate from Yjs WebSocket) | Auto-reconnect, one-way fits notifications, don't multiplex on Yjs |
| PostgreSQL multi-tenant | Row-Level Security (RLS) | DB-enforced isolation, simpler than schema-per-user |
| OS base | Alpine Linux | Smallest footprint (~235MB), Docker-native, proven kiosk use |
| Kiosk compositor | Cage | Purpose-built single-app Wayland compositor |
| ISO build | Alpine mkimage | Most maintainable for small team, CI-friendly |
| Update mechanism | Container-based | OS immutable, only containers change |
| Orchestration | Docker Compose | Right level for single-server 5-20 users |
| WebSocket transport | Raw WebSocket (not Socket.IO) | Lowest latency, production standard for terminals |
