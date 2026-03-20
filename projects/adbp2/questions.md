# Question Bank — ADBP v2

**Campaign type**: BrickLayer 2.0
**Generated**: 2026-03-19T00:00:00Z
**Modes selected**: diagnose, research, validate, predict, frontier

**Mode selection rationale**:
- `diagnose` — The baseline simulation produces a persistent STRAINED verdict across all 60 months because CRR never reaches the burn gate (1.0). This is partially by design but the simulation also has structural gaps (no treasury wallet, admin fee logic needs scrutiny, CRR math during simultaneous mint+fee steps) that warrant systematic investigation before any scenario optimization.
- `research` — Multiple critical assumptions lack external validation: employee participation rate (~2,000 tokens/month), vendor acceptance scale, regulatory classification of a fixed-value utility credit, and competitive landscape of B2B loyalty/credit instruments.
- `validate` — Three architectural claims are being relied upon without verification: (1) that per-token escrow growth is truly scale-invariant, (2) that admin fee deduction from fee revenue (not escrow) is correctly modeled, and (3) that the VENDOR_CAPACITY_PER_EMPLOYEE multiplier is realistic.
- `predict` — Two known failure boundaries exist (CRR_MINT_PAUSE at 0.40, CRR_CRITICAL at 0.35). Understanding what cascades from a CRR drop toward those thresholds — and how quickly a slow-growth scenario could arrive there — is necessary before the system is deployed.
- `frontier` — The closed-loop B2B auto-cycle mechanism is novel. There may be structural improvements (dynamic fee scaling, treasury separation, tiered burn schedules) that the current model is not exploring.

No `audit` mode — project-brief.md explicitly excludes regulatory analysis from scope (though research questions probe the boundary). No `evolve` or `benchmark` modes — baseline performance is not yet healthy enough to optimize.

---

## Wave 1

---

### D1.1: Does the simulation correctly model escrow backing growth as scale-invariant, or does rapid employee growth dilute per-token escrow because new mints add $1 of escrow against $2 of new obligation simultaneously?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: Each new month, minting adds circulating_tokens × MINT_PRICE to escrow while adding circulating_tokens × TOKEN_FACE_VALUE to obligations — a net dilution of (TOKEN_FACE_VALUE - MINT_PRICE) × new_tokens per month. During high-growth phases (months 20–50 where employee count grows 10x–20x), this dilution force may be larger than the fee+interest inflow, actively suppressing CRR rather than letting it rise. The project-brief claims fee-based escrow growth is "constant regardless of scale" but that claim applies to per-token growth from fees — not the simultaneous dilution from new mints.
**Agent**: diagnose-analyst
**Success criterion**: A per-month breakdown showing: (a) escrow inflow from fees+interest, (b) CRR dilution from new mints, and (c) net CRR delta for each month — confirming whether dilution consistently dominates during high-growth phases.

---

### D1.2: Does the admin fee calculation correctly prevent admin fees from exceeding total fee revenue, and does the current $0.01–$0.05 cap produce rational behavior at both low employee counts (month 1–3) and high employee counts (month 50–60)?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: At month 1 with 100 employees and ~200,000 tokens, fee_revenue = $4,500 and admin_fees_paid = $0.01 × 200,000 = $2,000 — consuming 44% of fee revenue. By month 60 with 5M employees and ~10B tokens, the capped $0.05 × tokens would vastly exceed fee_revenue, so admin_fee_per_token should collapse to ADMIN_FEE_FLOOR. The concern is whether the `affordable = fee_revenue / circulating_tokens` computation at early scale produces an admin_fee_per_token below the floor, and whether the `min(admin_fee_per_token * circulating_tokens, fee_revenue)` guard actually fires at any point.
**Agent**: diagnose-analyst
**Success criterion**: A trace of admin_fee_per_token and admin_fees_paid / fee_revenue ratio across all 60 months, confirming the guard logic fires correctly and escrow inflow is never negative.

---

### D1.3: Does the simulation's treatment of "no treasury wallet" mean all surplus escrow (escrow_net) is permanently locked in the escrow pool and unavailable for operational costs, and does this omission create a false picture of system profitability?

**Status**: PENDING
**Mode**: diagnose
**Priority**: HIGH
**Hypothesis**: The simulation tracks `escrow_net = escrow_pool - (circulating_tokens × TOKEN_FACE_VALUE)` as the buffer above obligations, but this surplus is still inside the escrow pool — not in a separately accessible treasury. Real-world operations require a treasury from which salaries, infrastructure, and BD costs are paid. If escrow_net represents surplus that is structurally inaccessible, then the system has zero mechanism to fund operations until burns activate and surplus escrow is explicitly siphoned to treasury. The simulation does not model this split, which means all "STRAINED but solvent" months may be hiding an operational funding crisis.
**Agent**: diagnose-analyst
**Success criterion**: A clear description of how the simulation handles treasury vs. escrow separation, whether escrow_net is operationally accessible, and what the actual operational funding timeline looks like under the baseline scenario.

---

### D1.4: At month 60 with 5,000,000 employees each minting 2,000 tokens/month, does the CAPACITY_RATIO constraint (tokens ≤ 50% of vendor capacity) actually bind, and if vendor capacity is set to 3,000 tokens/employee, what is the maximum circulating supply the model allows vs. what the growth curve demands?

**Status**: PENDING
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: Month 60 maximum vendor capacity = 5,000,000 employees × 3,000 tokens = 15,000,000,000. Capacity headroom at 50% = 7,500,000,000 tokens. Monthly mint demand = 5,000,000 × 2,000 = 10,000,000,000 tokens/month. With auto-cycle burning none of them (CRR < 1.0 throughout), circulating_tokens accumulates monthly. By month 20–30, circulating_tokens may exceed the capacity ceiling, forcing capacity_headroom = 0 and halting new mints — effectively preventing system growth without the simulation raising a FAILURE verdict.
**Agent**: diagnose-analyst
**Success criterion**: The month at which circulating_tokens first hits or approaches the capacity ceiling, and what the simulation's behavior is when capacity_headroom reaches 0.

---

### D1.5: Does the dynamic_burn_rate function correctly return 0 for all months where CRR < 1.0, and is there any code path where burn_rate could be non-zero despite CRR being below BURN_ELIGIBLE_CRR?

**Status**: PENDING
**Mode**: diagnose
**Priority**: MEDIUM
**Hypothesis**: The burn guard `if crr >= BURN_ELIGIBLE_CRR` in run_simulation() should prevent any burn. However, dynamic_burn_rate() uses `normalized = (crr - BURN_ELIGIBLE_CRR) / (CRR_OVERCAPITALIZED - BURN_ELIGIBLE_CRR)` with a `max(0.0, ...)` clamp — if called with crr < 1.0 it would return BURN_RATE_FLOOR (0.02). The guard should prevent this call, but the interaction between the outer guard and the inner clamp warrants explicit verification. Any accidental burn when CRR < 1.0 would violate a core system invariant.
**Agent**: diagnose-analyst
**Success criterion**: Confirmation that zero tokens are burned in any month where CRR < 1.0 throughout all 60 months, with the specific code path traced.

---

### R1.1: What is the actual participation rate for voluntary employer-sponsored credit and purchasing benefit programs, and does the assumed 2,000 tokens/month/employee (~$2,000/month in purchasing volume) reflect realistic behavior?

**Status**: PENDING
**Mode**: research
**Priority**: HIGH
**Hypothesis**: The $45/month fee + $2,000/month in token spending implies employees are routing a significant share of discretionary spend through the system. Comparable programs (commuter benefits, FSAs, corporate discount programs) typically see 20–40% voluntary participation and average utilization well below maximums. If actual per-employee token volume is 500 tokens/month rather than 2,000, fee-based escrow growth rates drop 75% and the burn gate timeline extends substantially beyond 60 months.
**Agent**: research-analyst
**Success criterion**: At least 3 comparable programs (commuter benefits, FSA, corporate discount/loyalty schemes) with documented participation rates and average utilization per enrolled employee. A calibrated estimate for realistic token volume per employee.

---

### R1.2: How do US financial regulators (FinCEN, SEC, CFTC) currently classify closed-loop utility credit instruments with fixed face value, non-redeemable for cash, auto-cycling B2B with a burn mechanism — and has any analogous system faced enforcement action?

**Status**: PENDING
**Mode**: research
**Priority**: HIGH
**Hypothesis**: The system's fixed $2 face value and non-redeemability for cash likely exempts it from most money transmission and securities laws under existing closed-loop exemptions (similar to gift cards, arcade tokens, or corporate scrip). However, the $1→$2 amplification feature (employees receive 2x purchasing power) may attract scrutiny as a form of unlicensed credit or consumer financial product, particularly if the platform grows to millions of users. The burn mechanism also creates a deflationary property that could be analogized to a commodity instrument.
**Agent**: research-analyst
**Success criterion**: A regulatory classification assessment covering FinCEN MSB rules, SEC Howey test, CFTC commodity analysis, and any state money-transmitter licensing obligations. Identification of at least one analogous instrument that has received regulatory guidance or faced action.

---

### R1.3: What is the realistic vendor acceptance network build timeline, and what is the minimum vendor network size and geographic distribution needed to make a $2,000/month per-employee spending level achievable?

**Status**: PENDING
**Mode**: research
**Priority**: HIGH
**Hypothesis**: The simulation assumes vendor capacity of 3,000 tokens per employee in the system — implicitly assuming a robust vendor network scales with employee enrollment. In practice, vendor recruitment is a separate sales motion that typically lags employee onboarding by 6–18 months. If vendor capacity is only 500 tokens/employee during the first 24 months (the critical CRR-building phase), minting is capacity-constrained and fee income drops dramatically, preventing CRR from rising toward the burn gate.
**Agent**: research-analyst
**Success criterion**: Comparable B2B network build timelines (corporate card programs, gift card networks, FSA vendor networks), a realistic vendor capacity ramp model for the first 24 months, and its impact on simulation inputs.

---

### R1.4: Are there analogous closed-loop B2B credit recycling systems that have operated at scale, and what were their key failure modes?

**Status**: PENDING
**Mode**: research
**Priority**: MEDIUM
**Hypothesis**: The closest analogues are corporate scrip systems (company towns), B2B barter exchange networks (ITEX, BizX), and corporate loyalty point networks (airline miles, hotel points). Scrip systems historically failed due to regulatory bans (federal scrip prohibition in 1938) or employer insolvency. Barter networks face liquidity problems when supply-demand imbalances emerge. The ADBP auto-cycle mechanism is novel but the failure modes of its analogues (liquidity crises, regulatory intervention, network collapse on key participant exit) are directly applicable.
**Agent**: research-analyst
**Success criterion**: At least 2 historical analogues analyzed for failure modes, with explicit mapping of each failure mode to whether/how the ADBP mechanism is exposed to or insulated from it.

---

### V1.1: Does the claim that "per-token escrow growth from fees is constant regardless of system scale" hold mathematically under the actual simulation logic, specifically when EMPLOYEE_FEE_MONTHLY and admin fee deduction interact with a growing circulating supply?

**Status**: PENDING
**Mode**: validate
**Priority**: HIGH
**Hypothesis**: The project-brief states: "per-token escrow growth rate from fees = (fee × fee_to_escrow_pct) / 2000 — this is CONSTANT regardless of system scale." But the simulation does NOT use a fee_to_escrow_pct parameter — it deducts admin fees from fee_revenue and routes the remainder to escrow. As circulating_tokens grows and admin_fee_per_token is capped at $0.05, the admin fee extraction rate as a percentage of total fee revenue changes with scale. This means the per-token net escrow contribution from fees is not actually constant — it depends on the ratio of (admin fee per token × circulating tokens) to (employee count × fee). Validate whether this invariant holds in the simulation code as written.
**Agent**: design-reviewer
**Success criterion**: A mathematical derivation confirming or refuting per-token fee escrow contribution constancy across three scale points (month 1, month 30, month 60) using actual simulation variable values.

---

### V1.2: Does the growth curve extrapolation in build_growth_curve() produce a realistic employee count trajectory from month 14 onward, and is the exponential interpolation from 250,000 to 5,000,000 over 47 months achievable?

**Status**: PENDING
**Mode**: validate
**Priority**: MEDIUM
**Hypothesis**: The GROWTH_CURVE constant defines 13 monthly checkpoints ending at 250,000 employees in month 13. The remaining 47 months are extrapolated exponentially to reach 5,000,000. The implied CAGR for months 13–60 is (5,000,000 / 250,000)^(12/47) - 1 ≈ 73% annual growth sustained for nearly 4 years. This is an extremely aggressive enterprise B2B growth curve — comparable to top-decile SaaS companies. Validate whether this growth profile is internally consistent with the vendor capacity model (vendors must scale proportionally) and whether slower growth curves produce meaningfully different CRR trajectories.
**Agent**: design-reviewer
**Success criterion**: The implied annual growth rates by phase, comparison to at least one real comparable growth benchmark, and a simulation run at 50% of the baseline growth rate showing the CRR trajectory difference.

---

### V1.3: Does the simulation correctly implement the invariant that the first B2B spend has no burn (only an admin fee from escrow), or is every monthly auto-cycle treated identically regardless of whether a token is on its first or subsequent B2B transaction?

**Status**: PENDING
**Mode**: validate
**Priority**: HIGH
**Hypothesis**: The project-brief states "First spend has no burn — only an admin fee released from escrow." However, the simulation models all tokens in a single pool with no per-token lifecycle tracking — it applies the same burn logic (CRR-gated, rate-scaled) to all circulating tokens uniformly each month. If the "first spend no burn" invariant is a real system rule, the simulation violates it by never distinguishing freshly minted tokens from re-cycled tokens. This would overstate burns when burns do activate and could affect the CRR trajectory in later months.
**Agent**: design-reviewer
**Success criterion**: A clear statement of whether the simulation intentionally approximates this per-token rule at the pool level, whether that approximation is valid given the monthly auto-cycle cadence, and whether implementing per-token lifecycle tracking would materially change the CRR trajectory.

---

### P1.1: If employee growth stalls at 500,000 employees (month 20 equivalent) and no new employees join for 12 months, does the CRR trajectory move toward or away from the burn gate, and does the system reach MINT_PAUSED or INSOLVENT status?

**Status**: PENDING
**Mode**: predict
**Priority**: HIGH
**Hypothesis**: With a fixed employee base, fee income stabilizes but circulating_tokens continues to accumulate (no burns below CRR 1.0). As circulating supply grows toward the vendor capacity ceiling, capacity_headroom eventually forces new_tokens to 0. At that point fee revenue is constant, interest accrues on a fixed escrow pool, and CRR climbs slowly. The growth stall scenario may actually be better for CRR than continued hypergrowth, because hypergrowth dilutes per-token escrow faster than fees can compensate. Validate this hypothesis.
**Agent**: cascade-analyst
**Success criterion**: CRR trajectory for a 12-month growth stall at 500,000 employees (months 20–32), showing whether CRR rises, falls, or plateaus, and whether any MINT_PAUSED or INSOLVENT verdict occurs.

---

### P1.2: If the employee fee is cut from $45/month to $20/month (representing competitive pressure or employer resistance), what is the CRR trajectory across 60 months, and at what fee level does the system enter MINT_PAUSED territory?

**Status**: PENDING
**Mode**: predict
**Priority**: HIGH
**Hypothesis**: At $45/month fee with 100% flowing to escrow (minus admin fees), the simulation produces STRAINED but solvent. At $20/month fee, escrow inflow drops ~56% while the dilution from new mints is unchanged. The CRR trajectory likely trends downward faster than the admin fee extraction rate changes, potentially pushing the system toward CRR_MINT_PAUSE (0.40) in high-growth phases. The minimum viable fee to maintain CRR >= CRR_OPERATIONAL_TARGET (0.65) throughout 60 months is a critical business design parameter.
**Agent**: cascade-analyst
**Success criterion**: CRR trajectories for $20, $30, $45, and $60/month fee scenarios, identification of the minimum fee that keeps CRR above CRR_OPERATIONAL_TARGET (0.65) throughout all 60 months, and the first month where CRR_MINT_PAUSE is breached at the $20 scenario.

---

### P1.3: What happens to the system if 20% of participating employees exit simultaneously (mass employer offboarding) while remaining employees continue normal minting — does the circulating token pool contract fast enough to prevent a CRR collapse?

**Status**: PENDING
**Mode**: predict
**Priority**: MEDIUM
**Hypothesis**: Employee exit reduces fee income immediately but circulating tokens do not exit — tokens issued to departing employees' accounts continue cycling until burned. With CRR < 1.0 and no burns, exited-employee tokens remain in circulation permanently, diluting CRR. A 20% employee exit would reduce monthly fee income by 20% but NOT reduce the circulating token pool, causing a net CRR decline. Combined with the remaining employees' continued minting, the CRR compression could be severe. The system has no mechanism to force-burn or cancel tokens belonging to exited employees.
**Agent**: cascade-analyst
**Success criterion**: CRR trajectory after a sudden 20% employee exit at month 30, showing the delta versus baseline, whether the system recovers, and whether MINT_PAUSED or INSOLVENT status is reached.

---

### FR1.1: What would a treasury separation mechanism look like in this model — where a portion of the escrow surplus above a target CRR is routed to a separate operational treasury each month — and does adding this mechanism change the minimum fee required to sustain the system?

**Status**: PENDING
**Mode**: frontier
**Priority**: MEDIUM
**Hypothesis**: The current simulation has no treasury extraction mechanism — all fee income above admin fees flows to escrow, and escrow_net represents surplus that is structurally inaccessible. A viable real-world system needs to extract operational funding without breaching the escrow floor. A "surplus siphon" — routing (escrow_net - CRR_buffer × circulating × face_value) to treasury each month only when CRR exceeds a comfortable threshold — could allow sustainable operations without destabilizing the escrow pool. This mechanism might also accelerate burn activation by capping maximum CRR.
**Agent**: frontier-analyst
**Success criterion**: A proposed treasury extraction formula with threshold triggers, its impact on the CRR trajectory, and whether it changes the month of first burn activation under the baseline fee scenario.

---

### FR1.2: Is there a fee structure design — dynamic, tiered, or milestone-based — that accelerates the CRR trajectory to reach the burn gate by month 36 instead of month 55–60, without requiring employer fee increases beyond $75/month?

**Status**: PENDING
**Mode**: frontier
**Priority**: MEDIUM
**Hypothesis**: The current flat $45/month fee structure is suboptimal for CRR building because it treats all growth phases identically. A front-loaded fee structure (higher fees in months 1–24 when CRR building is critical, lower fees after burn activation reduces treasury dependence on fees) might accelerate burn activation while reducing long-term employer cost. Alternatively, a "founding employer" incentive (discounted fees in exchange for higher upfront escrow contribution) might seed the pool more efficiently than monthly fees alone.
**Agent**: frontier-analyst
**Success criterion**: At least two alternative fee structure designs with modeled CRR trajectories showing the first burn activation month, compared against the $45/month flat baseline. Each design must stay within $75/month maximum fee and maintain CRR >= CRR_OPERATIONAL_TARGET throughout.

---

### FR1.3: Could the ADBP system operate with a self-adjusting burn threshold — where BURN_ELIGIBLE_CRR adapts downward over time as the system proves solvency — and what invariants would need to hold for this to be safe?

**Status**: PENDING
**Mode**: frontier
**Priority**: LOW
**Hypothesis**: The fixed CRR 1.0 burn gate is conservative by design — it requires the escrow pool to equal 100% of all token face value obligations before any burns can occur. An adaptive threshold (starting at 1.0 for the first 24 months, then stepping down to 0.85 as the system demonstrates stable operations, then 0.75 at month 48) would activate burns earlier, reducing circulating supply growth and relieving vendor capacity pressure. The risk is that early burn activation reduces escrow depth, making the system more vulnerable to sudden CRR shocks. Explore what safety invariants would need to hold.
**Agent**: frontier-analyst
**Success criterion**: A design sketch of an adaptive burn threshold schedule, with the CRR trajectory and first-burn month under each schedule, plus an explicit list of safety invariants that must hold (e.g., minimum escrow buffer, maximum burn rate at reduced threshold) for this to be sound.
