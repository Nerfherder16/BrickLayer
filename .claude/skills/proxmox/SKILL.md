---
name: proxmox
description: Use when managing Proxmox VMs, LXC containers, storage, snapshots, or running commands inside VMs. Uses Proxmox MCP tools directly.
---

# Proxmox Management

**Host**: `100.99.135.123:8006` | Token: `root@pam!mcpserver`

## VM Inventory

| ID | Name | Type | IP | SSH | Notes |
|----|------|------|----|-----|-------|
| 100 | Windows11-Gaming | QEMU | — | — | Stopped, gaming rig |
| 101 | CasaOS | QEMU | 192.168.50.19 | nerfherder@ pubkey | Docker host, all services |
| 102 | recall-ollama | QEMU | 192.168.50.62 / Tailscale 100.70.195.84 | nerfherder / lacetimcat1216 | GPU inference, Recall API |
| 103 | ubuntu-claude | QEMU | 192.168.50.35 | nerfherder@ pubkey (no password) | Claude Code runner, QEMU agent installed |
| 104 | bricklayer-train | LXC | — | — | BrickLayer training |
| 105 | codevvos | LXC | — | — | CodevvOS project |

## MCP Tool Patterns

### Check Status
```
proxmox_get_vms          → list all VMs with status
proxmox_get_vm_status    → node=pve, vmid=103
proxmox_get_node_status  → node=pve
proxmox_get_storage      → node=pve
```

### Power Management
```
proxmox_start_vm    → node=pve, vmid=103
proxmox_stop_vm     → node=pve, vmid=103  (hard stop)
proxmox_reboot_vm   → node=pve, vmid=103  (soft reboot — does NOT add new hardware)
```
> **Note**: Config changes (agent, hardware) require full stop+start, not just reboot.

### Run Commands Inside VM (requires QEMU guest agent)
```
proxmox_execute_vm_command → node=pve, vmid=103, command="df -h /"
```
- ubuntu-claude (103) has qemu-guest-agent installed
- Commands cannot use shell operators: ; & | ` $ ( ) { } [ ] < >
- Run one command at a time

### Disk Operations
```
proxmox_resize_disk_vm → node=pve, vmid=103, disk=scsi0, size=+20G
```
- After Proxmox resize, still need to grow partition inside VM:
  ```bash
  sudo growpart /dev/sda 3
  sudo pvresize /dev/sda3
  sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
  sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
  ```

### Snapshots
```
proxmox_create_snapshot_vm → node=pve, vmid=103, snapname="before-change"
proxmox_list_snapshots_vm  → node=pve, vmid=103
proxmox_rollback_snapshot_vm → node=pve, vmid=103, snapname="before-change"
```

### Enable QEMU Guest Agent on a VM
1. Update config via Proxmox API:
   ```bash
   curl -s -k -X PUT https://100.99.135.123:8006/api2/json/nodes/pve/qemu/VMID/config \
     -H "Authorization: PVEAPIToken=root@pam!mcpserver=69c9ecf2-c642-4017-8712-0654fa799c9a" \
     -d "agent=1"
   ```
2. SSH into VM and install: `sudo apt install -y qemu-guest-agent && sudo systemctl enable --now qemu-guest-agent`
3. Full **stop + start** the VM (reboot alone won't activate the virtio channel)

## Storage
- `local` — ISOs, backups, templates (93GB, 18% used)
- `local-lvm` — VM disks, LXC rootfs (1.71TB, ~50% used)

## Common Cleanup Commands (run via execute_vm_command)
```bash
# Disk usage
df -h /

# Large files
find / -xdev -size +200M

# Docker cleanup
docker system prune -f

# Journal logs
journalctl --vacuum-size=200M

# Apt cache
apt clean
```
