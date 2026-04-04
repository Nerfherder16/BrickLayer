import { describe, it, expect, beforeEach } from 'vitest';
import path from 'path';

describe('engine/runners/subprocess-runner — parseSubprocessSpec', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'subprocess-runner.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should parse command from simple test field', () => {
    const spec = mod._parseSubprocessSpec('npm test\nexpect_exit: 0');
    expect(spec.command).toBe('npm test');
    expect(spec.expectExit).toBe(0);
  });

  it('should parse all directives', () => {
    const spec = mod._parseSubprocessSpec(
      'python check.py\nexpect_exit: 1\nexpect_stdout: ok\nexpect_not_stdout: error\ntimeout: 60',
    );
    expect(spec.command).toBe('python check.py');
    expect(spec.expectExit).toBe(1);
    expect(spec.expectStdout).toBe('ok');
    expect(spec.expectNotStdout).toBe('error');
    expect(spec.timeout).toBe(60);
  });

  it('should strip code fences', () => {
    const spec = mod._parseSubprocessSpec('```bash\necho hello\n```');
    expect(spec.command).toBe('echo hello');
  });

  it('should join multiple command lines with &&', () => {
    const spec = mod._parseSubprocessSpec('cd /tmp\nls -la');
    expect(spec.command).toBe('cd /tmp && ls -la');
  });

  it('should return null command for empty test field', () => {
    const spec = mod._parseSubprocessSpec('');
    expect(spec.command).toBeNull();
  });

  it('should use defaults for missing directives', () => {
    const spec = mod._parseSubprocessSpec('echo hi');
    expect(spec.expectExit).toBe(0);
    expect(spec.expectStdout).toBeNull();
    expect(spec.expectNotStdout).toBeNull();
    expect(spec.timeout).toBe(30);
  });
});

describe('engine/runners/subprocess-runner — buildVerdict', () => {
  let mod;

  beforeEach(() => {
    const modPath = path.resolve(process.cwd(), 'src', 'engine', 'runners', 'subprocess-runner.js');
    delete require.cache[modPath];
    mod = require(modPath);
  });

  it('should return HEALTHY when exit code matches', () => {
    const result = mod._buildVerdict({
      command: 'echo hi',
      returncode: 0,
      stdout: 'hi\n',
      stderr: '',
      expectExit: 0,
      expectStdout: null,
      expectNotStdout: null,
    });
    expect(result.verdict).toBe('HEALTHY');
  });

  it('should return FAILURE when exit code mismatches', () => {
    const result = mod._buildVerdict({
      command: 'false',
      returncode: 1,
      stdout: '',
      stderr: '',
      expectExit: 0,
      expectStdout: null,
      expectNotStdout: null,
    });
    expect(result.verdict).toBe('FAILURE');
    expect(result.summary).toContain('exit code');
  });

  it('should return FAILURE when expected stdout missing', () => {
    const result = mod._buildVerdict({
      command: 'echo nope',
      returncode: 0,
      stdout: 'nope\n',
      stderr: '',
      expectExit: 0,
      expectStdout: 'yes',
      expectNotStdout: null,
    });
    expect(result.verdict).toBe('FAILURE');
  });

  it('should return FAILURE when forbidden stdout present', () => {
    const result = mod._buildVerdict({
      command: 'echo error found',
      returncode: 0,
      stdout: 'error found\n',
      stderr: '',
      expectExit: 0,
      expectStdout: null,
      expectNotStdout: 'error',
    });
    expect(result.verdict).toBe('FAILURE');
  });

  it('should use JSON verdict from stdout if present', () => {
    const jsonOut = JSON.stringify({ verdict: 'WARNING', summary: 'custom' });
    const result = mod._buildVerdict({
      command: 'check',
      returncode: 0,
      stdout: jsonOut,
      stderr: '',
      expectExit: 0,
      expectStdout: null,
      expectNotStdout: null,
    });
    expect(result.verdict).toBe('WARNING');
  });
});
