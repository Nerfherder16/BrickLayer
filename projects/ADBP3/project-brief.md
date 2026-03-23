# Project Brief — ADBP v3 (Reserve-Backed Credit System)

<!-- Highest-authority source. Agents treat every statement here as ground truth. -->
<!-- Last updated: 2026-03-20 — reflects confirmed mechanics after MC campaign -->

---

## What this system actually does

ADBP is a reserve-backed credit platform where employers mint tokens (credits) for employees on a monthly basis. Employees pay $1 per credit and receive $2 of purchasing power at participating vendors — a 50% discount amplification built into the credit's face value. The treasury holds the $1 inflow and accrues interest; it never redeems credits for cash. Credits can only leave the system via **discretionary burns**, which cost the treasury $2 per credit destroyed.

The system's central health metric is the **backing ratio**: `treasury_wallet / total_credits_outstanding`. This measures how many dollars the treasury holds per $1 of credit face value.

---

## Confirmed Mechanics (ground truth — do not re-derive)

### Treasury inflow
- Employee pays **$1.00 per credit** → full $1.00 goes to treasury wallet
- Treasury collects 100% of credit purchase price. No split. No admin cut from treasury.

### Interest
- Treasury wallet earns **4% APR**, compounded monthly (`monthly_rate = 4%/12 = 0.3333%`)
- Interest timing: prior-period interest is added to wallet at start of next period, then new inflow is added
- Formula: `wallet[t] = wallet[t-1] + interest[t-1] + inflow[t]`; then `interest[t] = wallet[t] × 0.003333`

### Admin revenue (separate from treasury)
- A **10% fee** on every credit purchase generates admin revenue
- This fee is tracked separately — it does NOT flow into the treasury wallet
- Distribution: pro-rata by vendor/employer recirculation share (the more credits a vendor/employer recirculates, the larger their share)
- At month 120 baseline: cumulative admin revenue ≈ $1.45B vs. $7.87B treasury wallet

### Burns (discretionary, threshold-triggered)
- Burns are **manual and discretionary** — not automatic, not transaction-based
- Treasury pays **$2.00 per credit burned** (this is the $2 FMV of the credit)
- Burns are triggered when the backing ratio exceeds a target threshold
- MC-optimal strategy: trigger at **114.6%** backing, burn **30.2%** of outstanding credits
- Affordability cap: post-burn backing ratio must never fall below **50%** (failure threshold)
- Cap formula: `max_burnable = (wallet - floor × total_credits) / (burn_cost_per_credit - floor)`

### No cash redemption
- Credits are **never redeemed for cash** by employees or vendors
- The only USD outflow from treasury is burn events
- Credits circulate within the closed B2B network at 12× annual velocity

### Employee growth
- Linear: `employees[t] = 1,000 + (t-1) × 1,000` (1K at month 1, 120K at month 120)
- Credits per employee: **2,000/month** (hard cap: 5,000/month)

---

## What the old spreadsheet got wrong (resolved)

| Old assumption | Correct understanding |
|---|---|
| Three fixed-date burns (months 13, 25, 37) at hardcoded sizes | Burns are discretionary and threshold-triggered — the fixed dates were an early estimate |
| $0.50 admin fee split to treasury | No admin fee to treasury; 10% employee fee goes to vendor/employer pool |
| Employee fee (10%) was display-only, not wired | 10% fee is real revenue — just tracked separately from treasury |
| Credits might be redeemable for cash | No cash redemption. Ever. Only treasury outflow is burns. |
| Unclear amplification math | Confirmed: $1 in → $2 purchasing power → $2 cost if burned |

---

## MC Campaign Findings (20,000 runs, 120 months, seed=42)

### Before affordability cap (original MC)
- HEALTHY: 97.67% | WARNING: 0.0% | FAILURE: 2.33% (466 runs)
- All 466 failures occurred at month 120 (not early collapse)
- Root cause: LOW trigger ratio (near 90%) + HIGH burn pct (27–35%) → post-burn backing crashed below 50%
- Wallet never went negative — failures were policy violations, not bankruptcy

### After affordability cap
- HEALTHY: 85.9% | WARNING: 14.1% | FAILURE: 0.0%
- Cap formula prevents post-burn backing from ever breaching the 50% floor
- WARNING outcomes are cases where backing ratio stays between 75–100% (healthy but not optimal)

### Safe zones (confirmed)
- Trigger >= 1.20×: 100% HEALTHY — trigger never fires in 10-year window, no burns
- Trigger >= 1.10×: 93.5% HEALTHY (with cap)
- Burn pct <= 10%: 100% HEALTHY (very low risk, minimal liability reduction)
- Danger zone: trigger < 1.00× AND burn pct > 25% simultaneously

### Optimal strategy (MC best score — maximize liability reduction while staying HEALTHY)
| Parameter | Value | Result |
|---|---|---|
| BURN_TRIGGER_RATIO | 1.146 (114.6%) | 1 burn fires at month 120 |
| BURN_PCT | 0.302 (30.2%) | 4.39B credits destroyed |
| BURN_MIN_COOLDOWN | 8 months | — |
| BURN_FIRST_ELIGIBLE | month 13 | Ramp-up protection |
| Min backing ratio | 77.69% | Well above 75% WARNING threshold |
| Verdict | HEALTHY | — |

### Conservative strategy (maximum stability)
| Parameter | Value | Result |
|---|---|---|
| BURN_TRIGGER_RATIO | 0.966 (96.6%) | 18 small burns |
| BURN_PCT | 0.021 (2.1%) | 12% of credits destroyed |
| Backing behavior | Pinned near 97–100% | Very stable |

---

## The numbers that cannot be wrong

| Fact | Value | Source |
|------|-------|--------|
| Credit purchase price | $1.00/credit | Confirmed |
| Treasury inflow per credit | $1.00 (full price) | Confirmed |
| Burn cost per credit | $2.00 (FMV) | Confirmed |
| Monthly interest rate | 4% APR ÷ 12 = 0.3333% | Confirmed |
| Employee fee rate | 10% of credits minted | Confirmed (separate from treasury) |
| Credits per employee (base) | 2,000/month | Confirmed |
| Credits per employee (cap) | 5,000/month | Hard cap |
| Employee growth | +1,000/month linear | Confirmed |
| Annual B2B velocity | 12× | Background context only |
| Failure threshold | backing < 50% | Confirmed |
| Warning threshold | backing < 75% | Confirmed |
| Credit FMV for tax | $2.00 | From legal doc |

---

## What this system is NOT

- Not a cryptocurrency or speculative token — credits are pegged to real USD reserves
- Not a fractional-reserve bank — backing ratio is meant to stay near or above 100%
- Not a cash redemption system — credits never convert back to dollars for employees
- Not a live system — model stress-tested; implementation pending
- Not a fully autonomous burn system — burns remain discretionary decisions

---

## Research scope (remaining open questions)

**Already answered by MC campaign:**
- ✅ What parameter combinations cause failure? → LOW trigger + HIGH burn pct simultaneously
- ✅ Can affordability cap eliminate all failures? → Yes, 0.0% failure rate confirmed
- ✅ What is the optimal burn strategy? → Trigger 114.6%, burn 30.2%, cooldown 8mo

**Still open:**
- What minimum interest rate keeps the system HEALTHY at baseline growth?
- What happens if employee growth stalls (plateaus instead of +1,000/month)?
- At what employee count does monthly interest income exceed monthly minting inflow?
- What if credits-per-employee behavior shifts (lower engagement, higher cap usage)?
- Long-term (months 121–240): does backing ratio continue climbing without burns?
- Regulatory classification risk for stored-value / closed-loop credit instruments
- Admin revenue economics: is 10% competitive vs. comparable employee benefit programs?
- Concentration risk: single large employer (>30% of credits) exits unexpectedly

## Documents in docs/ and their authority

| File | Authoritative for |
|------|------------------|
| `ADBP_Final_Model_Legal.pdf` | Legal structure, FMV definition, velocity, network rules |
| `design-philosophy.md` | System design intent and philosophy |
