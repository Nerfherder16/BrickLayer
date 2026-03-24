# Architecture -- bricklayer-v2

BrickLayer 2.0 self-audit campaign. This project stress-tests the BL 2.0 engine, Masonry orchestration, and the agent fleet using the engine's own research loop.

---

## Project Structure

```
bricklayer-v2/
  questions.md          -- Question bank (5 domains + 13 evolve waves + wave-mid)
  results.tsv           -- Tab-separated verdict log (56 entries)
  findings/             -- Per-question finding files
    evolve/             -- E1.x through E13.x findings
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
| Wave 13 Evolve | E13.1-E13.10 | MIXED (4 DONE, 2 WARNING, 2 PENDING, 1 PENDING_EXT, 1 BLOCKED) |
| Wave-mid | F-mid.1, F-mid.2, M-mid.1, M-mid.2, E-mid.1 | PENDING |

---

## Key Findings

- **E13.8** [BLOCKED] Wave 13: 3 candidate agents lack .md instruction files; eval pipeline cannot generate baselines without them.
- **E13.9** [WARNING] Wave 13: 9 agents have training data but no recorded eval baselines; karen (379 records) and quantitative-analyst (76) are top targets.
- **E13.7** [WARNING] Wave 13: 4 deterministic routing gaps identified; adding 14 lines raises coverage from 75% to ~90%.

---

## Agent Fleet (eval scores as of Wave 13)

| Agent | Score | Status |
|-------|-------|--------|
| karen | 1.00 | AT TARGET |
| regulatory-researcher | 1.00 | AT TARGET |
| quantitative-analyst | 0.90 | AT TARGET |
| competitive-analyst | ~0.92 | AT TARGET |
| research-analyst | 0.84 (live) | Near target (0.85) |
| synthesizer-bl2 | 0.62 (live) | Meets target (0.60) |
| git-nerd | 1.00 | AT CEILING |
| fix-implementer | 0.76 | No training data |
| peer-reviewer | -- | BLOCKED (no .md) |
| agent-auditor | -- | BLOCKED (no .md) |
| retrospective | -- | BLOCKED (no .md) |
| mortar | -- | 15 records, not evaluated |
| architect | -- | 15 records, not evaluated |
| devops | -- | 14 records, not evaluated |
| refactorer | -- | 12 records, not evaluated |
| overseer | -- | 6 records, not evaluated |

---

## Open Items

| ID | Verdict | Summary |
|----|---------|---------|
| E13.8 | BLOCKED | peer-reviewer/agent-auditor/retrospective have no .md instruction files |
| E13.7 | WARNING | 4 deterministic routing coverage gaps (eval, architect, diagnose, campaign patterns) |
| E13.9 | WARNING | 9 agents with training data have no eval baseline |
| E13.3 | PENDING | research-analyst prompt optimization on 38-record dataset |
| E13.5 | PENDING | synthesizer-bl2 optimization on 21-record combined dataset |
| E13.10 | PENDING_EXTERNAL | improve_agent.py 3-loop convergence test |
| F-mid.1 | PENDING | Mode dispatch in CI runner (Q1.1 fix spec ready) |
| F-mid.2 | PENDING | PENDING_EXTERNAL handling in CI runner (Q1.5 fix spec ready) |
| E-mid.1 | PENDING | karen prompt optimization (unblocked by E2.3) |
