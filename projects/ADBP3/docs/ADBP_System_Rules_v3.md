# American Dream Benefits Program — System Rules v3
**Confidential | March 2026**
**Status: Updated to reflect confirmed model mechanics**

---

## Introduction

**Goal:** Restore the American Dream — enable families to thrive on one job / one income again, without needing two incomes, debt, or constant financial pressure.

The American Dream Benefits Program is a third-party consumer discount platform with voluntary payroll facilitation that delivers substantial purchasing power for essentials.

**Core Mechanism:** A closed-loop discount-credit system powered by Solana blockchain. Employees voluntarily purchase Discount Credits (utility tokens) with after-tax dollars.

> $1 = 1 credit = $2 in purchasing power at participating essential vendors (50% discount)

---

## Program Participants

- **Vendors** — essential businesses (groceries, utilities, rent, gas, etc.) that participate, employ participating employees, accept & recirculate credits
- **Employers** — businesses that participate, employ participating employees, accept & recirculate credits
- **Employees** — any person working for a participating employer who voluntarily participates
- **Program** — operates the Solana smart contracts, treasury, and platform

---

## System Rules

### Credit Purchase

- Employees purchase credits post-tax via embedded fiat on-ramp (bank card, ACH, Apple Pay)
- **$1.00 paid by employee = 1 credit minted = $2.00 purchasing power at vendors**
- The full **$1.00 purchase price flows to the treasury** — this is the primary funding mechanism
- Employees are limited to **5,000 credits per month**
- No general cash redemption — credits are non-redeemable for cash and stay in the closed loop

### Admin Revenue Pool

- A **10% fee** on all credit purchases is collected as admin revenue
- At $1.00/credit, this equals $0.10 per credit minted
- This fee does **not** flow to the treasury — it is tracked and distributed separately
- Distribution is **pro-rata by recirculation share**: the more credits a vendor or employer recirculates within the network, the larger their share of the admin revenue pool
- This replaces the prior flat $0.50/credit fee structure

> **Why pro-rata?** It directly incentivizes recirculation — participants who actively move credits through the network earn proportionally more. A vendor recirculating 10% of total credits earns 10% of the admin pool.

### Recirculation Rules

- Vendors decide the maximum credits they accept in a 12-month period (their recirculation %)
- Employers and vendors recirculate credits for any of their expenses **except** payroll, health insurance, childcare, and taxes — creating an accounting wash ($X foregone income offset by $X saved)
- The **recirculation-to-mint ratio is 2:1** — a vendor/employer that can recirculate 100,000 credits allows their employees to mint 50,000 total
- Credits are automatically recirculated at month-end on behalf of vendors and employers
- Velocity is pegged at **12× per year** (background constraint — no direct treasury cash flow)

### Burn Mechanic (Discretionary)

- Burns are **manual and discretionary** — no automatic per-transaction burn
- The treasury pays **$2.00 per credit burned** (the $2 fair market value of the credit)
- Burns are threshold-triggered: a burn is authorized when the backing ratio (`treasury_wallet / total_credits`) exceeds a target threshold
- **Affordability cap:** post-burn backing ratio must never fall below the 50% floor
  - Cap formula: `max_burnable = (wallet − 0.50 × total_credits) / (2.00 − 0.50)`
- **MC-optimal strategy** (confirmed via 20,000-run Monte Carlo):
  - Trigger: backing ≥ 114.6%
  - Size: 30.2% of outstanding credits per event
  - Cooldown: 8 months minimum between burns
  - First eligible: month 13 (ramp-up protection)
  - Result: 1 burn event over 10 years, 30.2% of credits destroyed, 77.7% final backing (HEALTHY)

> **Why $2/credit?** The credit provides $2 of purchasing power. Burning a credit extinguishes a $2 obligation. The treasury pays $2 to retire $1 of face-value liability — the difference is the amplification cost built into the burn mechanism.

### Treasury Mechanics

| Flow | Amount | Direction |
|------|--------|-----------|
| Credit purchase | $1.00/credit | → Treasury |
| Interest income | 4% APR on wallet balance (monthly) | → Treasury |
| Burn event | $2.00/credit burned | ← Treasury |
| Admin fee | $0.10/credit (10%) | → Admin pool (separate) |

Interest timing: `wallet[t] = wallet[t-1] + interest[t-1] + inflow[t]`
Then: `interest[t] = wallet[t] × (0.04 / 12)`

### Solvency Thresholds

| Status | Backing Ratio | Definition |
|--------|--------------|------------|
| HEALTHY | ≥ 75% | Treasury holds ≥ $0.75 per $1 of credit outstanding |
| WARNING | 50% – 74% | Solvent but under pressure |
| FAILURE | < 50% | Treasury cannot cover basic obligations |

Primary metric: `backing_ratio = treasury_wallet / total_credits_outstanding`
Secondary metric: `burn_coverage = treasury_wallet / (total_credits × $2.00)`

---

## Recirculation Flywheel

1. Employee buys credits → smart contract mints tokens → $1/credit to treasury
2. Employee spends at vendors → 50% discount applied (2× amplification)
3. Vendor receives tokens → recirculates to suppliers, utilities, etc.
4. Loop continues at 12× annual velocity
5. No credits exit for cash, ever
6. Admin revenue pool distributed monthly pro-rata by recirculation share

---

## What Was Removed vs. Prior Version

| Prior Rule | Status | Replacement |
|---|---|---|
| $0.50 treasury fee per credit | **Removed** | Full $1.00 goes to treasury |
| $0.50 flat admin fee to vendor | **Removed** | 10% pool, pro-rata distribution |
| $0.50 flat admin fee to employer | **Removed** | Included in 10% pool above |
| 1.774% per-transaction burn | **Removed** | No automatic burn — discretionary only |

---

## Employee Purchase Capacity (2025 Estimates)

| Business Type | Annual Revenue | Recirc % | Dollar Volume Capacity |
|---|---|---|---|
| Multifamily Housing | $600B | 23% | $138.0B |
| Food Store (Grocery) | $1,600B | 86% | $1,376.0B |
| Electric & Gas Utility | $550B | 64% | $352.0B |
| Water Utility | $72.5B | 57% | $41.3B |
| Internet Service Provider | $437B | 45% | $196.7B |
| Gas Station | $700B | 94% | $658.0B |
| Car Service Center | $199B | 65% | $129.4B |
| **TOTAL** | **$4.16T** | — | **$2.90T** |

Hard ceiling: $2.9T amplified annual employee purchase capacity.

---

## Compliance & Regulatory Posture

- **Non-custodial utility token on Solana** (closed-loop discount access)
- **No private currency risk** (Stamp Payments Act § 486) — decentralized, non-redeemable for cash, platform-specific. 2026 guidance on tokenized assets and GENIUS Act (2025) reinforce exemption.
- **No ERISA risk** — third-party platform, not employer-sponsored. Vendor/employer admin revenue is compensation for recirculation participation, not a welfare benefit.
- **No money transmission / CVC risk** — MSB partner handles fiat entry. Closed-loop, non-cash-convertible credits are explicitly distinguished from convertible virtual currency per FinCEN guidance.
- **No private scrip risk** — decentralized design, no public circulation, no fiat substitution.
- **Barter tax compliance** — automated 1099-B reporting at $2 FMV per credit.
- **Regional launch** — 1–3 states to start.

---

## Bottom Line

One job. One family. One future. A win-win system that turns a $60,000 salary into $84,000 of essential purchasing power — while financially incentivizing participating vendors and employers through pro-rata recirculation rewards — powered by Solana blockchain, modern UX, and built-in compliance.

---

*This document supersedes the v1/v2 model rules. Key changes: full treasury funding ($1.00/credit vs. $0.50), pro-rata admin revenue (vs. flat $0.50 fee), removal of 1.774% transaction burn, addition of discretionary threshold-triggered burn mechanic at $2.00/credit.*
