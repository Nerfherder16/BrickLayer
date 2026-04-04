'use strict';
// engine/runners/swarm.js — Swarm meta-runner.
//
// Port of bl/runners/swarm.py to Node.js.
// Runs multiple sub-runners and aggregates verdicts.

const _VERDICT_ORDER = ['FAILURE', 'WARNING', 'INCONCLUSIVE', 'HEALTHY'];

function _verdictRank(verdict) {
  const idx = _VERDICT_ORDER.indexOf(verdict);
  return idx === -1 ? 2 : idx; // unknown = INCONCLUSIVE rank
}

function _aggregateWorst(results) {
  if (!results.length) return 'INCONCLUSIVE';
  let worst = results[0];
  for (const r of results) {
    if (_verdictRank(r.verdict) < _verdictRank(worst.verdict)) worst = r;
  }
  return worst.verdict;
}

function _aggregateMajority(results, weights) {
  if (!results.length) return 'INCONCLUSIVE';
  const tally = {};
  for (const r of results) {
    const w = weights[r.id] || 1;
    tally[r.verdict] = (tally[r.verdict] || 0) + w;
  }
  let best = null;
  let bestCount = -1;
  for (const [v, count] of Object.entries(tally)) {
    if (count > bestCount) {
      best = v;
      bestCount = count;
    }
  }
  return best;
}

function _aggregateAnyFailure(results) {
  for (const r of results) {
    if (r.verdict === 'FAILURE') return 'FAILURE';
  }
  return _aggregateWorst(results);
}

function _defaultWorkerRunner(workerDef) {
  const base = require('./base');
  const workerId = workerDef.id || 'unknown';
  const workerMode = workerDef.mode || '';
  const workerSpec = workerDef.spec || {};

  const runner = base.get(workerMode);
  if (!runner) {
    return {
      id: workerId,
      mode: workerMode,
      verdict: 'INCONCLUSIVE',
      summary: `No runner registered for mode '${workerMode}'`,
      data: { error: 'unknown_mode' },
      details: `Mode '${workerMode}' is not registered.`,
      duration_ms: 0,
    };
  }

  const question = {
    id: workerId,
    mode: workerMode,
    spec: workerSpec,
    ...Object.fromEntries(
      Object.entries(workerSpec).filter(([k]) => !['id', 'mode'].includes(k)),
    ),
  };

  const start = Date.now();
  try {
    const result = runner(question);
    return {
      id: workerId,
      mode: workerMode,
      verdict: result.verdict || 'INCONCLUSIVE',
      summary: result.summary || '',
      data: result.data || {},
      details: result.details || '',
      duration_ms: Date.now() - start,
    };
  } catch (err) {
    return {
      id: workerId,
      mode: workerMode,
      verdict: 'INCONCLUSIVE',
      summary: `Worker '${workerId}' raised an exception: ${err.message}`,
      data: { error: err.message },
      details: `Unhandled exception in worker '${workerId}': ${err.message}`,
      duration_ms: Date.now() - start,
    };
  }
}

function runSwarm(question, { workerRunner = null } = {}) {
  const spec = question.spec || question;
  const workers = spec.workers || [];

  if (!workers.length) {
    return {
      verdict: 'INCONCLUSIVE',
      summary: 'swarm runner: no workers defined in spec',
      data: { error: 'no_workers' },
      details: 'spec.workers must be a non-empty list of {id, mode, spec} dicts.',
    };
  }

  const maxConcurrency = spec.max_concurrency || workers.length;
  const timeoutSeconds = parseInt(spec.timeout_seconds || '120', 10);
  const aggregation = (spec.aggregation || 'worst').toLowerCase();
  const weights = spec.weights || {};

  const runWorker = workerRunner || _defaultWorkerRunner;
  const swarmStart = Date.now();

  const completedResults = [];
  const timedOutIds = [];
  const failedIds = [];

  // Run workers (synchronously for simplicity — async parallelism can be added later)
  const batch = workers.slice(0, maxConcurrency);
  for (const w of batch) {
    const result = runWorker(w, timeoutSeconds);
    completedResults.push(result);
    if (result.verdict === 'FAILURE' || result.verdict === 'INCONCLUSIVE') {
      failedIds.push(result.id);
    }
  }

  // Aggregate
  let overallVerdict;
  if (aggregation === 'majority') {
    overallVerdict = _aggregateMajority(completedResults, weights);
  } else if (aggregation === 'any_failure') {
    overallVerdict = _aggregateAnyFailure(completedResults);
  } else {
    overallVerdict = _aggregateWorst(completedResults);
  }

  // Build by_worker
  const byWorker = {};
  for (const r of completedResults) {
    byWorker[r.id] = {
      verdict: r.verdict,
      summary: r.summary,
      duration_ms: r.duration_ms,
    };
  }

  const workersComplete = completedResults.length - timedOutIds.length;
  const perWorkerSummary = completedResults.map(r => `${r.id}=${r.verdict}`).join(', ');
  const summary = `${workersComplete}/${workers.length} workers complete: ${perWorkerSummary}`;

  const totalDurationMs = Date.now() - swarmStart;

  const detailLines = [
    `Swarm: ${workers.length} workers, aggregation=${aggregation}, timeout=${timeoutSeconds}s, concurrency=${maxConcurrency}`,
    '',
  ];
  for (const r of completedResults) {
    detailLines.push(`  [${r.id}] mode=${r.mode} verdict=${r.verdict} duration=${r.duration_ms}ms`);
    if (r.summary) detailLines.push(`    summary: ${r.summary}`);
  }
  if (timedOutIds.length) {
    detailLines.push(`Timed-out workers: ${timedOutIds.join(', ')}`);
  }
  detailLines.push(`Total swarm duration: ${totalDurationMs}ms`);

  return {
    verdict: overallVerdict,
    summary,
    data: {
      workers_total: workers.length,
      workers_complete: workersComplete,
      workers_failed: completedResults.filter(r => r.verdict === 'FAILURE' || r.verdict === 'INCONCLUSIVE').length,
      by_worker: byWorker,
      combined_issues: [],
      aggregation,
      timed_out: timedOutIds,
      total_duration_ms: totalDurationMs,
    },
    details: detailLines.join('\n'),
  };
}

module.exports = {
  runSwarm,
  _verdictRank,
  _aggregateWorst,
  _aggregateMajority,
  _aggregateAnyFailure,
};
