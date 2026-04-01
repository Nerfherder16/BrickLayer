'use strict';
// engine/runners/agent.js — Specialist agent runner and output parsing.
//
// Port of bl/runners/agent.py to Node.js.

const { cfg } = require('../config');
const { spawnAgent, waitForAgent, spawnWave, collectWave } = require('../tmux');

const _ALL_VERDICTS = new Set([
  'HEALTHY', 'WARNING', 'FAILURE', 'INCONCLUSIVE',
  'DIAGNOSIS_COMPLETE', 'FIXED', 'FIX_FAILED',
  'COMPLIANT', 'NON_COMPLIANT', 'PARTIAL', 'NOT_APPLICABLE',
  'CALIBRATED', 'UNCALIBRATED', 'NOT_MEASURABLE',
  'IMPROVEMENT', 'REGRESSION',
  'IMMINENT', 'PROBABLE', 'POSSIBLE', 'UNLIKELY',
  'OK', 'DEGRADED', 'DEGRADED_TRENDING', 'ALERT', 'UNKNOWN',
  'PROMISING', 'BLOCKED', 'WEAK', 'SUBJECTIVE',
  'PENDING_EXTERNAL',
]);

function _verdictFromAgentOutput(agentName, output) {
  if (!output) return 'INCONCLUSIVE';

  if (agentName === 'security-hardener') {
    if ((output.risks_fixed || 0) > 0 || (output.changes_committed || 0) > 0) return 'HEALTHY';
    if ((output.risks_reported || 0) > 0) return 'WARNING';
  } else if (agentName === 'test-writer') {
    const before = output.coverage_before || 0;
    const after = output.coverage_after || 0;
    const written = output.tests_written || 0;
    if (written > 0 && after > before) return 'HEALTHY';
    if (written > 0) return 'WARNING';
  } else if (agentName === 'type-strictener') {
    const before = output.errors_before || 0;
    const after = output.errors_after || 0;
    const committed = output.changes_committed || 0;
    if (committed > 0 && after < before) return 'HEALTHY';
    if (committed > 0) return 'WARNING';
    if (output.mitigation_required === false) return 'HEALTHY';
    if (output.architectural_debt && !committed) return 'WARNING';
  } else if (agentName === 'perf-optimizer') {
    const pct = output.improvement_pct || 0;
    const committed = output.changes_committed || 0;
    if (committed > 0 && pct >= 20) return 'HEALTHY';
    if (committed > 0 && pct >= 5) return 'WARNING';
  } else {
    const selfVerdict = (output.verdict || '').toUpperCase();
    if (_ALL_VERDICTS.has(selfVerdict)) return selfVerdict;
    if ((output.changes_committed || 0) > 0) return 'HEALTHY';
  }

  const selfVerdict = (output.verdict || '').toUpperCase();
  if (_ALL_VERDICTS.has(selfVerdict)) return selfVerdict;

  return 'INCONCLUSIVE';
}

function _parseTextOutput(agentName, text) {
  const out = {};

  const commitMatches = text.match(/commit[ted]*\s+[`']?([0-9a-f]{7,})[`']?/gi);
  if (commitMatches) {
    out.changes_committed = commitMatches.length;
  }

  if (agentName === 'security-hardener') {
    let m = text.match(/(\d+)\s+risks?\s+fixed/i) || text.match(/(\d+)\s+\w[\w\s]+\s+fixed/i);
    if (m) out.risks_fixed = parseInt(m[1], 10);
    m = text.match(/(\d+)\s+risks?\s+(?:found|identified)/i);
    if (m) out.risks_found = parseInt(m[1], 10);
    m = text.match(/(\d+)\s+(?:new\s+)?(?:security\s+)?tests?\s+written/i);
    if (m) out.tests_written = parseInt(m[1], 10);
    m = text.match(/(\d+)\s+risks?\s+reported/i);
    if (m) out.risks_reported = parseInt(m[1], 10);
  } else if (agentName === 'test-writer') {
    let m = text.match(/(\d+)\s+tests?\s+written/i);
    if (m) out.tests_written = parseInt(m[1], 10);
    m = text.match(/coverage[:\s]+(\d+(?:\.\d+)?)%\s*[→\-]+\s*(\d+(?:\.\d+)?)%/);
    if (m) {
      out.coverage_before = parseFloat(m[1]) / 100;
      out.coverage_after = parseFloat(m[2]) / 100;
    }
  } else if (agentName === 'type-strictener') {
    const m = text.match(/(\d+)\s+errors?\s+[→\-]+\s*(\d+)/);
    if (m) {
      out.errors_before = parseInt(m[1], 10);
      out.errors_after = parseInt(m[2], 10);
    }
  } else if (agentName === 'perf-optimizer') {
    const m = text.match(/p99[:\s]+(\d+(?:\.\d+)?)ms\s*[→\-]+\s*(\d+(?:\.\d+)?)ms/);
    if (m) {
      out.p99_before = parseFloat(m[1]);
      out.p99_after = parseFloat(m[2]);
      if (out.p99_before > 0) {
        out.improvement_pct = Math.round((out.p99_before - out.p99_after) / out.p99_before * 1000) / 10;
      }
    }
  } else {
    let m = text.match(/^verdict:\s*(\w+)/im);
    if (m) out.verdict = m[1].toUpperCase();
    m = text.match(/^summary:\s*(.+)/im);
    if (m) out.summary = m[1].trim();
  }

  return out;
}

function _summaryFromAgentOutput(agentName, output) {
  if (!output) return `${agentName}: no structured output produced`;

  if (output.summary) return String(output.summary);

  if (agentName === 'security-hardener') {
    return `risks_found=${output.risks_found ?? '?'} fixed=${output.risks_fixed ?? '?'} committed=${output.changes_committed ?? '?'} tests_written=${output.tests_written ?? '?'}`;
  }
  if (agentName === 'test-writer') {
    const before = output.coverage_before || 0;
    const after = output.coverage_after || 0;
    return `coverage ${Math.round(before * 100)}% → ${Math.round(after * 100)}% (${output.tests_written ?? '?'} tests written)`;
  }
  if (agentName === 'type-strictener') {
    return `mypy errors ${output.errors_before ?? '?'} → ${output.errors_after ?? '?'} (${output.changes_committed ?? '?'} changes committed)`;
  }
  if (agentName === 'perf-optimizer') {
    return `p99 ${output.p99_before ?? '?'}ms → ${output.p99_after ?? '?'}ms (${(output.improvement_pct || 0).toFixed(1)}% improvement)`;
  }
  return `${agentName}: ${JSON.stringify(output).slice(0, 200)}`;
}

function parseAgentRaw(agentName, raw) {
  let agentText = raw;
  try {
    const wrapper = JSON.parse(raw);
    if (wrapper && typeof wrapper === 'object' && !Array.isArray(wrapper)) {
      agentText = wrapper.result || raw;
    }
  } catch {
    // not JSON wrapper
  }

  let agentOutput = {};
  const jsonMatch = agentText.match(/```json\s*(\{[\s\S]*?\})\s*```/);
  if (jsonMatch) {
    try {
      agentOutput = JSON.parse(jsonMatch[1]);
    } catch {
      // invalid JSON in block
    }
  }

  if (!Object.keys(agentOutput).length && agentText) {
    agentOutput = _parseTextOutput(agentName, agentText);
  }

  const verdict = _verdictFromAgentOutput(agentName, agentOutput);
  const summary = _summaryFromAgentOutput(agentName, agentOutput);

  return {
    verdict,
    summary,
    data: agentOutput,
    details: agentText.slice(0, 4000),
  };
}

function runAgent(question) {
  const agentName = (question.agent_name || '').trim();

  if (!agentName) {
    return {
      verdict: 'INCONCLUSIVE',
      summary: 'No agent specified — add **Agent**: <name> to question',
      data: {},
      details: '',
    };
  }

  try {
    const spawn = spawnAgent(agentName, question.prompt || '', {
      model: question.model || null,
      allowedTools: ['Read', 'Write', 'Edit', 'Bash', 'Glob', 'Grep'],
      cwd: cfg.recallSrc,
    });
    const result = waitForAgent(spawn, { timeout: 600 });

    if (result.exitCode === -1) {
      return {
        verdict: 'INCONCLUSIVE',
        summary: `${agentName} timed out after 600s`,
        data: {},
        details: 'Agent loop exceeded time limit',
      };
    }

    return parseAgentRaw(agentName, result.stdout);
  } catch (err) {
    return {
      verdict: 'INCONCLUSIVE',
      summary: `Agent error: ${err.message}`,
      data: {},
      details: err.message,
    };
  }
}

module.exports = {
  runAgent,
  parseAgentRaw,
  _verdictFromAgentOutput,
  _parseTextOutput,
  _summaryFromAgentOutput,
  _ALL_VERDICTS,
};
