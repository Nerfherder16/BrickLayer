# Architecture -- bricklayer-v2

BrickLayer 2.0 self-audit campaign. This project stress-tests the BL 2.0 engine, Masonry orchestration, and the agent fleet using the engine's own research loop.

---

## Project Structure

```
bricklayer-v2/
  questions.md          -- Question bank (5 domains + 14 evolve waves + wave-mid)
  results.tsv           -- Tab-separated verdict log (69 entries)
  findings/             -- Per-question finding files
    evolve/             -- E1.x through E14.x findings
    diagnose/           -- Q1.x diagnosis findings
    validate/           -- Q2.x validation findings
    research/           -- Q3.x research findings
    audit/              -- Q3.5 audit finding
    frontier/           -- Q3.3, Q5.x frontier findings
    synthesis.md        -- Current wave synthesis (rewritten each wave)
  .claude/agents/       -- Project-local agent copies
```

---

## Question Bank Summary

| Domain | Questions | Status |
|--------|-----------|--------|
| D1 -- Architecture (Diagnose) | Q1.1-Q1.5 | COMPLETE |
| D2 -- Mode Implementation (Validate) | Q2.1-Q2.5 | COMPLETE (3 WARNING) |
| D3 -- Per-Project Application (Research) | Q3.1-Q3.5 | COMPLETE |
| D4 -- Template Evolution (Evolve) | Q4.1-Q4.3 | COMPLETE |
| D5 -- Frontier | Q5.1-Q5.2 | COMPLETE |
| Wave 1-12 Evolve | E1.1-E12.3 | COMPLETE |
| Wave 13 Evolve | E13.1-E13.10 | COMPLETE (3 IMPROVEMENT, 1 HEALTHY, 3 WARNING, 1 BLOCKED, 1 PENDING_EXT) |
| Wave 14 Mid | F-mid.1, F-mid.2, M-mid.1, M-mid.2, E-mid.1 | MIXED (2 FIXED, 2 CALIBRATED, 1 PENDING_EXT) |
| Wave 14 Evolve | E14.1-E14.9, E13.5-verify | COMPLETE (5 IMPROVEMENT, 3 WARNING, 1 verify-IMPROVEMENT) |

---

## Key Findings

- **E14.9** [WARNING] Wave 14: Full-corpus live eval 0.58 (20/36); E12.1-live- family 94% but older families 14-33%; INCONCLUSIVE over-fires as WARNING; cross-family generalization is the primary gap.
- **E14.8** [WARNING] Wave 14: improve_agent.py UnicodeDecodeError crashes mid-loop; encoding='utf-8' fix needed in subprocess reader thread; loops 2-3 never ran.
- **E14.7** [IMPROVEMENT] Wave 14: Deterministic routing coverage raised 75% to 100%; 4 pattern sets added; E13.7 fully resolved.

---

## Agent Fleet (eval scores as of Wave 14)

| Agent | Score | Status |
|-------|-------|--------|
| karen | 0.90 | AT TARGET |
| regulatory-researcher | 1.00 | AT TARGET |
| quantitative-analyst | 0.40 (static) | Needs live eval |
| competitive-analyst | ~0.92 | AT TARGET |
| research-analyst | 0.58 (live full-corpus) / 0.94 (E12.1-live-) | Calibrated-family AT TARGET; generalization gap |
| synthesizer-bl2 | 0.55 (tool-free) / 0.62 (live) | Meets target (0.60) |
| git-nerd | 1.00 | AT CEILING |
| fix-implementer | 0.76 | No training data |
| peer-reviewer | -- | .md written (E14.3), not evaluated |
| agent-auditor | -- | .md written (E14.4), not evaluated |
| retrospective | -- | .md written (E14.4), not evaluated |
| frontier-analyst | -- | .md confirmed (E14.5), not evaluated |
| mortar | -- | 15 records, not evaluated |
| architect | -- | 15 records, not evaluated |
| devops | -- | 14 records, not evaluated |
| refactorer | -- | 12 records, not evaluated |
| overseer | -- | 6 records, not evaluated |

---

## Open Items

| ID | Verdict | Summary |
|----|---------|---------|
| E14.9 | WARNING | Full-corpus live eval 0.58 (20/36); INCONCLUSIVE over-fires; E12.1-live-15 persistent; older families 14-33% |
| E14.8 | WARNING | improve_agent.py UnicodeDecodeError in subprocess reader; encoding bug unfixed; loops 2-3 never ran |
| E14.1 | WARNING | E12.1-live-15 persistent (HEALTHY predicted WARNING); needs explicit calibration example |
| E14.6 | WARNING | quantitative-analyst static 0.40 unreliable; live eval needed for authoritative baseline |
| E-mid.1 | PENDING_EXTERNAL | karen prompt optimization -- needs manual Git Bash run |
