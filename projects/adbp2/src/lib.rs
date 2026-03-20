use pyo3::prelude::*;

/// Smoke test — validates that the maturin build chain works.
#[pyfunction]
fn hello() -> &'static str {
    "adbp2_mc loaded"
}

/// PyO3 module entry point.
#[pymodule]
fn adbp2_mc(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello, m)?)?;
    Ok(())
}
