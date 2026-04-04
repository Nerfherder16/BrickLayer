import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/crucible — recordScore + getAgentStatus', () => {
  let crucible, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-crucible-test-'));

    const cfgPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
    delete require.cache[cfgPath];

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'crucible.js');
    delete require.cache[modPath];
    crucible = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should record and retrieve agent status', () => {
    crucible.recordScore(tmpDir, { agent: 'test-agent', score: 0.85, checks: {}, details: 'Good' });
    const status = crucible.getAgentStatus(tmpDir, 'test-agent');
    expect(status.agent).toBe('test-agent');
    expect(status.run_count).toBe(1);
    expect(status.last_score).toBe(0.85);
    expect(status.status).toBe('active'); // not enough runs for promotion
  });

  it('should promote agent after MIN_RUNS with high average', () => {
    for (let i = 0; i < 4; i++) {
      crucible.recordScore(tmpDir, { agent: 'star', score: 0.9, checks: {} });
    }
    const status = crucible.getAgentStatus(tmpDir, 'star');
    expect(status.status).toBe('promoted');
    expect(status.avg_score).toBeCloseTo(0.9);
  });

  it('should flag agent with low average', () => {
    for (let i = 0; i < 4; i++) {
      crucible.recordScore(tmpDir, { agent: 'weak', score: 0.45, checks: {} });
    }
    const status = crucible.getAgentStatus(tmpDir, 'weak');
    expect(status.status).toBe('flagged');
  });

  it('should retire agent with very low average', () => {
    for (let i = 0; i < 4; i++) {
      crucible.recordScore(tmpDir, { agent: 'bad', score: 0.3, checks: {} });
    }
    const status = crucible.getAgentStatus(tmpDir, 'bad');
    expect(status.status).toBe('retired');
  });

  it('should return active for unknown agent', () => {
    const status = crucible.getAgentStatus(tmpDir, 'unknown-agent');
    expect(status.status).toBe('active');
    expect(status.run_count).toBe(0);
  });
});

describe('engine/crucible — _weighted', () => {
  let crucible;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'crucible.js');
    delete require.cache[modPath];
    crucible = require(modPath);
  });

  it('should compute weighted score correctly', () => {
    const checks = {
      check_a: [1.0, 0.5],
      check_b: [0.0, 0.5],
    };
    const [score, passRates] = crucible._weighted(checks);
    expect(score).toBeCloseTo(0.5);
    expect(passRates.check_a).toBe(1.0);
    expect(passRates.check_b).toBe(0.0);
  });

  it('should handle all-pass case', () => {
    const checks = {
      a: [1.0, 0.3],
      b: [1.0, 0.7],
    };
    const [score] = crucible._weighted(checks);
    expect(score).toBeCloseTo(1.0);
  });
});

describe('engine/crucible — scorers', () => {
  let crucible, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-crucible-score-'));

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'crucible.js');
    delete require.cache[modPath];
    crucible = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should score synthesizer based on synthesis.md structure', () => {
    const findingsDir = path.join(tmpDir, 'findings');
    fs.mkdirSync(findingsDir);
    fs.writeFileSync(
      path.join(findingsDir, 'synthesis.md'),
      `# Synthesis
## Critical Path
Reference to D1.1 and F2.3 findings.
Residual Risk remains high.
Phase 2 improvements needed.
Mitigation strategy outlined.`,
    );
    const score = crucible.scoreSynthesizer(tmpDir);
    expect(score.agent).toBe('synthesizer');
    expect(score.score).toBeGreaterThan(0.5);
  });

  it('should return 0 for synthesizer when synthesis.md missing', () => {
    const score = crucible.scoreSynthesizer(tmpDir);
    expect(score.score).toBe(0.0);
  });

  it('should return 0 for hypothesis-generator with no wave 2+ questions', () => {
    fs.writeFileSync(path.join(tmpDir, 'questions.md'), '# Questions\n## Q1.1 [research] Test\n**Status**: PENDING\n');
    const score = crucible.scoreHypothesisGenerator(tmpDir);
    expect(score.score).toBe(0.0);
  });
});

describe('engine/crucible — getAllStatuses', () => {
  let crucible, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-crucible-all-'));

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'crucible.js');
    delete require.cache[modPath];
    crucible = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should return statuses for all known agents', () => {
    const statuses = crucible.getAllStatuses(tmpDir);
    expect(statuses.length).toBeGreaterThanOrEqual(4);
    for (const s of statuses) {
      expect(s).toHaveProperty('agent');
      expect(s).toHaveProperty('status');
      expect(s).toHaveProperty('avg_score');
    }
  });
});
