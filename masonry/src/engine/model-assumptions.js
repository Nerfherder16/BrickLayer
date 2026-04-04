'use strict';
// engine/model-assumptions.js — Utility for reading and appending to model_assumptions.md.
//
// Port of bl/model_assumptions.py to Node.js.

const fs = require('fs');
const path = require('path');

const TEMPLATE = `# Model Assumptions Log

This file tracks design decisions about \`simulate.py\` and \`constants.py\`.
Trowel and specialist agents append here when they change model logic or discover important invariants.

## Format

Each entry:

\`\`\`
## [YYYY-MM-DD] <agent> — <one-line summary>
**Changed**: <what was modified>
**Why**: <reasoning>
**Impact**: <what findings this affects>
\`\`\`

## Entries

<!-- Trowel appends below -->
`;

function ensureExists(projectRoot) {
  const filePath = path.join(String(projectRoot), 'model_assumptions.md');
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, TEMPLATE, 'utf8');
  }
  return filePath;
}

function appendEntry(projectRoot, agent, summary, changed, why, impact) {
  const filePath = ensureExists(projectRoot);
  const today = new Date().toISOString().slice(0, 10);
  const entry = `\n## [${today}] ${agent} — ${summary}\n**Changed**: ${changed}\n**Why**: ${why}\n**Impact**: ${impact}\n`;
  const content = fs.readFileSync(filePath, 'utf8');
  fs.writeFileSync(filePath, content + entry, 'utf8');
}

module.exports = { ensureExists, appendEntry, TEMPLATE };
