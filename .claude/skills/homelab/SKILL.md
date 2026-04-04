---
name: homelab
description: Use when working with Docker, Proxmox, CasaOS deployments, or homelab infrastructure troubleshooting
---

# Homelab Infrastructure

## Key Hosts
| Device | IP | Purpose |
|--------|-----|---------|
| OPNsense | 192.168.50.1 | Gateway, firewall, Unbound DNS |
| CasaOS | 192.168.50.19 | Docker host (SSH: nerfherder@, pubkey) |
| Ollama VM | 192.168.50.62 | GPU inference (RTX 3090, 24GB VRAM) |
| Home Assistant | 192.168.50.20 | Smart home automation |
| VPS (Racknerd) | 104.168.64.181 | Reverse proxy for remote access |

## Docker on CasaOS
- Use `docker compose` (not `docker-compose`)
- Data: `/DATA/AppData/`
- Always check logs before suggesting fixes: `docker logs -f [container]`
- VPN-dependent containers route through Gluetun

## Proxmox
- **Hardware**: ASUS ROG Zenith Extreme X399, AMD Threadripper 1950X, RTX 3090
- **BIOS**: IOMMU enabled + "Enumerate all IOMMU in IVRs" (critical for X399)
- **VM config**: q35 machine type, OVMF (UEFI), `pcie=1,x-vga=1` for GPU passthrough

### Common Proxmox Issues
1. **VM won't start** → Check if GPU needs vendor-reset
2. **GPU passthrough fails** → Verify IOMMU groups
3. **Boot issues** → Add `nomodeset` to GRUB
4. **Ollama unreachable** → Ensure `OLLAMA_HOST=0.0.0.0:11434`

## Troubleshooting Checklist
1. Service not responding → `docker ps` + `docker logs`
2. GPU issues → IOMMU groups, `pcie=1,x-vga=1`
3. Network issues → OPNsense firewall rules, WireGuard tunnel status
4. VPN check → `docker exec gluetun wget -qO- https://ipinfo.io`

## Recall retrieves detailed service configs, port mappings, and infrastructure history automatically.
