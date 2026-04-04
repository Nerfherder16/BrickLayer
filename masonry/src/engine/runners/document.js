'use strict';
// engine/runners/document.js — Documentation completeness and accuracy runner.
//
// Port of bl/runners/document.py to Node.js.
// Exports pure check functions that operate on strings and file paths.

const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Regex patterns
// ---------------------------------------------------------------------------

const _ROUTE_CAPTURE_RE = /@(?:app|router)\.(?:get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]/gi;
const _FUNC_DEF_RE = /^\s*def ([a-zA-Z][a-zA-Z0-9_]*)\s*\(/gm;
const _CODE_BLOCK_RE = /```(\w+)?\n([\s\S]*?)```/g;
const _MARKDOWN_LINK_RE = /\[([^\]]+)\]\(([^)]+)\)/g;

// ---------------------------------------------------------------------------
// Check: endpoint_coverage
// ---------------------------------------------------------------------------

function _checkEndpointCoverage(sourceFiles, docText, pattern, minCoverage) {
  const routeRe = new RegExp(pattern, 'gi');
  const foundRoutes = [];

  for (const sf of sourceFiles) {
    let src;
    try {
      src = fs.readFileSync(sf, 'utf8');
    } catch {
      continue;
    }

    if (!routeRe.test(src)) continue;
    routeRe.lastIndex = 0;

    // Extract route paths
    const captureRe = new RegExp(_ROUTE_CAPTURE_RE.source, 'gi');
    let m;
    while ((m = captureRe.exec(src)) !== null) {
      foundRoutes.push(m[1]);
    }
  }

  if (foundRoutes.length === 0) {
    return {
      passed: true,
      coverage: null,
      issues: [],
      count: 0,
      note: 'No routes found in source — check that code_path points to API files',
    };
  }

  const documented = [];
  const missing = [];
  for (const route of foundRoutes) {
    if (docText.includes(route)) {
      documented.push(route);
    } else {
      missing.push(route);
    }
  }

  const coverage = documented.length / foundRoutes.length;
  const passed = coverage >= minCoverage;

  return {
    passed,
    coverage: Math.round(coverage * 1000) / 1000,
    issues: missing.map((r) => `Missing: ${r}`),
    count: foundRoutes.length,
  };
}

// ---------------------------------------------------------------------------
// Check: function_coverage
// ---------------------------------------------------------------------------

function _checkFunctionCoverage(sourceFiles, docText, minCoverage) {
  const publicFuncs = [];

  for (const sf of sourceFiles) {
    let src;
    try {
      src = fs.readFileSync(sf, 'utf8');
    } catch {
      continue;
    }

    const funcRe = new RegExp(_FUNC_DEF_RE.source, 'gm');
    let m;
    while ((m = funcRe.exec(src)) !== null) {
      const name = m[1];
      if (!name.startsWith('_')) {
        publicFuncs.push(name);
      }
    }
  }

  // Deduplicate while preserving order
  const seen = new Set();
  const uniqueFuncs = [];
  for (const fn of publicFuncs) {
    if (!seen.has(fn)) {
      seen.add(fn);
      uniqueFuncs.push(fn);
    }
  }

  if (uniqueFuncs.length === 0) {
    return {
      passed: true,
      coverage: null,
      issues: [],
      count: 0,
      note: 'No public functions found in source',
    };
  }

  const documented = uniqueFuncs.filter((fn) => docText.includes(fn));
  const missing = uniqueFuncs.filter((fn) => !docText.includes(fn));

  const coverage = documented.length / uniqueFuncs.length;
  const passed = coverage >= minCoverage;

  return {
    passed,
    coverage: Math.round(coverage * 1000) / 1000,
    issues: missing.map((fn) => `Undocumented function: ${fn}`),
    count: uniqueFuncs.length,
  };
}

// ---------------------------------------------------------------------------
// Check: example_syntax
// ---------------------------------------------------------------------------

function _tryParsePython(code) {
  // Basic Python syntax validation — check for obvious syntax errors
  // This is a simplified check since we don't have a Python parser in Node.
  // Check for unbalanced parens/brackets/braces and incomplete constructs.
  let parens = 0;
  let brackets = 0;
  let braces = 0;
  for (const ch of code) {
    if (ch === '(') parens++;
    else if (ch === ')') parens--;
    else if (ch === '[') brackets++;
    else if (ch === ']') brackets--;
    else if (ch === '{') braces++;
    else if (ch === '}') braces--;
    if (parens < 0 || brackets < 0 || braces < 0) {
      return 'Unbalanced brackets';
    }
  }
  if (parens !== 0) return 'Unbalanced parentheses';
  if (brackets !== 0) return 'Unbalanced brackets';
  if (braces !== 0) return 'Unbalanced braces';
  return null;
}

function _tryParseJson(code) {
  try {
    JSON.parse(code);
    return null;
  } catch (e) {
    return e.message;
  }
}

const _SYNTAX_PARSERS = {
  python: _tryParsePython,
  py: _tryParsePython,
  json: _tryParseJson,
};

function _checkExampleSyntax(docText, languages) {
  const langSet = new Set((languages || []).map((l) => l.toLowerCase()));
  let total = 0;
  const failedBlocks = [];

  const codeBlockRe = new RegExp(_CODE_BLOCK_RE.source, 'g');
  let m;
  while ((m = codeBlockRe.exec(docText)) !== null) {
    const lang = (m[1] || '').toLowerCase().trim();
    const code = m[2];

    if (langSet.size > 0 && !langSet.has(lang)) continue;

    const parser = _SYNTAX_PARSERS[lang];
    if (!parser) continue;

    total++;
    const error = parser(code);
    if (error !== null) {
      const snippet = code.slice(0, 60).replace(/\n/g, ' ').trim();
      failedBlocks.push(`Invalid ${lang} block: ${error} — \`${snippet}...\``);
    }
  }

  if (total === 0) {
    return {
      passed: true,
      coverage: null,
      issues: [],
      count: 0,
      note: 'No parseable code blocks found',
    };
  }

  const failRate = failedBlocks.length / total;
  const passed = failRate <= 0.20;

  return {
    passed,
    coverage: Math.round((1.0 - failRate) * 1000) / 1000,
    issues: failedBlocks,
    count: total,
  };
}

// ---------------------------------------------------------------------------
// Check: dead_links
// ---------------------------------------------------------------------------

function _checkDeadLinks(docPaths, docText) {
  const baseDirs = docPaths
    .map((dp) => (typeof dp === 'string' ? dp : String(dp)))
    .filter((dp) => fs.existsSync(dp))
    .map((dp) => path.dirname(dp));
  const baseDir = baseDirs.length > 0 ? baseDirs[0] : '.';

  const allLinks = [];
  const linkRe = new RegExp(_MARKDOWN_LINK_RE.source, 'g');
  let m;
  while ((m = linkRe.exec(docText)) !== null) {
    allLinks.push([m[1], m[2]]);
  }

  const dead = [];
  let checked = 0;

  for (const [text, url] of allLinks) {
    // Skip external links
    if (/^(https?|ftp|mailto):/.test(url) || url.startsWith('#')) continue;

    // Strip fragment
    const localPath = url.split('#')[0];
    if (!localPath) continue;

    checked++;
    const resolved = path.resolve(baseDir, localPath);
    if (!fs.existsSync(resolved)) {
      dead.push(`Dead link: [${text}](${url})`);
    }
  }

  return {
    passed: dead.length === 0,
    coverage: null,
    issues: dead,
    count: checked,
  };
}

// ---------------------------------------------------------------------------
// Check: keyword_presence
// ---------------------------------------------------------------------------

function _checkKeywordPresence(docText, keywords) {
  const docLower = docText.toLowerCase();
  const missing = [];
  for (const kw of keywords) {
    if (!docLower.includes(kw.toLowerCase())) {
      missing.push(`Missing keyword: '${kw}'`);
    }
  }

  const total = keywords.length;
  const present = total - missing.length;
  const coverage = total > 0 ? present / total : 1.0;

  return {
    passed: missing.length === 0,
    coverage: Math.round(coverage * 1000) / 1000,
    issues: missing,
    count: total,
  };
}

// ---------------------------------------------------------------------------
// Verdict logic
// ---------------------------------------------------------------------------

const _COVERAGE_CHECK_TYPES = new Set(['endpoint_coverage', 'function_coverage']);

function _determineVerdict(checkResults, minCoverage) {
  let hasFailure = false;
  let hasWarning = false;

  for (const [checkType, result] of Object.entries(checkResults)) {
    const passed = result.passed || false;
    const coverage = result.coverage;

    if (!passed) {
      if (_COVERAGE_CHECK_TYPES.has(checkType) && coverage !== null && coverage !== undefined) {
        if (coverage < minCoverage) {
          hasFailure = true;
        } else {
          hasWarning = true;
        }
      } else if (checkType === 'example_syntax') {
        hasFailure = true;
      } else if (checkType === 'freshness') {
        hasFailure = true;
      } else if (checkType === 'dead_links') {
        hasWarning = true;
      } else if (checkType === 'keyword_presence') {
        hasWarning = true;
      } else {
        hasFailure = true;
      }
    } else {
      if (coverage !== null && coverage !== undefined && coverage < 1.0) {
        hasWarning = true;
      }
    }
  }

  if (hasFailure) return 'FAILURE';
  if (hasWarning) return 'WARNING';
  return 'HEALTHY';
}

module.exports = {
  _checkEndpointCoverage,
  _checkFunctionCoverage,
  _checkExampleSyntax,
  _checkDeadLinks,
  _checkKeywordPresence,
  _determineVerdict,
};
