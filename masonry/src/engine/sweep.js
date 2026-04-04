'use strict';
// engine/sweep.js — Parameter sweep harness.
//
// Port of bl/sweep.py to Node.js. Validates sweep parameters against
// a project's simulate.py SCENARIO PARAMETERS block. The actual sweep
// execution calls the simulate module (Python) as a subprocess.

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

/**
 * Check that paramName exists in simulate.py's SCENARIO PARAMETERS block.
 * @returns {[boolean, string]} [ok, errorMessage]
 */
function validateSweepParameter(projectRoot, paramName) {
  const simulatePath = path.join(projectRoot, 'simulate.py');
  if (!fs.existsSync(simulatePath)) {
    return [false, `SWEEP_BLOCKED: simulate.py not found in ${projectRoot}`];
  }

  const content = fs.readFileSync(simulatePath, 'utf8');
  if (!content.includes('# SCENARIO PARAMETERS')) {
    return [false, "SWEEP_BLOCKED: no '# SCENARIO PARAMETERS' block found in simulate.py"];
  }

  const block = content.slice(content.indexOf('# SCENARIO PARAMETERS'));
  if (!block.includes(paramName)) {
    return [false, `SWEEP_BLOCKED: parameter '${paramName}' not found in simulate.py SCENARIO PARAMETERS block`];
  }

  return [true, ''];
}

/**
 * Run a sweep by calling the Python simulate module as a subprocess.
 * This delegates to Python since simulate.py is a Python file.
 */
function sweep(projectDir, paramName, values, scenarios, baseParams) {
  const [ok, err] = validateSweepParameter(projectDir, paramName);
  if (!ok) return [{ error: err, param_name: paramName }];

  const effectiveScenarios = scenarios || ['baseline'];
  const results = [];

  for (const scenario of effectiveScenarios) {
    for (const value of values) {
      const params = { ...(baseParams || {}), [paramName]: value };
      try {
        // Call Python sweep subprocess
        const script = `
import json, sys
sys.path.insert(0, ${JSON.stringify(projectDir)})
import simulate
for k, v in json.loads(sys.argv[1]).items():
    setattr(simulate, k, v)
records, failure_reason = simulate.run_simulation()
evaluation = simulate.evaluate(records, failure_reason)
print(json.dumps({
    "verdict": evaluation.get("verdict", "FAILURE"),
    "failure_reason": failure_reason,
    "final_primary": records[-1]["primary"] if records else 0.0,
    "record_count": len(records),
}))
`;
        const output = execFileSync('python3', ['-c', script, JSON.stringify(params)], {
          encoding: 'utf8',
          timeout: 60000,
          cwd: projectDir,
        });
        const result = JSON.parse(output.trim());
        results.push({
          param_name: paramName,
          param_value: value,
          scenario,
          ...result,
        });
      } catch (e) {
        results.push({
          param_name: paramName,
          param_value: value,
          scenario,
          verdict: 'FAILURE',
          failure_reason: e.message,
          final_primary: 0.0,
          record_count: 0,
        });
      }
    }
  }

  results.sort((a, b) => {
    if (a.scenario !== b.scenario) return a.scenario < b.scenario ? -1 : 1;
    return a.param_value < b.param_value ? -1 : a.param_value > b.param_value ? 1 : 0;
  });

  return results;
}

module.exports = {
  validateSweepParameter,
  sweep,
};
