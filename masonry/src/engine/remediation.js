'use strict';
// engine/remediation.js — Remediation feasibility estimation (C-29).
//
// Port of bl/quality.py to Node.js.
// Note: renamed to remediation.js to avoid collision with runners/quality.js.

function estimateRemediationFeasibility({
  actionType,
  currentMean,
  healthyThreshold,
  floor = null,
  nAffected = 0,
  corpusSize = 1,
}) {
  if (actionType === 'amnesty' && floor !== null) {
    let projected, delta, reason;

    if (floor <= currentMean) {
      projected = currentMean;
      delta = 0;
      reason = `amnesty floor=${floor.toFixed(2)} <= current mean=${currentMean.toFixed(3)} — no delta possible`;
    } else {
      const maxDelta = (floor - currentMean) * (nAffected / corpusSize);
      projected = currentMean + maxDelta;
      delta = maxDelta;
      reason = `amnesty floor=${floor.toFixed(2)} on ${nAffected}/${corpusSize} memories → projected_mean=${projected.toFixed(3)}`;
    }

    return {
      feasible: projected >= healthyThreshold,
      projectedMean: projected,
      delta,
      reason,
    };
  }

  // Unknown action type
  return {
    feasible: null,
    projectedMean: null,
    delta: null,
    reason: `unknown action_type '${actionType}' — cannot estimate`,
  };
}

module.exports = { estimateRemediationFeasibility };
