'use strict';

const fs = require('fs');
const path = require('path');

function _appendConsensusLog(project_dir, task_id, votes, final_verdict, escalated) {
  try {
    const autopilotDir = path.join(project_dir, '.autopilot');
    if (!fs.existsSync(autopilotDir)) fs.mkdirSync(autopilotDir, { recursive: true });
    const logFile = path.join(autopilotDir, 'consensus-log.jsonl');
    const entry = JSON.stringify({ timestamp: new Date().toISOString(), task_id, votes, final_verdict, escalated });
    fs.appendFileSync(logFile, entry + '\n', 'utf8');
  } catch (_) {}
}

function toolConsensusCheck(args) {
  const { project_path, action, mode = 'check', approved_by } = args;
  const autopilotDir = path.join(project_path, '.autopilot');
  const consensusFile = path.join(autopilotDir, 'consensus.json');

  let consensus = { approvals: [] };
  try {
    if (fs.existsSync(consensusFile)) consensus = JSON.parse(fs.readFileSync(consensusFile, 'utf8'));
  } catch (_) {}
  if (!Array.isArray(consensus.approvals)) consensus.approvals = [];

  if (mode === 'list') return { approvals: consensus.approvals, total: consensus.approvals.length };

  const actionNorm = action.trim().toLowerCase();
  const existing = consensus.approvals.find(a => a.action.toLowerCase() === actionNorm);

  if (mode === 'check') {
    if (existing) return { approved: true, action, approved_by: existing.approved_by, approved_at: existing.approved_at, note: existing.note || null };
    return { approved: false, action, message: "No prior approval found. Call with mode='approve' after human confirmation." };
  }

  if (mode === 'approve') {
    if (!approved_by) return { error: "approved_by is required when mode='approve'" };
    if (existing) { existing.approved_by = approved_by; existing.approved_at = new Date().toISOString(); }
    else consensus.approvals.push({ action: action.trim(), approved_by, approved_at: new Date().toISOString() });
    try {
      fs.mkdirSync(autopilotDir, { recursive: true });
      fs.writeFileSync(consensusFile, JSON.stringify(consensus, null, 2), 'utf8');
    } catch (err) { return { error: `Failed to write consensus.json: ${err.message}` }; }
    return { recorded: true, action, approved_by, total_approvals: consensus.approvals.length };
  }

  return { error: `Unknown mode: ${mode}. Use 'check' | 'approve' | 'list'` };
}

function toolReviewConsensus(args) {
  const { votes, task_id, project_dir } = args;
  const VALID_VERDICTS = ['APPROVED', 'BLOCKED', 'NEEDS_REVISION'];

  const skipped = [];
  const valid = [];
  for (const v of Array.isArray(votes) ? votes : []) {
    if (typeof v.reviewer === 'string' && VALID_VERDICTS.includes(v.verdict) &&
        typeof v.confidence === 'number' && v.confidence >= 0 && v.confidence <= 1 &&
        typeof v.summary === 'string') {
      valid.push(v);
    } else {
      skipped.push(v.reviewer || '(unknown)');
    }
  }

  if (valid.length < 2) {
    const result = {
      final_verdict: 'BLOCKED',
      vote_breakdown: [],
      reasoning: `Insufficient valid votes (${valid.length} valid, ${skipped.length} skipped). Minimum 2 required.`,
      escalate: true, task_id, timestamp: new Date().toISOString(),
    };
    _appendConsensusLog(project_dir, task_id, valid, 'BLOCKED', true);
    return result;
  }

  const scores = { APPROVED: 0, BLOCKED: 0, NEEDS_REVISION: 0 };
  const reviewersByVerdict = { APPROVED: [], BLOCKED: [], NEEDS_REVISION: [] };
  let totalWeight = 0;
  for (const v of valid) { scores[v.verdict] += v.confidence; reviewersByVerdict[v.verdict].push(v.reviewer); totalWeight += v.confidence; }

  const share = {};
  for (const verdict of VALID_VERDICTS) share[verdict] = totalWeight > 0 ? scores[verdict] / totalWeight : 0;

  const sorted = VALID_VERDICTS.slice().sort((a, b) => scores[b] - scores[a]);
  const top = sorted[0];
  const second = sorted[1];
  const isTie = Math.abs(scores[top] - scores[second]) < 0.001;

  let winner;
  let escalate;
  if (isTie) { winner = 'BLOCKED'; escalate = true; }
  else { winner = top; escalate = winner === 'BLOCKED'; }

  let final_verdict;
  if (winner === 'APPROVED') { final_verdict = 'APPROVED'; escalate = false; }
  else if (winner === 'BLOCKED') { final_verdict = 'BLOCKED'; escalate = true; }
  else { final_verdict = 'BLOCKED'; if (!isTie) escalate = false; }

  const vote_breakdown = VALID_VERDICTS.filter(v => scores[v] > 0 || reviewersByVerdict[v].length > 0).map(v => ({
    verdict: v, weighted_score: Math.round(scores[v] * 1000) / 1000,
    share: Math.round(share[v] * 1000) / 1000, reviewers: reviewersByVerdict[v],
  }));

  const winnerShare = Math.round(share[winner] * 100);
  const winnerScore = Math.round(scores[winner] * 100) / 100;
  const reasonParts = vote_breakdown.sort((a, b) => b.share - a.share).map(b => `${b.verdict}: ${Math.round(b.share * 100)}%`);

  let reasoning;
  if (isTie) {
    reasoning = `Tie between ${top} and ${second} (both at ${Math.round(scores[top] * 100) / 100}). Conservative default: BLOCKED. Escalating.`;
  } else {
    reasoning = `${winner} won with ${winnerShare}% weighted share (${winnerScore}/${Math.round(totalWeight * 100) / 100}). ${reasonParts.join('. ')}.`;
  }
  if (skipped.length > 0) reasoning += ` Skipped malformed votes from: ${skipped.join(', ')}.`;

  const result = { final_verdict, vote_breakdown, reasoning, escalate, task_id, timestamp: new Date().toISOString() };
  _appendConsensusLog(project_dir, task_id, valid, final_verdict, escalate);
  return result;
}

module.exports = { toolConsensusCheck, toolReviewConsensus };
