'use strict';
// engine/runners/baseline-check.js — Baseline regression check runner.
//
// Port of bl/runners/baseline_check.py to Node.js.
// Exports pure spec-parsing functions. The full runner requires
// bl/baseline (load_baseline, diff_against_baseline) at runtime.

function _parseBaselineCheckSpec(question) {
  const spec = {
    question_id: null,
    current_result_file: null,
    project_dir: null,
    fail_on_verdict_change: true,
    fail_on_metric_regression: {},
  };

  const rawSpec = question.spec || question.Spec;

  if (rawSpec && typeof rawSpec === 'object' && !Array.isArray(rawSpec)) {
    spec.question_id = rawSpec.question_id || null;
    spec.current_result_file = rawSpec.current_result_file || null;
    spec.project_dir = rawSpec.project_dir || null;

    const fovc = rawSpec.fail_on_verdict_change;
    if (fovc === undefined || fovc === null) {
      spec.fail_on_verdict_change = true;
    } else {
      spec.fail_on_verdict_change = !['false', '0', 'no'].includes(
        String(fovc).toLowerCase(),
      );
    }

    const fomr = rawSpec.fail_on_metric_regression;
    if (fomr && typeof fomr === 'object') {
      for (const [k, v] of Object.entries(fomr)) {
        spec.fail_on_metric_regression[k] = parseFloat(v);
      }
    }
    return spec;
  }

  // Fall back to line-by-line text parsing
  let text = '';
  if (typeof rawSpec === 'string') {
    text = rawSpec;
  } else {
    text = question.test || question.Test || '';
  }

  let inMetricBlock = false;

  for (const rawLine of text.split('\n')) {
    const stripped = rawLine.trim();
    if (!stripped || stripped.startsWith('```')) {
      inMetricBlock = false;
      continue;
    }

    const low = stripped.toLowerCase();

    if (inMetricBlock) {
      if (stripped.includes(':')) {
        const colonIdx = stripped.indexOf(':');
        const key = stripped.slice(0, colonIdx).trim();
        const val = stripped.slice(colonIdx + 1).trim();
        const num = parseFloat(val);
        if (!isNaN(num)) {
          spec.fail_on_metric_regression[key] = num;
        }
      }
      continue;
    }

    if (low.startsWith('question_id:')) {
      spec.question_id = stripped
        .split(':')
        .slice(1)
        .join(':')
        .trim()
        .replace(/^["']|["']$/g, '');
    } else if (low.startsWith('current_result_file:')) {
      spec.current_result_file = stripped.split(':').slice(1).join(':').trim();
    } else if (low.startsWith('project_dir:')) {
      spec.project_dir = stripped.split(':').slice(1).join(':').trim();
    } else if (low.startsWith('fail_on_verdict_change:')) {
      const val = stripped.split(':').slice(1).join(':').trim().toLowerCase();
      spec.fail_on_verdict_change = !['false', '0', 'no'].includes(val);
    } else if (low.startsWith('fail_on_metric_regression:')) {
      inMetricBlock = true;
    }
  }

  return spec;
}

module.exports = {
  _parseBaselineCheckSpec,
};
