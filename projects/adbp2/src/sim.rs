use crate::params::SimParams;

/// A single month's simulation record — mirrors Python's records.append({...}) dict.
#[derive(Debug, Clone)]
pub struct MonthRecord {
    pub month: usize,
    pub employees: i64,
    pub new_tokens_minted: f64,
    pub circulating_tokens: f64,
    pub escrow_pool: f64,
    pub escrow_net: f64,
    pub per_token_escrow: f64,
    pub crr: f64,
    pub burn_rate_pct: f64,
    pub tokens_burned: f64,
    pub reimbursements_paid: f64,
    pub operator_revenue: f64,
    pub fee_revenue: f64,
    pub interest_escrow: f64,
    pub total_capacity: f64,
    pub capacity_utilization_pct: f64,
    pub minting_paused: bool,
    pub verdict: String,
}

/// Result of a single simulation run.
#[derive(Debug, Clone)]
pub struct SimResult {
    pub records: Vec<MonthRecord>,
    pub failure_reason: Option<String>,
}

/// Aggregated evaluation result — mirrors Python's evaluate() return dict.
#[derive(Debug, Clone)]
pub struct EvalResult {
    pub primary_metric: f64,
    pub verdict: String,
    pub failure_reason: String,
    pub final_crr: f64,
    pub final_escrow_net: f64,
    pub final_employees: i64,
    pub first_burn_month: Option<usize>, // None = "never"
    pub peak_crr: f64,
    pub peak_crr_month: usize,
    pub burn_active_months: usize,
    pub months_simulated: usize,
}

/// Build the growth curve, extending to `months` via exponential interpolation.
/// Mirrors Python's build_growth_curve().
pub fn build_growth_curve(params: &SimParams) -> Vec<i64> {
    let months = params.simulation_months;
    let mut base: Vec<i64> = params.growth_curve.clone();

    if base.len() >= months {
        base.truncate(months);
        return base;
    }

    let last_count = *base.last().unwrap_or(&1) as f64;
    let remaining = months - base.len();
    let growth_factor = (params.growth_target_employees as f64 / last_count).powf(1.0 / remaining as f64);

    for i in 1..=(remaining) {
        let val = (last_count * growth_factor.powi(i as i32)) as i64;
        base.push(val.min(params.growth_target_employees));
    }

    base.truncate(months);
    base
}

/// Compute dynamic annual burn rate for a given CRR.
/// Mirrors Python's dynamic_burn_rate().
fn dynamic_burn_rate(crr: f64, params: &SimParams) -> f64 {
    if crr >= params.crr_overcapitalized {
        return params.burn_rate_ceiling;
    }
    let normalized = (crr - params.burn_eligible_crr) / (params.crr_overcapitalized - params.burn_eligible_crr);
    let normalized = normalized.max(0.0).min(1.0);
    params.burn_rate_floor + (params.burn_rate_ceiling - params.burn_rate_floor) * normalized
}

/// Compute the monthly verdict string for a given CRR and minting_paused state.
/// Mirrors Python's verdict_for().
fn verdict_for(crr: f64, minting_paused: bool, params: &SimParams) -> String {
    if crr < params.crr_critical {
        "INSOLVENT".to_string()
    } else if crr < params.crr_mint_pause || minting_paused {
        "MINT_PAUSED".to_string()
    } else if crr < params.crr_operational_target {
        "STRAINED".to_string()
    } else if crr > params.crr_overcapitalized {
        "OVERCAPITALIZED".to_string()
    } else {
        "HEALTHY".to_string()
    }
}

/// Run a deterministic simulation for the given parameters.
/// Line-for-line port of Python's run_simulation().
pub fn run_simulation(params: &SimParams) -> SimResult {
    let growth = build_growth_curve(params);

    let mut escrow_pool: f64 = 0.0;
    let mut circulating_tokens: f64 = 0.0;

    let mut failure_reason: Option<String> = None;
    let mut records: Vec<MonthRecord> = Vec::with_capacity(params.simulation_months);

    for (month_idx, &employee_count) in growth.iter().enumerate() {
        let month = month_idx + 1;

        // ── Pre-mint CRR check ─────────────────────────────────────────────
        let (pre_crr, minting_paused) = if circulating_tokens > 0.0 {
            let crr = escrow_pool / (circulating_tokens * params.token_face_value);
            (crr, crr < params.crr_mint_pause)
        } else {
            // System start — no tokens yet, default to design CRR
            (0.5_f64, false)
        };
        let _ = pre_crr; // used only for minting_paused check above

        // ── Step 1: Minting ────────────────────────────────────────────────
        let total_capacity = employee_count as f64 * params.vendor_capacity_per_employee;
        let capacity_headroom = (total_capacity * params.capacity_ratio - circulating_tokens).max(0.0);

        let new_tokens = if !minting_paused {
            let desired_mint = employee_count as f64 * params.expected_monthly_mint_per_employee;
            let hard_cap = employee_count as f64 * params.monthly_mint_cap_per_employee;
            desired_mint.min(capacity_headroom).min(hard_cap)
        } else {
            0.0
        };

        escrow_pool += new_tokens * params.mint_price;
        circulating_tokens += new_tokens;

        // ── Step 2: Fee collection — operator takes fee_to_operator_pct, rest to escrow ─
        let fee_revenue = employee_count as f64 * params.employee_fee_monthly;
        let operator_revenue = fee_revenue * params.fee_to_operator_pct;
        escrow_pool += fee_revenue * (1.0 - params.fee_to_operator_pct); // FEE_TO_ESCROW_PCT share

        // ── Step 3: Interest accrual ───────────────────────────────────────
        let interest_escrow = escrow_pool * params.monthly_interest_rate;
        escrow_pool += interest_escrow;

        // ── Step 4: CRR and per-token escrow ──────────────────────────────
        let (per_token_escrow, crr) = if circulating_tokens > 0.0 {
            (
                escrow_pool / circulating_tokens,
                escrow_pool / (circulating_tokens * params.token_face_value),
            )
        } else {
            (0.0, 0.5)
        };

        // ── Step 5b: Burn events (CRR >= burn_eligible_crr only) ──────────
        let mut tokens_burned = 0.0_f64;
        let mut reimbursements_paid = 0.0_f64;
        let mut burn_rate = 0.0_f64;

        if crr >= params.burn_eligible_crr && circulating_tokens > 0.0 {
            let annual_burn_rate = dynamic_burn_rate(crr, params);
            burn_rate = 1.0 - (1.0 - annual_burn_rate).powf(1.0 / 12.0);
            tokens_burned = circulating_tokens * burn_rate;

            // Vendor always receives exactly TOKEN_FACE_VALUE per burned token from escrow
            reimbursements_paid = (tokens_burned * params.token_face_value).min(escrow_pool);
            escrow_pool -= reimbursements_paid;
            circulating_tokens -= tokens_burned;
        }

        // ── Step 6: Final state ────────────────────────────────────────────
        let (per_token_escrow_final, crr_final) = if circulating_tokens > 0.0 {
            (
                escrow_pool / circulating_tokens,
                escrow_pool / (circulating_tokens * params.token_face_value),
            )
        } else {
            (0.0, 0.5)
        };
        let _ = per_token_escrow; // Step 4 value superseded by Step 6

        let escrow_net = escrow_pool - (circulating_tokens * params.token_face_value);
        let capacity_utilization = if total_capacity > 0.0 {
            circulating_tokens / total_capacity
        } else {
            0.0
        };
        let monthly_verdict = verdict_for(crr_final, minting_paused, params);

        // Python rounds: new_tokens_minted/circulating_tokens/tokens_burned to int,
        // escrow_pool/escrow_net to 2dp, per_token_escrow to 4dp, crr to 4dp,
        // burn_rate_pct to 2dp, reimbursements_paid/operator_revenue/fee_revenue/
        // interest_escrow to 2dp, total_capacity to 0dp, capacity_utilization_pct to 2dp.
        records.push(MonthRecord {
            month,
            employees: employee_count,
            new_tokens_minted: new_tokens.round(),
            circulating_tokens: circulating_tokens.round(),
            escrow_pool: round2(escrow_pool),
            escrow_net: round2(escrow_net),
            per_token_escrow: round4(per_token_escrow_final),
            crr: round4(crr_final),
            burn_rate_pct: round2(burn_rate * 100.0),
            tokens_burned: tokens_burned.round(),
            reimbursements_paid: round2(reimbursements_paid),
            operator_revenue: round2(operator_revenue),
            fee_revenue: round2(fee_revenue),
            interest_escrow: round2(interest_escrow),
            total_capacity: total_capacity.round(),
            capacity_utilization_pct: round2(capacity_utilization * 100.0),
            minting_paused,
            verdict: monthly_verdict,
        });

        // Failure check
        if crr_final < params.crr_critical && circulating_tokens > 0.0 {
            failure_reason = Some(format!(
                "INSOLVENT at month {} — CRR={:.3}",
                month, crr_final
            ));
            break;
        }
    }

    SimResult {
        records,
        failure_reason,
    }
}

/// Evaluate simulation results — mirrors Python's evaluate().
pub fn evaluate(result: &SimResult, params: &SimParams) -> EvalResult {
    if result.records.is_empty() {
        return EvalResult {
            primary_metric: 0.0,
            verdict: "FAILURE".to_string(),
            failure_reason: "No records produced".to_string(),
            final_crr: 0.0,
            final_escrow_net: 0.0,
            final_employees: 0,
            first_burn_month: None,
            peak_crr: 0.0,
            peak_crr_month: 0,
            burn_active_months: 0,
            months_simulated: 0,
        };
    }

    let last = result.records.last().unwrap();
    let crr = last.crr;

    let verdict = if result.failure_reason.is_some() || crr < params.failure_threshold {
        "FAILURE".to_string()
    } else if crr < params.warning_threshold {
        "WARNING".to_string()
    } else {
        last.verdict.clone()
    };

    let first_burn_month = result.records.iter()
        .find(|r| r.tokens_burned > 0.0)
        .map(|r| r.month);

    let peak_record = result.records.iter()
        .max_by(|a, b| a.crr.partial_cmp(&b.crr).unwrap_or(std::cmp::Ordering::Equal))
        .unwrap();

    let burn_active_months = result.records.iter()
        .filter(|r| r.tokens_burned > 0.0)
        .count();

    EvalResult {
        primary_metric: crr,
        verdict,
        failure_reason: result.failure_reason.clone().unwrap_or_else(|| "NONE".to_string()),
        final_crr: round4(crr),
        final_escrow_net: round2(last.escrow_net),
        final_employees: last.employees,
        first_burn_month,
        peak_crr: peak_record.crr,
        peak_crr_month: peak_record.month,
        burn_active_months,
        months_simulated: result.records.len(),
    }
}

// ── Rounding helpers (mirror Python's round() behavior) ────────────────────

#[inline]
pub fn round2(x: f64) -> f64 {
    (x * 100.0).round() / 100.0
}

#[inline]
pub fn round4(x: f64) -> f64 {
    (x * 10000.0).round() / 10000.0
}
