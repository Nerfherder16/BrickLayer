'use strict';
// engine/runners/contract.js — Static analysis runner for Solana/Anchor contracts.
//
// Port of bl/runners/contract.py to Node.js.
// Exports pure check functions that operate on in-memory source strings.
// The full runner wraps these with file collection and verdict aggregation.

const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Finding helpers
// ---------------------------------------------------------------------------

function _makeFinding(filePath, lineNo, snippet, severity, message) {
  return {
    file: String(filePath),
    line: lineNo,
    snippet: snippet.trim().slice(0, 120),
    severity,
    message,
  };
}

function _linesWithNumbers(src) {
  return src.split('\n').map((line, i) => [i + 1, line]);
}

function _readFile(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf8');
  } catch {
    return '';
  }
}

// ---------------------------------------------------------------------------
// Check: overflow_patterns
// ---------------------------------------------------------------------------

const _ARITH_OP_RE = /\b(\w+)\s*([+\-*])\s*(\w+)\b(?!\s*\()/;
const _SAFE_ARITH_RE = /\b(?:checked_add|checked_sub|checked_mul|checked_div|saturating_add|saturating_sub|saturating_mul|wrapping_add|wrapping_sub|wrapping_mul|u128::from|i128::from|overflow_ops)\b/;
const _SKIP_LINE_RE = /^\s*(?:\/\/|use |pub use |#\[|let\s+\w+\s*=\s*")/;

function _checkOverflowPatterns(files) {
  const findings = [];

  for (const filePath of files) {
    const src = _readFile(filePath);
    if (!src) continue;

    for (const [lineNo, line] of _linesWithNumbers(src)) {
      if (_SKIP_LINE_RE.test(line)) continue;

      const stripped = line.trim();
      if (stripped.startsWith('//') || stripped.startsWith('*')) continue;
      if (_SAFE_ARITH_RE.test(line)) continue;

      const m = line.match(_ARITH_OP_RE);
      if (!m) continue;

      const [, lhs, op, rhs] = m;

      // Skip numeric literals and loop variables
      if (/^\d+$/.test(lhs) || /^\d+$/.test(rhs)) continue;
      if (['i', 'j', 'k', 'n', 'idx', 'len'].includes(lhs)) continue;
      if (lhs.length < 2 || rhs.length < 2) continue;

      findings.push(
        _makeFinding(
          filePath,
          lineNo,
          stripped.slice(0, 80),
          'warning',
          `Unchecked arithmetic '${lhs} ${op} ${rhs}' — use checked_/saturating_ variants`,
        ),
      );
    }
  }

  return findings;
}

// ---------------------------------------------------------------------------
// Check: seed_canonicalization
// ---------------------------------------------------------------------------

const _CREATE_PDA_RE = /\bcreate_program_address\s*\(/;

function _checkSeedCanonicalization(files) {
  const findings = [];

  for (const filePath of files) {
    const src = _readFile(filePath);
    if (!src) continue;

    for (const [lineNo, line] of _linesWithNumbers(src)) {
      if (_CREATE_PDA_RE.test(line)) {
        findings.push(
          _makeFinding(
            filePath,
            lineNo,
            line.trim().slice(0, 80),
            'warning',
            'create_program_address used — prefer find_program_address to enforce canonical bump',
          ),
        );
      }
    }
  }

  return findings;
}

// ---------------------------------------------------------------------------
// Check: pattern_search
// ---------------------------------------------------------------------------

function _checkPatternSearch(files, patterns) {
  const findings = [];

  const compiled = [];
  for (const p of patterns) {
    const raw = p.pattern || '';
    if (!raw) continue;
    try {
      compiled.push([
        new RegExp(raw),
        p.severity || 'warning',
        p.message || raw,
      ]);
    } catch {
      // Skip invalid patterns
    }
  }

  for (const filePath of files) {
    const src = _readFile(filePath);
    if (!src) continue;

    for (const [lineNo, line] of _linesWithNumbers(src)) {
      for (const [patRe, severity, message] of compiled) {
        if (patRe.test(line)) {
          findings.push(
            _makeFinding(filePath, lineNo, line.trim().slice(0, 80), severity, message),
          );
          break; // One finding per line
        }
      }
    }
  }

  return findings;
}

// ---------------------------------------------------------------------------
// Verdict determination
// ---------------------------------------------------------------------------

function _determineVerdict(
  allFindings,
  signerFailures,
  reentrancyCount,
  uncheckedFields,
  overflowCount,
  maxUncheckedFields,
  maxOverflowSites,
) {
  const reasonsFailure = [];
  const reasonsWarning = [];

  if (signerFailures > 0) {
    reasonsFailure.push(`${signerFailures} handler(s) with no signer check`);
  }
  if (reentrancyCount > 0) {
    reasonsFailure.push(`${reentrancyCount} reentrancy pattern(s)`);
  }
  if (uncheckedFields > maxUncheckedFields) {
    reasonsFailure.push(
      `${uncheckedFields} unchecked field(s) (max ${maxUncheckedFields})`,
    );
  }

  if (overflowCount > maxOverflowSites) {
    reasonsWarning.push(
      `${overflowCount} unchecked arithmetic site(s) (threshold ${maxOverflowSites})`,
    );
  }

  // Critical findings from pattern_search also cause FAILURE
  const patternCriticals = allFindings.filter(
    (f) =>
      f.severity === 'critical' &&
      !f.message.includes('Handler') &&
      !f.message.toLowerCase().includes('reentrancy'),
  );
  if (patternCriticals.length > 0) {
    reasonsFailure.push(`${patternCriticals.length} critical pattern finding(s)`);
  }

  const total = allFindings.length;
  let verdict;
  let summary;

  if (reasonsFailure.length > 0) {
    verdict = 'FAILURE';
    summary = reasonsFailure.join('; ');
    if (reasonsWarning.length > 0) {
      summary += ' | warnings: ' + reasonsWarning.join('; ');
    }
  } else if (
    reasonsWarning.length > 0 ||
    allFindings.some((f) => f.severity === 'warning')
  ) {
    verdict = 'WARNING';
    const parts = reasonsWarning.slice();
    if (parts.length === 0) {
      const warningCount = allFindings.filter((f) => f.severity === 'warning').length;
      parts.push(`${warningCount} warning(s)`);
    }
    summary = parts.join('; ');
  } else {
    verdict = 'HEALTHY';
    summary = `No issues found — ${total} total findings (all info)`;
  }

  if (total === 0) {
    summary = 'No findings';
  }

  return [verdict, summary];
}

module.exports = {
  _makeFinding,
  _checkOverflowPatterns,
  _checkSeedCanonicalization,
  _checkPatternSearch,
  _determineVerdict,
};
