import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/history — recordVerdict + getHistory', () => {
  let history, tmpDir, cfgMod;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-history-test-'));

    const cfgPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
    delete require.cache[cfgPath];
    cfgMod = require(cfgPath);
    cfgMod.cfg.historyDb = path.join(tmpDir, 'history.db');

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'history.js');
    delete require.cache[modPath];
    history = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should record and retrieve a verdict', () => {
    history.recordVerdict('Q1', 'HEALTHY', 'All good');
    const rows = history.getHistory('Q1');
    expect(rows).toHaveLength(1);
    expect(rows[0].question_id).toBe('Q1');
    expect(rows[0].verdict).toBe('HEALTHY');
    expect(rows[0].summary).toBe('All good');
  });

  it('should record multiple verdicts for same question', () => {
    history.recordVerdict('Q1', 'WARNING', 'First');
    history.recordVerdict('Q1', 'FAILURE', 'Second');
    history.recordVerdict('Q1', 'HEALTHY', 'Third');
    const rows = history.getHistory('Q1');
    expect(rows).toHaveLength(3);
    // newest first
    expect(rows[0].verdict).toBe('HEALTHY');
    expect(rows[2].verdict).toBe('WARNING');
  });

  it('should respect limit parameter', () => {
    for (let i = 0; i < 10; i++) {
      history.recordVerdict('Q1', 'HEALTHY', `Run ${i}`);
    }
    const rows = history.getHistory('Q1', 3);
    expect(rows).toHaveLength(3);
  });

  it('should store failure_type and confidence', () => {
    history.recordVerdict('Q2', 'FAILURE', 'Broke', 'timeout', 'high', 'run-123');
    const rows = history.getHistory('Q2');
    expect(rows[0].failure_type).toBe('timeout');
    expect(rows[0].confidence).toBe('high');
    expect(rows[0].run_id).toBe('run-123');
  });

  it('should return empty array for unknown question', () => {
    expect(history.getHistory('Q99')).toEqual([]);
  });
});

describe('engine/history — getAllLatest', () => {
  let history, tmpDir, cfgMod;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-hist-latest-'));

    const cfgPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
    delete require.cache[cfgPath];
    cfgMod = require(cfgPath);
    cfgMod.cfg.historyDb = path.join(tmpDir, 'history.db');

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'history.js');
    delete require.cache[modPath];
    history = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should return latest verdict per question', () => {
    history.recordVerdict('Q1', 'WARNING', 'First');
    history.recordVerdict('Q1', 'HEALTHY', 'Updated');
    history.recordVerdict('Q2', 'FAILURE', 'Broken');
    const latest = history.getAllLatest();
    expect(latest).toHaveLength(2);
    const q1 = latest.find(r => r.question_id === 'Q1');
    expect(q1.verdict).toBe('HEALTHY');
  });
});

describe('engine/history — detectRegression', () => {
  let history, tmpDir, cfgMod;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-hist-regr-'));

    const cfgPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
    delete require.cache[cfgPath];
    cfgMod = require(cfgPath);
    cfgMod.cfg.historyDb = path.join(tmpDir, 'history.db');

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'history.js');
    delete require.cache[modPath];
    history = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should detect HEALTHY -> FAILURE regression', () => {
    history.recordVerdict('Q1', 'HEALTHY', 'Good');
    history.recordVerdict('Q1', 'FAILURE', 'Broke');
    const reg = history.detectRegression('Q1', 'FAILURE');
    expect(reg).not.toBeNull();
    expect(reg.previous_verdict).toBe('HEALTHY');
    expect(reg.new_verdict).toBe('FAILURE');
  });

  it('should return null for non-regression transitions', () => {
    history.recordVerdict('Q1', 'WARNING', 'Warn');
    history.recordVerdict('Q1', 'HEALTHY', 'Fixed');
    expect(history.detectRegression('Q1', 'HEALTHY')).toBeNull();
  });

  it('should return null with insufficient history', () => {
    history.recordVerdict('Q1', 'FAILURE', 'First ever');
    expect(history.detectRegression('Q1', 'FAILURE')).toBeNull();
  });

  it('should detect COMPLIANT -> NON_COMPLIANT regression', () => {
    history.recordVerdict('Q3', 'COMPLIANT', 'Pass');
    history.recordVerdict('Q3', 'NON_COMPLIANT', 'Fail');
    const reg = history.detectRegression('Q3', 'NON_COMPLIANT');
    expect(reg).not.toBeNull();
    expect(reg.previous_verdict).toBe('COMPLIANT');
  });
});

describe('engine/history — getRegressions', () => {
  let history, tmpDir, cfgMod;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-hist-regrs-'));

    const cfgPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
    delete require.cache[cfgPath];
    cfgMod = require(cfgPath);
    cfgMod.cfg.historyDb = path.join(tmpDir, 'history.db');

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'history.js');
    delete require.cache[modPath];
    history = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should scan all questions and return regressions', () => {
    history.recordVerdict('Q1', 'HEALTHY', 'Good');
    history.recordVerdict('Q1', 'FAILURE', 'Broke');
    history.recordVerdict('Q2', 'WARNING', 'OK');
    history.recordVerdict('Q2', 'HEALTHY', 'Better');
    const regs = history.getRegressions();
    expect(regs).toHaveLength(1);
    expect(regs[0].question_id).toBe('Q1');
  });
});

describe('engine/history — regressionReport', () => {
  let history, tmpDir, cfgMod;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-hist-report-'));

    const cfgPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
    delete require.cache[cfgPath];
    cfgMod = require(cfgPath);
    cfgMod.cfg.historyDb = path.join(tmpDir, 'history.db');

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'history.js');
    delete require.cache[modPath];
    history = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should return empty string when no regressions', () => {
    expect(history.regressionReport()).toBe('');
  });

  it('should return formatted report with regressions', () => {
    history.recordVerdict('Q1', 'HEALTHY', 'Good');
    history.recordVerdict('Q1', 'WARNING', 'Degraded');
    const report = history.regressionReport();
    expect(report).toContain('REGRESSIONS DETECTED');
    expect(report).toContain('Q1');
    expect(report).toContain('HEALTHY -> WARNING');
  });
});
