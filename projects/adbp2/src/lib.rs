use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

pub mod mc;
pub mod params;
pub mod sim;
pub mod stats;

pub use params::{MCDistributionConfig, SimParams};

// ── Utility: build records list from Vec<MonthRecord> ─────────────────────────

fn records_to_pylist<'py>(py: Python<'py>, records: &[sim::MonthRecord]) -> PyResult<Bound<'py, PyList>> {
    let list = PyList::empty(py);
    for r in records {
        let rec = PyDict::new(py);
        rec.set_item("month", r.month)?;
        rec.set_item("employees", r.employees)?;
        rec.set_item("new_tokens_minted", r.new_tokens_minted)?;
        rec.set_item("circulating_tokens", r.circulating_tokens)?;
        rec.set_item("escrow_pool", r.escrow_pool)?;
        rec.set_item("escrow_net", r.escrow_net)?;
        rec.set_item("per_token_escrow", r.per_token_escrow)?;
        rec.set_item("crr", r.crr)?;
        rec.set_item("burn_rate_pct", r.burn_rate_pct)?;
        rec.set_item("tokens_burned", r.tokens_burned)?;
        rec.set_item("reimbursements_paid", r.reimbursements_paid)?;
        rec.set_item("admin_fees_paid", r.admin_fees_paid)?;
        rec.set_item("fee_revenue", r.fee_revenue)?;
        rec.set_item("interest_escrow", r.interest_escrow)?;
        rec.set_item("total_capacity", r.total_capacity)?;
        rec.set_item("capacity_utilization_pct", r.capacity_utilization_pct)?;
        rec.set_item("minting_paused", r.minting_paused)?;
        rec.set_item("verdict", &r.verdict)?;
        list.append(rec)?;
    }
    Ok(list)
}

fn eval_to_pydict<'py>(py: Python<'py>, eval: &sim::EvalResult) -> PyResult<Bound<'py, PyDict>> {
    let out = PyDict::new(py);
    out.set_item("primary_metric", eval.primary_metric)?;
    out.set_item("verdict", &eval.verdict)?;
    out.set_item("failure_reason", &eval.failure_reason)?;
    out.set_item("final_crr", eval.final_crr)?;
    out.set_item("final_escrow_net", eval.final_escrow_net)?;
    out.set_item("final_employees", eval.final_employees)?;
    match eval.first_burn_month {
        Some(m) => out.set_item("first_burn_month", m)?,
        None => out.set_item("first_burn_month", "never")?,
    }
    out.set_item("peak_crr", eval.peak_crr)?;
    out.set_item("peak_crr_month", eval.peak_crr_month)?;
    out.set_item("burn_active_months", eval.burn_active_months)?;
    out.set_item("months_simulated", eval.months_simulated)?;
    Ok(out)
}

fn pydict_to_sim_result<'py>(result_dict: &Bound<'py, PyDict>) -> PyResult<(sim::SimResult, ())> {
    let records_obj = result_dict.get_item("records")?
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("evaluate: 'records' key missing"))?;
    let records_list = records_obj.downcast::<PyList>()
        .map_err(|_| pyo3::exceptions::PyValueError::new_err("evaluate: 'records' must be a list"))?;

    let mut records = Vec::with_capacity(records_list.len());
    for item in records_list.iter() {
        let rec = item.downcast::<PyDict>()
            .map_err(|_| pyo3::exceptions::PyValueError::new_err("evaluate: each record must be a dict"))?;

        macro_rules! get_f64 {
            ($k:expr) => {
                rec.get_item($k)?
                    .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!("record missing '{}'", $k)))?
                    .extract::<f64>()
                    .map_err(|_| pyo3::exceptions::PyValueError::new_err(format!("record '{}' must be float", $k)))?
            };
        }
        macro_rules! get_i64 {
            ($k:expr) => {
                rec.get_item($k)?
                    .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!("record missing '{}'", $k)))?
                    .extract::<i64>()
                    .map_err(|_| pyo3::exceptions::PyValueError::new_err(format!("record '{}' must be int", $k)))?
            };
        }
        macro_rules! get_usize {
            ($k:expr) => {
                rec.get_item($k)?
                    .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!("record missing '{}'", $k)))?
                    .extract::<usize>()
                    .map_err(|_| pyo3::exceptions::PyValueError::new_err(format!("record '{}' must be int", $k)))?
            };
        }

        let minting_paused = rec.get_item("minting_paused")?
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("record missing 'minting_paused'"))?
            .extract::<bool>()?;
        let verdict_val = rec.get_item("verdict")?
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("record missing 'verdict'"))?
            .extract::<String>()?;

        records.push(sim::MonthRecord {
            month: get_usize!("month"),
            employees: get_i64!("employees"),
            new_tokens_minted: get_f64!("new_tokens_minted"),
            circulating_tokens: get_f64!("circulating_tokens"),
            escrow_pool: get_f64!("escrow_pool"),
            escrow_net: get_f64!("escrow_net"),
            per_token_escrow: get_f64!("per_token_escrow"),
            crr: get_f64!("crr"),
            burn_rate_pct: get_f64!("burn_rate_pct"),
            tokens_burned: get_f64!("tokens_burned"),
            reimbursements_paid: get_f64!("reimbursements_paid"),
            admin_fees_paid: get_f64!("admin_fees_paid"),
            fee_revenue: get_f64!("fee_revenue"),
            interest_escrow: get_f64!("interest_escrow"),
            total_capacity: get_f64!("total_capacity"),
            capacity_utilization_pct: get_f64!("capacity_utilization_pct"),
            minting_paused,
            verdict: verdict_val,
        });
    }

    let failure_reason = match result_dict.get_item("failure_reason")? {
        Some(v) if !v.is_none() => Some(v.extract::<String>()?),
        _ => None,
    };

    Ok((sim::SimResult { records, failure_reason }, ()))
}

fn mc_output_to_pydict<'py>(py: Python<'py>, out: &stats::MCOutput) -> PyResult<Bound<'py, PyDict>> {
    let d = PyDict::new(py);
    d.set_item("n_samples", out.n_samples)?;

    // crr_trajectory
    let traj = PyDict::new(py);
    traj.set_item("p10", PyList::new(py, &out.crr_trajectory.p10)?)?;
    traj.set_item("p50", PyList::new(py, &out.crr_trajectory.p50)?)?;
    traj.set_item("p90", PyList::new(py, &out.crr_trajectory.p90)?)?;
    d.set_item("crr_trajectory", traj)?;

    // p_burn_activates
    let burn = PyDict::new(py);
    burn.set_item("within_12mo", out.p_burn_activates.within_12mo)?;
    burn.set_item("within_24mo", out.p_burn_activates.within_24mo)?;
    burn.set_item("within_36mo", out.p_burn_activates.within_36mo)?;
    burn.set_item("within_48mo", out.p_burn_activates.within_48mo)?;
    burn.set_item("within_60mo", out.p_burn_activates.within_60mo)?;
    d.set_item("p_burn_activates", burn)?;

    d.set_item("p_ruin", out.p_ruin)?;

    // first_burn_month_distribution
    let fbm = PyDict::new(py);
    fbm.set_item("p10", out.first_burn_month_distribution.p10)?;
    fbm.set_item("p50", out.first_burn_month_distribution.p50)?;
    fbm.set_item("p90", out.first_burn_month_distribution.p90)?;
    fbm.set_item("never_pct", out.first_burn_month_distribution.never_pct)?;
    d.set_item("first_burn_month_distribution", fbm)?;

    // final_crr_distribution
    let fcd = PyDict::new(py);
    fcd.set_item("p10", out.final_crr_distribution.p10)?;
    fcd.set_item("p50", out.final_crr_distribution.p50)?;
    fcd.set_item("p90", out.final_crr_distribution.p90)?;
    fcd.set_item("mean", out.final_crr_distribution.mean)?;
    fcd.set_item("std", out.final_crr_distribution.std)?;
    d.set_item("final_crr_distribution", fcd)?;

    // per_sample_summaries
    let summaries = PyList::empty(py);
    for eval in &out.per_sample_summaries {
        summaries.append(eval_to_pydict(py, eval)?)?;
    }
    d.set_item("per_sample_summaries", summaries)?;

    Ok(d)
}

// ── Smoke test ─────────────────────────────────────────────────────────────────

/// Smoke test — validates that the maturin build chain works.
#[pyfunction]
fn hello() -> &'static str {
    "adbp2_mc loaded"
}

// ── Run simulation ─────────────────────────────────────────────────────────────

/// Run a deterministic single simulation from a Python dict of parameters.
/// Returns {"records": [...], "failure_reason": str|None}.
#[pyfunction]
fn run_simulation<'py>(py: Python<'py>, params_dict: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
    let params = SimParams::from_dict(params_dict)?;
    let result = sim::run_simulation(&params);

    let out = PyDict::new(py);
    out.set_item("records", records_to_pylist(py, &result.records)?)?;
    out.set_item("failure_reason", result.failure_reason.as_deref())?;
    Ok(out)
}

// ── Evaluate ───────────────────────────────────────────────────────────────────

/// Evaluate simulation records from run_simulation output dict.
/// Returns evaluation result dict.
#[pyfunction]
fn evaluate<'py>(py: Python<'py>, result_dict: &Bound<'py, PyDict>, params_dict: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
    let params = SimParams::from_dict(params_dict)?;
    let (sim_result, _) = pydict_to_sim_result(result_dict)?;
    let eval = sim::evaluate(&sim_result, &params);
    eval_to_pydict(py, &eval)
}

// ── Monte Carlo ────────────────────────────────────────────────────────────────

/// Run Monte Carlo simulation with Rayon parallelism.
/// params_dict: full simulation params (same schema as run_simulation)
/// mc_config_dict: MCDistributionConfig dict (all keys optional)
/// n_samples: number of MC samples
/// seed: optional u64 seed for reproducibility (None = random)
/// include_per_sample: if True, include per-sample eval results in output
/// Returns MCOutput dict.
#[pyfunction]
#[pyo3(signature = (params_dict, mc_config_dict, n_samples, seed=None, include_per_sample=false))]
fn run_monte_carlo<'py>(
    py: Python<'py>,
    params_dict: &Bound<'py, PyDict>,
    mc_config_dict: &Bound<'py, PyDict>,
    n_samples: usize,
    seed: Option<u64>,
    include_per_sample: bool,
) -> PyResult<Bound<'py, PyDict>> {
    let base_params = SimParams::from_dict(params_dict)?;
    let mc_config = MCDistributionConfig::from_dict(mc_config_dict)?;
    let output = mc::run_monte_carlo(&base_params, &mc_config, n_samples, seed, include_per_sample);
    mc_output_to_pydict(py, &output)
}

// ── Test helpers ───────────────────────────────────────────────────────────────

/// Expose sample_params for Python testing (Task 4).
#[pyfunction]
fn sample_params_test<'py>(
    py: Python<'py>,
    base_dict: &Bound<'py, PyDict>,
    mc_dict: &Bound<'py, PyDict>,
    seed: u64,
) -> PyResult<Bound<'py, PyDict>> {
    let base = SimParams::from_dict(base_dict)?;
    let config = MCDistributionConfig::from_dict(mc_dict)?;
    let sampled = mc::sample_params_for_test(&base, &config, seed);
    sampled.to_py_dict(py)
}

/// Expose percentile calculation for Python testing (Task 5).
#[pyfunction]
fn percentile_test(data: Vec<f64>, p: f64) -> f64 {
    stats::percentile(&data, p)
}

// ── Module ─────────────────────────────────────────────────────────────────────

/// PyO3 module entry point.
#[pymodule]
fn adbp2_mc(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello, m)?)?;
    m.add_function(wrap_pyfunction!(run_simulation, m)?)?;
    m.add_function(wrap_pyfunction!(evaluate, m)?)?;
    m.add_function(wrap_pyfunction!(run_monte_carlo, m)?)?;
    m.add_function(wrap_pyfunction!(sample_params_test, m)?)?;
    m.add_function(wrap_pyfunction!(percentile_test, m)?)?;
    m.add_class::<SimParams>()?;
    m.add_class::<MCDistributionConfig>()?;
    Ok(())
}
