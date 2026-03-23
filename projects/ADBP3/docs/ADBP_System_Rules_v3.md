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

> **Why pro-rata?** It directly incentivizes recirculation — participants who actively move credits through the network earn proportionally more. A vendor recirculating 10% of total credits earns 10% of the admin pool.

### Recirculation Rules

- Vendors decide the maximum credits they accept in a 12-month period (their recirculation %)
- Employers and vendors recirculate credits for any of their expenses **except** payroll and taxes — creating an accounting wash ($X foregone income offset by $X saved)
- The **recirculation-to-mint ratio is 2:1** — a vendor/employer that can recirculate 100,000 credits allows their employees to mint 50,000 total
- Credits are automatically recirculated at month-end on behalf of vendors and employers
- Velocity is pegged at **12× per year** 

### Burn Mechanic (Discretionary)

- Burns are **manual and discretionary** — no automatic per-transaction burn
- The treasury pays **$2.00 per credit burned** (the $2 fair market value of the credit)
- Burns are threshold-triggered: a burn is authorized when the backing ratio (`treasury_wallet / total_credits`) exceeds a target threshold
- **Affordability cap:** post-burn backing ratio must never fall below the 50% floor
  - Cap formula: `max_burnable = (wallet − 0.50 × total_credits) / (2.00 − 0.50)`
- **MC-optimal strategy** (confirmed via 300,000-run Monte Carlo — 3 seeds × 100,000 runs × 240 months):
  - Trigger: backing ≥ 133.2%
  - Size: 34.9% of outstanding credits per event
  - Cooldown: 18 months minimum between burns
  - First eligible: month 20 (ramp-up protection)
  - Result: 1 burn event over 20 years, 34.9% of credits destroyed, 97.3% final backing (HEALTHY)
  - Seed stability: 85.63% – 85.75% HEALTHY across all seeds (fully converged, 0.12pp spread)
  - FAILURE rate: 0.00% across all 300,000 runs (structural solvency guarantee — see below)

> **Why $2/credit?** The credit provides $2 of purchasing power. Burning a credit extinguishes a $2 obligation. The treasury pays $2 to retire $1 of face-value liability — the difference is the amplification cost built into the burn mechanism.

### Structural Solvency Guarantee

The system carries a **mathematical identity** that prevents treasury failure in the absence of burn events:

> `treasury_wallet = Σ(inflows) + interest ≥ Σ(credits_minted × $1.00) = total_credits_outstanding`

Because every credit minted adds exactly $1.00 to the treasury, and interest only adds further, the backing ratio cannot fall below 100% without an explicit burn. This is confirmed by stress tests across all parameter combinations: zero-interest, 75% employee loss, extreme CPE, and combined adversity all return minimum backing of exactly 100.0%.

Implications:
- **FAILURE (< 50% backing) is structurally impossible** from market conditions alone
- Burns are the only mechanism that can reduce backing below 100% — the affordability cap (`max_burnable = (wallet − 0.50 × total_credits) / 1.50`) mathematically prevents post-burn backing from dropping below 50%
- WARNING states (50–74%) can only be reached by a burn event, and only if burn parameters are set aggressively — the MC-optimal strategy never enters WARNING

### Credit Expiry

Credits carry a **velocity of 12× per year** — each credit cycles through the network approximately monthly. Programs at this velocity observe annual breakage (inactivity-driven non-redemption) of approximately **5–7%**.

**Expiry mechanics:**

- **Cohort expiry**: Credits issued in month T expire at month T + window. Recommended window: **36 months** (legally defensible under CARD Act precedent for non-financial instruments, operationally consistent with similar closed-loop platforms)
- **Breakage rate**: Credits not redeemed within any rolling period are removed from circulation at **$0 cost** to treasury (the $1 inflow was already collected; the $2 obligation simply terminates)
- **Economic impact**: Expiry is strictly more treasury-efficient than burns — $0/credit vs $2/credit. Expiry causes backing ratio to climb faster, which in turn triggers more frequent burns and higher total credit destruction

**Research baselines for expiry windows:**

| Program Type | Typical Window | Notes |
|---|---|---|
| Gift cards (CARD Act) | 5 years minimum | Statutory floor for consumer protection |
| Closed-loop corporate perks | 24–36 months | Standard practice; legally defensible |
| Loyalty / rewards points | 12–24 months inactivity | Forfeiture on inactivity, not calendar expiry |
| Commuter / FSA benefits | Monthly rolling | Strict regulatory use-it-or-lose-it |
| **ADBP (recommended)** | **36 months** | Generous, consumer-friendly, aligns with essential-spending context |

**Expiry + burn combined scenario** (36mo window, 6% annual breakage, MC-optimal burns):
- 5 burn events over 10 years
- 66.4% of all credits ever minted destroyed (expiry + burns combined)
- 99.1% final backing (HEALTHY)

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

1. Employee buys credits → smart contract mints tokens → $1/credit to treasury → $0.10/ credit to escrow
2. Employee spends at vendors → 50% discount applied (2× amplification)
3. Vendor receives tokens → recirculates to suppliers, utilities, etc.
4. Loop continues at 12× annual velocity
5. No credits exit for cash, ever
6. Admin revenue pool distributed monthly pro-rata by recirculation share from escrow wallet

## Essential Businesses (Vendors)

 1. Health Insurance Providers
 2. Gas Stations
 3. Grocery Stores
 4. Rental Housing
 5. Internet Service Provider
 6. Electric and Gas Utilities
 7. Water Utilities
 8. Childcare Facilities
 9. Car Service (Repairs)

---

## Compliance & Regulatory Posture

•	Non-custodial utility token on Solana (closed-loop discount access).
•	No private currency risk under Stamp Payments Act (§ 486) - decentralized, no centralized issuer. Credits are utility tokens in a closed-loop system, non-redeemable for cash, decentralized on Solana, and not intended as general currency. 2026 guidance on tokenized assets distinguishes utility tokens from scrip if they are platform-specific and non-convertible. The GENIUS Act (2025) for stable coins explicitly exempts non-currency digital assets, reinforcing this.
•	No ERISA risk - third-party platform, not employer-sponsored. No welfare benefit triggers like health insurance or childcare. Vendors and employers earn a fair market value fixed admin fee for offering a discount and recirculating credits.
•	No money transmission / CVC risk - MSB partner handles fiat entry. Per FinCEN's longstanding guidance, convertible virtual currency (CVC) is virtual currency that either has an equivalent value in real currency or acts as a substitute for it. Closed-loop systems where credits cannot exit for cash are explicitly distinguished from CVC.
•	No private scrip risk - the Stamp Payments Act targets private currencies that compete with fiat, not closed-loop discounts. Decentralized, blockchain-based utility tokens without cash equivalence or broad circulation are generally exempt. Credits recirculate indefinitely but only for essentials among participants - no public circulation or fiat substitution outside the loop. The decentralized design (no central issuer) further reduces risk.
•	Barter tax compliance - automated 1099-B reporting at $2 FMV per credit.
•	Regional launch - NJ to start with regional expansion as the business grows.

## Bottom Line

One job. One family. One future. A win-win system that can turn a $60,000 salary into a potential $120,000 of essential purchasing power while financially incentivizing the vendor or employer - powered by Solana blockchain, modern UX, and built-in compliance.
Ready to launch regionally and scale responsibly.
