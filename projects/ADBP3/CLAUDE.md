# ADBP3 — Session Context

## What This Is

ADBP3 is a reserve-backed credit platform on Solana. Employers mint credits for employees on a monthly basis. Employees pay $1/credit and receive $2 of purchasing power at participating vendors — a 50% discount amplification. The treasury holds the $1 inflow and accrues interest; credits only leave the system via **discretionary burns** ($2/credit destroyed).

**Central health metric:** `backing_ratio = treasury_wallet / total_credits_outstanding`

## Ground Truth Mechanics (do NOT re-derive)

| Parameter | Value | Source |
|-----------|-------|--------|
| Credit purchase price | $1.00/credit | `constants.py` |
| Treasury capture | 100% of purchase price | `project-brief.md` |
| Interest rate | 4% APR, monthly compound | `constants.py` |
| Admin fee | 10% of purchase, separate from treasury | `constants.py` |
| Burn cost | $2/credit | `project-brief.md` |
| Target backing ratio | ≥ 1.0 | `project-brief.md` |

Always read `constants.py` before running any simulation. Do not override confirmed parameters without explicit instruction.

## Key Files

| File | Purpose |
|------|---------|
| `project-brief.md` | Highest authority — confirmed mechanics |
| `constants.py` | Ground-truth parameters for all sims |
| `simulate.py` | Core treasury simulation |
| `monte_carlo.py` | Monte Carlo backing ratio analysis |
| `analyze.py` | Campaign findings post-processor |
| `questions.md` | Active BrickLayer research questions |
| `results.tsv` | Accumulated simulation results |
| `findings/` | BrickLayer campaign findings |

## Simulation Commands

```bash
cd /home/nerfherder/Dev/Bricklayer2.0/projects/ADBP3

# Always use MPLBACKEND=Agg for headless runs
MPLBACKEND=Agg python simulate.py
MPLBACKEND=Agg python monte_carlo.py
python analyze.py
```

## BrickLayer Campaign Status

This project has an active BrickLayer research campaign. Before making architecture changes, check `questions.md` for relevant open questions and `findings/` for prior verdicts.

Use `/masonry-status` to see campaign state.

## Skills

Use `/anchor-workflow` for Anchor build/test/deploy and simulation commands.
