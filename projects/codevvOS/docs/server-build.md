# Server Build — Hardware Specification

Last updated: 2026-04-01

## Parts List ($14,332)

| # | Component | Model | Qty | Each | Total |
|---|-----------|-------|-----|------|-------|
| 1 | CPU | AMD TR PRO 9975WX 32C/64T | 1 | $3,924 | $3,924 |
| 2 | Motherboard | ASUS Pro WS WRX90E-SAGE SE | 1 | $1,247 | $1,247 |
| 3 | RAM | SK Hynix DDR5-6400 ECC RDIMM 32GB CL52 | 8 | $250 | $2,000 |
| 4 | GPU | RTX 3090 24GB (used) | 2 | $800 | $1,600 |
| 5 | Storage (Boot) | Samsung 990 PRO 4TB (ZFS mirror) | 2 | $700 | $1,400 |
| 6 | Storage (AI) | Samsung 990 PRO 4TB (ZFS mirror) | 2 | $700 | $1,400 |
| 7 | Storage (Data) | WD Black SN850X 8TB | 1 | $900 | $900 |
| 8 | Cooling | Enermax LIQTECH XTR 360mm | 1 | $200 | $200 |
| 9 | Fans | Noctua NF-A14 PWM 140mm | 6 | $25 | $150 |
| 10 | PSU | Corsair HX1500i 1500W Platinum | 1 | $350 | $350 |
| 11 | Rack | Sysracks 12U 35" Premium (custom fab) | 1 | $420 | $420 |
| 12 | UPS | CyberPower OR2200PFCRT2U 2000VA/1540W | 1 | $741 | $741 |
| 13 | KVM | Apache Guacamole (free software) | 1 | $0 | $0 |

## Amazon ASINs (for purchasing)

| Component | ASIN |
|-----------|------|
| CPU (TR PRO 9975WX) | `B0FJ6K1FMP` |
| Motherboard (WRX90E-SAGE SE) | `B0CQRYXWWQ` |
| Samsung 990 PRO 4TB | `B0CHGT1KFJ` |
| WD Black SN850X 8TB | `B0D9WT512W` |
| Enermax LIQTECH XTR 360mm | `B0DSZMM1PR` |
| Corsair HX1500i | `B0B3S8GMCK` |
| Sysracks 12U 35" | `B017QVBWMU` |
| CyberPower OR2200PFCRT2U | `B003OJAHW0` |
| RAM (SK Hynix) | Search ServerSupply.com for HMCG84AHBRA |
| GPU (RTX 3090 used) | eBay |
| KVM (PiKVM alternative) | Apache Guacamole (free) |

Note: "Server Build" shopping list exists on Amazon Business account with CPU already added.

## Key Design Decisions

- **Cooler:** Arctic Liquid Freezer III 420mm was incompatible with sTR5. Swapped to Enermax LIQTECH XTR 360mm (100% IHS coverage, 550W+ TDP).
- **UPS:** CyberPower CP1500 was only 1000W real power — too thin. Upgraded to OR2200PFCRT2U (1540W).
- **GPU:** 2x RTX 3090 chosen over 1x RTX 4090. Same 24GB VRAM each, 48GB total, saves $500, ~85% per-card speed. Best price/performance for LLM inference.
- **RAM:** Standard SK Hynix CL52 ECC RDIMMs at ~$250/stick instead of V-Color EXPO at $450/stick. Saves $1,600.
- **Rack:** Custom fabrication for EEB motherboard + 360mm radiator mounting inside Sysracks 12U enclosure.
- **KVM:** Apache Guacamole (free) replaces PiKVM v4 Mini ($200). Add cheap IP KVM dongle later if BIOS-level access needed.

## Proxmox Configuration

- Bare metal Proxmox VE on boot ZFS mirror
- IOMMU enabled for GPU passthrough (WRX90E has clean IOMMU groups per PCIe slot)
- 1x RTX 3090 → LLM inference VM (Ollama)
- 1x RTX 3090 → compute VM or second Ollama instance
- CodeVV-OS VM: 16 threads, 64GB RAM
- GPU VM: 8 threads, 32GB RAM
- ZFS pools: boot (mirror), AI (mirror), data (single)
