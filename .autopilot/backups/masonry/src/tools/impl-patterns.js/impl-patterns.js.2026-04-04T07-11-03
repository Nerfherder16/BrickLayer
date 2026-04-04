'use strict';

const fs = require('fs');
const path = require('path');
const { httpRequest } = require('./impl-utils');
const { loadConfig } = require('./config');

async function toolPatternStore(args) {
  const { pattern_name, content, lang, framework, layer } = args;
  const cfg = loadConfig();

  const tags = [`lang:${lang}`, `framework:${framework}`];
  if (layer) tags.push(`layer:${layer}`);
  tags.push('source:manual');

  const payload = JSON.stringify({
    content: `# ${pattern_name}\n\n${content}`,
    domain: 'build-patterns',
    tags,
    metadata: { pattern_name, lang, framework, layer: layer || null },
  });

  try {
    const resp = await Promise.race([
      httpRequest(`${process.env.RECALL_HOST || cfg.recallHost}/memory/store`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload),
          ...(cfg.recallApiKey ? { Authorization: `Bearer ${cfg.recallApiKey}` } : {}),
        },
      }, payload),
      new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 8000)),
    ]);
    if (resp.status >= 400) return { stored: false, error: `Recall returned HTTP ${resp.status}` };
    return { stored: true, pattern_name, lang, framework, layer, tags };
  } catch (err) {
    return { stored: false, error: err.message };
  }
}

async function toolPatternSearch(args) {
  const { query, lang, framework, limit = 5 } = args;
  const cfg = loadConfig();

  const searchBody = { query, domains: ['build-patterns'], limit };
  if (lang) searchBody.tags = [`lang:${lang}`];
  if (framework && searchBody.tags) searchBody.tags.push(`framework:${framework}`);
  else if (framework) searchBody.tags = [`framework:${framework}`];

  const payload = JSON.stringify(searchBody);

  try {
    const resp = await Promise.race([
      httpRequest(`${process.env.RECALL_HOST || cfg.recallHost}/search/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload),
          ...(cfg.recallApiKey ? { Authorization: `Bearer ${cfg.recallApiKey}` } : {}),
        },
      }, payload),
      new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 8000)),
    ]);
    if (resp.status >= 400) return { error: `Recall returned HTTP ${resp.status}`, results: [] };
    const data = resp.body;
    const results = Array.isArray(data) ? data : (data.results || data.memories || []);
    return { results, count: results.length, query, lang, framework };
  } catch (err) {
    return { error: err.message, results: [] };
  }
}

function toolPatternDecay(args) {
  const { project_dir } = args;
  const confPath = path.join(project_dir, '.autopilot', 'pattern-confidence.json');

  let store = {};
  try {
    store = JSON.parse(fs.readFileSync(confPath, 'utf8'));
  } catch {
    return { decayed: 0, pruned: 0, remaining: 0, pruned_ids: [] };
  }

  const now = Date.now();
  const DECAY_PER_HOUR = 0.005;
  const PRUNE_THRESHOLD = 0.2;

  const prunedIds = [];
  const surviving = {};
  let decayedCount = 0;

  for (const [key, entry] of Object.entries(store)) {
    const lastUsed = entry.last_used ? new Date(entry.last_used).getTime() : now;
    const hoursElapsed = (now - lastUsed) / 3600000;
    const decayed = Math.max(0.0, entry.confidence - DECAY_PER_HOUR * hoursElapsed);
    if (decayed !== entry.confidence) decayedCount++;
    if (decayed < PRUNE_THRESHOLD) {
      prunedIds.push(key);
    } else {
      surviving[key] = { ...entry, confidence: decayed };
    }
  }

  try {
    fs.writeFileSync(confPath, JSON.stringify(surviving, null, 2), 'utf8');
  } catch (err) {
    return { error: err.message };
  }

  return { decayed: decayedCount, pruned: prunedIds.length, remaining: Object.keys(surviving).length, pruned_ids: prunedIds };
}

module.exports = { toolPatternStore, toolPatternSearch, toolPatternDecay };
