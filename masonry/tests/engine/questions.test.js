import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

const SAMPLE_QUESTIONS_MD = `# Questions

## Q1 [research] API latency investigation

**Mode**: research
**Target**: api-server
**Hypothesis**: API responds within 200ms
**Test**: curl /health
**Verdict threshold**: p99 < 200ms
**Status**: PENDING

## Q2 [quality] Code review

**Mode**: quality
**Target**: src/
**Hypothesis**: Code follows standards
**Verdict threshold**: No critical violations
**Agent**: karen
**Status**: PENDING

## D1.2 [performance] Load test

**Mode**: performance
**Target**: api-server
**Hypothesis**: Handles 1000 rps
**Verdict threshold**: No errors under load
**Operational Mode**: benchmark
**Status**: PENDING

## Q3 [static] Security scan

**Mode**: static
**Target**: src/
**Hypothesis**: No vulnerabilities
**Verdict threshold**: Zero CVEs
**Resume After**: Q1
**Status**: PENDING
`;

describe('engine/questions — parseQuestions', () => {
  let questions, tmpDir, cfgMod;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-questions-test-'));

    const cfgPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
    delete require.cache[cfgPath];
    cfgMod = require(cfgPath);
    cfgMod.cfg.questionsMd = path.join(tmpDir, 'questions.md');
    cfgMod.cfg.resultsTsv = path.join(tmpDir, 'results.tsv');

    fs.writeFileSync(cfgMod.cfg.questionsMd, SAMPLE_QUESTIONS_MD, 'utf8');

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'questions.js');
    delete require.cache[modPath];
    questions = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should parse all questions from markdown', () => {
    const qs = questions.parseQuestions();
    expect(qs).toHaveLength(4);
    expect(qs[0].id).toBe('Q1');
    expect(qs[1].id).toBe('Q2');
    expect(qs[2].id).toBe('D1.2');
    expect(qs[3].id).toBe('Q3');
  });

  it('should extract fields correctly', () => {
    const qs = questions.parseQuestions();
    const q1 = qs[0];
    expect(q1.mode).toBe('research');
    expect(q1.title).toBe('API latency investigation');
    expect(q1.target).toBe('api-server');
    expect(q1.hypothesis).toBe('API responds within 200ms');
    expect(q1.verdict_threshold).toBe('p99 < 200ms');
    expect(q1.status).toBe('PENDING');
  });

  it('should parse agent and operational_mode fields', () => {
    const qs = questions.parseQuestions();
    expect(qs[1].agent_name).toBe('karen');
    expect(qs[2].operational_mode).toBe('benchmark');
  });

  it('should accept BL 2.0 IDs like D1.2', () => {
    const qs = questions.parseQuestions();
    const d = qs.find(q => q.id === 'D1.2');
    expect(d).toBeDefined();
    expect(d.mode).toBe('performance');
  });

  it('should classify question_type from header tag', () => {
    const qs = questions.parseQuestions();
    // quality and static are code_audit tags
    expect(qs[1].question_type).toBe('code_audit');
    expect(qs[3].question_type).toBe('code_audit');
    // research and performance are behavioral
    expect(qs[0].question_type).toBe('behavioral');
    expect(qs[2].question_type).toBe('behavioral');
  });

  it('should parse resume_after field', () => {
    const qs = questions.parseQuestions();
    expect(qs[3].resume_after).toBe('Q1');
  });
});

describe('engine/questions — getQuestionStatus', () => {
  let questions, tmpDir, cfgMod;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-qstatus-test-'));

    const cfgPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
    delete require.cache[cfgPath];
    cfgMod = require(cfgPath);
    cfgMod.cfg.resultsTsv = path.join(tmpDir, 'results.tsv');
    cfgMod.cfg.questionsMd = path.join(tmpDir, 'questions.md');

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'questions.js');
    delete require.cache[modPath];
    questions = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should return PENDING when results.tsv does not exist', () => {
    expect(questions.getQuestionStatus('Q1')).toBe('PENDING');
  });

  it('should return verdict from results.tsv', () => {
    fs.writeFileSync(
      cfgMod.cfg.resultsTsv,
      'question_id\tverdict\nQ1\tHEALTHY\nQ2\tFAILURE\n',
      'utf8',
    );
    expect(questions.getQuestionStatus('Q1')).toBe('HEALTHY');
    expect(questions.getQuestionStatus('Q2')).toBe('FAILURE');
  });

  it('should return PENDING for unknown question', () => {
    fs.writeFileSync(
      cfgMod.cfg.resultsTsv,
      'question_id\tverdict\nQ1\tHEALTHY\n',
      'utf8',
    );
    expect(questions.getQuestionStatus('Q99')).toBe('PENDING');
  });
});

describe('engine/questions — getNextPending', () => {
  let questions;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'questions.js');
    delete require.cache[modPath];
    questions = require(modPath);
  });

  it('should return first PENDING question', () => {
    const qs = [
      { id: 'Q1', status: 'DONE' },
      { id: 'Q2', status: 'PENDING' },
      { id: 'Q3', status: 'PENDING' },
    ];
    expect(questions.getNextPending(qs).id).toBe('Q2');
  });

  it('should skip parked statuses', () => {
    const qs = [
      { id: 'Q1', status: 'DIAGNOSIS_COMPLETE' },
      { id: 'Q2', status: 'BLOCKED' },
      { id: 'Q3', status: 'PENDING' },
    ];
    expect(questions.getNextPending(qs).id).toBe('Q3');
  });

  it('should return null when no PENDING questions', () => {
    const qs = [
      { id: 'Q1', status: 'DONE' },
      { id: 'Q2', status: 'FIXED' },
    ];
    expect(questions.getNextPending(qs)).toBeNull();
  });

  it('should skip question gated by unresolved resume_after ID', () => {
    const qs = [
      { id: 'Q1', status: 'PENDING', resume_after: '' },
      { id: 'Q2', status: 'PENDING', resume_after: 'Q1' },
    ];
    // Q1 is PENDING (unresolved), so Q2 should be skipped, Q1 returned
    expect(questions.getNextPending(qs).id).toBe('Q1');
  });

  it('should allow question when resume_after ID is resolved', () => {
    const qs = [
      { id: 'Q1', status: 'DONE' },
      { id: 'Q2', status: 'PENDING', resume_after: 'Q1' },
    ];
    expect(questions.getNextPending(qs).id).toBe('Q2');
  });

  it('should skip question gated by future datetime', () => {
    const future = new Date(Date.now() + 86400000).toISOString();
    const qs = [
      { id: 'Q1', status: 'PENDING', resume_after: future },
      { id: 'Q2', status: 'PENDING', resume_after: '' },
    ];
    expect(questions.getNextPending(qs).id).toBe('Q2');
  });

  it('should allow question when resume_after datetime has passed', () => {
    const past = new Date(Date.now() - 86400000).toISOString();
    const qs = [
      { id: 'Q1', status: 'PENDING', resume_after: past },
    ];
    expect(questions.getNextPending(qs).id).toBe('Q1');
  });
});

describe('engine/questions — getQuestionById', () => {
  let questions;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'questions.js');
    delete require.cache[modPath];
    questions = require(modPath);
  });

  it('should return matching question', () => {
    const qs = [{ id: 'Q1' }, { id: 'Q2' }, { id: 'Q3' }];
    expect(questions.getQuestionById(qs, 'Q2').id).toBe('Q2');
  });

  it('should return null for missing ID', () => {
    const qs = [{ id: 'Q1' }];
    expect(questions.getQuestionById(qs, 'Q99')).toBeNull();
  });
});

describe('engine/questions — syncStatusFromResults', () => {
  let questions, tmpDir, cfgMod;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-sync-test-'));

    const cfgPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
    delete require.cache[cfgPath];
    cfgMod = require(cfgPath);
    cfgMod.cfg.questionsMd = path.join(tmpDir, 'questions.md');
    cfgMod.cfg.resultsTsv = path.join(tmpDir, 'results.tsv');

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'questions.js');
    delete require.cache[modPath];
    questions = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should update PENDING to DONE for HEALTHY verdict', () => {
    fs.writeFileSync(cfgMod.cfg.questionsMd, SAMPLE_QUESTIONS_MD, 'utf8');
    fs.writeFileSync(
      cfgMod.cfg.resultsTsv,
      'question_id\tverdict\nQ1\tHEALTHY\n',
      'utf8',
    );
    const count = questions.syncStatusFromResults();
    expect(count).toBe(1);
    const text = fs.readFileSync(cfgMod.cfg.questionsMd, 'utf8');
    // Q1 block should have DONE, Q2 should still be PENDING
    expect(text).toContain('**Status**: DONE');
    expect(text).toMatch(/Q2[\s\S]*\*\*Status\*\*: PENDING/);
  });

  it('should preserve FAILURE verdict in status', () => {
    fs.writeFileSync(cfgMod.cfg.questionsMd, SAMPLE_QUESTIONS_MD, 'utf8');
    fs.writeFileSync(
      cfgMod.cfg.resultsTsv,
      'question_id\tverdict\nQ2\tFAILURE\n',
      'utf8',
    );
    questions.syncStatusFromResults();
    const text = fs.readFileSync(cfgMod.cfg.questionsMd, 'utf8');
    expect(text).toContain('**Status**: FAILURE');
  });

  it('should return 0 when files do not exist', () => {
    expect(questions.syncStatusFromResults()).toBe(0);
  });
});
