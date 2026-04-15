/**
 * hook-benchmark-cases.js — All hook test cases.
 * Exported as an async function that receives the shared context from hook-benchmark.js.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

module.exports = async function runCases(ctx) {
  const {
    mock, MOCK_RECALL, MOCK_OLLAMA,
    hook, rhook, runHook, test,
    assertExitCode, assertStderr, assertNoStderr,
    assertCalledPath, assertNotCalledPath,
    assertUnderMs, assertNotTimedOut,
    saveGate, setGate, restoreGate, makeBigJs,
  } = ctx;

  // ── recall-retrieve ──────────────────────────────────────────────────────────
  // Hook calls /search/browse (not /retrieve). Needs substantive prompt to pass
  // the internal shouldSkip() guard. Include session_id to activate all paths.

  await test('recall-retrieve: calls /search/browse for substantive prompt', async () => {
    mock.clear();
    const r = await runHook(rhook('recall-retrieve.js'),
      { hook_event_name: 'UserPromptSubmit', session_id: 'test-session-123',
        prompt: 'how does the masonry routing pipeline classify incoming prompts into agent lanes' },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertExitCode(r, 0);
    assertCalledPath(mock.requests, '/search/browse');
  });

  await test('recall-retrieve: skips when recall_degraded file present', async () => {
    mock.clear();
    const tmpCwd = fs.mkdtempSync(path.join(os.tmpdir(), 'recall-test-'));
    fs.mkdirSync(path.join(tmpCwd, '.mas'), { recursive: true });
    fs.writeFileSync(path.join(tmpCwd, '.mas', 'recall_degraded'), '');
    try {
      const r = await runHook(rhook('recall-retrieve.js'),
        { hook_event_name: 'UserPromptSubmit', session_id: 'test-session-456',
          cwd: tmpCwd, prompt: 'how does the routing pipeline work in masonry hooks system' },
        { env: { RECALL_HOST: MOCK_RECALL } });
      assertExitCode(r, 0);
      assertNotCalledPath(mock.requests, '/search/browse');
    } finally {
      fs.rmSync(tmpCwd, { recursive: true, force: true });
    }
  });

  await test('recall-retrieve: completes under 1500ms with mock backend', async () => {
    const r = await runHook(rhook('recall-retrieve.js'),
      { hook_event_name: 'UserPromptSubmit', session_id: 'test-session-789',
        prompt: 'how does the masonry routing pipeline classify incoming prompts' },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertExitCode(r, 0);
    assertUnderMs(r, 1500);
  });

  // ── observe-edit ─────────────────────────────────────────────────────────────

  await test('observe-edit: sends /observe/file-change for .js Write', async () => {
    mock.clear();
    const r = await runHook(rhook('observe-edit.js'),
      { tool_name: 'Write', tool_input: { file_path: '/home/user/project/utils.js', content: 'const x = 1;' } },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertExitCode(r, 0);
    await new Promise(res => setTimeout(res, 200));
    assertCalledPath(mock.requests, '/observe/file-change');
  });

  await test('observe-edit: skips binary files (.png)', async () => {
    mock.clear();
    const r = await runHook(rhook('observe-edit.js'),
      { tool_name: 'Write', tool_input: { file_path: '/home/user/project/logo.png', content: 'binary' } },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertExitCode(r, 0);
    await new Promise(res => setTimeout(res, 200));
    assertNotCalledPath(mock.requests, '/observe/file-change');
  });

  await test('observe-edit: skips node_modules paths', async () => {
    mock.clear();
    const r = await runHook(rhook('observe-edit.js'),
      { tool_name: 'Write', tool_input: { file_path: '/project/node_modules/lodash/index.js', content: 'x' } },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertExitCode(r, 0);
    await new Promise(res => setTimeout(res, 200));
    assertNotCalledPath(mock.requests, '/observe/file-change');
  });

  await test('observe-edit: exits under 500ms (fire-and-forget)', async () => {
    const r = await runHook(rhook('observe-edit.js'),
      { tool_name: 'Write', tool_input: { file_path: '/project/utils.js', content: 'x' } },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertExitCode(r, 0);
    assertUnderMs(r, 500);
  });

  // ── session-save ─────────────────────────────────────────────────────────────

  await test('session-save: sends /observe/session-snapshot', async () => {
    mock.clear();
    const r = await runHook(rhook('session-save.js'),
      { session_id: 'sess-abc123', stop_hook_active: false },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertExitCode(r, 0);
    assertCalledPath(mock.requests, '/observe/session-snapshot');
  });

  await test('session-save: skips when stop_hook_active=true', async () => {
    mock.clear();
    const r = await runHook(rhook('session-save.js'),
      { session_id: 'sess-abc123', stop_hook_active: true },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertExitCode(r, 0);
    assertNotCalledPath(mock.requests, '/observe/session-snapshot');
  });

  await test('session-save: completes under 500ms with mock backend', async () => {
    const r = await runHook(rhook('session-save.js'),
      { session_id: 'sess-abc123', stop_hook_active: false },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertExitCode(r, 0);
    assertUnderMs(r, 500);
  });

  // ── masonry-prompt-inject ────────────────────────────────────────────────────

  await test('masonry-prompt-inject: exits 0 for valid prompt', async () => {
    const r = await runHook(hook('masonry-prompt-inject.js'),
      { hook_event_name: 'UserPromptSubmit', prompt: 'how do I configure the router' },
      { env: { RECALL_HOST: MOCK_RECALL, OLLAMA_HOST: MOCK_OLLAMA } });
    assertExitCode(r, 0);
  });

  await test('masonry-prompt-inject: exits 0 for empty prompt', async () => {
    const r = await runHook(hook('masonry-prompt-inject.js'),
      { hook_event_name: 'UserPromptSubmit', prompt: '' },
      { env: { RECALL_HOST: MOCK_RECALL, OLLAMA_HOST: MOCK_OLLAMA } });
    assertExitCode(r, 0);
  });

  // ── masonry-prompt-router ────────────────────────────────────────────────────

  await test('masonry-prompt-router: exits 0 for any prompt', async () => {
    const r = await runHook(hook('masonry-prompt-router.js'),
      { hook_event_name: 'UserPromptSubmit', prompt: 'implement the login endpoint using FastAPI' },
      { env: { OLLAMA_HOST: MOCK_OLLAMA } });
    assertExitCode(r, 0);
  });

  await test('masonry-prompt-router: completes under 300ms for short prompts', async () => {
    const r = await runHook(hook('masonry-prompt-router.js'),
      { hook_event_name: 'UserPromptSubmit', prompt: 'what is 2+2' },
      { env: { OLLAMA_HOST: MOCK_OLLAMA } });
    assertExitCode(r, 0);
    assertUnderMs(r, 300);
  });

  // ── masonry-jcodemunch-nudge ─────────────────────────────────────────────────

  await test('masonry-jcodemunch-nudge: BLOCKS large source file (>20KB)', async () => {
    const jsFile = path.join(os.tmpdir(), `nudge-big-${Date.now()}.js`);
    fs.writeFileSync(jsFile, makeBigJs(22000));
    try {
      const r = await runHook(hook('masonry-jcodemunch-nudge.js'),
        { tool_name: 'Read', tool_input: { file_path: jsFile } }, {});
      assertExitCode(r, 2);
      assertStderr(r, 'BLOCKED');
    } finally {
      try { fs.unlinkSync(jsFile); } catch {}
    }
  });

  await test('masonry-jcodemunch-nudge: NUDGES medium source file (3-20KB)', async () => {
    const jsFile = path.join(os.tmpdir(), `nudge-med-${Date.now()}.js`);
    fs.writeFileSync(jsFile, makeBigJs(4500));
    try {
      const r = await runHook(hook('masonry-jcodemunch-nudge.js'),
        { tool_name: 'Read', tool_input: { file_path: jsFile } }, {});
      assertExitCode(r, 0);
      assertStderr(r, 'jcodemunch');
    } finally {
      try { fs.unlinkSync(jsFile); } catch {}
    }
  });

  await test('masonry-jcodemunch-nudge: silent for small source file (<3KB)', async () => {
    const jsFile = path.join(os.tmpdir(), `nudge-small-${Date.now()}.js`);
    fs.writeFileSync(jsFile, 'const x = 1;\n'.repeat(10));
    try {
      const r = await runHook(hook('masonry-jcodemunch-nudge.js'),
        { tool_name: 'Read', tool_input: { file_path: jsFile } }, {});
      assertExitCode(r, 0);
      assertNoStderr(r, 'jcodemunch');
    } finally {
      try { fs.unlinkSync(jsFile); } catch {}
    }
  });

  await test('masonry-jcodemunch-nudge: silent for non-code files (.md)', async () => {
    const mdFile = path.join(os.tmpdir(), `nudge-doc-${Date.now()}.md`);
    fs.writeFileSync(mdFile, makeBigJs(9000).replace(/x/g, '#'));
    try {
      const r = await runHook(hook('masonry-jcodemunch-nudge.js'),
        { tool_name: 'Read', tool_input: { file_path: mdFile } }, {});
      assertExitCode(r, 0);
      assertNoStderr(r, 'jcodemunch');
    } finally {
      try { fs.unlinkSync(mdFile); } catch {}
    }
  });

  // ── masonry-content-guard ────────────────────────────────────────────────────
  // AWS key built at runtime — literal must not appear in source.

  await test('masonry-content-guard: blocks AWS access key pattern', async () => {
    const fakeKey = ['AKIA', 'IOSFODNN7EXAMPLE'].join('');
    const r = await runHook(hook('masonry-content-guard.js'),
      { tool_name: 'Write',
        tool_input: { file_path: '/project/config.js', content: `const key = "${fakeKey}";` } },
      {});
    assertExitCode(r, 2);
    assertStderr(r, 'AWS');
  });

  await test('masonry-content-guard: allows clean write', async () => {
    const r = await runHook(hook('masonry-content-guard.js'),
      { tool_name: 'Write',
        tool_input: { file_path: '/project/utils.js', content: 'function add(a, b) { return a + b; }' } },
      {});
    assertExitCode(r, 0);
  });

  // ── masonry-block-no-verify ──────────────────────────────────────────────────

  await test('masonry-block-no-verify: blocks --no-verify in Bash', async () => {
    const r = await runHook(hook('masonry-block-no-verify.js'),
      { tool_name: 'Bash', tool_input: { command: 'git commit --no-verify -m "skip hooks"' } },
      {});
    assertExitCode(r, 2);
  });

  await test('masonry-block-no-verify: allows normal git commit', async () => {
    const r = await runHook(hook('masonry-block-no-verify.js'),
      { tool_name: 'Bash', tool_input: { command: 'git commit -m "feat: add feature"' } },
      {});
    assertExitCode(r, 0);
  });

  // ── masonry-file-size-guard ──────────────────────────────────────────────────

  await test('masonry-file-size-guard: warns on 450-line file (no hard-block)', async () => {
    const f = path.join(os.tmpdir(), `sz-warn-${Date.now()}.py`);
    const content = 'x = 1\n'.repeat(450);
    fs.writeFileSync(f, content);
    try {
      const r = await runHook(hook('masonry-file-size-guard.js'),
        { tool_name: 'Write', tool_input: { file_path: f, content } }, {});
      if (r.exitCode === 2) {
        throw new Error('hard-blocked at 450 lines — should only warn');
      }
    } finally {
      try { fs.unlinkSync(f); } catch {}
    }
  });

  await test('masonry-file-size-guard: allows small file', async () => {
    const r = await runHook(hook('masonry-file-size-guard.js'),
      { tool_name: 'Write',
        tool_input: { file_path: '/project/utils.py', content: 'def add(a, b):\n    return a + b\n' } },
      {});
    assertExitCode(r, 0);
  });

  // ── masonry-routing-gate ─────────────────────────────────────────────────────
  // Hook reads /tmp/masonry-mortar-gate.json (hardcoded path). Save + restore.

  await test('masonry-routing-gate: allows write when mortar_consulted=true', async () => {
    const saved = saveGate();
    setGate(true);
    try {
      const r = await runHook(hook('masonry-routing-gate.js'),
        { tool_name: 'Write', tool_input: { file_path: '/tmp/test-out.js' }, cwd: '/tmp' }, {});
      assertExitCode(r, 0);
    } finally {
      restoreGate(saved);
    }
  });

  await test('masonry-routing-gate: blocks non-exempt write when mortar_consulted=false', async () => {
    const saved = saveGate();
    setGate(false);
    try {
      const r = await runHook(hook('masonry-routing-gate.js'),
        { tool_name: 'Write',
          tool_input: { file_path: '/home/user/project/src/app.js' },
          cwd: '/home/user/project' },
        {});
      assertExitCode(r, 2);
    } finally {
      restoreGate(saved);
    }
  });

  // ── masonry-stop-runner ──────────────────────────────────────────────────────
  // Runs 10 background hooks in parallel; slowest internal timeout is 3000ms.
  // Passes mock env so HTTP-calling hooks get fast responses.

  await test('masonry-stop-runner: completes under 3500ms', async () => {
    const r = await runHook(hook('masonry-stop-runner.js'),
      { session_id: 'sess-test', stop_hook_active: false },
      { env: { RECALL_HOST: MOCK_RECALL, OLLAMA_HOST: MOCK_OLLAMA }, timeoutMs: 10000 });
    assertNotTimedOut(r);
    assertUnderMs(r, 3500);
  });

  await test('masonry-stop-runner: exits 0 (never blocks stop)', async () => {
    const r = await runHook(hook('masonry-stop-runner.js'),
      { session_id: 'sess-test', stop_hook_active: false },
      { env: { RECALL_HOST: MOCK_RECALL, OLLAMA_HOST: MOCK_OLLAMA }, timeoutMs: 10000 });
    assertExitCode(r, 0);
  });

  // ── masonry-stop-checker ─────────────────────────────────────────────────────

  await test('masonry-stop-checker: completes under 1000ms', async () => {
    const r = await runHook(hook('masonry-stop-checker.js'),
      { session_id: 'sess-test', stop_hook_active: false },
      { env: { RECALL_HOST: MOCK_RECALL }, timeoutMs: 10000 });
    assertNotTimedOut(r);
    assertUnderMs(r, 1000);
  });

  // ── Performance regression guards ────────────────────────────────────────────

  await test('PERF: recall-retrieve <1500ms (was hanging at 3s timeout)', async () => {
    const r = await runHook(rhook('recall-retrieve.js'),
      { hook_event_name: 'UserPromptSubmit', session_id: 'perf-test',
        prompt: 'how does the masonry routing pipeline classify incoming prompts' },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertUnderMs(r, 1500);
  });

  await test('PERF: observe-edit <500ms (was 1039ms broken readStdin)', async () => {
    const r = await runHook(rhook('observe-edit.js'),
      { tool_name: 'Write', tool_input: { file_path: '/project/x.js', content: 'x' } },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertUnderMs(r, 500);
  });

  await test('PERF: session-save <500ms (was 2035ms broken readStdin)', async () => {
    const r = await runHook(rhook('session-save.js'),
      { session_id: 'sess-perf', stop_hook_active: false },
      { env: { RECALL_HOST: MOCK_RECALL } });
    assertUnderMs(r, 500);
  });

  await test('PERF: masonry-jcodemunch-nudge <200ms', async () => {
    const jsFile = path.join(os.tmpdir(), `perf-nudge-${Date.now()}.js`);
    fs.writeFileSync(jsFile, 'const x = 1;\n');
    try {
      const r = await runHook(hook('masonry-jcodemunch-nudge.js'),
        { tool_name: 'Read', tool_input: { file_path: jsFile } }, {});
      assertUnderMs(r, 200);
    } finally {
      try { fs.unlinkSync(jsFile); } catch {}
    }
  });
};
