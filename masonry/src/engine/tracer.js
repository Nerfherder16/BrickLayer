'use strict';
// engine/tracer.js — Per-step introspection tracer.
//
// Port of bl/tracer.py to Node.js.

const fs = require('fs');
const path = require('path');

function _appendTrace(trace, projectRoot) {
  try {
    const tracesPath = path.join(String(projectRoot), 'traces.jsonl');
    fs.appendFileSync(tracesPath, JSON.stringify(trace) + '\n', 'utf8');
  } catch (exc) {
    process.stderr.write(`[tracer] local write failed: ${exc.message}\n`);
  }
}

function traced(fn, projectRoot) {
  return function wrapper(question) {
    const start = process.hrtime.bigint();
    let result = {};
    try {
      result = fn(question);
    } catch (exc) {
      result = {
        verdict: 'INCONCLUSIVE',
        summary: `Runner raised exception: ${exc.message}`,
        data: {},
        details: String(exc),
        failure_type: 'tool_failure',
        confidence: 'uncertain',
      };
      const elapsedMs = Number(process.hrtime.bigint() - start) / 1e6;
      const trace = _buildTrace(question, result, elapsedMs);
      _appendTrace(trace, projectRoot);
      throw exc;
    }
    const elapsedMs = Number(process.hrtime.bigint() - start) / 1e6;
    const trace = _buildTrace(question, result, elapsedMs);
    _appendTrace(trace, projectRoot);
    return result;
  };
}

function _buildTrace(question, result, elapsedMs) {
  return {
    timestamp: new Date().toISOString(),
    thought: question.title || question.id || '',
    tool_call: `${question.mode || 'unknown'}:${question.agent || question.id || ''}`,
    verdict: result.verdict || 'UNKNOWN',
    result_summary: (result.summary || '').slice(0, 200),
    latency_ms: Math.round(elapsedMs * 10) / 10,
    confidence: result.confidence || 'uncertain',
    error_type: result.failure_type || null,
    question_id: question.id || null,
    domain: question.domain || null,
  };
}

function loadTraces(projectRoot) {
  const tracesPath = path.join(String(projectRoot), 'traces.jsonl');
  if (!fs.existsSync(tracesPath)) return [];

  const traces = [];
  const content = fs.readFileSync(tracesPath, 'utf8');
  for (const line of content.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    try {
      traces.push(JSON.parse(trimmed));
    } catch {
      // skip malformed lines
    }
  }
  return traces;
}

module.exports = { traced, loadTraces };
