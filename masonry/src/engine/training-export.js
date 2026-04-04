'use strict';
// engine/training-export.js — BrickLayer → Training System bridge.
//
// Port of bl/training_export.py to Node.js.
// Reads BrickLayer campaign artifacts and converts them into Trace records.

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const {
  computeTrajectoryScore,
  confidenceStrToFloat,
  isSftEligible,
  verdictToBinaryPass,
  verdictToCriticFlag,
  verdictToPartialCredit,
} = require('./training-schema');

// ---------------------------------------------------------------------------
// Finding parser
// ---------------------------------------------------------------------------

function parseFinding(text) {
  const result = {
    verdict: 'INCONCLUSIVE',
    severity: 'Info',
    confidence: 0.5,
    needs_human: true,
    failure_type: null,
    mode: 'simulate',
    summary: '',
  };

  if (!text) return result;

  const patterns = {
    verdict: /^\*\*Verdict\*\*:\s*(.+)$/m,
    severity: /^\*\*Severity\*\*:\s*(.+)$/m,
    confidence: /^\*\*Confidence\*\*:\s*(.+)$/m,
    needs_human: /^\*\*Needs Human\*\*:\s*(.+)$/m,
    failure_type: /^\*\*Failure Type\*\*:\s*(.+)$/m,
    mode: /^\*\*Mode\*\*:\s*(.+)$/m,
  };

  for (const [key, pat] of Object.entries(patterns)) {
    const m = text.match(pat);
    if (m) result[key] = m[1].trim();
  }

  // Normalise types
  result.verdict = String(result.verdict).toUpperCase().trim();

  const confNum = parseFloat(result.confidence);
  if (!isNaN(confNum)) {
    result.confidence = confNum;
  } else {
    result.confidence = confidenceStrToFloat(result.confidence);
  }

  const needsRaw = String(result.needs_human).toLowerCase().trim();
  result.needs_human = ['true', '1', 'yes'].includes(needsRaw);

  // Extract Summary section
  const summaryMatch = text.match(/## Summary\s*\n(.+?)(?:\n##|\Z)/s);
  if (summaryMatch) {
    result.summary = summaryMatch[1].trim().slice(0, 200);
  }

  return result;
}

// ---------------------------------------------------------------------------
// Trace builder
// ---------------------------------------------------------------------------

function makeTrace({
  questionId, taskDomain, taskDescription, agentName,
  tracerRecord, scoredEntry, verdict, confidenceRaw,
  needsHuman, wave, mode,
}) {
  const evalScore = (scoredEntry || {}).score;
  const trajectoryScore = computeTrajectoryScore(evalScore, verdict, confidenceRaw);
  const confidenceFloat = confidenceStrToFloat(confidenceRaw);
  const sftEligible = isSftEligible(verdict, trajectoryScore, needsHuman);
  const criticFlag = verdictToCriticFlag(verdict);

  // GRPO group key
  const grpoKey = `${agentName}:${taskDomain}:${wave}`;
  const grpoGroupId = crypto.createHash('md5').update(grpoKey).digest('hex').slice(0, 12);

  // Build step
  const modePart = tracerRecord.tool_call || `${mode}:${questionId}`;
  const step = {
    step_index: 0,
    action_type: 'tool_call',
    thought: tracerRecord.thought || taskDescription,
    action: {
      type: 'tool_call',
      tool: modePart.includes(':') ? modePart.split(':')[0] : mode,
      args: { question_id: questionId, domain: taskDomain },
    },
    observation: tracerRecord.result_summary || '',
    tool_event: {
      tool_name: modePart,
      args: { question_id: questionId },
      success: tracerRecord.error_type == null,
      result: tracerRecord.result_summary,
      error: tracerRecord.error_type,
      latency_ms: tracerRecord.latency_ms || 0.0,
      timestamp: tracerRecord.timestamp || new Date().toISOString(),
    },
    critic_score: trajectoryScore,
    critic_flag: criticFlag,
    critic_reason: `verdict=${verdict} confidence=${confidenceFloat.toFixed(2)}`,
    elapsed_ms: tracerRecord.latency_ms || 0.0,
    timestamp: tracerRecord.timestamp || new Date().toISOString(),
  };

  // OutcomeSignal
  const outcome = {
    binary_pass: verdictToBinaryPass(verdict),
    partial_credit: verdictToPartialCredit(verdict),
    verifier_details: {
      verdict,
      confidence: confidenceFloat,
      needs_human: needsHuman,
      eval_score_raw: evalScore,
    },
    error: tracerRecord.error_type,
  };

  // Deterministic UUID v5
  const NS_DNS = '6ba7b810-9dad-11d1-80b4-00c04fd430c8';
  const idInput = `bl:${questionId}`;
  const idHash = crypto.createHash('sha1').update(NS_DNS + idInput).digest('hex');
  const traceId = [
    idHash.slice(0, 8), idHash.slice(8, 12),
    idHash.slice(12, 16), idHash.slice(16, 20),
    idHash.slice(20, 32),
  ].join('-');

  return {
    id: traceId,
    task_id: questionId,
    task_domain: taskDomain,
    task_description: taskDescription,
    agent_model: agentName,
    agent_temperature: 0.0,
    steps: [step],
    final_answer: tracerRecord.result_summary || '',
    outcome,
    trajectory_score: trajectoryScore,
    sft_eligible: sftEligible,
    grpo_group_id: grpoGroupId,
    grpo_reward: null,
    metadata: {
      verdict,
      severity: ((scoredEntry || {}).output || {}).severity || '',
      confidence: confidenceFloat,
      needs_human: needsHuman,
      wave,
      mode,
      source: 'bricklayer_campaign',
      bl_agent: agentName,
    },
    created_at: tracerRecord.timestamp || new Date().toISOString(),
  };
}

// ---------------------------------------------------------------------------
// Project export
// ---------------------------------------------------------------------------

function exportProject(projectDir, scoredIndex) {
  const tracesPath = path.join(projectDir, 'traces.jsonl');
  if (!fs.existsSync(tracesPath)) return [];

  const findingsDir = path.join(projectDir, 'findings');
  const traces = [];

  const lines = fs.readFileSync(tracesPath, 'utf8').split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    let rec;
    try { rec = JSON.parse(trimmed); } catch { continue; }

    const qid = rec.question_id;
    if (!qid) continue;

    // Look up scored entry
    const scored = (scoredIndex || {})[qid] || null;

    // Parse finding
    let finding = { verdict: 'INCONCLUSIVE', confidence: 0.5, needs_human: true, mode: 'simulate', summary: '' };
    const findingPath = path.join(findingsDir, `${qid}.md`);
    if (fs.existsSync(findingPath)) {
      finding = parseFinding(fs.readFileSync(findingPath, 'utf8'));
    }

    const verdict = finding.verdict || rec.verdict || 'INCONCLUSIVE';
    const confidenceRaw = finding.confidence || rec.confidence;
    const needsHuman = finding.needs_human !== undefined ? finding.needs_human : true;
    const toolCall = rec.tool_call || '';
    const mode = finding.mode || (toolCall.includes(':') ? toolCall.split(':')[0] : '') || 'simulate';
    const domain = rec.domain || 'unknown';
    const wave = (scored || {}).wave || 1;

    let agentName = (scored || {}).agent || 'unknown';
    if (agentName === 'unknown' && toolCall.includes(':')) {
      agentName = toolCall.split(':')[0];
    }

    const taskDescription = finding.summary || rec.thought || qid;

    const trace = makeTrace({
      questionId: qid,
      taskDomain: domain,
      taskDescription,
      agentName,
      tracerRecord: rec,
      scoredEntry: scored,
      verdict,
      confidenceRaw,
      needsHuman,
      wave,
      mode,
    });

    if (trace.trajectory_score != null && trace.trajectory_score >= 0) {
      traces.push(trace);
    }
  }

  return traces;
}

module.exports = {
  parseFinding,
  makeTrace,
  exportProject,
};
