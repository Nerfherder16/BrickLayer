import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/findings — classifyFailureType', () => {
  let findings;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'findings.js');
    delete require.cache[modPath];
    findings = require(modPath);
  });

  it('should return null for non-failure verdicts', () => {
    expect(findings.classifyFailureType({ verdict: 'HEALTHY' }, 'agent')).toBeNull();
    expect(findings.classifyFailureType({ verdict: 'WARNING' }, 'agent')).toBeNull();
    expect(findings.classifyFailureType({ verdict: 'FIXED' }, 'fix')).toBeNull();
    expect(findings.classifyFailureType({ verdict: 'COMPLIANT' }, 'audit')).toBeNull();
    expect(findings.classifyFailureType({ verdict: 'OK' }, 'monitor')).toBeNull();
    expect(findings.classifyFailureType({ verdict: 'BLOCKED' }, 'frontier')).toBeNull();
  });

  it('should detect timeout failures', () => {
    const result = { verdict: 'FAILURE', details: 'Request timed out after 30s' };
    expect(findings.classifyFailureType(result, 'agent')).toBe('timeout');
  });

  it('should detect tool_failure from connection errors', () => {
    const result = { verdict: 'FAILURE', details: 'Connection refused on port 8080' };
    expect(findings.classifyFailureType(result, 'agent')).toBe('tool_failure');
  });

  it('should detect syntax errors', () => {
    const result = { verdict: 'FAILURE', details: 'SyntaxError: invalid syntax at line 42' };
    expect(findings.classifyFailureType(result, 'agent')).toBe('syntax');
  });

  it('should classify correctness/performance mode as logic', () => {
    const result = { verdict: 'FAILURE', details: 'assertion failed' };
    expect(findings.classifyFailureType(result, 'correctness')).toBe('logic');
    expect(findings.classifyFailureType(result, 'performance')).toBe('logic');
  });

  it('should detect hallucination in agent mode', () => {
    const result = { verdict: 'FAILURE', details: 'no evidence found, cannot verify claim' };
    expect(findings.classifyFailureType(result, 'agent')).toBe('hallucination');
  });

  it('should return unknown for unclassifiable failures', () => {
    const result = { verdict: 'FAILURE', details: 'something went wrong' };
    expect(findings.classifyFailureType(result, 'agent')).toBe('unknown');
  });
});

describe('engine/findings — classifyConfidence', () => {
  let findings;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'findings.js');
    delete require.cache[modPath];
    findings = require(modPath);
  });

  it('should return uncertain for INCONCLUSIVE', () => {
    expect(findings.classifyConfidence({ verdict: 'INCONCLUSIVE' }, 'agent')).toBe('uncertain');
  });

  it('should handle performance mode with stages', () => {
    expect(findings.classifyConfidence({ verdict: 'HEALTHY', data: { stages: [1, 2, 3] } }, 'performance')).toBe('high');
    expect(findings.classifyConfidence({ verdict: 'HEALTHY', data: { stages: [1] } }, 'performance')).toBe('medium');
    expect(findings.classifyConfidence({ verdict: 'HEALTHY', data: {} }, 'performance')).toBe('uncertain');
  });

  it('should handle correctness mode with pass/fail counts', () => {
    expect(findings.classifyConfidence({ verdict: 'HEALTHY', data: { passed: 15, failed: 0 } }, 'correctness')).toBe('high');
    expect(findings.classifyConfidence({ verdict: 'HEALTHY', data: { passed: 3, failed: 1 } }, 'correctness')).toBe('medium');
    expect(findings.classifyConfidence({ verdict: 'HEALTHY', data: { passed: 1, failed: 0 } }, 'correctness')).toBe('low');
  });

  it('should detect concrete signals in agent mode', () => {
    expect(findings.classifyConfidence(
      { verdict: 'FAILURE', details: 'line 42 in /src/main.py: def foo(): error: assert failed' },
      'agent'
    )).toBe('high');
  });
});

describe('engine/findings — scoreResult', () => {
  let findings;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'findings.js');
    delete require.cache[modPath];
    findings = require(modPath);
  });

  it('should return a number between 0 and 1', () => {
    const score = findings.scoreResult({ verdict: 'HEALTHY', confidence: 'high' });
    expect(score).toBeGreaterThanOrEqual(0);
    expect(score).toBeLessThanOrEqual(1);
  });

  it('should score HEALTHY/high higher than FAILURE/low', () => {
    const good = findings.scoreResult({ verdict: 'HEALTHY', confidence: 'high' });
    const bad = findings.scoreResult({ verdict: 'FAILURE', confidence: 'low', failure_type: 'tool_failure' });
    expect(good).toBeGreaterThan(bad);
  });

  it('should score INCONCLUSIVE/uncertain near 0', () => {
    const score = findings.scoreResult({ verdict: 'INCONCLUSIVE', confidence: 'uncertain' });
    // evidence=0 * 0.4 + clarity=0 * 0.4 + execution=1.0 * 0.2 = 0.2
    expect(score).toBe(0.2);
  });
});

describe('engine/findings — writeFinding', () => {
  let findings, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-findings-test-'));

    const cfgPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
    delete require.cache[cfgPath];
    const { cfg } = require(cfgPath);
    cfg.findingsDir = tmpDir;

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'findings.js');
    delete require.cache[modPath];
    findings = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should write a finding markdown file', () => {
    const question = {
      id: 'Q1',
      title: 'Test Question',
      hypothesis: 'Does it work?',
      mode: 'research',
      target: 'test-target',
      verdict_threshold: 'Pass if green',
    };
    const result = {
      verdict: 'HEALTHY',
      summary: 'Everything looks good',
      details: 'Detailed evidence here',
      data: { key: 'value' },
    };

    const filePath = findings.writeFinding(question, result);
    expect(fs.existsSync(filePath)).toBe(true);

    const content = fs.readFileSync(filePath, 'utf8');
    expect(content).toContain('# Finding: Q1');
    expect(content).toContain('**Verdict**: HEALTHY');
    expect(content).toContain('Everything looks good');
    expect(content).toContain('Detailed evidence here');
  });

  it('should cap code_audit confidence to medium', () => {
    const question = {
      id: 'Q2',
      title: 'Code Audit',
      hypothesis: 'Is it secure?',
      mode: 'research',
      question_type: 'code_audit',
      target: 'test',
      verdict_threshold: 'Must pass audit',
    };
    const result = {
      verdict: 'HEALTHY',
      confidence: 'high',
      summary: 'Looks good',
      details: 'Evidence',
      data: {},
    };

    const filePath = findings.writeFinding(question, result);
    const content = fs.readFileSync(filePath, 'utf8');
    // code_audit HEALTHY gets downgraded to WARNING
    expect(content).toContain('**Verdict**: WARNING');
    // confidence capped at medium (0.6)
    expect(content).toContain('**Confidence**: 0.6');
  });
});

describe('engine/findings — updateResultsTsv', () => {
  let findings, tmpDir, cfgMod;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-tsv-test-'));

    const cfgPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
    delete require.cache[cfgPath];
    cfgMod = require(cfgPath);
    cfgMod.cfg.resultsTsv = path.join(tmpDir, 'results.tsv');
    cfgMod.cfg.questionsMd = path.join(tmpDir, 'questions.md');

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'findings.js');
    delete require.cache[modPath];
    findings = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should create results.tsv with header if it does not exist', () => {
    findings.updateResultsTsv('Q1', 'HEALTHY', 'All good');
    const content = fs.readFileSync(cfgMod.cfg.resultsTsv, 'utf8');
    expect(content).toContain('question_id\tverdict');
    expect(content).toContain('Q1\tHEALTHY');
  });

  it('should upsert existing rows', () => {
    findings.updateResultsTsv('Q1', 'WARNING', 'First run');
    findings.updateResultsTsv('Q1', 'HEALTHY', 'Second run');
    const lines = fs.readFileSync(cfgMod.cfg.resultsTsv, 'utf8').trim().split('\n');
    const q1Lines = lines.filter(l => l.startsWith('Q1'));
    expect(q1Lines).toHaveLength(1);
    expect(q1Lines[0]).toContain('HEALTHY');
  });

  it('should include failure_type and eval_score when provided', () => {
    findings.updateResultsTsv('Q2', 'FAILURE', 'Broken', 'timeout', 0.3);
    const content = fs.readFileSync(cfgMod.cfg.resultsTsv, 'utf8');
    expect(content).toContain('timeout');
    expect(content).toContain('0.300');
  });
});
