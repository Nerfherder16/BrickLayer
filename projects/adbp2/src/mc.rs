use rand::Rng;
use rand_distr::{Beta, Distribution, Normal};

use crate::params::{MCDistributionConfig, SimParams};
use crate::sim::{self, EvalResult, SimResult};
use crate::stats::{summarize_mc, MCOutput};

/// Sample a perturbed SimParams from the base params and MC distribution config.
/// Mirrors the sampling logic described in the spec.
pub fn sample_params(base: &SimParams, config: &MCDistributionConfig, rng: &mut impl Rng) -> SimParams {
    let mut p = base.clone();

    // mint_per_employee: Normal(mean, std) — overrides expected_monthly_mint_per_employee
    if let (Some(mean), Some(std)) = (config.mint_per_employee_mean, config.mint_per_employee_std) {
        if std > 0.0 {
            let dist = Normal::new(mean, std).unwrap();
            p.expected_monthly_mint_per_employee = dist.sample(rng).max(0.0);
        } else {
            p.expected_monthly_mint_per_employee = mean.max(0.0);
        }
    }

    // growth_multiplier: Normal(1.0, std) — scales each growth curve value
    if let Some(std) = config.growth_multiplier_std {
        if std > 0.0 {
            let dist = Normal::new(1.0_f64, std).unwrap();
            let multiplier = dist.sample(rng).max(0.01); // prevent near-zero
            p.growth_curve = p.growth_curve.iter()
                .map(|&v| ((v as f64 * multiplier).round() as i64).max(1))
                .collect();
        }
    }

    // annual_interest_rate: Normal(mean, std)
    if let (Some(mean), Some(std)) = (config.interest_rate_mean, config.interest_rate_std) {
        if std > 0.0 {
            let dist = Normal::new(mean, std).unwrap();
            p.annual_interest_rate = dist.sample(rng).max(0.0);
        } else {
            p.annual_interest_rate = mean.max(0.0);
        }
        p.monthly_interest_rate = p.annual_interest_rate / 12.0;
    }

    // fee_compliance_rate: Beta(alpha, beta) — fraction of employees who pay
    // Applied as a multiplier to employee_fee_monthly (conceptually: not all employees pay)
    // The Beta-distributed compliance multiplies fee_revenue by clamping in [0, 1].
    if let (Some(alpha), Some(beta_param)) = (config.fee_compliance_alpha, config.fee_compliance_beta) {
        if alpha > 0.0 && beta_param > 0.0 {
            let dist = Beta::new(alpha, beta_param).unwrap();
            let compliance = dist.sample(rng).clamp(0.0, 1.0);
            // Apply compliance as a scale factor on the fee
            p.employee_fee_monthly *= compliance;
        }
    }

    // vendor_capacity_per_employee: Normal(mean, std)
    if let (Some(mean), Some(std)) = (config.vendor_capacity_mean, config.vendor_capacity_std) {
        if std > 0.0 {
            let dist = Normal::new(mean, std).unwrap();
            p.vendor_capacity_per_employee = dist.sample(rng).max(0.0);
        } else {
            p.vendor_capacity_per_employee = mean.max(0.0);
        }
    }

    p
}

/// Expose sample_params to Python for testing (Task 4).
/// Returns the sampled params as a Python dict via to_py_dict().
pub fn sample_params_for_test(base: &SimParams, config: &MCDistributionConfig, seed: u64) -> SimParams {
    use rand::SeedableRng;
    use rand_chacha::ChaCha8Rng;
    let mut rng = ChaCha8Rng::seed_from_u64(seed);
    sample_params(base, config, &mut rng)
}

/// Run Monte Carlo simulation: N parallel samples via Rayon.
pub fn run_monte_carlo(
    base_params: &SimParams,
    mc_config: &MCDistributionConfig,
    n_samples: usize,
    seed: Option<u64>,
    include_per_sample: bool,
) -> MCOutput {
    use rand::SeedableRng;
    use rand_chacha::ChaCha8Rng;
    use rayon::prelude::*;

    // Pre-generate N sets of sampled params (sequential, deterministic from seed)
    let mut rng = match seed {
        Some(s) => ChaCha8Rng::seed_from_u64(s),
        None => ChaCha8Rng::from_entropy(),
    };

    let sampled_params: Vec<SimParams> = (0..n_samples)
        .map(|_| sample_params(base_params, mc_config, &mut rng))
        .collect();

    // Run simulations in parallel via Rayon
    let results: Vec<(SimResult, EvalResult)> = sampled_params
        .par_iter()
        .map(|p| {
            let result = sim::run_simulation(p);
            let eval = sim::evaluate(&result, p);
            (result, eval)
        })
        .collect();

    summarize_mc(results, base_params.simulation_months, include_per_sample)
}
