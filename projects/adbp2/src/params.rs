use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

/// All simulation parameters passed from Python at runtime.
/// Nothing is hardcoded — every value flows from Python.
#[derive(Debug, Clone)]
#[pyclass]
pub struct SimParams {
    // ── Scenario parameters (from simulate.py) ────────────────────────────
    pub employee_fee_monthly: f64,
    pub vendor_capacity_per_employee: f64,
    pub simulation_months: usize,

    // ── System constants (from constants.py) ──────────────────────────────
    pub token_face_value: f64,
    pub mint_price: f64,
    pub escrow_start_per_token: f64,

    pub burn_eligible_crr: f64,
    pub burn_rate_floor: f64,
    pub burn_rate_ceiling: f64,

    /// Fraction of monthly employee fee that goes to operator (not escrow).
    /// Mirrors Python's FEE_TO_OPERATOR_PCT constant.
    pub fee_to_operator_pct: f64,

    pub crr_operational_target: f64,
    pub crr_mint_pause: f64,
    pub crr_critical: f64,
    pub crr_overcapitalized: f64,

    pub capacity_ratio: f64,
    pub monthly_mint_cap_per_employee: f64,
    pub expected_monthly_mint_per_employee: f64,

    pub annual_interest_rate: f64,
    /// Computed internally: annual_interest_rate / 12.0
    pub monthly_interest_rate: f64,

    pub growth_curve: Vec<i64>,
    pub growth_target_employees: i64,

    pub failure_threshold: f64,
    pub warning_threshold: f64,
}

fn extract_f64(dict: &Bound<'_, PyDict>, key: &str) -> PyResult<f64> {
    match dict.get_item(key)? {
        Some(val) => val.extract::<f64>().map_err(|_| {
            pyo3::exceptions::PyValueError::new_err(format!(
                "SimParams: field '{}' must be a float, got: {:?}",
                key, val
            ))
        }),
        None => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "SimParams: required field '{}' is missing from params dict",
            key
        ))),
    }
}

fn extract_usize(dict: &Bound<'_, PyDict>, key: &str) -> PyResult<usize> {
    match dict.get_item(key)? {
        Some(val) => val.extract::<usize>().map_err(|_| {
            pyo3::exceptions::PyValueError::new_err(format!(
                "SimParams: field '{}' must be an integer, got: {:?}",
                key, val
            ))
        }),
        None => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "SimParams: required field '{}' is missing from params dict",
            key
        ))),
    }
}

fn extract_i64(dict: &Bound<'_, PyDict>, key: &str) -> PyResult<i64> {
    match dict.get_item(key)? {
        Some(val) => val.extract::<i64>().map_err(|_| {
            pyo3::exceptions::PyValueError::new_err(format!(
                "SimParams: field '{}' must be an integer, got: {:?}",
                key, val
            ))
        }),
        None => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "SimParams: required field '{}' is missing from params dict",
            key
        ))),
    }
}

fn extract_growth_curve(dict: &Bound<'_, PyDict>) -> PyResult<Vec<i64>> {
    match dict.get_item("growth_curve")? {
        Some(val) => {
            let list = val.downcast::<PyList>().map_err(|_| {
                pyo3::exceptions::PyValueError::new_err(
                    "SimParams: 'growth_curve' must be a list of integers",
                )
            })?;
            let mut curve = Vec::with_capacity(list.len());
            for item in list.iter() {
                let n = item.extract::<i64>().map_err(|_| {
                    pyo3::exceptions::PyValueError::new_err(
                        "SimParams: 'growth_curve' elements must be integers",
                    )
                })?;
                curve.push(n);
            }
            Ok(curve)
        }
        None => Err(pyo3::exceptions::PyValueError::new_err(
            "SimParams: required field 'growth_curve' is missing from params dict",
        )),
    }
}

#[pymethods]
impl SimParams {
    /// Construct SimParams from a Python dict.
    /// All fields are required; missing keys raise ValueError with the field name.
    #[new]
    pub fn from_dict(dict: &Bound<'_, PyDict>) -> PyResult<Self> {
        let annual_interest_rate = extract_f64(dict, "annual_interest_rate")?;
        Ok(SimParams {
            employee_fee_monthly: extract_f64(dict, "employee_fee_monthly")?,
            vendor_capacity_per_employee: extract_f64(dict, "vendor_capacity_per_employee")?,
            simulation_months: extract_usize(dict, "simulation_months")?,

            token_face_value: extract_f64(dict, "token_face_value")?,
            mint_price: extract_f64(dict, "mint_price")?,
            escrow_start_per_token: extract_f64(dict, "escrow_start_per_token")?,

            burn_eligible_crr: extract_f64(dict, "burn_eligible_crr")?,
            burn_rate_floor: extract_f64(dict, "burn_rate_floor")?,
            burn_rate_ceiling: extract_f64(dict, "burn_rate_ceiling")?,

            fee_to_operator_pct: extract_f64(dict, "fee_to_operator_pct")?,

            crr_operational_target: extract_f64(dict, "crr_operational_target")?,
            crr_mint_pause: extract_f64(dict, "crr_mint_pause")?,
            crr_critical: extract_f64(dict, "crr_critical")?,
            crr_overcapitalized: extract_f64(dict, "crr_overcapitalized")?,

            capacity_ratio: extract_f64(dict, "capacity_ratio")?,
            monthly_mint_cap_per_employee: extract_f64(dict, "monthly_mint_cap_per_employee")?,
            expected_monthly_mint_per_employee: extract_f64(
                dict,
                "expected_monthly_mint_per_employee",
            )?,

            annual_interest_rate,
            monthly_interest_rate: annual_interest_rate / 12.0,

            growth_curve: extract_growth_curve(dict)?,
            growth_target_employees: extract_i64(dict, "growth_target_employees")?,

            failure_threshold: extract_f64(dict, "failure_threshold")?,
            warning_threshold: extract_f64(dict, "warning_threshold")?,
        })
    }

    /// Convert SimParams back to a Python dict for round-trip verification.
    pub fn to_py_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let d = PyDict::new(py);
        d.set_item("employee_fee_monthly", self.employee_fee_monthly)?;
        d.set_item("vendor_capacity_per_employee", self.vendor_capacity_per_employee)?;
        d.set_item("simulation_months", self.simulation_months)?;
        d.set_item("token_face_value", self.token_face_value)?;
        d.set_item("mint_price", self.mint_price)?;
        d.set_item("escrow_start_per_token", self.escrow_start_per_token)?;
        d.set_item("burn_eligible_crr", self.burn_eligible_crr)?;
        d.set_item("burn_rate_floor", self.burn_rate_floor)?;
        d.set_item("burn_rate_ceiling", self.burn_rate_ceiling)?;
        d.set_item("fee_to_operator_pct", self.fee_to_operator_pct)?;
        d.set_item("crr_operational_target", self.crr_operational_target)?;
        d.set_item("crr_mint_pause", self.crr_mint_pause)?;
        d.set_item("crr_critical", self.crr_critical)?;
        d.set_item("crr_overcapitalized", self.crr_overcapitalized)?;
        d.set_item("capacity_ratio", self.capacity_ratio)?;
        d.set_item("monthly_mint_cap_per_employee", self.monthly_mint_cap_per_employee)?;
        d.set_item(
            "expected_monthly_mint_per_employee",
            self.expected_monthly_mint_per_employee,
        )?;
        d.set_item("annual_interest_rate", self.annual_interest_rate)?;
        d.set_item("monthly_interest_rate", self.monthly_interest_rate)?;
        let curve_list = PyList::new(py, &self.growth_curve)?;
        d.set_item("growth_curve", curve_list)?;
        d.set_item("growth_target_employees", self.growth_target_employees)?;
        d.set_item("failure_threshold", self.failure_threshold)?;
        d.set_item("warning_threshold", self.warning_threshold)?;
        Ok(d)
    }
}

/// MCDistributionConfig — stochastic overrides for Monte Carlo runs.
/// All fields are optional; omitted keys use base parameter values deterministically.
#[derive(Debug, Clone, Default)]
#[pyclass]
pub struct MCDistributionConfig {
    // mint_per_employee: Normal(mean, std) — overrides expected_monthly_mint_per_employee
    pub mint_per_employee_mean: Option<f64>,
    pub mint_per_employee_std: Option<f64>,

    // growth_multiplier: Normal(1.0, std) — scales each growth curve value
    pub growth_multiplier_std: Option<f64>,

    // annual_interest_rate: Normal(mean, std)
    pub interest_rate_mean: Option<f64>,
    pub interest_rate_std: Option<f64>,

    // fee_compliance_rate: Beta(alpha, beta) — fraction of employees who pay
    pub fee_compliance_alpha: Option<f64>,
    pub fee_compliance_beta: Option<f64>,

    // vendor_capacity_per_employee: Normal(mean, std)
    pub vendor_capacity_mean: Option<f64>,
    pub vendor_capacity_std: Option<f64>,
}

fn opt_f64(dict: &Bound<'_, PyDict>, key: &str) -> PyResult<Option<f64>> {
    match dict.get_item(key)? {
        Some(val) => {
            if val.is_none() {
                Ok(None)
            } else {
                Ok(Some(val.extract::<f64>().map_err(|_| {
                    pyo3::exceptions::PyValueError::new_err(format!(
                        "MCDistributionConfig: field '{}' must be a float or None",
                        key
                    ))
                })?))
            }
        }
        None => Ok(None),
    }
}

#[pymethods]
impl MCDistributionConfig {
    #[new]
    pub fn from_dict(dict: &Bound<'_, PyDict>) -> PyResult<Self> {
        Ok(MCDistributionConfig {
            mint_per_employee_mean: opt_f64(dict, "mint_per_employee_mean")?,
            mint_per_employee_std: opt_f64(dict, "mint_per_employee_std")?,
            growth_multiplier_std: opt_f64(dict, "growth_multiplier_std")?,
            interest_rate_mean: opt_f64(dict, "interest_rate_mean")?,
            interest_rate_std: opt_f64(dict, "interest_rate_std")?,
            fee_compliance_alpha: opt_f64(dict, "fee_compliance_alpha")?,
            fee_compliance_beta: opt_f64(dict, "fee_compliance_beta")?,
            vendor_capacity_mean: opt_f64(dict, "vendor_capacity_mean")?,
            vendor_capacity_std: opt_f64(dict, "vendor_capacity_std")?,
        })
    }
}
