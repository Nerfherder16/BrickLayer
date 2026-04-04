'use strict';
// engine/runners/quality.js — Static quality analysis runner.
//
// Port of bl/runners/quality.py to Node.js.

const fs = require('fs');

function _analyzeQualityPatterns(question, files, content, missing, totalLines) {
  const hypothesis = (question.hypothesis || '').toLowerCase();

  // Logger mismatch detection
  if (hypothesis.includes('structlog') && (hypothesis.includes('stdlib') || hypothesis.includes('logging.getlogger') || hypothesis.includes('mismatch'))) {
    const failures = [];
    const warnings = [];
    for (const fpath of files) {
      let src;
      try {
        src = fs.readFileSync(fpath, 'utf8');
      } catch {
        continue;
      }
      const fname = fpath.split('/').pop();
      const hasStdlib = /^import logging\b/m.test(src);
      const hasStructlog = /import structlog/.test(src);
      const stdlibKwargCalls = src.match(/(?:logging\.\w+|logger\.\w+)\([^)]*,\s*\w+=/g);
      const usesStdlibLogger = /logging\.getLogger\(\)/.test(src);
      if (hasStdlib && hasStructlog) {
        if (stdlibKwargCalls && usesStdlibLogger) {
          failures.push(`${fname}: stdlib logger called with kwargs — TypeError in except blocks`);
        } else {
          warnings.push(`${fname}: mixed imports (stdlib + structlog) but no kwarg-passing found`);
        }
      }
    }
    if (failures.length) return ['FAILURE', `Logger mismatch: ${failures.join('; ')}`];
    if (warnings.length) return ['WARNING', `Mixed logger imports: ${warnings.join('; ')}`];
    return ['HEALTHY', `Checked ${files.length} files — all consistently use structlog`];
  }

  // utcnow deprecation
  if (hypothesis.includes('utcnow')) {
    const hits = content.match(/datetime\.utcnow\(\)/g);
    if (hits) {
      const fileHits = files.filter(f => {
        try { return fs.readFileSync(f, 'utf8').includes('datetime.utcnow()'); } catch { return false; }
      }).map(f => f.split('/').pop());
      return ['FAILURE', `Found ${hits.length} datetime.utcnow() calls in ${fileHits.length} files: ${fileHits.slice(0, 5).join(', ')}`];
    }
    return ['HEALTHY', `No datetime.utcnow() calls found in ${files.length} files`];
  }

  // N+1 query pattern
  if (hypothesis.includes('n+1') || (hypothesis.includes('loop') && hypothesis.includes('db'))) {
    const loopDbPattern = content.match(/for\s+\w+\s+in\s+\w+[^:]+:\s*\n(?:.*\n){0,5}.*(?:session\.|qdrant\.|redis\.)/g);
    if (loopDbPattern) {
      return ['FAILURE', `Potential N+1 pattern: DB call inside result loop (${loopDbPattern.length} instances)`];
    }
    return ['HEALTHY', 'No N+1 DB-inside-loop patterns detected'];
  }

  // Fallback
  if (missing.length) {
    return ['INCONCLUSIVE', `Read ${files.length - missing.length}/${files.length} files (${totalLines} lines). Missing: ${missing.join(', ')}`];
  }
  return ['INCONCLUSIVE', `Read ${files.length} source files (${totalLines} lines) — requires agent analysis for verdict`];
}

function runQuality(question) {
  const target = question.target || '';
  if (!target) {
    return {
      verdict: 'INCONCLUSIVE',
      summary: 'No target specified',
      data: { target },
      details: 'Check target field in questions.md',
    };
  }

  // Simplified file collection — in real use, cfg.recallSrc would be used
  return {
    verdict: 'INCONCLUSIVE',
    summary: `Quality runner: target=${target}`,
    data: { target },
    details: 'File collection delegated to actual project context',
  };
}

module.exports = {
  runQuality,
  _analyzeQualityPatterns,
};
