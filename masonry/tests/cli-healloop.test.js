/**
 * masonry/tests/cli-healloop.test.js
 *
 * Tests for masonry/src/engine/cli/healloop.js
 *
 * Strategy: spawn the CLI as a child process and assert on stdout JSON.
 * Engine calls are controlled via environment variables:
 *   BRICKLAYER_HEAL_LOOP=1          — enable the loop (otherwise env_not_set)
 *   BRICKLAYER_TEST_RUNNER_VERDICT  — comma-separated verdicts returned by the
 *                                     stub runAgent on successive calls
 *
 * No real agent processes are spawned; no disk writes are required.
 */

import { describe, it, expect } from 'vitest';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CLI = path.resolve(__dirname, '../src/engine/cli/healloop.js');

const BASE_ENV = {
  ...process.env,
  // Prevent real Ollama / Recall calls from any transitive import
  OLLAMA_HOST: '127.0.0.1:19999',
  RECALL_HOST: 'http://127.0.0.1:19998',
};

/** Run the CLI and return parsed stdout JSON. Throws on non-zero exit. */
function run(args, env = {}) {
  const stdout = execFileSync(process.execPath, [CLI, ...args], {
    encoding: 'utf8',
    timeout: 15_000,
    env: { ...BASE_ENV, ...env },
  });
  return JSON.parse(stdout.trim());
}

/** Run the CLI and capture stdout + exit code even on failure. */
function runRaw(args, env = {}) {
  try {
    const stdout = execFileSync(process.execPath, [CLI, ...args], {
      encoding: 'utf8',
      timeout: 15_000,
      env: { ...BASE_ENV, ...env },
    });
    return { stdout: stdout.trim(), code: 0 };
  } catch (err) {
    return { stdout: (err.stdout || '').trim(), code: err.status ?? 1 };
  }
}

// ---------------------------------------------------------------------------
// Guard: BRICKLAYER_HEAL_LOOP not set
// ---------------------------------------------------------------------------

describe('healloop.js — env_not_set guard', () => {
  it('should output env_not_set and exit 0 when BRICKLAYER_HEAL_LOOP is absent', () => {
    const { stdout, code } = runRaw(
      ['--project-dir', '/tmp', '--question-id', 'q1', '--verdict', 'FAILURE'],
      { BRICKLAYER_HEAL_LOOP: undefined },
    );
    expect(code).toBe(0);
    const out = JSON.parse(stdout);
    expect(out).toEqual({ ran: false, reason: 'env_not_set' });
  });

  it('should output env_not_set when BRICKLAYER_HEAL_LOOP is "0"', () => {
    const out = run(
      ['--project-dir', '/tmp', '--question-id', 'q1', '--verdict', 'FAILURE'],
      { BRICKLAYER_HEAL_LOOP: '0' },
    );
    expect(out).toEqual({ ran: false, reason: 'env_not_set' });
  });
});

// ---------------------------------------------------------------------------
// Guard: verdict not applicable
// ---------------------------------------------------------------------------

describe('healloop.js — verdict_not_applicable guard', () => {
  const healEnv = { BRICKLAYER_HEAL_LOOP: '1' };

  it('should output verdict_not_applicable for HEALTHY', () => {
    const out = run(
      ['--project-dir', '/tmp', '--question-id', 'q1', '--verdict', 'HEALTHY'],
      healEnv,
    );
    expect(out).toEqual({ ran: false, reason: 'verdict_not_applicable' });
  });

  it('should output verdict_not_applicable for WARNING', () => {
    const out = run(
      ['--project-dir', '/tmp', '--question-id', 'q1', '--verdict', 'WARNING'],
      healEnv,
    );
    expect(out).toEqual({ ran: false, reason: 'verdict_not_applicable' });
  });

  it('should output verdict_not_applicable for FIXED', () => {
    const out = run(
      ['--project-dir', '/tmp', '--question-id', 'q1', '--verdict', 'FIXED'],
      healEnv,
    );
    expect(out).toEqual({ ran: false, reason: 'verdict_not_applicable' });
  });

  it('should exit 0 for verdict_not_applicable', () => {
    const { code } = runRaw(
      ['--project-dir', '/tmp', '--question-id', 'q1', '--verdict', 'HEALTHY'],
      healEnv,
    );
    expect(code).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Heal loop runs: FAILURE verdict
// ---------------------------------------------------------------------------

describe('healloop.js — FAILURE verdict triggers heal loop', () => {
  it('should output ran:true when verdict=FAILURE and env is set', () => {
    // Stub: diagnose → DIAGNOSIS_COMPLETE, fix → FIXED
    const out = run(
      ['--project-dir', '/tmp', '--question-id', 'q-fail-1', '--verdict', 'FAILURE', '--max-cycles', '1'],
      {
        BRICKLAYER_HEAL_LOOP: '1',
        BRICKLAYER_TEST_RUNNER_VERDICT: 'DIAGNOSIS_COMPLETE,FIXED',
      },
    );
    expect(out.ran).toBe(true);
    expect(typeof out.cycles).toBe('number');
    expect(out.final_verdict).toBeDefined();
  });

  it('should report FIXED when stub returns DIAGNOSIS_COMPLETE then FIXED', () => {
    const out = run(
      ['--project-dir', '/tmp', '--question-id', 'q-fix-1', '--verdict', 'FAILURE', '--max-cycles', '2'],
      {
        BRICKLAYER_HEAL_LOOP: '1',
        BRICKLAYER_TEST_RUNNER_VERDICT: 'DIAGNOSIS_COMPLETE,FIXED',
      },
    );
    expect(out.ran).toBe(true);
    expect(out.final_verdict).toBe('FIXED');
  });

  it('should exhaust cycles when stub always returns FIX_FAILED', () => {
    // diagnose→DIAGNOSIS_COMPLETE, fix→FIX_FAILED (loops back to FAILURE)
    // With max-cycles=2 it will exhaust
    const out = run(
      ['--project-dir', '/tmp', '--question-id', 'q-exhaust-1', '--verdict', 'FAILURE', '--max-cycles', '2'],
      {
        BRICKLAYER_HEAL_LOOP: '1',
        // cycle1: diag→DIAGNOSIS_COMPLETE, fix→FIX_FAILED
        // cycle2: diag→DIAGNOSIS_COMPLETE, fix→FIX_FAILED → exhausted
        BRICKLAYER_TEST_RUNNER_VERDICT: 'DIAGNOSIS_COMPLETE,FIX_FAILED,DIAGNOSIS_COMPLETE,FIX_FAILED',
      },
    );
    expect(out.ran).toBe(true);
    // The engine sets HEAL_EXHAUSTED after exhausting cycles
    expect(['HEAL_EXHAUSTED', 'FIX_FAILED', 'FAILURE']).toContain(out.final_verdict);
  });

  it('should exit 0 even when loop exhausts', () => {
    const { code } = runRaw(
      ['--project-dir', '/tmp', '--question-id', 'q-exhaust-2', '--verdict', 'FAILURE', '--max-cycles', '1'],
      {
        BRICKLAYER_HEAL_LOOP: '1',
        BRICKLAYER_TEST_RUNNER_VERDICT: 'DIAGNOSIS_COMPLETE,FIX_FAILED',
      },
    );
    expect(code).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Heal loop runs: DIAGNOSIS_COMPLETE verdict
// ---------------------------------------------------------------------------

describe('healloop.js — DIAGNOSIS_COMPLETE verdict triggers heal loop', () => {
  it('should output ran:true when verdict=DIAGNOSIS_COMPLETE and env is set', () => {
    const out = run(
      ['--project-dir', '/tmp', '--question-id', 'q-diag-1', '--verdict', 'DIAGNOSIS_COMPLETE', '--max-cycles', '1'],
      {
        BRICKLAYER_HEAL_LOOP: '1',
        BRICKLAYER_TEST_RUNNER_VERDICT: 'FIXED',
      },
    );
    expect(out.ran).toBe(true);
    expect(out.final_verdict).toBe('FIXED');
  });

  it('should skip the diagnose phase and go straight to fix when starting at DIAGNOSIS_COMPLETE', () => {
    // Only one agent call should happen (fix-implementer only, no diagnose)
    const out = run(
      ['--project-dir', '/tmp', '--question-id', 'q-diag-2', '--verdict', 'DIAGNOSIS_COMPLETE', '--max-cycles', '1'],
      {
        BRICKLAYER_HEAL_LOOP: '1',
        BRICKLAYER_TEST_RUNNER_VERDICT: 'FIXED',
      },
    );
    expect(out.ran).toBe(true);
    expect(out.final_verdict).toBe('FIXED');
    // cycles should be 1 (one fix call = ceil(1/2) = 1)
    expect(out.cycles).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// Output shape contract
// ---------------------------------------------------------------------------

describe('healloop.js — output shape', () => {
  it('stdout must be valid single-line JSON for env_not_set', () => {
    const { stdout } = runRaw(
      ['--project-dir', '/tmp', '--question-id', 'q1', '--verdict', 'FAILURE'],
      { BRICKLAYER_HEAL_LOOP: undefined },
    );
    expect(() => JSON.parse(stdout)).not.toThrow();
    expect(stdout.split('\n').filter(Boolean)).toHaveLength(1);
  });

  it('stdout must be valid single-line JSON for verdict_not_applicable', () => {
    const { stdout } = runRaw(
      ['--project-dir', '/tmp', '--question-id', 'q1', '--verdict', 'HEALTHY'],
      { BRICKLAYER_HEAL_LOOP: '1' },
    );
    expect(() => JSON.parse(stdout)).not.toThrow();
    expect(stdout.split('\n').filter(Boolean)).toHaveLength(1);
  });

  it('stdout must be valid single-line JSON when loop runs', () => {
    const { stdout } = runRaw(
      ['--project-dir', '/tmp', '--question-id', 'q1', '--verdict', 'FAILURE', '--max-cycles', '1'],
      {
        BRICKLAYER_HEAL_LOOP: '1',
        BRICKLAYER_TEST_RUNNER_VERDICT: 'DIAGNOSIS_COMPLETE,FIXED',
      },
    );
    expect(() => JSON.parse(stdout)).not.toThrow();
    expect(stdout.split('\n').filter(Boolean)).toHaveLength(1);
  });

  it('ran:true result must include cycles (number) and final_verdict (string)', () => {
    const out = run(
      ['--project-dir', '/tmp', '--question-id', 'q1', '--verdict', 'FAILURE', '--max-cycles', '1'],
      {
        BRICKLAYER_HEAL_LOOP: '1',
        BRICKLAYER_TEST_RUNNER_VERDICT: 'DIAGNOSIS_COMPLETE,FIXED',
      },
    );
    expect(out).toHaveProperty('ran', true);
    expect(out).toHaveProperty('cycles');
    expect(typeof out.cycles).toBe('number');
    expect(out).toHaveProperty('final_verdict');
    expect(typeof out.final_verdict).toBe('string');
  });
});

// ---------------------------------------------------------------------------
// --max-cycles respected
// ---------------------------------------------------------------------------

describe('healloop.js — --max-cycles argument', () => {
  it('should respect --max-cycles 1 and exhaust after one cycle with FIX_FAILED', () => {
    const out = run(
      ['--project-dir', '/tmp', '--question-id', 'q-mc-1', '--verdict', 'FAILURE', '--max-cycles', '1'],
      {
        BRICKLAYER_HEAL_LOOP: '1',
        BRICKLAYER_TEST_RUNNER_VERDICT: 'DIAGNOSIS_COMPLETE,FIX_FAILED',
      },
    );
    expect(out.ran).toBe(true);
    // Only one cycle was allowed, so it must have exhausted or returned FIX_FAILED state
    expect(['HEAL_EXHAUSTED', 'FIX_FAILED', 'FAILURE']).toContain(out.final_verdict);
  });
});
