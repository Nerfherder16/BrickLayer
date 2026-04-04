# BrickLayer 2.0 — Research Roadmap

Last updated: 2026-04-04

---

## Wave 14 — Evolve (complete)

- [x] Run evolve-mode campaign on bricklayer-v2
- [x] Fix tmux per-spawn gate (`BL_GATE_FILE`)
- [x] Fix Recall bridge — remove dead `decay_conflicting_memories()`
- [x] WSL-portable paths in mortar, bl-verifier, e2e agents
- [x] Dynamic mortar-gate loader from agent_registry.yml

### Open Items from Wave 14

- [ ] E14.9 — Full-corpus live eval 0.58 (20/36); INCONCLUSIVE over-fires; cross-family generalization gap — needs calibration
- [ ] E14.8 — improve_agent.py UnicodeDecodeError in subprocess reader — encoding fix needed
- [ ] E14.1 — E12.1-live-15 persistent (HEALTHY predicted WARNING) — needs calibration example
- [ ] E14.6 — quantitative-analyst static 0.40 unreliable; live eval needed
- [ ] E-mid.1 — karen prompt optimization — manual Git Bash run needed

---

## Infrastructure (ongoing, 2026-04-04)

- [x] Routing rules rewritten — dev tasks route to rough-in directly; Mortar handles campaigns/docs
- [x] `@agent-name:` self-invoke bypass in masonry-prompt-router.js
- [x] masonry-mortar-enforcer.js: allow direct specialist spawns from main session
- [x] network-map.md global rule — full LAN/Tailscale/VPS topology (single source of truth)
- [x] homelab skill and self-host.md updated to reference network-map.md
- [x] ubuntu-claude Tailscale SSH documented; workspace path confirmed
- [x] Proxmox skill added
- [x] deploy-claude.sh: atomic write, mcpServers sync from ~/.claude.json
- [x] secret redaction from mcp-servers.json
- [x] tmux terminal profiles for Tim and Nick in VS Code
- [ ] karen prompt optimization (E-mid.1) — pending manual run
- [ ] improve_agent.py UnicodeDecodeError fix (E14.8)

---

## Wave 15 — Predict (planned)

- [ ] Generate Wave 15 question bank for bricklayer-v2
- [ ] Run predict-mode campaign — forecast degradation risks
- [ ] Evaluate routing accuracy after prompt-router refactor
- [ ] Benchmark mortar-enforcer overhead (direct-spawn vs. routed)
- [ ] Verify cross-machine sync (WSL → ubuntu-claude → farmstand)

---

## Wave 16 — Monitor (planned)

- [ ] Establish baseline health metrics for all active projects
- [ ] Wire Monitor mode to System-Recall for persistent health history
- [ ] Alert thresholds for DEGRADED → ALERT transitions

---

## Recall 2.0 (active, recall-arch-frontier/)

- [x] 256-question frontier research complete
- [ ] Rust rewrite scaffolding — driven by frontier findings
- [ ] Qdrant + Neo4j schema validated against Recall 2.0 design
- [ ] Heal loop validation on Recall 2.0

---

## ADBP3 (active, projects/ADBP3/)

- [ ] Solana Anchor program — discount-credit token logic
- [ ] Employee utility token — 50% purchasing power amplification
- [ ] Security audit via masonry-security-review
- [ ] Mainnet deployment checklist

---

## Meta / Tooling

- [ ] Crucible: schedule quarterly agent benchmarks
- [ ] Kiln (BrickLayerHub): status tiles for all active campaigns
- [ ] training_export.py: automate export after each wave
- [ ] jCodeMunch: enforce symbol-first retrieval across all agents (audit pending)
