# Monte Carlo Campaign Findings — ADBP v3

**Date:** 2026-03-20
**Runs:** 20,000
**Duration per run:** 120 months (10 years)
**Seed:** 42 (reproducible)

---

## Parameter Space Sampled

| Parameter | Range | Distribution |
|---|---|---|
| BURN_TRIGGER_RATIO | 0.90 – 1.60 | Uniform |
| BURN_PCT | 2% – 35% | Uniform |
| BURN_MIN_COOLDOWN | 3 – 24 months | Uniform integer |
| BURN_FIRST_ELIGIBLE | 6 – 24 months | Uniform integer |

---

## Phase 1: Without Affordability Cap

| Verdict | Count | Rate |
|---|---|---|
| HEALTHY | 19,534 | 97.67% |
| WARNING | 0 | 0.00% |
| FAILURE | 466 | 2.33% |

### Failure Analysis

All 466 failures share the same root cause and timing:

- **All failed at month 120** — no early collapses whatsoever
- Wallet never went negative — failures were backing-ratio policy violations (backing < 50%), not bankruptcy
- Root cause: burn event triggered when backing was near threshold, but burn cost ($2/credit × large pct) pushed post-burn backing below the 50% floor

**Failure parameter signature:**
| Parameter | Failure runs |
|---|---|
| Trigger ratio | Mean 0.97×, median 0.97× (near 90–100%) |
| Burn pct | Mean 29.9%, median 30.1% (high — near max) |

**Why it happens mechanically:**
1. Backing ratio slowly climbs to ~0.97× (trigger met)
2. Burn fires: 30% of 14.5B credits = 4.35B credits × $2 = $8.7B cost
3. Wallet had ~$14.1B → post-burn = $5.4B
4. Post-burn backing: $5.4B / 10.15B credits = **0.53** — just above floor
5. But when trigger is 0.95× and burn is 33%: post-burn crashes to 0.43 → FAILURE

**The danger zone:** trigger < 1.00× AND burn_pct > 27% simultaneously.
At these combinations, the pre-burn backing is too thin relative to the burn cost.

---

## Phase 2: With Affordability Cap

Cap formula:
```
max_burnable = (wallet - FAILURE_THRESHOLD × total_credits) / (BURN_COST_PER_CREDIT - FAILURE_THRESHOLD)
```
This caps burn size so that post-burn backing never drops below 50%.

| Verdict | Count | Rate |
|---|---|---|
| HEALTHY | 17,180 | 85.90% |
| WARNING | 2,820 | 14.10% |
| FAILURE | 0 | 0.00% |

**Result: cap eliminates all failures.**

WARNING outcomes (14.1%) are cases where backing stays between 75–100% throughout — the system is financially sound but the backing ratio isn't climbing above the HEALTHY threshold by month 120. These are NOT failures.

---

## Burn Strategy Safe Zones

| Trigger ratio | HEALTHY rate | Behavior |
|---|---|---|
| >= 1.20× | 100% | Burns never fire in 10-year window |
| 1.10–1.20× | 93.5% | Occasional large burns, mostly HEALTHY |
| 1.00–1.10× | ~80% | Burns fire more often, more variation |
| < 1.00× | Risk zone | Requires cap; many WARNING outcomes |

| Burn pct | HEALTHY rate |
|---|---|
| <= 10% | ~100% | Very conservative, minimal liability reduction |
| 10–20% | ~95% | Safe range |
| 20–30% | ~88% | Good balance |
| > 30% | Risk zone | Requires cap to avoid floor breach |

---

## Optimal Strategies

### Aggressive — Maximum Liability Reduction

**Goal:** Destroy as many credits as possible while staying HEALTHY

| Parameter | Value |
|---|---|
| BURN_TRIGGER_RATIO | 1.146 (114.6%) |
| BURN_PCT | 0.302 (30.2%) |
| BURN_MIN_COOLDOWN | 8 months |
| BURN_FIRST_ELIGIBLE | month 13 |

**Result at month 120:**
- 1 burn event fires (month 120)
- 4.39B credits burned (30.2% of all minted)
- Burn cost: $8.77B
- Post-burn backing ratio: 77.69% (HEALTHY)
- Treasury wallet: $7.87B
- Min backing ever: 77.69% (the burn itself)
- **Verdict: HEALTHY**

### Conservative — Maximum Stability

**Goal:** Keep backing ratio pinned near 100%, many small burns

| Parameter | Value |
|---|---|
| BURN_TRIGGER_RATIO | 0.966 (96.6%) |
| BURN_PCT | 0.021 (2.1%) |
| BURN_MIN_COOLDOWN | 6 months |
| BURN_FIRST_ELIGIBLE | month 13 |

**Result at month 120:**
- 18 burn events fire
- ~12% of credits destroyed total
- Backing ratio stays pinned near 97–100%
- Min backing: ~97%
- **Verdict: HEALTHY**

### No Burns — Natural Growth Only

Set `BURN_TRIGGER_RATIO = 9.999` (trigger never fires in 10yr window).

**Result at month 120 (baseline):**
- 0 burn events
- Backing ratio climbs from 100% at month 1 → 114.5% at month 119
- Treasury wallet: $16.35B
- Total credits outstanding: 14.28B
- **Verdict: HEALTHY** (backing well above 75%)

---

## Key Insight: Baseline Is Naturally Healthy

Without ANY burns, the system reaches 114.5% backing by month 120. This means:
- The treasury accumulates surplus faster than credits are issued
- Interest income (4% APR on a growing wallet) compounds significantly
- By month 120, monthly interest alone ≈ $26.2M

The burn strategy is about **managing the surplus** (reducing future liability), not about maintaining solvency. The system is solvent by design as long as it's growing.

---

## What Burns Are Actually For

Burns reduce the total outstanding credit liability. Each credit burned:
- Removes $1 of face-value liability from the system
- Costs $2 from treasury (the $2 purchasing power the credit represents)
- Improves the ratio of treasury assets to outstanding obligations long-term

The optimal question is not "can we afford burns?" but "when and how much should we burn to efficiently manage the liability book?"

---

## Files

| File | Purpose |
|---|---|
| `monte_carlo.py` | Full MC engine, 20,000 runs, scoring, results output |
| `diagnose_failures.py` | Re-runs all 20,000 scenarios to extract and analyze the 466 failure cases |
| `simulate.py` | Final model using MC-optimal parameters (trigger 114.6%, burn 30.2%, cap active) |
| `constants.py` | Immutable system rules |
