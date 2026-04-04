'use strict';

const fs = require('fs');
const path = require('path');

function lifecyclePath() {
  return path.join(process.cwd(), '.masonry', 'pattern-lifecycle.json');
}

function loadStore() {
  const p = lifecyclePath();
  try {
    if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (_) {}
  return {};
}

function saveStore(store) {
  const p = lifecyclePath();
  const dir = path.dirname(p);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(p, JSON.stringify(store, null, 2), 'utf8');
}

function defaultEntry(id) {
  return {
    id,
    tier: 'draft',
    usage_count: 0,
    quality: 0.5,
    last_used: null,
    created_at: new Date().toISOString(),
  };
}

function computeTier(entry) {
  if (entry.usage_count >= 3 && entry.quality >= 0.6) return 'promoted';
  if (entry.usage_count <= 1 && entry.quality < 0.4) return 'stale';
  return 'draft';
}

const SCHEMAS = [
  {
    name: 'masonry_pattern_use',
    description: 'Increment usage_count for a build pattern. Creates the entry if missing.',
    inputSchema: {
      type: 'object',
      properties: {
        pattern_id: { type: 'string', description: 'Pattern identifier' },
      },
      required: ['pattern_id'],
    },
  },
  {
    name: 'masonry_pattern_quality',
    description: 'Update quality score for a pattern and check promotion eligibility.',
    inputSchema: {
      type: 'object',
      properties: {
        pattern_id: { type: 'string' },
        quality: { type: 'number', description: '0.0 – 1.0 quality score' },
        feedback: { type: 'string', description: 'Optional human feedback string' },
      },
      required: ['pattern_id', 'quality'],
    },
  },
  {
    name: 'masonry_pattern_promote',
    description: 'Force promote a pattern to the "promoted" tier.',
    inputSchema: {
      type: 'object',
      properties: {
        pattern_id: { type: 'string' },
      },
      required: ['pattern_id'],
    },
  },
  {
    name: 'masonry_pattern_demote',
    description: 'Force demote a pattern to the "stale" tier.',
    inputSchema: {
      type: 'object',
      properties: {
        pattern_id: { type: 'string' },
      },
      required: ['pattern_id'],
    },
  },
];

function handle(name, args = {}) {
  switch (name) {
    case 'masonry_pattern_use': {
      const { pattern_id } = args;
      const store = loadStore();
      if (!store[pattern_id]) store[pattern_id] = defaultEntry(pattern_id);
      const entry = store[pattern_id];
      entry.usage_count += 1;
      entry.last_used = new Date().toISOString();
      saveStore(store);
      return { success: true, pattern_id, usage_count: entry.usage_count, tier: entry.tier };
    }

    case 'masonry_pattern_quality': {
      const { pattern_id, quality, feedback } = args;
      const store = loadStore();
      if (!store[pattern_id]) store[pattern_id] = defaultEntry(pattern_id);
      const entry = store[pattern_id];
      const prevTier = entry.tier;
      entry.quality = quality;
      if (feedback !== undefined) entry.feedback = feedback;
      entry.tier = computeTier(entry);
      saveStore(store);
      return {
        success: true,
        pattern_id,
        quality,
        tier: entry.tier,
        promoted: prevTier !== 'promoted' && entry.tier === 'promoted',
      };
    }

    case 'masonry_pattern_promote': {
      const { pattern_id } = args;
      const store = loadStore();
      if (!store[pattern_id]) store[pattern_id] = defaultEntry(pattern_id);
      store[pattern_id].tier = 'promoted';
      saveStore(store);
      return { success: true, pattern_id, tier: 'promoted' };
    }

    case 'masonry_pattern_demote': {
      const { pattern_id } = args;
      const store = loadStore();
      if (!store[pattern_id]) store[pattern_id] = defaultEntry(pattern_id);
      store[pattern_id].tier = 'stale';
      saveStore(store);
      return { success: true, pattern_id, tier: 'stale' };
    }

    default:
      throw new Error(`pattern-lifecycle: unknown tool ${name}`);
  }
}

module.exports = { handle, schemas: SCHEMAS };
