# Context Diet — 50% Token Reduction

**Goal**: Cut ~40K token/turn base context to ~20K by stubbing conditional rules, compressing always-relevant rules, deduplicating CLAUDE.md, and auditing injections.

**Strategy**: conservative
**Branch**: autopilot/context-diet-20260406

## Tasks

### Task 1 — Backup originals to rules/full/
Create `~/.claude/rules/full/` and copy ALL current rules files as-is. Safety net before modifications.
- **Test**: `diff -r ~/.claude/rules/ ~/.claude/rules/full/` shows zero differences for copied files
- **Savings**: 0 (setup)

### Task 2 — Stub network-map.md [depends:1]
Replace 12.6KB file with 3-line stub + pointer to `~/.claude/rules/full/network-map.md`.
- **Savings**: ~3,000 tokens/turn

### Task 3 — Stub testing-strategies-coverage.md [depends:1]
Replace 10.6KB file with stub + pointer.
- **Savings**: ~2,500 tokens/turn

### Task 4 — Stub golang-rules.md [depends:1]
Replace 5.5KB file with stub + pointer.
- **Savings**: ~1,300 tokens/turn

### Task 5 — Stub standards-design.md [depends:1]
Replace 7.2KB file with stub + pointer.
- **Savings**: ~1,700 tokens/turn

### Task 6 — Stub standards-accessibility.md [depends:1]
Replace 4.4KB file with stub + pointer.
- **Savings**: ~1,000 tokens/turn

### Task 7 — Stub python-rules, typescript-rules, gh-cli, team-vault [depends:1]
Replace 4 smaller conditional files with stubs. Combined 14.8KB → ~800 bytes.
- **Savings**: ~3,500 tokens/turn

### Task 8 — Compress workflow-enforcement.md [depends:1]
Trim from 7.9KB to ~3.5KB. Remove verbose examples, keep rules and tables.
- **Savings**: ~1,000 tokens/turn

### Task 9 — Compress tdd, execution-verification, git-operations, debugging, verification [depends:1]
Compress 5 always-relevant files by removing redundant examples. Target 50% reduction each.
- **Savings**: ~3,500 tokens/turn

### Task 10 — Compress vexor-search.md and jcodemunch.md [depends:1]
Remove duplicate jCodeMunch section from vexor, trim examples in both.
- **Savings**: ~800 tokens/turn

### Task 11 — Deduplicate CLAUDE.md files [depends:1,2,3,4,5,6,7,8,9,10]
Remove BL-specific content from global `~/.claude/CLAUDE.md` (keep in project CLAUDE.md only). Target global from 20.8KB to ~12KB.
- **Savings**: ~2,000 tokens/turn

### Task 12 — Hook injection audit [depends:1]
Read-only audit of 8 hooks that inject systemMessage. Measure token count per hook. Write findings to `docs/reviews/2026-04-06-hook-injection-audit.md`.
- **Savings**: identifies future savings

### Task 13 — Skill description audit [depends:1]
Read-only audit of 62 skill descriptions loaded at session start. Measure total token overhead. Write findings to `docs/reviews/2026-04-06-skill-description-audit.md`.
- **Savings**: identifies future savings

### Task 14 — Measure and verify [depends:11,12,13] [phase_end]
Run `wc -c` on all auto-loaded files. Compare against baseline. Verify <20K tokens/turn achieved. Write results to `docs/reviews/2026-04-06-context-diet-results.md`.

## Baseline Measurements

| Source | Before (bytes) | Before (tokens) |
|--------|---------------|-----------------|
| Rules files | 127,700 | ~31,925 |
| Global CLAUDE.md | 20,800 | ~5,200 |
| Project CLAUDE.md | 12,200 | ~3,050 |
| **Total** | **160,700** | **~40,175** |

## Target

| Source | After (bytes) | After (tokens) |
|--------|--------------|----------------|
| Rules files | <50,000 | ~12,500 |
| Global CLAUDE.md | <13,000 | ~3,250 |
| Project CLAUDE.md | ~13,000 | ~3,250 |
| **Total** | **<76,000** | **<19,000** |

**Reduction: 50.5% (~20,300 tokens/turn saved)**

## Notes

- No content deletion — full versions preserved in `~/.claude/rules/full/`
- No code changes in tasks 1-11 — pure file reorganization
- Tasks 12-13 are audit only — no hook modifications
- Strategy: conservative (critical config files)
- Engine layers touched: none (config/docs only)
