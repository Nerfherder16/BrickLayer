import { describe, it, expect, beforeEach } from 'vitest';
import path from 'path';

describe('engine/runners/agent — verdictFromAgentOutput', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'agent.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should return INCONCLUSIVE for empty output', () => {
    expect(mod._verdictFromAgentOutput('agent', {})).toBe('INCONCLUSIVE');
    expect(mod._verdictFromAgentOutput('agent', null)).toBe('INCONCLUSIVE');
  });

  it('should return self verdict for generic agents', () => {
    expect(mod._verdictFromAgentOutput('diagnose-analyst', { verdict: 'FAILURE' })).toBe('FAILURE');
    expect(mod._verdictFromAgentOutput('fix-implementer', { verdict: 'FIXED' })).toBe('FIXED');
  });

  it('should return HEALTHY for changes_committed > 0 on generic agents', () => {
    expect(mod._verdictFromAgentOutput('custom-agent', { changes_committed: 2 })).toBe('HEALTHY');
  });

  it('should handle security-hardener with risks_fixed', () => {
    expect(mod._verdictFromAgentOutput('security-hardener', { risks_fixed: 3 })).toBe('HEALTHY');
  });

  it('should handle security-hardener with only risks_reported', () => {
    expect(mod._verdictFromAgentOutput('security-hardener', { risks_reported: 2 })).toBe('WARNING');
  });

  it('should handle test-writer with coverage improvement', () => {
    expect(mod._verdictFromAgentOutput('test-writer', {
      tests_written: 5, coverage_before: 0.5, coverage_after: 0.7,
    })).toBe('HEALTHY');
  });

  it('should handle test-writer with tests but no coverage improvement', () => {
    expect(mod._verdictFromAgentOutput('test-writer', {
      tests_written: 3, coverage_before: 0.5, coverage_after: 0.5,
    })).toBe('WARNING');
  });

  it('should handle type-strictener with errors reduced', () => {
    expect(mod._verdictFromAgentOutput('type-strictener', {
      changes_committed: 1, errors_before: 10, errors_after: 5,
    })).toBe('HEALTHY');
  });

  it('should handle perf-optimizer with good improvement', () => {
    expect(mod._verdictFromAgentOutput('perf-optimizer', {
      changes_committed: 1, improvement_pct: 25,
    })).toBe('HEALTHY');
  });
});

describe('engine/runners/agent — parseTextOutput', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'agent.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should extract commits from text', () => {
    const result = mod._parseTextOutput('agent', 'committed `abc1234` and committed `def5678`');
    expect(result.changes_committed).toBe(2);
  });

  it('should extract verdict/summary for generic agents', () => {
    const text = 'Verdict: FAILURE\nSummary: Something broke';
    const result = mod._parseTextOutput('diagnose-analyst', text);
    expect(result.verdict).toBe('FAILURE');
    expect(result.summary).toBe('Something broke');
  });

  it('should extract security-hardener metrics', () => {
    const text = '3 risks fixed. 1 risk reported. 2 security tests written.';
    const result = mod._parseTextOutput('security-hardener', text);
    expect(result.risks_fixed).toBe(3);
    expect(result.risks_reported).toBe(1);
    expect(result.tests_written).toBe(2);
  });

  it('should extract test-writer metrics', () => {
    const text = '5 tests written\ncoverage: 45.2% → 72.1%';
    const result = mod._parseTextOutput('test-writer', text);
    expect(result.tests_written).toBe(5);
    expect(result.coverage_before).toBeCloseTo(0.452);
    expect(result.coverage_after).toBeCloseTo(0.721);
  });
});

describe('engine/runners/agent — parseAgentRaw', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'agent.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should parse JSON block from agent output', () => {
    const raw = 'Some text\n```json\n{"verdict": "HEALTHY", "summary": "All good"}\n```\nMore text';
    const result = mod.parseAgentRaw('diagnose-analyst', raw);
    expect(result.verdict).toBe('HEALTHY');
    expect(result.summary).toBe('All good');
  });

  it('should unwrap Claude CLI JSON wrapper', () => {
    const wrapper = JSON.stringify({
      result: 'Analysis done\n```json\n{"verdict": "WARNING", "summary": "Watch out"}\n```',
    });
    const result = mod.parseAgentRaw('agent', wrapper);
    expect(result.verdict).toBe('WARNING');
  });

  it('should fall back to text parsing when no JSON block', () => {
    const raw = 'Verdict: FAILURE\nSummary: Things are broken';
    const result = mod.parseAgentRaw('diagnose-analyst', raw);
    expect(result.verdict).toBe('FAILURE');
  });

  it('should return INCONCLUSIVE for empty output', () => {
    const result = mod.parseAgentRaw('agent', '');
    expect(result.verdict).toBe('INCONCLUSIVE');
  });
});

describe('engine/runners/agent — summaryFromAgentOutput', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'agent.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should return summary key if present', () => {
    expect(mod._summaryFromAgentOutput('agent', { summary: 'Custom summary' })).toBe('Custom summary');
  });

  it('should format security-hardener output', () => {
    const s = mod._summaryFromAgentOutput('security-hardener', { risks_found: 5, risks_fixed: 3 });
    expect(s).toContain('risks_found=5');
    expect(s).toContain('fixed=3');
  });

  it('should format test-writer output', () => {
    const s = mod._summaryFromAgentOutput('test-writer', {
      coverage_before: 0.5, coverage_after: 0.7, tests_written: 4,
    });
    expect(s).toContain('50%');
    expect(s).toContain('70%');
  });

  it('should handle empty output', () => {
    const s = mod._summaryFromAgentOutput('agent', null);
    expect(s).toContain('no structured output');
  });
});
