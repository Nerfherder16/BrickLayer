# CodeVV OS — Roadmap

Tracks planned work across project phases. Derived from `project-brief.md`.

---

## Phase 1: Proof of Concept

- [ ] Boot Alpine Linux into Docker Compose running CodeVV
- [ ] Chromium kiosk mode as sole local UI (Cage/Sway compositor)
- [ ] Validate multi-user browser access over LAN
- [ ] `wait-for-healthy.sh` service health polling on boot
- [ ] Package as bootable ISO

## Phase 2: OS Features

- [ ] xterm.js integrated terminal (WebSocket to backend shell)
- [ ] System file browser (extend existing CodeVV file browser)
- [ ] App launcher / dock UI (React component)
- [ ] OS-style login screen (leveraging existing FastAPI auth + JWT)
- [ ] System settings panel (user mgmt, network, display)

## Phase 3: Production Deployment

- [ ] Deploy on Proxmox Threadripper PRO server
- [ ] GPU passthrough for Ollama LLM inference (2x RTX 3090)
- [ ] ZFS storage pools configured (boot mirror, AI mirror, data)
- [ ] Apache Guacamole for remote access fallback
- [ ] Monitoring stack (Grafana + Prometheus)

## Phase 4: Polish & Distribution

- [ ] Custom branding and boot splash
- [ ] Auto-update mechanism
- [ ] Bare-metal installer
- [ ] End-user documentation
