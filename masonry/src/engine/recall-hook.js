'use strict';
// engine/recall-hook.js — Extract Recall payload from BL 2.0 finding text.
//
// Port of bl/recall_hook.py to Node.js.

const FAILURE_SET = new Set(['FAILURE', 'INCONCLUSIVE', 'INCONCLUSIVE-FORMAT-ERROR']);

function extractRecallPayload(findingText, agentName, questionId, project) {
  let [verdict, summary] = _extractFromJson(findingText);

  if (verdict === null) {
    [verdict, summary] = _extractFromVerdictLine(findingText);
  }

  if (verdict === null) return null;

  return _buildPayload(verdict, summary || '', agentName, questionId, project);
}

function _extractFromJson(findingText) {
  const blocks = [...findingText.matchAll(/```json\s*(.*?)```/gs)];
  if (blocks.length === 0) return [null, null];

  const lastBlock = blocks[blocks.length - 1][1].trim();
  let data;
  try {
    data = JSON.parse(lastBlock);
  } catch {
    return [null, null];
  }

  const verdict = data.verdict;
  if (!verdict) return [null, null];

  const summary = data.summary || data.simulation_result || '';
  return [String(verdict), String(summary)];
}

function _extractFromVerdictLine(findingText) {
  const verdictMatch = findingText.match(/\*\*Verdict\*\*:\s*([\w-]+)/);
  if (!verdictMatch) return [null, null];

  const verdict = verdictMatch[1];
  let summary = '';
  const evidenceMatch = findingText.match(/##\s+Evidence\s*\n+([\s\S]*)/);
  if (evidenceMatch) {
    summary = evidenceMatch[1].slice(0, 200);
  }

  return [verdict, summary];
}

function _buildPayload(verdict, summary, agentName, questionId, project) {
  const importance = FAILURE_SET.has(verdict) ? 0.9 : 0.7;
  const content = `${agentName} ${questionId}: verdict=${verdict}. ${summary}`;
  return {
    content,
    domain: `${project}-bricklayer`,
    tags: [
      'bricklayer',
      `agent:${agentName}`,
      'type:finding',
      `verdict:${verdict}`,
    ],
    importance,
    durability: 'durable',
  };
}

module.exports = { extractRecallPayload, FAILURE_SET };
