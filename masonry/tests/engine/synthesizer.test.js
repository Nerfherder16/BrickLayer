import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/synthesizer — _buildFindingsCorpus', () => {
  let synthesizer, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-synth-test-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'synthesizer.js');
    delete require.cache[modPath];
    synthesizer = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should return fallback message when no findings or results', () => {
    const corpus = synthesizer._buildFindingsCorpus(
      path.join(tmpDir, 'findings'),
      path.join(tmpDir, 'results.tsv'),
    );
    expect(corpus).toContain('No findings or results');
  });

  it('should include results.tsv content', () => {
    const resultsPath = path.join(tmpDir, 'results.tsv');
    fs.writeFileSync(resultsPath, 'question_id\tverdict\nQ1\tHEALTHY\n');
    const corpus = synthesizer._buildFindingsCorpus(
      path.join(tmpDir, 'findings'),
      resultsPath,
    );
    expect(corpus).toContain('Results Summary');
    expect(corpus).toContain('Q1\tHEALTHY');
  });

  it('should include finding markdown files', () => {
    const findingsDir = path.join(tmpDir, 'findings');
    fs.mkdirSync(findingsDir);
    fs.writeFileSync(path.join(findingsDir, 'Q1.md'), '**Verdict**: FAILURE\nBroken');
    const corpus = synthesizer._buildFindingsCorpus(findingsDir, path.join(tmpDir, 'results.tsv'));
    expect(corpus).toContain('Q1');
    expect(corpus).toContain('Broken');
  });

  it('should prioritize high-severity findings when over budget', () => {
    const findingsDir = path.join(tmpDir, 'findings');
    fs.mkdirSync(findingsDir);
    // Create many low-severity findings and one high-severity
    for (let i = 0; i < 20; i++) {
      fs.writeFileSync(
        path.join(findingsDir, `Q${i}.md`),
        `**Verdict**: COMPLIANT\n${'x'.repeat(500)}`,
      );
    }
    fs.writeFileSync(
      path.join(findingsDir, 'CRITICAL.md'),
      `**Verdict**: FAILURE\nThis is critical`,
    );

    const corpus = synthesizer._buildFindingsCorpus(
      findingsDir,
      path.join(tmpDir, 'results.tsv'),
    );
    // FAILURE finding should survive truncation
    expect(corpus).toContain('This is critical');
  });
});

describe('engine/synthesizer — parseRecommendation', () => {
  let synthesizer;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'synthesizer.js');
    delete require.cache[modPath];
    synthesizer = require(modPath);
  });

  it('should extract STOP from recommendation section', () => {
    const text = `## Validated Bets\n\n## Recommended Next Action\n\nSTOP — all hypotheses confirmed.`;
    expect(synthesizer.parseRecommendation(text)).toBe('STOP');
  });

  it('should extract PIVOT from recommendation section', () => {
    const text = `## Recommended Next Action\n\nPIVOT — new direction needed.`;
    expect(synthesizer.parseRecommendation(text)).toBe('PIVOT');
  });

  it('should extract CONTINUE from recommendation section', () => {
    const text = `## Recommended Next Action\n\nCONTINUE — more evidence needed.`;
    expect(synthesizer.parseRecommendation(text)).toBe('CONTINUE');
  });

  it('should default to CONTINUE when no recommendation found', () => {
    expect(synthesizer.parseRecommendation('no recommendation here')).toBe('CONTINUE');
  });

  it('should prefer section-scoped scan over full-text scan', () => {
    // STOP in body but CONTINUE in recommendation section
    const text = `## Dead Ends\n\nSTOP probing this path.\n\n## Recommended Next Action\n\nCONTINUE — more questions needed.`;
    expect(synthesizer.parseRecommendation(text)).toBe('CONTINUE');
  });
});

describe('engine/synthesizer — _readDoctrine', () => {
  let synthesizer, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-synth-doc-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'synthesizer.js');
    delete require.cache[modPath];
    synthesizer = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should return empty string when doctrine.md does not exist', () => {
    expect(synthesizer._readDoctrine(tmpDir)).toBe('');
  });

  it('should return doctrine content when file exists', () => {
    fs.writeFileSync(path.join(tmpDir, 'doctrine.md'), '# Project doctrine\nRule 1\n');
    const content = synthesizer._readDoctrine(tmpDir);
    expect(content).toContain('Rule 1');
  });
});
