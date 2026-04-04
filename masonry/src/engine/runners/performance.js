'use strict';
// engine/runners/performance.js — Async HTTP load-test runner utilities.
//
// Port of bl/runners/performance.py to Node.js.
// Exports the pure _percentile utility. The full runner requires
// an HTTP client and live API target at runtime.

function _percentile(values, p) {
  if (!values.length) return 0.0;
  const sorted = [...values].sort((a, b) => a - b);
  const idx = Math.min(Math.floor(sorted.length * p / 100), sorted.length - 1);
  return sorted[idx];
}

module.exports = {
  _percentile,
};
