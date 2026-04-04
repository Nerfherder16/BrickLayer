import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/healloop — isEnabled / maxCycles', () => {
  let healloop;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'healloop.js');
    delete require.cache[modPath];
    healloop = require(modPath);
  });

  afterEach(() => {
    delete process.env.BRICKLAYER_HEAL_LOOP;
    delete process.env.BRICKLAYER_HEAL_MAX_CYCLES;
  });

  it('should be disabled by default', () => {
    expect(healloop.isEnabled()).toBe(false);
  });

  it('should be enabled when env var is set to 1', () => {
    process.env.BRICKLAYER_HEAL_LOOP = '1';
    expect(healloop.isEnabled()).toBe(true);
  });

  it('should default to 3 max cycles', () => {
    expect(healloop.maxCycles()).toBe(3);
  });

  it('should respect BRICKLAYER_HEAL_MAX_CYCLES env var', () => {
    process.env.BRICKLAYER_HEAL_MAX_CYCLES = '5';
    expect(healloop.maxCycles()).toBe(5);
  });
});

describe('engine/healloop — _syntheticQuestion', () => {
  let healloop;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'healloop.js');
    delete require.cache[modPath];
    healloop = require(modPath);
  });

  it('should create a synthetic question with correct ID format', () => {
    const original = { id: 'Q1', mode: 'research', title: 'Test', target: 'api' };
    const q = healloop._syntheticQuestion(original, 'diagnose-analyst', 'Q1', 1, 'diagnose');
    expect(q.id).toBe('Q1_heal1_diag');
    expect(q.agent_name).toBe('diagnose-analyst');
    expect(q.operational_mode).toBe('diagnose');
    expect(q.question_type).toBe('behavioral');
  });

  it('should use fix short form for fix-implementer', () => {
    const original = { id: 'Q1', mode: 'research', title: 'Test', target: 'api' };
    const q = healloop._syntheticQuestion(original, 'fix-implementer', 'Q1', 2, 'fix');
    expect(q.id).toBe('Q1_heal2_fix');
  });
});

describe('engine/healloop — runHealLoop', () => {
  let healloop, tmpDir, cfgMod;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-heal-test-'));
    fs.mkdirSync(path.join(tmpDir, 'findings'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.claude', 'agents'), { recursive: true });

    const cfgPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
    delete require.cache[cfgPath];
    cfgMod = require(cfgPath);
    cfgMod.cfg.findingsDir = path.join(tmpDir, 'findings');
    cfgMod.cfg.resultsTsv = path.join(tmpDir, 'results.tsv');
    cfgMod.cfg.questionsMd = path.join(tmpDir, 'questions.md');
    cfgMod.cfg.agentsDir = path.join(tmpDir, '.claude', 'agents');

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'healloop.js');
    delete require.cache[modPath];
    healloop = require(modPath);

    process.env.BRICKLAYER_HEAL_LOOP = '1';
    process.env.BRICKLAYER_HEAL_MAX_CYCLES = '2';
  });

  afterEach(() => {
    delete process.env.BRICKLAYER_HEAL_LOOP;
    delete process.env.BRICKLAYER_HEAL_MAX_CYCLES;
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should return initial result when not enabled', () => {
    delete process.env.BRICKLAYER_HEAL_LOOP;
    const result = { verdict: 'FAILURE', summary: 'Broke' };
    const findingPath = path.join(tmpDir, 'findings', 'Q1.md');
    fs.writeFileSync(findingPath, '# Finding\n');
    const final = healloop.runHealLoop({ id: 'Q1' }, result, findingPath, () => ({}));
    expect(final.verdict).toBe('FAILURE');
  });

  it('should return initial result for non-failure verdicts', () => {
    const result = { verdict: 'HEALTHY', summary: 'All good' };
    const findingPath = path.join(tmpDir, 'findings', 'Q1.md');
    fs.writeFileSync(findingPath, '# Finding\n');
    const final = healloop.runHealLoop({ id: 'Q1' }, result, findingPath, () => ({}));
    expect(final.verdict).toBe('HEALTHY');
  });

  it('should reach FIXED when agents succeed', () => {
    // Create agent files so _agentExists passes
    fs.writeFileSync(path.join(cfgMod.cfg.agentsDir, 'diagnose-analyst.md'), '# Agent');
    fs.writeFileSync(path.join(cfgMod.cfg.agentsDir, 'fix-implementer.md'), '# Agent');

    const findingPath = path.join(tmpDir, 'findings', 'Q1.md');
    fs.writeFileSync(findingPath, '# Finding\n**Verdict**: FAILURE\n');

    let callCount = 0;
    const mockRunner = (_q) => {
      callCount++;
      if (callCount === 1) {
        // diagnose-analyst returns DIAGNOSIS_COMPLETE
        return { verdict: 'DIAGNOSIS_COMPLETE', summary: 'Found root cause', details: '', data: {} };
      }
      // fix-implementer returns FIXED
      return { verdict: 'FIXED', summary: 'Applied fix', details: '', data: {} };
    };

    const final = healloop.runHealLoop(
      { id: 'Q1', title: 'Test', hypothesis: 'H', mode: 'research', target: 't', verdict_threshold: 'pass' },
      { verdict: 'FAILURE', summary: 'Broke', details: '', data: {} },
      findingPath,
      mockRunner,
    );
    expect(final.verdict).toBe('FIXED');
  });

  it('should exhaust cycles and write HEAL_EXHAUSTED', () => {
    fs.writeFileSync(path.join(cfgMod.cfg.agentsDir, 'diagnose-analyst.md'), '# Agent');
    fs.writeFileSync(path.join(cfgMod.cfg.agentsDir, 'fix-implementer.md'), '# Agent');

    const findingPath = path.join(tmpDir, 'findings', 'Q1.md');
    fs.writeFileSync(findingPath, '# Finding\n');

    let callCount = 0;
    const mockRunner = (_q) => {
      callCount++;
      // Alternate: diagnose succeeds, fix always fails
      if (callCount % 2 === 1) {
        return { verdict: 'DIAGNOSIS_COMPLETE', summary: 'Diagnosed', details: '', data: {} };
      }
      return { verdict: 'FIX_FAILED', summary: 'Fix did not work', details: '', data: {} };
    };

    const final = healloop.runHealLoop(
      { id: 'Q2', title: 'Test', hypothesis: 'H', mode: 'research', target: 't', verdict_threshold: 'pass' },
      { verdict: 'FAILURE', summary: 'Broke', details: '', data: {} },
      findingPath,
      mockRunner,
    );

    // Should have exhausted cycles
    const findingContent = fs.readFileSync(findingPath, 'utf8');
    expect(findingContent).toContain('EXHAUSTED');
  });
});
