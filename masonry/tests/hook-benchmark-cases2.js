/**
 * hook-benchmark-cases2.js — Additional hook test cases (registered hooks not in cases.js).
 *
 * Covers: masonry-dangerous-cmd, masonry-tdd-enforcer, masonry-context-safety,
 *         masonry-approver, masonry-subagent-tracker, masonry-tool-failure,
 *         masonry-register, masonry-mortar-enforcer, masonry-dep-audit,
 *         masonry-post-write-runner, masonry-pre-protect, masonry-auto-pr,
 *         masonry-build-outcome, masonry-mistake-monitor, masonry-pre-compact,
 *         masonry-post-compact, masonry-session-start, masonry-hook-watch
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

module.exports = async function runCases2(ctx) {
  const {
    hook, runHook, test,
    assertExitCode, assertStderr, assertNoStderr,
    assertUnderMs, assertNotTimedOut, MOCK_RECALL, MOCK_OLLAMA,
  } = ctx;

  // ─── masonry-dangerous-cmd ───────────────────────────────────────────────────

  await test('masonry-dangerous-cmd: allows normal git commit', async () => {
    const r = await runHook(hook('masonry-dangerous-cmd.js'),
      { tool_name: 'Bash', tool_input: { command: 'git commit -m "feat: add login"' }, cwd: '/tmp' },
      {});
    assertExitCode(r, 0);
  });

  await test('masonry-dangerous-cmd: allows git stash (not drop)', async () => {
    const r = await runHook(hook('masonry-dangerous-cmd.js'),
      { tool_name: 'Bash', tool_input: { command: 'git stash' }, cwd: '/tmp' },
      {});
    assertExitCode(r, 0);
  });

  await test('masonry-dangerous-cmd: blocks force push to main', async () => {
    const r = await runHook(hook('masonry-dangerous-cmd.js'),
      { tool_name: 'Bash', tool_input: { command: 'git push origin main --force' }, cwd: '/tmp' },
      {});
    // Blocks because target branch is "main" — no git state needed for this check
    assertExitCode(r, 2);
  });

  await test('masonry-dangerous-cmd: allows force push to feature branch', async () => {
    const r = await runHook(hook('masonry-dangerous-cmd.js'),
      { tool_name: 'Bash', tool_input: { command: 'git push origin feature/auth --force' }, cwd: '/tmp' },
      {});
    assertExitCode(r, 0);
  });

  await test('masonry-dangerous-cmd: passes through non-Bash tools', async () => {
    const r = await runHook(hook('masonry-dangerous-cmd.js'),
      { tool_name: 'Write', tool_input: { file_path: '/tmp/x.js', content: 'x' } },
      {});
    assertExitCode(r, 0);
  });

  // ─── masonry-tdd-enforcer ────────────────────────────────────────────────────

  await test('masonry-tdd-enforcer: exits 0 for exempt .json file', async () => {
    const r = await runHook(hook('masonry-tdd-enforcer.js'),
      { tool_name: 'Write', tool_input: { file_path: '/project/tsconfig.json', content: '{}' } },
      {});
    assertExitCode(r, 0);
  });

  await test('masonry-tdd-enforcer: warns (no block) for impl file outside build mode', async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'tdd-warn-'));
    const implFile = path.join(tmpDir, 'utils.py');
    fs.writeFileSync(implFile, 'def add(a, b): return a + b\n');
    try {
      // No .autopilot/mode file → outside build mode → warn only, exit 0
      const r = await runHook(hook('masonry-tdd-enforcer.js'),
        { tool_name: 'Write', tool_input: { file_path: implFile, content: 'def add(a,b): return a+b\n' } },
        {});
      assertExitCode(r, 0);
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  await test('masonry-tdd-enforcer: BLOCKS impl file in build mode without test', async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'tdd-block-'));
    const apDir = path.join(tmpDir, '.autopilot');
    fs.mkdirSync(apDir, { recursive: true });
    fs.writeFileSync(path.join(apDir, 'mode'), 'build');
    const srcDir = path.join(tmpDir, 'src');
    fs.mkdirSync(srcDir, { recursive: true });
    const implFile = path.join(srcDir, 'utils.py');
    fs.writeFileSync(implFile, 'def add(a, b): return a + b\n');
    try {
      const r = await runHook(hook('masonry-tdd-enforcer.js'),
        { tool_name: 'Write', tool_input: { file_path: implFile, content: 'def add(a,b): return a+b\n' } },
        {});
      assertExitCode(r, 2);
      assertStderr(r, 'TDD enforcer');
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  // ─── masonry-context-safety ──────────────────────────────────────────────────

  await test('masonry-context-safety: exits 0 for non-ExitPlanMode tool', async () => {
    const r = await runHook(hook('masonry-context-safety.js'),
      { tool_name: 'Write', tool_input: { file_path: '/tmp/x.js' } },
      {});
    assertExitCode(r, 0);
  });

  await test('masonry-context-safety: exits 0 for ExitPlanMode without active build', async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ctx-safe-'));
    try {
      const r = await runHook(hook('masonry-context-safety.js'),
        { tool_name: 'ExitPlanMode', cwd: tmpDir },
        {});
      assertExitCode(r, 0);
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  await test('masonry-context-safety: BLOCKS ExitPlanMode during active IN_PROGRESS build', async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ctx-block-'));
    const apDir = path.join(tmpDir, '.autopilot');
    fs.mkdirSync(apDir, { recursive: true });
    fs.writeFileSync(path.join(apDir, 'mode'), 'build');
    fs.writeFileSync(path.join(apDir, 'progress.json'),
      JSON.stringify({ tasks: [{ status: 'IN_PROGRESS', description: 'implement auth endpoint' }] }));
    try {
      const r = await runHook(hook('masonry-context-safety.js'),
        { tool_name: 'ExitPlanMode', cwd: tmpDir },
        {});
      assertExitCode(r, 2);
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  // ─── masonry-approver ────────────────────────────────────────────────────────

  await test('masonry-approver: exits 0 without active build mode (no auto-approve)', async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'approver-idle-'));
    try {
      const r = await runHook(hook('masonry-approver.js'),
        { tool_name: 'Write', cwd: tmpDir,
          tool_input: { file_path: path.join(tmpDir, 'utils.py') } },
        {});
      assertExitCode(r, 0);
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  await test('masonry-approver: auto-approves Write in build mode', async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'approver-build-'));
    const apDir = path.join(tmpDir, '.autopilot');
    fs.mkdirSync(apDir, { recursive: true });
    fs.writeFileSync(path.join(apDir, 'mode'), 'build');
    // progress.json must exist and be fresh (isFresh check in findAutopilotMode)
    fs.writeFileSync(path.join(apDir, 'progress.json'),
      JSON.stringify({ tasks: [{ status: 'IN_PROGRESS', description: 'implement utils' }] }));
    try {
      const r = await runHook(hook('masonry-approver.js'),
        { tool_name: 'Write', cwd: tmpDir,
          tool_input: { file_path: path.join(tmpDir, 'utils.py') } },
        {});
      assertExitCode(r, 0);
      if (!r.stdout.includes('allow')) {
        throw new Error(`stdout should contain "allow" in build mode, got: ${r.stdout.slice(0, 200)}`);
      }
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  await test('masonry-approver: exits 0 under 400ms', async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'approver-perf-'));
    try {
      const r = await runHook(hook('masonry-approver.js'),
        { tool_name: 'Write', cwd: tmpDir,
          tool_input: { file_path: path.join(tmpDir, 'x.js') } },
        {});
      assertUnderMs(r, 400);
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  // ─── masonry-subagent-tracker ────────────────────────────────────────────────

  await test('masonry-subagent-tracker: exits 0 for SubagentStart', async () => {
    const r = await runHook(hook('masonry-subagent-tracker.js'),
      { hook_event_name: 'SubagentStart', subagent_type: 'developer',
        agent_name: 'test-agent', session_id: 'sess-track-001' },
      {});
    assertExitCode(r, 0);
  });

  await test('masonry-subagent-tracker: completes under 500ms', async () => {
    const r = await runHook(hook('masonry-subagent-tracker.js'),
      { hook_event_name: 'SubagentStart', subagent_type: 'researcher',
        agent_name: 'test-agent-2', session_id: 'sess-track-002' },
      {});
    assertUnderMs(r, 500);
  });

  // ─── masonry-tool-failure ────────────────────────────────────────────────────

  await test('masonry-tool-failure: exits 0 (never blocks)', async () => {
    const r = await runHook(hook('masonry-tool-failure.js'),
      { tool_name: 'Bash', tool_response: 'Error: command not found: foobar',
        cwd: os.tmpdir() },
      {});
    assertExitCode(r, 0);
  });

  await test('masonry-tool-failure: emits retry guidance to stderr', async () => {
    const r = await runHook(hook('masonry-tool-failure.js'),
      { tool_name: 'Write', tool_response: 'Error: ENOENT: no such file or directory',
        cwd: os.tmpdir() },
      {});
    assertExitCode(r, 0);
    assertStderr(r, 'Masonry');
  });

  // ─── masonry-register ────────────────────────────────────────────────────────

  await test('masonry-register: exits 0 for UserPromptSubmit', async () => {
    const r = await runHook(hook('masonry-register.js'),
      { hook_event_name: 'UserPromptSubmit', session_id: 'reg-sess-001',
        prompt: 'how does the routing work', cwd: os.tmpdir() },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertExitCode(r, 0);
  });

  await test('masonry-register: completes under 2000ms', async () => {
    const r = await runHook(hook('masonry-register.js'),
      { hook_event_name: 'UserPromptSubmit', session_id: 'reg-sess-002',
        prompt: 'what is the architecture', cwd: os.tmpdir() },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertUnderMs(r, 2000);
  });

  // ─── masonry-mortar-enforcer ─────────────────────────────────────────────────

  await test('masonry-mortar-enforcer: approves "mortar" subagent from main session', async () => {
    const r = await runHook(hook('masonry-mortar-enforcer.js'),
      { tool_name: 'Agent', tool_input: { subagent_type: 'mortar', prompt: 'route this request' } },
      {});
    assertExitCode(r, 0);
    if (r.stdout && r.stdout.includes('block')) {
      throw new Error(`mortar subagent should be approved, got block: ${r.stdout.slice(0, 200)}`);
    }
  });

  await test('masonry-mortar-enforcer: blocks empty subagent_type', async () => {
    const r = await runHook(hook('masonry-mortar-enforcer.js'),
      { tool_name: 'Agent', tool_input: { subagent_type: '', prompt: 'do something' } },
      {});
    assertExitCode(r, 0);
    if (!r.stdout.includes('block')) {
      throw new Error(`empty subagent_type should be blocked, stdout: ${r.stdout.slice(0, 200)}`);
    }
  });

  await test('masonry-mortar-enforcer: passes through non-Agent tools', async () => {
    const r = await runHook(hook('masonry-mortar-enforcer.js'),
      { tool_name: 'Write', tool_input: { file_path: '/tmp/x.js' } },
      {});
    assertExitCode(r, 0);
  });

  // ─── masonry-dep-audit ───────────────────────────────────────────────────────

  await test('masonry-dep-audit: exits 0 for non-package.json file', async () => {
    const r = await runHook(hook('masonry-dep-audit.js'),
      { tool_name: 'Write', tool_input: { file_path: '/project/utils.py', content: 'x' } },
      {});
    assertExitCode(r, 0);
  });

  await test('masonry-dep-audit: exits 0 (never blocks, advisory only)', async () => {
    // Even for package.json, this hook only warns — never blocks
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'dep-audit-'));
    const pkgFile = path.join(tmpDir, 'package.json');
    fs.writeFileSync(pkgFile, JSON.stringify({ name: 'test', dependencies: {} }));
    try {
      const r = await runHook(hook('masonry-dep-audit.js'),
        { tool_name: 'Write', tool_input: { file_path: pkgFile, content: '{}' } },
        { timeoutMs: 15000 }); // npm audit can be slow
      assertExitCode(r, 0);
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  // ─── masonry-pre-protect ─────────────────────────────────────────────────────

  await test('masonry-pre-protect: allows write to non-protected file', async () => {
    const r = await runHook(hook('masonry-pre-protect.js'),
      { tool_name: 'Write', cwd: os.tmpdir(),
        tool_input: { file_path: path.join(os.tmpdir(), 'utils.py'), content: 'x' } },
      {});
    assertExitCode(r, 0);
  });

  await test('masonry-pre-protect: allows write to masonry-state.json when no lock exists', async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'preprotect-'));
    const stateFile = path.join(tmpDir, 'masonry-state.json');
    try {
      const r = await runHook(hook('masonry-pre-protect.js'),
        { tool_name: 'Write', cwd: tmpDir,
          tool_input: { file_path: stateFile, content: '{}' } },
        {});
      // No lock file exists → allowed
      assertExitCode(r, 0);
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  // ─── masonry-auto-pr ─────────────────────────────────────────────────────────

  await test('masonry-auto-pr: exits 0 when no .autopilot dir (skips silently)', async () => {
    const r = await runHook(hook('masonry-auto-pr.js'),
      { hook_event_name: 'SubagentStop', subagent_type: 'developer', cwd: os.tmpdir() },
      {});
    assertExitCode(r, 0);
  });

  // ─── masonry-build-outcome ───────────────────────────────────────────────────

  await test('masonry-build-outcome: exits 0 for non-progress.json write', async () => {
    const r = await runHook(hook('masonry-build-outcome.js'),
      { tool_name: 'Write', tool_input: { file_path: '/project/utils.py', content: 'x' } },
      {});
    assertExitCode(r, 0);
  });

  // ─── masonry-mistake-monitor ─────────────────────────────────────────────────

  await test('masonry-mistake-monitor: exits 0 for successful bash command', async () => {
    const r = await runHook(hook('masonry-mistake-monitor.js'),
      { tool_name: 'Bash', tool_input: { command: 'echo hello' }, tool_response: 'hello' },
      {});
    assertExitCode(r, 0);
  });

  await test('masonry-mistake-monitor: exits 0 for failed bash (logs, never blocks)', async () => {
    const r = await runHook(hook('masonry-mistake-monitor.js'),
      { tool_name: 'Bash', tool_input: { command: 'cat /nonexistent' },
        tool_response: 'cat: /nonexistent: No such file or directory\nExit code 1' },
      {});
    assertExitCode(r, 0);
  });

  // ─── masonry-pre-compact ─────────────────────────────────────────────────────

  await test('masonry-pre-compact: exits 0 for minimal input', async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'precompact-'));
    try {
      const r = await runHook(hook('masonry-pre-compact.js'),
        { cwd: tmpDir, messages: [] },
        { env: { RECALL_HOST: MOCK_RECALL } });
      assertExitCode(r, 0);
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  // ─── masonry-post-compact ────────────────────────────────────────────────────

  await test('masonry-post-compact: exits 0 with no snapshot files', async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'postcompact-'));
    try {
      const r = await runHook(hook('masonry-post-compact.js'),
        { cwd: tmpDir },
        {});
      assertExitCode(r, 0);
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  await test('masonry-post-compact: re-injects build state after compaction', async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'postcompact2-'));
    const apDir = path.join(tmpDir, '.autopilot');
    fs.mkdirSync(apDir, { recursive: true });
    fs.writeFileSync(path.join(apDir, 'compact-state.json'),
      JSON.stringify({ mode: 'build', project: 'test-project', done: 3, total: 5 }));
    try {
      const r = await runHook(hook('masonry-post-compact.js'),
        { cwd: tmpDir },
        {});
      assertExitCode(r, 0);
      if (!r.stdout.includes('RESUMED')) {
        throw new Error(`post-compact should emit RESUMED message, stdout: ${r.stdout.slice(0, 300)}`);
      }
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  // ─── masonry-session-start ───────────────────────────────────────────────────

  await test('masonry-session-start: exits 0 for clean session start', async () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sessstart-'));
    try {
      const r = await runHook(hook('masonry-session-start.js'),
        { session_id: 'new-sess-001', cwd: tmpDir },
        { env: { RECALL_HOST: MOCK_RECALL }, timeoutMs: 8000 });
      assertExitCode(r, 0);
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  // ─── masonry-hook-watch ──────────────────────────────────────────────────────

  await test('masonry-hook-watch: exits 0 for non-hook file (no smoke test triggered)', async () => {
    const r = await runHook(hook('masonry-hook-watch.js'),
      { tool_name: 'Write', tool_input: { file_path: '/project/utils.py', content: 'x' } },
      {});
    assertExitCode(r, 0);
  });

  // ─── masonry-post-write-runner ───────────────────────────────────────────────

  await test('masonry-post-write-runner: exits 0 (parallel runner)', async () => {
    const r = await runHook(hook('masonry-post-write-runner.js'),
      { tool_name: 'Write', tool_input: { file_path: '/tmp/test.py', content: 'x = 1\n' } },
      { env: { RECALL_HOST: MOCK_RECALL, OLLAMA_HOST: MOCK_OLLAMA }, timeoutMs: 35000 });
    assertExitCode(r, 0);
  });

  await test('PERF: masonry-post-write-runner completes under 32000ms (longest hook=30s)', async () => {
    const r = await runHook(hook('masonry-post-write-runner.js'),
      { tool_name: 'Write', tool_input: { file_path: '/tmp/perf.js', content: 'const x = 1;\n' } },
      { env: { RECALL_HOST: MOCK_RECALL, OLLAMA_HOST: MOCK_OLLAMA }, timeoutMs: 35000 });
    assertNotTimedOut(r);
    assertUnderMs(r, 32000);
  });
};
