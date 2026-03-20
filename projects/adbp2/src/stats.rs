use crate::sim::{EvalResult, MonthRecord, SimResult};

/// Full Monte Carlo output structure.
/// Serialized to Python dict via to fields — mirrors the spec schema.
#[derive(Debug, Clone, Default)]
pub struct CRRTrajectory {
    pub p10: Vec<f64>,
    pub p50: Vec<f64>,
    pub p90: Vec<f64>,
}

#[derive(Debug, Clone, Default)]
pub struct PBurnActivates {
    pub within_12mo: f64,
    pub within_24mo: f64,
    pub within_36mo: f64,
    pub within_48mo: f64,
    pub within_60mo: f64,
}

#[derive(Debug, Clone, Default)]
pub struct FirstBurnDist {
    pub p10: f64,
    pub p50: f64,
    pub p90: f64,
    pub never_pct: f64,
}

#[derive(Debug, Clone, Default)]
pub struct FinalCRRDist {
    pub p10: f64,
    pub p50: f64,
    pub p90: f64,
    pub mean: f64,
    pub std: f64,
}

#[derive(Debug, Clone)]
pub struct MCOutput {
    pub n_samples: usize,
    pub crr_trajectory: CRRTrajectory,
    pub p_burn_activates: PBurnActivates,
    pub p_ruin: f64,
    pub first_burn_month_distribution: FirstBurnDist,
    pub final_crr_distribution: FinalCRRDist,
    pub per_sample_summaries: Vec<EvalResult>,
}

/// Compute the p-th percentile of a sorted (or unsorted) data slice.
/// Uses linear interpolation matching numpy's default method.
pub fn percentile(data: &[f64], p: f64) -> f64 {
    assert!(!data.is_empty(), "percentile: empty data");
    assert!((0.0..=100.0).contains(&p), "percentile: p must be in [0, 100]");

    let mut sorted = data.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let n = sorted.len();

    if n == 1 {
        return sorted[0];
    }

    // numpy linear interpolation method
    let index = (p / 100.0) * (n as f64 - 1.0);
    let lower = index.floor() as usize;
    let upper = index.ceil() as usize;
    let frac = index - lower as f64;

    if lower == upper {
        sorted[lower]
    } else {
        sorted[lower] * (1.0 - frac) + sorted[upper] * frac
    }
}

/// Summarize a collection of (SimResult, EvalResult) pairs into MCOutput.
pub fn summarize_mc(
    results: Vec<(SimResult, EvalResult)>,
    simulation_months: usize,
    include_per_sample: bool,
) -> MCOutput {
    let n = results.len();
    if n == 0 {
        return MCOutput {
            n_samples: 0,
            crr_trajectory: CRRTrajectory::default(),
            p_burn_activates: PBurnActivates::default(),
            p_ruin: 0.0,
            first_burn_month_distribution: FirstBurnDist::default(),
            final_crr_distribution: FinalCRRDist::default(),
            per_sample_summaries: vec![],
        };
    }

    // ── CRR trajectory bands ───────────────────────────────────────────────
    let mut p10_traj = Vec::with_capacity(simulation_months);
    let mut p50_traj = Vec::with_capacity(simulation_months);
    let mut p90_traj = Vec::with_capacity(simulation_months);

    for month_idx in 0..simulation_months {
        let mut crr_at_month: Vec<f64> = results.iter()
            .filter_map(|(sr, _)| sr.records.get(month_idx).map(|r| r.crr))
            .collect();

        if crr_at_month.is_empty() {
            // All runs terminated before this month — use 0.0 as sentinel
            p10_traj.push(0.0);
            p50_traj.push(0.0);
            p90_traj.push(0.0);
        } else {
            // Runs that terminated early are treated as CRR=0 (insolvent)
            // Pad to n samples with 0.0 if some runs were shorter
            let short_count = n - crr_at_month.len();
            crr_at_month.extend(std::iter::repeat(0.0_f64).take(short_count));
            p10_traj.push(percentile(&crr_at_month, 10.0));
            p50_traj.push(percentile(&crr_at_month, 50.0));
            p90_traj.push(percentile(&crr_at_month, 90.0));
        }
    }

    // ── P(burn activates within N months) ─────────────────────────────────
    let burn_within = |limit_months: usize| -> f64 {
        let count = results.iter().filter(|(sr, er)| {
            match er.first_burn_month {
                Some(m) => m <= limit_months,
                None => false,
            }
        }).count();
        count as f64 / n as f64
    };

    let p_burn_activates = PBurnActivates {
        within_12mo: burn_within(12),
        within_24mo: burn_within(24),
        within_36mo: burn_within(36),
        within_48mo: burn_within(48),
        within_60mo: burn_within(60),
    };

    // ── P(ruin) ────────────────────────────────────────────────────────────
    let ruin_count = results.iter()
        .filter(|(_, er)| er.verdict == "FAILURE" || er.verdict == "INSOLVENT")
        .count();
    let p_ruin = ruin_count as f64 / n as f64;

    // ── First burn month distribution ─────────────────────────────────────
    let burn_months: Vec<f64> = results.iter()
        .filter_map(|(_, er)| er.first_burn_month.map(|m| m as f64))
        .collect();
    let never_pct = (n - burn_months.len()) as f64 / n as f64;

    let first_burn_dist = if burn_months.is_empty() {
        FirstBurnDist {
            p10: 0.0,
            p50: 0.0,
            p90: 0.0,
            never_pct: 1.0,
        }
    } else {
        FirstBurnDist {
            p10: percentile(&burn_months, 10.0),
            p50: percentile(&burn_months, 50.0),
            p90: percentile(&burn_months, 90.0),
            never_pct,
        }
    };

    // ── Final CRR distribution ─────────────────────────────────────────────
    let final_crrs: Vec<f64> = results.iter().map(|(_, er)| er.final_crr).collect();
    let mean_crr = final_crrs.iter().sum::<f64>() / n as f64;
    let variance = final_crrs.iter().map(|x| (x - mean_crr).powi(2)).sum::<f64>() / n as f64;

    let final_crr_dist = FinalCRRDist {
        p10: percentile(&final_crrs, 10.0),
        p50: percentile(&final_crrs, 50.0),
        p90: percentile(&final_crrs, 90.0),
        mean: mean_crr,
        std: variance.sqrt(),
    };

    // ── Per-sample summaries ───────────────────────────────────────────────
    let per_sample = if include_per_sample {
        results.iter().map(|(_, er)| er.clone()).collect()
    } else {
        vec![]
    };

    MCOutput {
        n_samples: n,
        crr_trajectory: CRRTrajectory {
            p10: p10_traj,
            p50: p50_traj,
            p90: p90_traj,
        },
        p_burn_activates,
        p_ruin,
        first_burn_month_distribution: first_burn_dist,
        final_crr_distribution: final_crr_dist,
        per_sample_summaries: per_sample,
    }
}
