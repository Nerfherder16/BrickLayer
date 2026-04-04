'use strict';
// engine/runners/simulate.js — Simulation parameter-sweep runner.
//
// Port of bl/runners/simulate.py to Node.js.
// Exports pure spec-parsing, value coercion, and script-patching functions.
// The full runner requires subprocess execution at runtime.

const CODE_FENCE = '```';

function _coerceValue(raw) {
  const low = raw.toLowerCase();
  if (['true', 'yes'].includes(low)) return true;
  if (['false', 'no'].includes(low)) return false;

  const asInt = parseInt(raw, 10);
  if (String(asInt) === raw) return asInt;

  const asFloat = parseFloat(raw);
  if (!isNaN(asFloat) && String(asFloat) === raw) return asFloat;

  return raw;
}

function _parseSimulateSpec(testField) {
  const spec = {
    script: 'simulate.py',
    stress_param: null,
    stress_range: null,
    stress_steps: 8,
    baseline_check: true,
    timeout: 30,
    params: {},
  };

  let inParamsBlock = false;

  for (const rawLine of testField.split('\n')) {
    const stripped = rawLine.trim();

    if (stripped.startsWith(CODE_FENCE)) continue;

    if (!stripped) {
      inParamsBlock = false;
      continue;
    }

    const low = stripped.toLowerCase();

    if (low.startsWith('script:')) {
      spec.script = stripped.split(':').slice(1).join(':').trim();
      inParamsBlock = false;
      continue;
    }

    if (low.startsWith('stress_param:')) {
      spec.stress_param = stripped.split(':').slice(1).join(':').trim();
      inParamsBlock = false;
      continue;
    }

    if (low.startsWith('stress_range:')) {
      const rawRange = stripped.split(':').slice(1).join(':').trim();
      const numbers = rawRange.match(/[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?/g);
      if (numbers && numbers.length >= 2) {
        spec.stress_range = [parseFloat(numbers[0]), parseFloat(numbers[1])];
      }
      inParamsBlock = false;
      continue;
    }

    if (low.startsWith('stress_steps:')) {
      const val = parseInt(stripped.split(':').slice(1).join(':').trim(), 10);
      if (!isNaN(val)) spec.stress_steps = Math.max(2, val);
      inParamsBlock = false;
      continue;
    }

    if (low.startsWith('baseline_check:')) {
      const val = stripped.split(':').slice(1).join(':').trim().toLowerCase();
      spec.baseline_check = !['false', '0', 'no'].includes(val);
      inParamsBlock = false;
      continue;
    }

    if (low.startsWith('timeout:')) {
      const val = parseInt(stripped.split(':').slice(1).join(':').trim(), 10);
      if (!isNaN(val)) spec.timeout = val;
      inParamsBlock = false;
      continue;
    }

    if (low.startsWith('params:')) {
      inParamsBlock = true;
      const remainder = stripped.split(':').slice(1).join(':').trim();
      if (remainder) {
        const kvMatch = remainder.match(/^(\w+)\s*:\s*(.+)/);
        if (kvMatch) {
          spec.params[kvMatch[1]] = _coerceValue(kvMatch[2].trim());
        }
      }
      continue;
    }

    if (inParamsBlock) {
      const kvMatch = stripped.match(/^(\w+)\s*:\s*(.+)/);
      if (kvMatch) {
        spec.params[kvMatch[1]] = _coerceValue(kvMatch[2].trim());
      }
      continue;
    }
  }

  return spec;
}

function _formatValue(value) {
  if (typeof value === 'boolean') return value ? 'True' : 'False';
  if (typeof value === 'string') return JSON.stringify(value);
  return String(value);
}

function _patchScriptSource(source, paramOverrides) {
  const lines = source.split('\n');
  const patchedParams = new Set();

  for (let i = 0; i < lines.length; i++) {
    for (const [param, value] of Object.entries(paramOverrides)) {
      if (patchedParams.has(param)) continue;

      const pattern = new RegExp(
        '^(\\s*' + param.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\s*=\\s*)(.+?)(\\s*(?:#.*)?)$',
      );
      const m = lines[i].match(pattern);
      if (m) {
        const trailing = m[3].trim().startsWith('#') ? m[3] : '';
        lines[i] = `${m[1]}${_formatValue(value)}${trailing}`;
        patchedParams.add(param);
        break;
      }
    }
  }

  // Append missing parameters
  const missing = Object.keys(paramOverrides).filter((p) => !patchedParams.has(p));
  if (missing.length > 0) {
    lines.push('');
    lines.push('# -- simulate runner overrides --');
    for (const param of missing.sort()) {
      lines.push(`${param} = ${_formatValue(paramOverrides[param])}`);
    }
  }

  return lines.join('\n');
}

module.exports = {
  _coerceValue,
  _parseSimulateSpec,
  _formatValue,
  _patchScriptSource,
};
