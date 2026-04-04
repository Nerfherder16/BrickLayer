# Research Questions — CodeVV OS

Status values: PENDING | IN_PROGRESS | DONE | INCONCLUSIVE

---

## Domain 1 — Boot & ISO Engineering

| ID | Status | Question |
|----|--------|---------|
| 1.1 | PENDING | What is the minimum Alpine Linux configuration needed to boot into Docker Compose + Chromium kiosk? Target image size? |
| 1.2 | PENDING | What is the correct Cage/Sway compositor configuration for a single-app kiosk that auto-restarts on crash? |
| 1.3 | PENDING | How should `wait-for-healthy.sh` poll Docker service health before launching the kiosk browser? Timeout strategy? |
| 1.4 | PENDING | What is the optimal ISO build pipeline (Alpine `mkimage` vs custom)? Can it be fully automated in CI? |
| 1.5 | PENDING | What boot time is achievable from GRUB to usable CodeVV UI? Where are the bottlenecks? |

---

## Domain 2 — Multi-User & Networking

| ID | Status | Question |
|----|--------|---------|
| 2.1 | PENDING | How many concurrent Yjs users can a single CodeVV deployment handle before performance degrades? |
| 2.2 | PENDING | What is the correct Nginx configuration for WebSocket proxying (Yjs + LiveKit) with SSL termination? |
| 2.3 | PENDING | How should user sessions be isolated? Per-user PostgreSQL schemas, shared tables, or namespace separation? |
| 2.4 | PENDING | What happens when multiple users edit the same file simultaneously? Conflict resolution strategy? |
| 2.5 | PENDING | What is the network latency impact of routing all AI inference through a separate GPU VM vs local? |

---

## Domain 3 — Proxmox & Hardware Integration

| ID | Status | Question |
|----|--------|---------|
| 3.1 | PENDING | What is the correct IOMMU group configuration for GPU passthrough on the WRX90E-SAGE SE? |
| 3.2 | PENDING | How should ZFS pools be configured for optimal performance across boot, AI, and data workloads? |
| 3.3 | PENDING | What Proxmox resource limits prevent the CodeVV-OS VM from starving the GPU VM (or vice versa)? |
| 3.4 | PENDING | How should Proxmox backups be configured for CodeVV user data and project files? |
| 3.5 | PENDING | What is the thermal profile of 2x RTX 3090 + TR PRO 9975WX in a 12U rack enclosure? Cooling adequacy? |

---

## Domain 4 — OS Features (Phase 2)

| ID | Status | Question |
|----|--------|---------|
| 4.1 | PENDING | What is the security model for xterm.js terminal access? Per-user sandboxing, or shared shell with RBAC? |
| 4.2 | PENDING | How should the system file browser handle permissions when multiple users access the same filesystem? |
| 4.3 | PENDING | What app launcher model works best for a single-page React app? Tabs, panels, or virtual desktops? |
| 4.4 | PENDING | How should OS-level settings (network, display, users) be exposed without giving users root access? |
| 4.5 | PENDING | What notification transport works for system events (build status, collab invites, AI completion)? |

---

## Domain 5 — Security & Operations

| ID | Status | Question |
|----|--------|---------|
| 5.1 | PENDING | What is the attack surface of a kiosk browser pointed at localhost? How to harden? |
| 5.2 | PENDING | How should auto-updates work for a Docker Compose-based OS? Rolling updates vs full ISO replacement? |
| 5.3 | PENDING | What monitoring metrics matter most? Resource usage, user sessions, AI inference latency? |
| 5.4 | PENDING | How should secrets (JWT keys, API tokens, SSL certs) be managed in a bootable ISO context? |
| 5.5 | PENDING | What is the disaster recovery plan? Time-to-restore from backup to working system? |
