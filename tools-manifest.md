# Tools Manifest

This file lists all MCP tools and CLI tools available to Masonry agents.
Mortar prepends this to every agent spawn prompt.

## masonry

### masonry_run_simulation
Run a single simulation with the given parameters.
- **project_path** (required): Absolute path to project directory containing simulate.py
- **months** (optional): Number of months to simulate (default: 36)
- **monthly_growth_rate** (optional): Monthly growth rate decimal
- **churn_rate** (optional): Monthly churn rate decimal
- **price_per_unit** (optional): Revenue per unit
- **ops_cost_base** (optional): Base operating cost
- **Returns**: `{verdict, failure_reason, records, ...eval fields}`

Example:
```json
{"tool": "masonry_run_simulation", "project_path": "/path/to/project", "months": 36, "churn_rate": 0.05}
```

### masonry_sweep
Run a parameter sweep across multiple values and optionally multiple scenarios.
- **project_path** (required): Absolute path to project directory
- **param_name** (required): Parameter name to sweep (e.g. "churn_rate")
- **values** (required): Array of numeric values to test
- **scenarios** (optional): Array of scenario name strings
- **base_params** (optional): Object of base parameter overrides
- **Returns**: `{results: [...], count: N}` where each result has param_name, param_value, scenario, verdict, failure_reason, final_primary, record_count

Example:
```json
{"tool": "masonry_sweep", "project_path": "/path/to/project", "param_name": "churn_rate", "values": [0.03, 0.05, 0.08, 0.12]}
```
