# Token Efficiency Roadmap

**Created:** 2026-04-06  
**Context:** BrickLayer 2.0 + Masonry ecosystem  
**Model:** claude-sonnet-4-6 (1M token context window)

---

## Key Facts

| Metric | Value |
|--------|-------|
| Model context window | 1,000,000 tokens |
| Claude Code reported % | Against 200K (bug — CC not updated for 1M yet) |
| Auto-compact threshold (updated) | 95% → fires at 190K now, 950K when CC updates |
| Static overhead per session | ~50K tokens (CLAUDE.md + rules + tool defs + hooks) |
| Turns before compact (200K regime) | ~280 turns |
| Turns before compact (1M regime, future) | ~1,800 turns |
| Dominant cost | Cache reads (~99.9% of effective tokens) |
| Cache discount rate | 10% of full input price |

### How session costs work

```
effective_tokens = input_tokens + (cache_read_tokens × 0.1)

Cut 10K from static context → save 10K × turns × 0.1 effective per turn
Over a 1,395-turn session = 1.4M effective tokens saved
```

---

## Completed ✅

### C1 — CLAUDE.md Trim
**Saved:** ~1,575 tokens/turn → ~220K eff/large session  
Removed Engine Architecture table, Runner Types table, Project Structure tree, Key Concepts glossary, Authority Hierarchy table, Agent Routing 4-layer table. Condensed to 1–2 line references. Actionable routing rules kept intact.  
`CLAUDE.md`: 253 lines → 148 lines (41% reduction)

### C2 — Statusline % Fix
**Impact:** Accuracy (was showing 5× inflated %)  
`used_percentage` from Claude Code is calculated against 200K. Rescaled by `× 0.2` to show real usage against 1M. What showed as `52%` now correctly shows `10%`.  
Files: `~/.claude/hud/masonry-statusline.js`, `masonry/src/hooks/masonry-context-safety.js`

### C3 — Statusline Token Display Fix
**Impact:** Accuracy + usefulness  
Was showing `0 tok` (raw input_tokens rounds to 0k). Now shows `effective_tokens` (billing-relevant) from last completed session. Sessions under 1K eff suppressed as noise. Label: `tok` → `eff`.

### C4 — Auto-Compact Threshold
**Impact:** More headroom before compact  
`DISABLE_AUTO_COMPACT_THRESHOLD`: 85 → 95  
Now: fires at 190K (was 170K). When CC updates to 1M: automatically fires at 950K — no change needed.

---

## Roadmap

### P1 — Install Cozempic (PreCompact Pruning)
**Estimated savings: ~2.8M eff tokens/large session (~15–25%)**  
**Effort: 30 min**

[github.com/Ruya-AI/cozempic](https://github.com/Ruya-AI/cozempic) hooks into `PreCompact` and applies 13 pruning strategies before Claude's compaction fires.

Key strategies for this setup:

| Strategy | Removes | Saves |
|----------|---------|-------|
| `document-dedup` | CLAUDE.md re-injected multiple times/session | 0–44% |
| `tool-result-age` | Old tool outputs (minified/stubbed) | 10–40% |
| `progress-collapse` | Consecutive progress ticks | 40–48% |
| `compact-summary-collapse` | Messages already captured in prior summaries | 85–95% |
| `stale-reads` | File reads superseded by later edits | varies |

The `document-dedup` finding is critical — CLAUDE.md is re-injected multiple times per session in agentic setups. This is confirmed by the cozempic team and by Claude Code's own changelog fix for nested CLAUDE.md re-injection.

**Install:**
```bash
pip install cozempic
cozempic init  # adds PreCompact hook to settings.json
```

---

### P2 — `.claudeignore` Audit
**Estimated savings: 30–94% of session-start exploration tokens**  
**Effort: 10 min**

Verify these are blocked (add if missing):

```
__pycache__/
*.pyc
*.pyo
masonry/node_modules/
masonry/training_data/scored_*.jsonl
.autopilot/archive/
.autopilot/backups/
findings/
bricklayer-v2/
recall-arch-frontier/
results.tsv
.mas/
```

Training data, findings dirs, and campaign archives should never be scanned at session start.

---

### P3 — Short@Tags Compression for `~/.claude/rules/`
**Estimated savings: ~700K eff tokens/large session**  
**Effort: 2–3 hrs**

Rules files are injected every session as verbose paragraphs. Paragraph-style rules get summarized away during compaction then re-injected, creating a compaction-survival problem. Short@Tags encodes protocols as single tokens that survive compaction:

```markdown
# BEFORE (paragraph — lost on compact, re-injected next session):
Never write secrets to the filesystem. Always use Azure Key Vault.
Route secrets through stdin pipes, never CLI args or stdout.

# AFTER (survives compact as single token):
#COMPUSEC #VAULT_ONLY: Secrets → env var → stdin pipe. Never filesystem, CLI args, stdout.
```

Rules files to compress (by size/impact):
- `full/execution-verification.md` — verbose with examples
- `full/tdd-enforcement.md` — essays on "why TDD"
- `full/systematic-debugging.md` — long phase descriptions
- `full/workflow-enforcement.md` — repeated tables

Target: rules injection ~10K tokens → ~3K tokens per session.

---

### P4 — Hook Injection Audit (Zero-State Suppression)
**Estimated savings: ~280K eff tokens/large session**  
**Effort: 1 hr**

Hooks inject context blocks even when there's nothing to report. Fix: skip injection when all values are zero/empty.

Hooks to audit:
- `masonry-session-summary.js` — emits telemetry blocks with 0 agents, 0 Recall hits
- `masonry-system-status.js` — injects status even when unchanged from last turn
- `masonry-ema-collector.js` — outputs context when no EMA data exists

Pattern to add:
```javascript
if (noActiveState) process.exit(0);  // nothing to report, stay silent
```

---

### P5 — MCP Tool List Stabilization (Cache-Bust Prevention) ✅ DONE
**Estimated savings: 50–200K tokens per cache-bust event avoided**  
**Effort: 30 min**

Changing MCP tool definition ordering between turns invalidates the prompt cache (confirmed bug #42647). Fix: remove unused MCP servers — each injects its full schema every turn even when never called.

Check actual tool usage from logs:
```bash
tail -10 ~/.mas/token-log.jsonl | python3 -c "
import json, sys, collections
counts = collections.Counter()
for l in sys.stdin:
    d = json.loads(l.strip())
    counts.update(d.get('tool_footprint', {}).keys())
print(counts.most_common())
"
```

Remove any `mcpServers` entries from `~/.claude/settings.json` that don't appear.

---

### P6 — Read-Once PostToolUse Hook ✅ DONE
**Estimated savings: 60–90% of Read tool token usage**  
**Effort: 2 hrs**

jCodeMunch handles symbol-level reads but full-file `Read` calls still hit. A `PostToolUse` hook tracks files read this session and blocks redundant re-reads.

From Boucle blog (March 2026), independently validated by GitHub issues #7772 and #38733.

Build `masonry-read-dedup.js`:
- Track files read this session in `/tmp/masonry-reads-{sessionId}.json`
- On subsequent Read of same file: check if file mtime has changed
- If unchanged, block and return "already in context" notice

---

### P7 — Agent Registry Description Trim (Deferred)
**Estimated savings: ~50K eff tokens per routing session**  
**Effort: 1 hr**

`masonry/agent_registry.yml` (76KB, 108 agents) — descriptions average 115 chars, duplicating info already in `capabilities:` arrays. Full YAML parsed at routing time.

Target: trim all descriptions to ≤5 words.

```yaml
# BEFORE:
description: Implements code to pass tests in TDD RED-GREEN-REFACTOR cycle

# AFTER:
description: "Code implementation (TDD)"
```

---

### P8 — Bug #43603 Workaround (Post-Compact Double Injection)
**Estimated savings: 10–20K tokens per compact event**  
**Effort: Awareness only — no fix available yet**

After `/compact`, Claude Code auto-reads recently-used files back into context. If `UserPromptSubmit` hooks inject those same files → they arrive twice.

**Workaround:** Don't `Read` hook-injected state files (masonry-state.json, progress.json, mode) in the turns immediately before a compact.

Tracking: [GitHub Issue #43603](https://github.com/anthropics/claude-code/issues/43603)

---

## Projected Total Savings

Based on a representative large session (1,395 turns, 18.1M effective tokens):

| Item | Status | Eff Tokens Saved | % of Session |
|------|--------|-----------------|--------------|
| C1 CLAUDE.md trim | ✅ Done | ~220K | 1.2% |
| C2–C4 Statusline + threshold | ✅ Done | accuracy | — |
| P1 Cozempic | Next | ~2,790K | 15.4% |
| P2 .claudeignore | Next | variable | 1–5% |
| P3 Short@Tags rules | Planned | ~697K | 3.9% |
| P4 Hook zero-state | Planned | ~280K | 1.5% |
| P5 MCP stabilization | **DONE** | avoids loss | removed 8 unused servers |
| P6 Read-once hook | **DONE** | ~500K | masonry-read-dedup.js wired |
| P7 Registry trim | Deferred | ~50K | descriptions not injected into Claude context; embeddings cached |
| **Total** | | **~4,537K** | **~25%** |

**18.1M → ~13.6M effective tokens per large session.**

At Sonnet 4.6 pricing ($3/MTok input, $0.30/MTok cache reads):
- Estimated current session cost: ~$5.40
- After optimizations: ~$4.05
- **Savings: ~$1.35/session**

---

## Context Window Roadmap Note

Claude Code v2.1.92 calculates `context_window.used_percentage` against 200K despite Sonnet/Opus 4.6 having a 1M context window. Statusline rescaling (`× 0.2`) should be removed once CC ships the fix.

When CC updates to 1M:
- Auto-compact threshold (95%) automatically applies to 1M → fires at **950K**
- Turns before compact: ~280 → ~1,800 (6× longer conversations)
- Compaction frequency drops ~6×, eliminating most Bug #43603 exposure
- Remove the `× 0.2` rescaling from statusline and context-safety hook
