import { describe, it, expect, beforeAll, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('runners/document', () => {
  let mod, tmpDir;

  beforeAll(() => {
    const modPath = path.resolve(
      process.cwd(), 'src', 'engine', 'runners', 'document.js',
    );
    delete require.cache[modPath];
    mod = require(modPath);
  });

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-document-'));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('_checkEndpointCoverage', () => {
    it('should find routes in source and check docs', () => {
      const srcDir = path.join(tmpDir, 'src');
      fs.mkdirSync(srcDir);
      fs.writeFileSync(
        path.join(srcDir, 'api.py'),
        '@app.get("/users")\ndef get_users(): pass\n@app.post("/items")\ndef create_item(): pass\n',
      );
      const docText = 'API Reference\n/users endpoint\n';
      const result = mod._checkEndpointCoverage(
        [path.join(srcDir, 'api.py')],
        docText,
        '@(app|router)\\.(get|post|put|delete|patch)',
        0.8,
      );
      expect(result.count).toBe(2);
      expect(result.coverage).toBe(0.5);
      expect(result.passed).toBe(false);
    });

    it('should return passed true when no routes found', () => {
      const srcDir = path.join(tmpDir, 'src');
      fs.mkdirSync(srcDir);
      fs.writeFileSync(path.join(srcDir, 'util.py'), 'def helper(): pass\n');
      const result = mod._checkEndpointCoverage(
        [path.join(srcDir, 'util.py')],
        'docs',
        '@(app|router)\\.(get|post)',
        0.8,
      );
      expect(result.passed).toBe(true);
      expect(result.count).toBe(0);
    });
  });

  describe('_checkFunctionCoverage', () => {
    it('should find public functions and check docs', () => {
      const srcDir = path.join(tmpDir, 'src');
      fs.mkdirSync(srcDir);
      fs.writeFileSync(
        path.join(srcDir, 'lib.py'),
        'def calculate_total(): pass\ndef _private(): pass\ndef process_order(): pass\n',
      );
      const docText = 'Functions\ncalculate_total\n';
      const result = mod._checkFunctionCoverage(
        [path.join(srcDir, 'lib.py')],
        docText,
        0.8,
      );
      expect(result.count).toBe(2); // calculate_total and process_order
      expect(result.coverage).toBe(0.5);
      expect(result.passed).toBe(false);
    });
  });

  describe('_checkExampleSyntax', () => {
    it('should pass valid Python blocks', () => {
      const docText = '```python\nx = 1 + 2\n```\n';
      const result = mod._checkExampleSyntax(docText, ['python']);
      expect(result.passed).toBe(true);
      expect(result.count).toBe(1);
    });

    it('should fail invalid Python blocks', () => {
      const docText = '```python\ndef foo(\n```\n';
      const result = mod._checkExampleSyntax(docText, ['python']);
      expect(result.passed).toBe(false);
      expect(result.issues.length).toBeGreaterThanOrEqual(1);
    });

    it('should pass valid JSON blocks', () => {
      const docText = '```json\n{"key": "value"}\n```\n';
      const result = mod._checkExampleSyntax(docText, ['json']);
      expect(result.passed).toBe(true);
    });

    it('should fail invalid JSON blocks', () => {
      const docText = '```json\n{invalid json}\n```\n';
      const result = mod._checkExampleSyntax(docText, ['json']);
      expect(result.passed).toBe(false);
    });

    it('should skip languages without parsers', () => {
      const docText = '```rust\nfn main() {}\n```\n';
      const result = mod._checkExampleSyntax(docText, ['rust']);
      expect(result.count).toBe(0);
    });
  });

  describe('_checkKeywordPresence', () => {
    it('should pass when all keywords present', () => {
      const docText = 'Installation guide\nUsage instructions\nConfiguration options\n';
      const result = mod._checkKeywordPresence(docText, ['installation', 'usage', 'configuration']);
      expect(result.passed).toBe(true);
      expect(result.coverage).toBe(1.0);
    });

    it('should fail when keywords missing', () => {
      const docText = 'Installation guide\n';
      const result = mod._checkKeywordPresence(docText, ['installation', 'usage']);
      expect(result.passed).toBe(false);
      expect(result.coverage).toBe(0.5);
      expect(result.issues).toContainEqual("Missing keyword: 'usage'");
    });
  });

  describe('_checkDeadLinks', () => {
    it('should pass when all local links resolve', () => {
      fs.writeFileSync(path.join(tmpDir, 'other.md'), 'content');
      const docPath = path.join(tmpDir, 'README.md');
      fs.writeFileSync(docPath, '');
      const docText = '[See other](other.md)\n[External](https://example.com)\n';
      const result = mod._checkDeadLinks([docPath], docText);
      expect(result.passed).toBe(true);
    });

    it('should fail for dead local links', () => {
      const docPath = path.join(tmpDir, 'README.md');
      fs.writeFileSync(docPath, '');
      const docText = '[Missing](does-not-exist.md)\n';
      const result = mod._checkDeadLinks([docPath], docText);
      expect(result.passed).toBe(false);
      expect(result.issues.length).toBeGreaterThanOrEqual(1);
    });

    it('should skip external links', () => {
      const docPath = path.join(tmpDir, 'README.md');
      const docText = '[External](https://example.com)\n[Mail](mailto:a@b.com)\n';
      const result = mod._checkDeadLinks([docPath], docText);
      expect(result.passed).toBe(true);
      expect(result.count).toBe(0);
    });
  });

  describe('_determineVerdict', () => {
    it('should return HEALTHY when all pass', () => {
      const results = {
        keyword_presence: { passed: true, coverage: 1.0 },
      };
      expect(mod._determineVerdict(results, 0.8)).toBe('HEALTHY');
    });

    it('should return FAILURE for failed coverage check', () => {
      const results = {
        endpoint_coverage: { passed: false, coverage: 0.5 },
      };
      expect(mod._determineVerdict(results, 0.8)).toBe('FAILURE');
    });

    it('should return WARNING for dead links', () => {
      const results = {
        dead_links: { passed: false, coverage: null },
      };
      expect(mod._determineVerdict(results, 0.8)).toBe('WARNING');
    });

    it('should return WARNING for keyword_presence failure', () => {
      const results = {
        keyword_presence: { passed: false, coverage: 0.5 },
      };
      expect(mod._determineVerdict(results, 0.8)).toBe('WARNING');
    });

    it('should return WARNING when passed but coverage < 1.0', () => {
      const results = {
        function_coverage: { passed: true, coverage: 0.9 },
      };
      expect(mod._determineVerdict(results, 0.8)).toBe('WARNING');
    });
  });
});
