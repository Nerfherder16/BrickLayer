---
name: anchor-workflow
description: >-
  Solana/Anchor development workflow for ADBP3. Build, test, and deploy Anchor
  programs. Run simulations (simulate.py, monte_carlo.py, analyze.py). Check
  backing ratio, treasury health, and token mechanics. Use when working on the
  ADBP reserve-backed credit system.
tools: Bash, Read, Glob, Grep
---

# Anchor Workflow — ADBP3

You are assisting with the ADBP3 Solana reserve-backed credit platform. This skill covers:
- Anchor smart contract build/test/deploy
- Python simulation and analysis scripts
- Monte Carlo modeling of treasury mechanics
- Backing ratio and fee optimization

## Project Location

```
/home/nerfherder/Dev/Bricklayer2.0/projects/ADBP3/
```

## Key Files

| File | Purpose |
|------|---------|
| `simulate.py` | Core treasury simulation |
| `monte_carlo.py` | Monte Carlo backing ratio analysis |
| `analyze.py` | Campaign findings analyzer |
| `constants.py` | Ground-truth system parameters |
| `project-brief.md` | Confirmed mechanics (do not re-derive) |
| `ARCHITECTURE.md` | System architecture |

## Common Commands

### Anchor (when Anchor.toml / programs/ exist)

```bash
# Build programs
cd /path/to/anchor-project && anchor build

# Run tests
anchor test

# Deploy to devnet
anchor deploy --provider.cluster devnet

# Verify IDL
anchor idl fetch <program_id> --provider.cluster devnet
```

### Python Simulations

```bash
cd /home/nerfherder/Dev/Bricklayer2.0/projects/ADBP3

# Run core simulation
MPLBACKEND=Agg python simulate.py

# Monte Carlo analysis
MPLBACKEND=Agg python monte_carlo.py

# Analyze findings
python analyze.py

# Run all sims
MPLBACKEND=Agg python simulate.py && python analyze.py
```

## System Mechanics (ground truth — never re-derive)

- Employee pays **$1.00/credit** → 100% to treasury wallet
- Treasury earns **4% APR** compounded monthly
- **10% admin fee** on purchases → separate from treasury
- Discretionary burns cost treasury **$2/credit**
- Health metric: `backing_ratio = treasury_wallet / total_credits_outstanding`
- Target backing ratio: ≥ 1.0 (fully backed)

## Workflow

1. Read `project-brief.md` and `constants.py` before any simulation changes
2. Never modify confirmed mechanics in `constants.py` without explicit instruction
3. Use `MPLBACKEND=Agg` for headless matplotlib runs
4. Check `results.tsv` for prior simulation results before running new ones
5. Findings go in `findings/` — use BrickLayer finding format
