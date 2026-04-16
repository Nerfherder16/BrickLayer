# BrickLayer 2.0 — Research Roadmap

Last updated: 2026-04-15

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
- [x] Learning loop: `masonry_pattern_promote` / `masonry_pattern_demote` MCP tools
- [x] `masonry-build-outcome.js` hook — auto-promotes/demotes patterns on DONE/FAILED transitions
- [x] Session-start pattern decay + top-5 agent confidence hint in `context-data.js`
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

## DX Tooling (complete — 2026-04-15)

- [x] Agent Performance HUD — live table of confidence scores + verdict distribution on port 7824 (`masonry/src/hud/`)
- [x] Spec Drift Detector — compares spec file list vs git diff; outputs `drift-report.md` + `drift-summary.txt`
- [x] Drift inject — surfaces last build drift summary at session open via `masonry-session-start` hook
- [x] Project Chronicle — SQLite session ledger with REST API + Chronicle tab in brainstorm canvas
- [x] `/drift` skill — on-demand drift detection from any session

---

## Meta / Tooling

- [ ] Crucible: schedule quarterly agent benchmarks
- [ ] Kiln (BrickLayerHub): status tiles for all active campaigns
- [ ] training_export.py: automate export after each wave
- [ ] jCodeMunch: enforce symbol-first retrieval across all agents (audit pending)

---

## Unwired Features (in-progress, from economizer audit 2026-04-05)

### F2 — JS Engine Partial Migration (DONE — 2026-04-06)
The `masonry/src/engine/` JS layer (55 files) is a deliberate Node.js port of `bl/`.
Decision: **partial migration** — wire JS modules into MCP tools and hook fast-path only.
Python stays for campaign runner, DSPy, scoring, crucible.

- [x] Wire `masonry/src/engine/` modules into MCP tools: `masonry_route`, `masonry_status`, `masonry_registry_list` (eliminates Python IPC hop for per-prompt calls)
- [x] Wire JS `healloop.js` into MCP `masonry_run_question` tool (JS engine already complete, just needs connection)
- [x] Document the dual-engine architecture in ARCHITECTURE.md — which layer owns what
- [x] Add `NOT_YET_WIRED` marker to JS engine README until connections are made

### F3 — masonry-guard.js: wire + flush queue (DONE — 2026-04-06)
3-strike PostToolUse error pattern guard — well-written, complementary to tool-failure.js,
but its warning queue (`/tmp/masonry-guard-{sessionId}.ndjson`) is never read.

- [x] Register `masonry-guard.js` in `settings.json` as PostToolUse (no matcher, async)
- [x] Add queue reader — `masonry-guard-flush.js` on UserPromptSubmit flushes warnings as systemMessage
- [ ] Add benchmark test case for masonry-guard.js

### F5 — Heal loop wiring (DONE — 2026-04-06)
`bl/healloop.py` is complete (FAILURE → diagnose-analyst → fix-implementer → FIXED state machine,
env-gated at `BRICKLAYER_HEAL_LOOP=1`, max 3 cycles). Never called from any runner.

- [x] Wire `run_heal_loop()` into `bl/runners/agent.py` at verdict evaluation point
- [x] Verify `diagnose-analyst.md` and `fix-implementer.md` existence check works (built into healloop.py)
- [x] Add integration test: mock FAILURE verdict → confirm heal loop fires and cycles correctly

### F6 — DSPy pipeline: fix default model + create generated/ dir (DONE — 2026-04-06)
`configure_dspy(backend="ollama")` defaults to `model="claude-sonnet-4-6"` which Ollama rejects.
Full MIPROv2 deferred at wave 22 (R22.2 PENDING). `generated/` dir missing.

- [x] Fix `configure_dspy` default model to `qwen3:14b` when backend is `"ollama"`
- [x] Create `masonry/src/dspy_pipeline/generated/.gitkeep`
- [x] Delete empty `optimized/` root directory
- [ ] Verify `masonry_onboard` MCP tool succeeds after dir creation
- [ ] Resume R22.2: full MIPROv2 trial with `qwen3:14b` on routing agent

### F7 — Wire scratch/tracer/history into campaign loop (IN PROGRESS)
Three designed, tested, env-gated features with zero callers in production.

- [ ] `history.py`: wire into `bl/runners/agent.py` after verdict — write to SQLite ledger unconditionally
- [ ] `tracer.py`: wire into same point behind `BRICKLAYER_TRACE_RECALL=1` env gate
- [ ] `scratch.py`: wire signal parsing into `bl/findings.py` when findings are written
