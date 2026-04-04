'use strict';
// engine/json-validate.js — Validate the JSON output block in BL 2.0 findings.
//
// Port of bl/json_validate.py to Node.js.

const REQUIRED_JSON_FIELDS = new Set(['verdict', 'question_id']);

const _JSON_FENCE_PATTERN = /```json\s*\n(.*?)```/gs;

function validateFindingJson(findingText) {
  const matches = [...findingText.matchAll(_JSON_FENCE_PATTERN)];
  if (matches.length === 0) return [null, null];

  const raw = matches[matches.length - 1][1].trim();

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (exc) {
    return [null, `JSON parse error: ${exc.message}`];
  }

  const keys = new Set(Object.keys(parsed));
  const missing = [...REQUIRED_JSON_FIELDS].filter(f => !keys.has(f));
  if (missing.length > 0) {
    return [null, `missing required fields: ${missing.sort().join(', ')}`];
  }

  return [parsed, null];
}

function isRetry(questionStatus) {
  return questionStatus.includes('PENDING_RETRY') || questionStatus.includes('FORMAT-RETRY');
}

module.exports = { validateFindingJson, isRetry, REQUIRED_JSON_FIELDS };
