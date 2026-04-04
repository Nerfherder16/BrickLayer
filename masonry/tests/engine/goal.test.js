import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/goal — _parseGoal', () => {
  let goal;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'goal.js');
    delete require.cache[modPath];
    goal = require(modPath);
  });

  it('should parse all goal.md fields', () => {
    const text = `# Research Goal
**Goal**: Investigate API latency under load
**Target**: http://localhost:8200
**Focus**: D1, D4, D5
**Max questions**: 8
**Context**: Running on ARM64`;
    const result = goal._parseGoal(text);
    expect(result.goal).toBe('Investigate API latency under load');
    expect(result.target).toBe('http://localhost:8200');
    expect(result.focus).toEqual(['D1', 'D4', 'D5']);
    expect(result.max_questions).toBe(8);
    expect(result.context).toBe('Running on ARM64');
  });

  it('should use defaults for optional fields', () => {
    const text = '**Goal**: Test something';
    const result = goal._parseGoal(text);
    expect(result.goal).toBe('Test something');
    expect(result.target).toBe('');
    expect(result.focus).toEqual([]);
    expect(result.max_questions).toBe(6);
    expect(result.context).toBe('');
  });

  it('should throw for missing Goal field', () => {
    expect(() => goal._parseGoal('no goal here')).toThrow('missing required');
  });
});

describe('engine/goal — _parseGoalQuestions', () => {
  let goal;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'goal.js');
    delete require.cache[modPath];
    goal = require(modPath);
  });

  it('should parse valid question blocks split by ---', () => {
    const raw = `---
## QG1.1 [DIAGNOSE] Test question
**Status**: PENDING
**Hypothesis**: Something
---
## QG1.2 [AUDIT] Another question
**Status**: PENDING
**Hypothesis**: Something else
---`;
    const blocks = goal._parseGoalQuestions(raw);
    expect(blocks).toHaveLength(2);
    expect(blocks[0]).toContain('QG1.1');
    expect(blocks[1]).toContain('QG1.2');
  });

  it('should skip blocks missing Status: PENDING', () => {
    const raw = `---
## QG1.1 [DIAGNOSE] Missing status
**Hypothesis**: Something
---`;
    const blocks = goal._parseGoalQuestions(raw);
    expect(blocks).toHaveLength(0);
  });

  it('should skip blocks without ## QG header', () => {
    const raw = `---
Some random text
**Status**: PENDING
---`;
    const blocks = goal._parseGoalQuestions(raw);
    expect(blocks).toHaveLength(0);
  });
});

describe('engine/goal — _getNextWaveIndex', () => {
  let goal;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'goal.js');
    delete require.cache[modPath];
    goal = require(modPath);
  });

  it('should return 1 for empty text', () => {
    expect(goal._getNextWaveIndex('')).toBe(1);
  });

  it('should return next wave after existing QG questions', () => {
    const text = '## QG2.1 [DIAGNOSE] Q1\n## QG2.2 [AUDIT] Q2\n';
    expect(goal._getNextWaveIndex(text)).toBe(3);
  });

  it('should consider BL 2.0 IDs too', () => {
    const text = '## D5.1 [DIAGNOSE] Q1\n## F3.2 [FIX] Q2\n';
    expect(goal._getNextWaveIndex(text)).toBe(6);
  });
});

describe('engine/goal — generateGoalQuestions', () => {
  let goal, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-goal-test-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'goal.js');
    delete require.cache[modPath];
    goal = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should return empty when goal.md not found', () => {
    const result = goal.generateGoalQuestions(
      path.join(tmpDir, 'goal.md'),
      path.join(tmpDir, 'questions.md'),
      true,
    );
    expect(result).toEqual([]);
  });

  it('should return empty when goal.md has no Goal field', () => {
    fs.writeFileSync(path.join(tmpDir, 'goal.md'), 'no goal field\n');
    const result = goal.generateGoalQuestions(
      path.join(tmpDir, 'goal.md'),
      path.join(tmpDir, 'questions.md'),
      true,
    );
    expect(result).toEqual([]);
  });
});
