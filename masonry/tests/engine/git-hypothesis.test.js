import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

describe('engine/git-hypothesis — parseDiffFiles', () => {
  let gitHyp;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'git-hypothesis.js');
    delete require.cache[modPath];
    gitHyp = require(modPath);
  });

  it('should parse unified diff into file entries', () => {
    const diff = `diff --git a/src/auth.py b/src/auth.py
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,3 +1,5 @@
 import os
+import jwt
+from auth_utils import validate_token
 def login():
-    pass
`;
    const files = gitHyp.parseDiffFiles(diff);
    expect(files).toHaveLength(1);
    expect(files[0].file).toBe('src/auth.py');
    expect(files[0].added_lines).toContain('import jwt');
    expect(files[0].removed_lines).toContain('    pass');
  });

  it('should detect new files', () => {
    const diff = `diff --git a/new.py b/new.py
new file mode 100644
--- /dev/null
+++ b/new.py
@@ -0,0 +1,2 @@
+def hello():
+    print("hi")
`;
    const files = gitHyp.parseDiffFiles(diff);
    expect(files[0].is_new_file).toBe(true);
  });

  it('should return empty for empty diff', () => {
    expect(gitHyp.parseDiffFiles('')).toEqual([]);
  });

  it('should handle multiple files', () => {
    const diff = `diff --git a/a.py b/a.py
+added to a
diff --git a/b.py b/b.py
+added to b
`;
    const files = gitHyp.parseDiffFiles(diff);
    expect(files).toHaveLength(2);
    expect(files[0].file).toBe('a.py');
    expect(files[1].file).toBe('b.py');
  });
});

describe('engine/git-hypothesis — matchPatterns', () => {
  let gitHyp;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'git-hypothesis.js');
    delete require.cache[modPath];
    gitHyp = require(modPath);
  });

  it('should match concurrency patterns', () => {
    const files = [{ file: 'server.py', added_lines: ['import asyncio', 'lock = threading.Lock()'], removed_lines: [] }];
    const matches = gitHyp.matchPatterns(files);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].pattern_name).toBe('concurrency');
    expect(matches[0].domain).toBe('D4');
  });

  it('should match auth patterns', () => {
    const files = [{ file: 'login.py', added_lines: ['def authenticate(token):', '  jwt.decode(token)'], removed_lines: [] }];
    const matches = gitHyp.matchPatterns(files);
    const authMatch = matches.find(m => m.pattern_name === 'auth_access_control');
    expect(authMatch).toBeDefined();
  });

  it('should deduplicate per file+pattern', () => {
    const files = [{ file: 'a.py', added_lines: ['threading.Lock()', 'asyncio.run()', 'concurrent.futures'], removed_lines: [] }];
    const matches = gitHyp.matchPatterns(files);
    const concurrencyMatches = matches.filter(m => m.pattern_name === 'concurrency');
    expect(concurrencyMatches).toHaveLength(1);
  });

  it('should return empty for no matches', () => {
    const files = [{ file: 'readme.md', added_lines: ['# Hello world'], removed_lines: [] }];
    expect(gitHyp.matchPatterns(files)).toEqual([]);
  });
});

describe('engine/git-hypothesis — appendToQuestionsMd', () => {
  let gitHyp, tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-gith-test-'));
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'git-hypothesis.js');
    delete require.cache[modPath];
    gitHyp = require(modPath);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should append questions to questions.md', () => {
    const qPath = path.join(tmpDir, 'questions.md');
    fs.writeFileSync(qPath, '# Questions\n\n');
    const questions = [{
      id: 'GH-abc123-1',
      title: 'Concurrency risk in server.py',
      mode: 'diagnose',
      domain: 'D4',
      status: 'PENDING',
      priority: 'high',
      source: 'git_hypothesis',
      commit_sha: 'abc123',
      question: 'Does server.py handle concurrent access safely?',
    }];
    const count = gitHyp.appendToQuestionsMd(tmpDir, questions);
    expect(count).toBe(1);
    const content = fs.readFileSync(qPath, 'utf8');
    expect(content).toContain('Concurrency risk');
    expect(content).toContain('PENDING');
    expect(content).toContain('git_hypothesis');
  });

  it('should return 0 for empty questions', () => {
    fs.writeFileSync(path.join(tmpDir, 'questions.md'), '# Questions\n');
    expect(gitHyp.appendToQuestionsMd(tmpDir, [])).toBe(0);
  });
});
