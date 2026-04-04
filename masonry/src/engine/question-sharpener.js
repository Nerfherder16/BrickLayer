'use strict';
// engine/question-sharpener.js — Question sharpening feedback loop.
//
// Port of bl/question_sharpener.py to Node.js.
// Reads INCONCLUSIVE findings and narrows PENDING questions in the same mode/domain.

const fs = require('fs');
const path = require('path');
const os = require('os');

function _extractFindingMode(content) {
  const match = content.match(/\*\*Mode\*\*:\s*(\S+)/);
  return match ? match[1].trim() : null;
}

function _findingKeyword(content) {
  const summaryMatch = content.match(/^##\s+Summary\s*\n(.*?)(?=^##|\Z)/ms);
  if (!summaryMatch) return 'inconclusive';

  const summaryText = summaryMatch[1].trim();
  const words = summaryText.split(/\s+/).filter(Boolean);
  if (words.length === 0) return 'inconclusive';

  return words.slice(0, 3).map(w => w.toLowerCase()).join('-');
}

function sharpenPendingQuestions(projectDir, maxSharpen = 5, dryRun = false) {
  const questionsPath = path.join(projectDir, 'questions.md');
  const findingsDir = path.join(projectDir, 'findings');

  if (!fs.existsSync(questionsPath)) return [];
  if (!fs.existsSync(findingsDir) || !fs.statSync(findingsDir).isDirectory()) return [];

  // Step 1: collect INCONCLUSIVE findings and their modes
  const inconclusiveModes = [];
  const inconclusiveKeywords = [];

  const findingFiles = fs.readdirSync(findingsDir)
    .filter(f => f.endsWith('.md'))
    .sort();

  for (const fname of findingFiles) {
    const content = fs.readFileSync(path.join(findingsDir, fname), 'utf8');
    if (!content.includes('**Verdict**: INCONCLUSIVE')) continue;
    const mode = _extractFindingMode(content);
    if (mode) {
      inconclusiveModes.push(mode.toLowerCase());
      inconclusiveKeywords.push(_findingKeyword(content));
    }
  }

  if (inconclusiveModes.length === 0) return [];

  // Step 2: read questions.md and find PENDING question blocks to sharpen
  let text = fs.readFileSync(questionsPath, 'utf8');

  const blockPattern = /^(###\s+(\S+)\s+—\s+.+)$/gm;
  const blockStarts = [];
  let m;
  while ((m = blockPattern.exec(text)) !== null) {
    blockStarts.push({
      start: m.index,
      headerEnd: m.index + m[0].length,
      headerLine: m[1],
      qid: m[2],
    });
  }

  const modifiedIds = [];
  const replacements = [];

  for (let i = 0; i < blockStarts.length; i++) {
    if (modifiedIds.length >= maxSharpen) break;

    const { start, headerEnd, headerLine, qid } = blockStarts[i];
    const nextStart = i + 1 < blockStarts.length ? blockStarts[i + 1].start : text.length;
    const blockBody = text.slice(headerEnd, nextStart);

    if (!blockBody.includes('**Status**: PENDING')) continue;
    if (blockBody.includes('**Sharpened**: true')) continue;

    const modeMatch = blockBody.match(/\*\*Mode\*\*:\s*(\S+)/);
    if (!modeMatch) continue;
    const questionMode = modeMatch[1].trim().toLowerCase();

    let keyword = null;
    for (let j = 0; j < inconclusiveModes.length; j++) {
      if (inconclusiveModes[j] === questionMode) {
        keyword = inconclusiveKeywords[j];
        break;
      }
    }
    if (keyword === null) continue;

    const newHeader = headerLine + ` [narrowed: ${keyword}]`;
    const newBlockBody = blockBody.replace(
      '**Status**: PENDING',
      '**Status**: PENDING\n**Sharpened**: true',
    );

    replacements.push({ start, end: nextStart, newText: newHeader + newBlockBody });
    modifiedIds.push(qid);
  }

  if (modifiedIds.length === 0 || dryRun) return modifiedIds;

  // Apply replacements from end to start
  for (let i = replacements.length - 1; i >= 0; i--) {
    const { start, end, newText } = replacements[i];
    text = text.slice(0, start) + newText + text.slice(end);
  }

  // Atomic write via temp file + rename
  const tmpPath = path.join(projectDir, `questions_${process.pid}.tmp`);
  try {
    fs.writeFileSync(tmpPath, text, 'utf8');
    fs.renameSync(tmpPath, questionsPath);
  } catch (err) {
    try { fs.unlinkSync(tmpPath); } catch (_) { /* ignore */ }
    throw err;
  }

  return modifiedIds;
}

module.exports = {
  _extractFindingMode,
  _findingKeyword,
  sharpenPendingQuestions,
};
