---
name: homelab
description: Use when working with Docker, Proxmox, CasaOS deployments, or homelab infrastructure troubleshooting
---

# Homelab Infrastructure

**Full network map is in `~/.claude/rules/network-map.md` — that is the single source of truth.**
Everything below is a quick-reference summary; update the network map for permanent changes.

## Quick Host Reference

| Host | IP | SSH | Role |
|------|----|-----|------|
| OPNsense | 192.168.50.1 | Web UI | Gateway, firewall, Unbound DNS |
| farmstand (CasaOS) | 192.168.50.19 | `nerfherder@farmstand` (Tailscale) | Docker host |
| ollama-vm | 192.168.50.62 | `nerfherder@192.168.50.62` | RTX 3090 inference |
| ubuntu-claude | 192.168.50.35 | `nerfherder@192.168.50.35` | Claude Code runner |
| Home Assistant | 192.168.50.20 | — | Smart home |
| VPS (Racknerd) | 104.168.64.181 | `root@104.168.64.181` | Reverse proxy |

## Docker on CasaOS

- Command: `docker compose` (never `docker-compose`)
- Data root: `/DATA/AppData/`
- Diagnose first: `docker logs -f [container]` before suggesting any fix
- VPN containers: route through Gluetun

## Proxmox

- **Hardware**: ASUS ROG Zenith Extreme X399, Threadripper 1950X, RTX 3090
- **BIOS**: IOMMU enabled + "Enumerate all IOMMU in IVRs" (critical for X399)
- **GPU passthrough**: q35 + OVMF + `pcie=1,x-vga=1`

## Troubleshooting Checklist

1. Service not responding → `docker ps` then `docker logs -f [name]`
2. GPU passthrough fails → check IOMMU groups, vendor-reset on VM restart
3. Network issue → OPNsense firewall rules, WireGuard tunnel status (`ping 192.168.50.19` from VPS)
4. VPN container → `docker exec gluetun wget -qO- https://ipinfo.io`
5. Ollama unreachable → ensure `OLLAMA_HOST=0.0.0.0:11434`

## Credentials

Stored in Recall — never hardcoded. Query examples:
- `porkbun API key` → DNS management keys
- `opnsense password` → firewall admin
- `casaos login` → CasaOS admin

See network-map.md for the full credentials index.
