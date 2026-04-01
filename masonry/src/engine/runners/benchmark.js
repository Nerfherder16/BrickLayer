'use strict';
// engine/runners/benchmark.js — ML inference endpoint benchmark runner.
//
// Port of bl/runners/benchmark.py to Node.js.
// Exports pure spec-parsing and utility functions.
// The full runner requires httpx-equivalent HTTP client at runtime.

function _coerce(raw) {
  const low = raw.toLowerCase();
  if (['null', 'none', '~'].includes(low)) return null;
  if (['true', 'yes'].includes(low)) return true;
  if (['false', 'no'].includes(low)) return false;

  // Strip surrounding quotes
  if (
    (raw.startsWith('"') && raw.endsWith('"')) ||
    (raw.startsWith("'") && raw.endsWith("'"))
  ) {
    return raw.slice(1, -1);
  }

  const asInt = parseInt(raw, 10);
  if (String(asInt) === raw) return asInt;

  const asFloat = parseFloat(raw);
  if (!isNaN(asFloat) && String(asFloat) === raw) return asFloat;

  return raw;
}

function _percentile(values, p) {
  if (values.length === 1) return values[0];
  const sorted = [...values].sort((a, b) => a - b);
  const idx = (p / 100.0) * (sorted.length - 1);
  const lo = Math.floor(idx);
  const hi = Math.min(lo + 1, sorted.length - 1);
  const frac = idx - lo;
  return sorted[lo] + frac * (sorted[hi] - sorted[lo]);
}

function _parseSpecText(text) {
  const spec = {};
  let currentSection = null;
  let currentListItem = null;
  let listTarget = null;

  for (const rawLine of text.split('\n')) {
    const stripped = rawLine.trim();
    if (!stripped || stripped.startsWith('#')) continue;

    const indent = rawLine.length - rawLine.trimStart().length;

    // List item under a nested section
    if (stripped.startsWith('- ') && currentSection && indent >= 4) {
      if (currentListItem !== null && listTarget !== null) {
        listTarget.push(currentListItem);
      }
      currentListItem = {};
      const rest = stripped.slice(2).trim();
      if (rest.includes(':')) {
        const colonIdx = rest.indexOf(':');
        const k = rest.slice(0, colonIdx).trim();
        const v = rest.slice(colonIdx + 1).trim();
        if (v) currentListItem[k] = _coerce(v);
      }
      continue;
    }

    // Key: value inside a list item (deeper indent)
    if (currentListItem !== null && indent >= 6 && stripped.includes(':')) {
      const colonIdx = stripped.indexOf(':');
      const k = stripped.slice(0, colonIdx).trim();
      const v = stripped.slice(colonIdx + 1).trim();
      if (v) currentListItem[k] = _coerce(v);
      continue;
    }

    // Flush pending list item when indent drops
    if (currentListItem !== null && indent < 6) {
      if (listTarget !== null) {
        listTarget.push(currentListItem);
      }
      currentListItem = null;
      listTarget = null;
    }

    // Nested key: value under a section (indent 2-5)
    if (indent >= 2 && currentSection && stripped.includes(':')) {
      const colonIdx = stripped.indexOf(':');
      const key = stripped.slice(0, colonIdx).trim();
      const valStr = stripped.slice(colonIdx + 1).trim();
      if (!spec[currentSection] || typeof spec[currentSection] !== 'object') {
        spec[currentSection] = {};
      }
      if (!valStr) {
        // Start of a nested list (e.g. "prompts:")
        spec[currentSection][key] = [];
        listTarget = spec[currentSection][key];
      } else {
        spec[currentSection][key] = _coerce(valStr);
      }
      continue;
    }

    // Top-level key: value (indent 0-1)
    if (stripped.includes(':') && indent < 2) {
      const colonIdx = stripped.indexOf(':');
      const key = stripped.slice(0, colonIdx).trim();
      const valStr = stripped.slice(colonIdx + 1).trim();
      if (!valStr) {
        // Section header
        spec[key] = {};
        currentSection = key;
      } else {
        spec[key] = _coerce(valStr);
        currentSection = null;
      }
      continue;
    }
  }

  // Flush trailing list item
  if (currentListItem !== null && listTarget !== null) {
    listTarget.push(currentListItem);
  }

  return spec;
}

function _extractSpec(question) {
  const spec = question.spec;
  if (spec && typeof spec === 'object' && !Array.isArray(spec)) {
    return spec;
  }

  const testField = question.test || question.Test || '';
  if (testField) {
    return _parseSpecText(testField);
  }

  return null;
}

module.exports = {
  _coerce,
  _percentile,
  _parseSpecText,
  _extractSpec,
};
