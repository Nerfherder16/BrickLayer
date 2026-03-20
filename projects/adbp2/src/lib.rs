use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

pub mod params;
pub mod sim;

pub use params::{MCDistributionConfig, SimParams};

/// Smoke test — validates that the maturin build chain works.
#[pyfunction]
fn hello() -> &'static str {
    "adbp2_mc loaded"
}

/// Run a deterministic single simulation from a Python dict of parameters.
/// Returns a Python dict with "records" (list of dicts) and "failure_reason" (str or None).
#[pyfunction]
fn run_simulation<'py>(py: Python<'py>, params_dict: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
    let params = SimParams::from_dict(params_dict)?;
    let result = sim::run_simulation(&params);

    let out = PyDict::new(py);

    // Build records list
    let records_list = PyList::empty(py);
    for r in &result.records {
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
        records_list.append(rec)?;
    }
    out.set_item("records", records_list)?;
    out.set_item("failure_reason", result.failure_reason.as_deref())?;

    Ok(out)
}

/// Evaluate simulation records. Accepts the output dict from run_simulation
/// and the params dict. Returns an evaluation result dict.
#[pyfunction]
fn evaluate<'py>(py: Python<'py>, result_dict: &Bound<'py, PyDict>, params_dict: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
    let params = SimParams::from_dict(params_dict)?;

    // Reconstruct SimResult from the Python dict
    let records_obj = result_dict.get_item("records")?
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("evaluate: 'records' key missing"))?;
    let records_list = records_obj.downcast::<PyList>()
        .map_err(|_| pyo3::exceptions::PyValueError::new_err("evaluate: 'records' must be a list"))?;

    let mut records = Vec::with_capacity(records_list.len());
    for item in records_list.iter() {
        let rec = item.downcast::<PyDict>()
            .map_err(|_| pyo3::exceptions::PyValueError::new_err("evaluate: each record must be a dict"))?;

        fn get_f64(d: &Bound<'_, PyDict>, k: &str) -> PyResult<f64> {
            d.get_item(k)?
                .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!("record missing '{}'", k)))?
                .extract::<f64>()
                .map_err(|_| pyo3::exceptions::PyValueError::new_err(format!("record '{}' must be float", k)))
        }
        fn get_i64(d: &Bound<'_, PyDict>, k: &str) -> PyResult<i64> {
            d.get_item(k)?
                .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!("record missing '{}'", k)))?
                .extract::<i64>()
                .map_err(|_| pyo3::exceptions::PyValueError::new_err(format!("record '{}' must be int", k)))
        }
        fn get_usize(d: &Bound<'_, PyDict>, k: &str) -> PyResult<usize> {
            d.get_item(k)?
                .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!("record missing '{}'", k)))?
                .extract::<usize>()
                .map_err(|_| pyo3::exceptions::PyValueError::new_err(format!("record '{}' must be int", k)))
        }

        let minting_paused = rec.get_item("minting_paused")?
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("record missing 'minting_paused'"))?
            .extract::<bool>()?;
        let verdict_val = rec.get_item("verdict")?
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("record missing 'verdict'"))?
            .extract::<String>()?;

        records.push(sim::MonthRecord {
            month: get_usize(rec, "month")?,
            employees: get_i64(rec, "employees")?,
            new_tokens_minted: get_f64(rec, "new_tokens_minted")?,
            circulating_tokens: get_f64(rec, "circulating_tokens")?,
            escrow_pool: get_f64(rec, "escrow_pool")?,
            escrow_net: get_f64(rec, "escrow_net")?,
            per_token_escrow: get_f64(rec, "per_token_escrow")?,
            crr: get_f64(rec, "crr")?,
            burn_rate_pct: get_f64(rec, "burn_rate_pct")?,
            tokens_burned: get_f64(rec, "tokens_burned")?,
            reimbursements_paid: get_f64(rec, "reimbursements_paid")?,
            admin_fees_paid: get_f64(rec, "admin_fees_paid")?,
            fee_revenue: get_f64(rec, "fee_revenue")?,
            interest_escrow: get_f64(rec, "interest_escrow")?,
            total_capacity: get_f64(rec, "total_capacity")?,
            capacity_utilization_pct: get_f64(rec, "capacity_utilization_pct")?,
            minting_paused,
            verdict: verdict_val,
        });
    }

    let failure_reason = match result_dict.get_item("failure_reason")? {
        Some(v) if !v.is_none() => Some(v.extract::<String>()?),
        _ => None,
    };

    let sim_result = sim::SimResult { records, failure_reason };
    let eval = sim::evaluate(&sim_result, &params);

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

/// PyO3 module entry point.
#[pymodule]
fn adbp2_mc(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello, m)?)?;
    m.add_function(wrap_pyfunction!(run_simulation, m)?)?;
    m.add_function(wrap_pyfunction!(evaluate, m)?)?;
    m.add_class::<SimParams>()?;
    m.add_class::<MCDistributionConfig>()?;
    Ok(())
}
