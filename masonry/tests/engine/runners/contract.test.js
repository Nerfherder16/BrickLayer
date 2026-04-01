import { describe, it, expect, beforeAll, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('runners/contract', () => {
  let mod, tmpDir;

  beforeAll(() => {
    const modPath = path.resolve(
      process.cwd(), 'src', 'engine', 'runners', 'contract.js',
    );
    delete require.cache[modPath];
    mod = require(modPath);
  });

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-contract-'));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('_makeFinding', () => {
    it('should create a finding object', () => {
      const f = mod._makeFinding('/src/lib.rs', 10, 'pub field: AccountInfo', 'warning', 'Test msg');
      expect(f.file).toBe('/src/lib.rs');
      expect(f.line).toBe(10);
      expect(f.severity).toBe('warning');
      expect(f.message).toBe('Test msg');
      expect(f.snippet).toBe('pub field: AccountInfo');
    });

    it('should truncate snippet to 120 chars', () => {
      const long = 'x'.repeat(200);
      const f = mod._makeFinding('/f.rs', 1, long, 'info', 'msg');
      expect(f.snippet.length).toBeLessThanOrEqual(120);
    });
  });

  describe('_checkOverflowPatterns', () => {
    it('should flag unchecked arithmetic', () => {
      const src = 'let result = amount + fee;\n';
      fs.writeFileSync(path.join(tmpDir, 'lib.rs'), src);
      const findings = mod._checkOverflowPatterns([path.join(tmpDir, 'lib.rs')]);
      expect(findings.length).toBeGreaterThanOrEqual(1);
      expect(findings[0].message).toContain('Unchecked arithmetic');
    });

    it('should skip lines with safe arithmetic', () => {
      const src = 'let result = amount.checked_add(fee).unwrap();\n';
      fs.writeFileSync(path.join(tmpDir, 'lib.rs'), src);
      const findings = mod._checkOverflowPatterns([path.join(tmpDir, 'lib.rs')]);
      expect(findings).toHaveLength(0);
    });

    it('should skip comments and imports', () => {
      const src = '// amount + fee\nuse crate::a + b;\n';
      fs.writeFileSync(path.join(tmpDir, 'lib.rs'), src);
      const findings = mod._checkOverflowPatterns([path.join(tmpDir, 'lib.rs')]);
      expect(findings).toHaveLength(0);
    });

    it('should skip single-char variables', () => {
      const src = 'let x = i + j;\n';
      fs.writeFileSync(path.join(tmpDir, 'lib.rs'), src);
      const findings = mod._checkOverflowPatterns([path.join(tmpDir, 'lib.rs')]);
      expect(findings).toHaveLength(0);
    });
  });

  describe('_checkSeedCanonicalization', () => {
    it('should flag create_program_address usage', () => {
      const src = 'let addr = create_program_address(&seeds, &program_id);\n';
      fs.writeFileSync(path.join(tmpDir, 'lib.rs'), src);
      const findings = mod._checkSeedCanonicalization([path.join(tmpDir, 'lib.rs')]);
      expect(findings.length).toBeGreaterThanOrEqual(1);
      expect(findings[0].message).toContain('create_program_address');
    });

    it('should not flag find_program_address', () => {
      const src = 'let (addr, bump) = find_program_address(&seeds, &program_id);\n';
      fs.writeFileSync(path.join(tmpDir, 'lib.rs'), src);
      const findings = mod._checkSeedCanonicalization([path.join(tmpDir, 'lib.rs')]);
      expect(findings).toHaveLength(0);
    });
  });

  describe('_checkPatternSearch', () => {
    it('should find user-defined patterns', () => {
      const src = 'unsafe { ptr::write(buf, val); }\n';
      fs.writeFileSync(path.join(tmpDir, 'lib.rs'), src);
      const patterns = [
        { pattern: 'unsafe', severity: 'warning', message: 'Unsafe block detected' },
      ];
      const findings = mod._checkPatternSearch([path.join(tmpDir, 'lib.rs')], patterns);
      expect(findings.length).toBeGreaterThanOrEqual(1);
      expect(findings[0].message).toBe('Unsafe block detected');
    });

    it('should skip invalid regex patterns', () => {
      const src = 'normal code\n';
      fs.writeFileSync(path.join(tmpDir, 'lib.rs'), src);
      const patterns = [
        { pattern: '[invalid', severity: 'warning', message: 'Bad regex' },
      ];
      const findings = mod._checkPatternSearch([path.join(tmpDir, 'lib.rs')], patterns);
      expect(findings).toHaveLength(0);
    });
  });

  describe('_determineVerdict', () => {
    it('should return HEALTHY for no findings', () => {
      const [verdict] = mod._determineVerdict([], 0, 0, 0, 0, 0, 5);
      expect(verdict).toBe('HEALTHY');
    });

    it('should return FAILURE for signer failures', () => {
      const findings = [
        { severity: 'critical', message: 'Handler no signer' },
      ];
      const [verdict] = mod._determineVerdict(findings, 1, 0, 0, 0, 0, 5);
      expect(verdict).toBe('FAILURE');
    });

    it('should return FAILURE for reentrancy', () => {
      const findings = [
        { severity: 'critical', message: 'reentrancy in fn' },
      ];
      const [verdict] = mod._determineVerdict(findings, 0, 1, 0, 0, 0, 5);
      expect(verdict).toBe('FAILURE');
    });

    it('should return WARNING for overflow above threshold', () => {
      const findings = Array(6).fill(null).map((_, i) => ({
        severity: 'warning',
        message: `overflow ${i}`,
      }));
      const [verdict] = mod._determineVerdict(findings, 0, 0, 0, 6, 0, 5);
      expect(verdict).toBe('WARNING');
    });

    it('should return FAILURE for unchecked fields above max', () => {
      const findings = [{ severity: 'warning', message: 'unchecked field' }];
      const [verdict] = mod._determineVerdict(findings, 0, 0, 1, 0, 0, 5);
      expect(verdict).toBe('FAILURE');
    });
  });
});
