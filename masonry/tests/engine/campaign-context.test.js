import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/campaign-context — _parseFinding', () => {
  let campaignContext;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'campaign-context.js');
    delete require.cache[modPath];
    campaignContext = require(modPath);
  });

  it('should parse verdict, severity, and summary from finding markdown', () => {
    const md = `# Finding: Q1 — Test

**Verdict**: FAILURE
**Severity**: High

## Summary

Something broke badly
`;
    const result = campaignContext._parseFinding('Q1', md);
    expect(result.id).toBe('Q1');
    expect(result.verdict).toBe('FAILURE');
    expect(result.severity).toBe('High');
    expect(result.summary).toBe('Something broke badly');
  });

  it('should return UNKNOWN verdict when not found', () => {
    const result = campaignContext._parseFinding('Q2', 'no verdict here');
    expect(result.verdict).toBe('UNKNOWN');
  });

  it('should truncate summary to 120 chars', () => {
    const longSummary = 'A'.repeat(200);
    const md = `**Verdict**: WARNING\n\n## Summary\n\n${longSummary}`;
    const result = campaignContext._parseFinding('Q3', md);
    expect(result.summary.length).toBeLessThanOrEqual(120);
  });
});

describe('engine/campaign-context — _severityRank', () => {
  let campaignContext;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'campaign-context.js');
    delete require.cache[modPath];
    campaignContext = require(modPath);
  });

  it('should rank critical < high < medium < low', () => {
    expect(campaignContext._severityRank('', 'Critical')).toBeLessThan(
      campaignContext._severityRank('', 'High'),
    );
    expect(campaignContext._severityRank('', 'High')).toBeLessThan(
      campaignContext._severityRank('', 'Medium'),
    );
    expect(campaignContext._severityRank('', 'Medium')).toBeLessThan(
      campaignContext._severityRank('', 'Low'),
    );
  });

  it('should fall back to verdict mapping when severity is empty', () => {
    expect(campaignContext._severityRank('FAILURE', '')).toBe(1); // high
    expect(campaignContext._severityRank('IMMINENT', '')).toBe(0); // critical
    expect(campaignContext._severityRank('WARNING', '')).toBe(2); // medium
  });
});

describe('engine/campaign-context — topFindings', () => {
  let campaignContext, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-cc-test-'));

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'campaign-context.js');
    delete require.cache[modPath];
    campaignContext = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should return empty array when dir does not exist', () => {
    const result = campaignContext._topFindings(path.join(tmpDir, 'nonexistent'));
    expect(result).toEqual([]);
  });

  it('should parse and sort findings by severity', () => {
    const findingsDir = path.join(tmpDir, 'findings');
    fs.mkdirSync(findingsDir);

    fs.writeFileSync(path.join(findingsDir, 'Q1.md'), `**Verdict**: WARNING\n**Severity**: Medium\n\n## Summary\n\nMedium issue`);
    fs.writeFileSync(path.join(findingsDir, 'Q2.md'), `**Verdict**: FAILURE\n**Severity**: High\n\n## Summary\n\nCritical issue`);
    fs.writeFileSync(path.join(findingsDir, 'Q3.md'), `**Verdict**: HEALTHY\n**Severity**: Info\n\n## Summary\n\nAll good`);

    const results = campaignContext._topFindings(findingsDir, 5);
    expect(results).toHaveLength(3);
    // High (Q2) should come before Medium (Q1) which comes before Info (Q3)
    expect(results[0].id).toBe('Q2');
    expect(results[1].id).toBe('Q1');
  });

  it('should exclude synthesis.md', () => {
    const findingsDir = path.join(tmpDir, 'findings');
    fs.mkdirSync(findingsDir);
    fs.writeFileSync(path.join(findingsDir, 'synthesis.md'), '# Synthesis\n');
    fs.writeFileSync(path.join(findingsDir, 'Q1.md'), `**Verdict**: HEALTHY\n\n## Summary\n\nOK`);

    const results = campaignContext._topFindings(findingsDir);
    expect(results).toHaveLength(1);
    expect(results[0].id).toBe('Q1');
  });
});

describe('engine/campaign-context — generate', () => {
  let campaignContext, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-ccgen-test-'));

    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'campaign-context.js');
    delete require.cache[modPath];
    campaignContext = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should generate campaign-context.md with project summary', () => {
    // Create project-brief.md
    fs.writeFileSync(
      path.join(tmpDir, 'project-brief.md'),
      '# Brief\n\nThis project tests campaign context generation.\n',
    );

    const outPath = campaignContext.generate(tmpDir, 1);
    expect(fs.existsSync(outPath)).toBe(true);

    const content = fs.readFileSync(outPath, 'utf8');
    expect(content).toContain('Campaign Context');
    expect(content).toContain('Wave 1');
    expect(content).toContain('This project tests campaign context generation.');
  });

  it('should include top findings in output', () => {
    fs.writeFileSync(path.join(tmpDir, 'project-brief.md'), '# Brief\n\nTest.\n');
    const findingsDir = path.join(tmpDir, 'findings');
    fs.mkdirSync(findingsDir);
    fs.writeFileSync(
      path.join(findingsDir, 'Q1.md'),
      '**Verdict**: FAILURE\n**Severity**: High\n\n## Summary\n\nAPI timeout detected',
    );

    campaignContext.generate(tmpDir, 2);
    const content = fs.readFileSync(path.join(tmpDir, 'campaign-context.md'), 'utf8');
    expect(content).toContain('Q1');
    expect(content).toContain('FAILURE');
    expect(content).toContain('API timeout detected');
  });

  it('should auto-detect wave from results.tsv', () => {
    fs.writeFileSync(path.join(tmpDir, 'project-brief.md'), '# Brief\n\nTest.\n');
    // 25 results = wave 3
    const header = 'question_id\tverdict\n';
    const rows = Array.from({ length: 25 }, (_, i) => `Q${i}\tHEALTHY`).join('\n');
    fs.writeFileSync(path.join(tmpDir, 'results.tsv'), header + rows + '\n');

    campaignContext.generate(tmpDir);
    const content = fs.readFileSync(path.join(tmpDir, 'campaign-context.md'), 'utf8');
    expect(content).toContain('Wave 3');
  });

  it('should include open hypotheses from .bl-weights.json', () => {
    fs.writeFileSync(path.join(tmpDir, 'project-brief.md'), '# Brief\n\nTest.\n');
    fs.writeFileSync(
      path.join(tmpDir, '.bl-weights.json'),
      JSON.stringify({
        Q10: { weight: 2.0, status: 'PENDING' },
        Q11: { weight: 0.5, status: 'PENDING' },
        Q12: { weight: 1.8, status: 'DONE' },
      }),
    );

    campaignContext.generate(tmpDir, 1);
    const content = fs.readFileSync(path.join(tmpDir, 'campaign-context.md'), 'utf8');
    // Q10 has high weight + PENDING = should appear
    expect(content).toContain('Q10');
    // Q11 is below threshold, Q12 is DONE — neither should appear
    expect(content).not.toContain('Q11');
    expect(content).not.toContain('Q12');
  });

  it('should handle missing project-brief.md gracefully', () => {
    const outPath = campaignContext.generate(tmpDir, 1);
    const content = fs.readFileSync(outPath, 'utf8');
    expect(content).toContain('No project brief found');
  });
});
