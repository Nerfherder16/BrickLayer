'use strict';
const fs = require('fs');
const path = require('path');

/**
 * Returns drift summary string for fresh sessions, null when unavailable.
 * @param {string} projectRoot - Project root directory
 * @returns {string|null}
 */
function getDriftSummary(projectRoot) {
  const filePath = path.join(projectRoot, '.autopilot', 'drift-summary.txt');
  try {
    const content = fs.readFileSync(filePath, 'utf8').trim();
    if (!content) return null;
    return '[Last build] ' + content;
  } catch {
    return null;
  }
}

module.exports = { getDriftSummary };
