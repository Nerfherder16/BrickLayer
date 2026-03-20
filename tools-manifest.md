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

## agent-fleet-management
Agent self-improvement tools. These are not MCP tools — they are agent files invoked by
mortar at specific trigger points during the campaign loop.

- `agent-auditor` — Scores agent fleet performance using findings and results.tsv. Writes AUDIT_REPORT.md.
  Trigger: every 10 questions (background) + wave end (foreground). Inputs: agents_dir, findings_dir, results_tsv.
  Output: `.claude/agents/AUDIT_REPORT.md` with fleet scorecard and underperformer analysis.

- `overseer` — Fleet manager. Reads agent_db.json + AUDIT_REPORT.md, rewrites underperforming agent .md files,
  creates new agents from FORGE_NEEDED.md. Trigger: when agent-auditor reports FLEET_UNDERPERFORMING.
  Inputs: agent_db_json, agents_dir, findings_dir, project_brief. Output: OVERSEER_REPORT.md, edited agent files.

- `skill-forge` — Distills campaign findings into reusable skills at ~/.claude/skills/. Writes skill_registry.json.
  Trigger: wave end (after synthesis). Inputs: synthesis_md, findings_dir, project_root, skill_registry_json,
  skills_dir (~/.claude/skills/), project_name. Output: new SKILL.md files + SKILL_FORGE_LOG.md.

- `forge-check` — Scans agent fleet for capability gaps. Writes FORGE_NEEDED.md if gaps found.
  Trigger: every 5 questions (background) + wave end. Inputs: agents_dir, findings_dir, questions_md.
  Output: `.claude/agents/FORGE_NEEDED.md` (consumed by overseer).

- `agent_db.json` — Per-agent performance database at project root. Written by mortar after every finding.
  Schema: `{ "agent_name": { runs, verdicts: {}, score, last_run, created, repair_count, last_repair, run_history: [] } }`.
  Python API: `from bl.agent_db import record_run, get_score, get_trend, get_underperformers`.

