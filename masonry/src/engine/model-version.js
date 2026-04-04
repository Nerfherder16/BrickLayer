'use strict';
// engine/model-version.js — Content hash of simulate.py + constants.py for finding correlation.
//
// Port of bl/model_version.py to Node.js.

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

function computeModelHash(projectRoot) {
  const root = String(projectRoot);
  let content = Buffer.alloc(0);
  let found = false;

  for (const fname of ['simulate.py', 'constants.py']) {
    const fpath = path.join(root, fname);
    try {
      const data = fs.readFileSync(fpath);
      content = Buffer.concat([content, data]);
      found = true;
    } catch {
      // file doesn't exist — skip
    }
  }

  if (!found) return 'no-model';
  return crypto.createHash('sha256').update(content).digest('hex').slice(0, 12);
}

function embedInFinding(content, modelHash) {
  if (content.includes('**Model hash**:')) return content;
  return content.trimEnd() + `\n\n**Model hash**: ${modelHash}\n`;
}

module.exports = { computeModelHash, embedInFinding };
