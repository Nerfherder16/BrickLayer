import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/recall-bridge', () => {
  let recallBridge;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'recall-bridge.js');
    delete require.cache[modPath];
    recallBridge = require(modPath);
  });

  it('should export searchPriorFindings, storeFinding, getAnalogousFailures, getCampaignContext', () => {
    expect(typeof recallBridge.searchPriorFindings).toBe('function');
    expect(typeof recallBridge.storeFinding).toBe('function');
    expect(typeof recallBridge.getAnalogousFailures).toBe('function');
    expect(typeof recallBridge.getCampaignContext).toBe('function');
  });

  it('searchPriorFindings should return [] for empty query', async () => {
    const result = await recallBridge.searchPriorFindings('');
    expect(result).toEqual([]);
  });

  it('storeFinding should return false for empty summary', async () => {
    const result = await recallBridge.storeFinding('Q1', 'HEALTHY', '', 'test-project');
    expect(result).toBe(false);
  });

  it('getAnalogousFailures should return [] for empty system type', async () => {
    const result = await recallBridge.getAnalogousFailures('');
    expect(result).toEqual([]);
  });

  it('getCampaignContext should return [] for empty project', async () => {
    const result = await recallBridge.getCampaignContext('');
    expect(result).toEqual([]);
  });

  it('_extractMemories should handle different response shapes', () => {
    expect(recallBridge._extractMemories(null)).toEqual([]);
    expect(recallBridge._extractMemories([])).toEqual([]);
    expect(recallBridge._extractMemories([{ content: 'a' }])).toEqual([{ content: 'a' }]);
    expect(recallBridge._extractMemories({ memories: [{ content: 'b' }] })).toEqual([{ content: 'b' }]);
    expect(recallBridge._extractMemories({ results: [{ content: 'c' }] })).toEqual([{ content: 'c' }]);
    expect(recallBridge._extractMemories({ data: [{ content: 'd' }] })).toEqual([{ content: 'd' }]);
    expect(recallBridge._extractMemories({})).toEqual([]);
  });

  it('_clean should extract only relevant fields', () => {
    const mem = {
      content: 'test content',
      importance: 0.8,
      tags: ['a', 'b'],
      created_at: '2024-01-01',
      internal_id: 'xyz',
      embedding: [1, 2, 3],
    };
    const cleaned = recallBridge._clean(mem);
    expect(cleaned).toEqual({
      content: 'test content',
      importance: 0.8,
      tags: ['a', 'b'],
      created_at: '2024-01-01',
    });
    expect(cleaned.internal_id).toBeUndefined();
    expect(cleaned.embedding).toBeUndefined();
  });
});
