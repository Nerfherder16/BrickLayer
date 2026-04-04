'use strict';
// engine/local-inference.js — Lightweight local model inference via Ollama.
//
// Port of bl/local_inference.py to Node.js.
// Provides heuristic fallbacks that work without Ollama. The LLM-based
// classify functions require Ollama and are exported separately.

const _FAILURE_VERDICTS = new Set([
  'FAILURE', 'INCONCLUSIVE', 'NON_COMPLIANT', 'REGRESSION',
]);

// --- Heuristic classifiers (no LLM needed) ---

function classifyFailureTypeHeuristic(result) {
  const verdict = result.verdict || '';
  if (!_FAILURE_VERDICTS.has(verdict)) return null;

  const combined = `${result.summary || ''} ${result.details || ''}`.toLowerCase();

  if (/timeout|readtimeout|time limit/i.test(combined)) return 'timeout';
  if (/modulenotfounderror|importerror|connection refused|subprocess failed|exit code|http error/i.test(combined)) return 'tool_failure';
  if (/syntaxerror|indentationerror|parse error/i.test(combined)) return 'syntax';
  if (/assert|expected.*got|test.*fail/i.test(combined)) return 'logic';
  if (/assumed|unclear|no data|speculation|hallucin/i.test(combined)) return 'hallucination';
  return 'unknown';
}

function classifyConfidenceHeuristic(result) {
  const verdict = result.verdict || '';
  const combined = `${result.summary || ''} ${result.details || ''}`.toLowerCase();

  if (verdict === 'INCONCLUSIVE') return 'uncertain';

  if (/\d+ passed|\bline \d+\b|\bfile .+\.py\b|measured|specific/i.test(combined)) return 'high';
  if (/warning|identified|found|detected/i.test(combined)) return 'medium';
  if (/possible|may|might|vague|unclear/i.test(combined)) return 'low';
  return 'uncertain';
}

function scoreResultHeuristic(result) {
  const verdict = result.verdict || '';
  if (verdict === 'HEALTHY') return 0.9;
  if (verdict === 'WARNING') return 0.6;
  if (verdict === 'FAILURE') return 0.3;
  if (verdict === 'INCONCLUSIVE') return 0.2;
  return 0.5;
}

module.exports = {
  classifyFailureTypeHeuristic,
  classifyConfidenceHeuristic,
  scoreResultHeuristic,
};
