#!/usr/bin/env node
/**
 * healloop.js
 * CLI wrapper for the BrickLayer self-healing loop state machine.
 *
 * Usage:
 *   node masonry/src/engine/cli/healloop.js \
 *     --project-dir <path> \
 *     --question-id <id> \
 *     --verdict <V> \
 *     [--max-cycles <N>]
 *
 * stdout: single-line JSON only (never mixed with other output).
 * stderr: diagnostic/progress messages.
 *
 * Exit codes:
 *   0 — always (including skipped / env_not_set)
 *   1 — unexpected crash only
 */

import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);

// ---------------------------------------------------------------------------
// Arg parsing
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  const args = { projectDir: null, questionId: null, verdict: null, maxCycles: 3 };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--project-dir' && argv[i + 1]) {
      args.projectDir = argv[++i];
    } else if (argv[i] === '--question-id' && argv[i + 1]) {
      args.questionId = argv[++i];
    } else if (argv[i] === '--verdict' && argv[i + 1]) {
      args.verdict = argv[++i];
    } else if (argv[i] === '--max-cycles' && argv[i + 1]) {
      const n = parseInt(argv[++i], 10);
      if (!isNaN(n) && n > 0) args.maxCycles = n;
    }
  }
  return args;
}

// ---------------------------------------------------------------------------
// runAgent factory
//
// In production: would delegate to a real agent runner subprocess.
// In tests:      BRICKLAYER_TEST_RUNNER_VERDICT controls the returned verdict
//                so the engine state machine can be exercised without spawning
//                real agent processes.
// ---------------------------------------------------------------------------

function makeRunAgent(projectDir) {
  const testVerdict = process.env.BRICKLAYER_TEST_RUNNER_VERDICT;

  if (testVerdict) {
    // Test stub — each call cycles through comma-separated verdicts.
    const verdicts = testVerdict.split(',').map((v) => v.trim());
    let callIndex = 0;
    return function stubRunAgent(question) {
      const verdict = verdicts[Math.min(callIndex, verdicts.length - 1)];
      callIndex++;
      process.stderr.write(`[healloop-cli] stub runAgent call ${callIndex} → ${verdict} (q=${question.id})\n`);
      return { verdict, summary: `stub result for ${question.id}`, details: '', data: {}, confidence: 'medium' };
    };
  }

  // Production: invoke Python BL runner via subprocess.
  // This path is not exercised in unit tests; real agent spawning
  // happens through bl/tmux or the Python runner layer.
  return function prodRunAgent(question) {
    process.stderr.write(`[healloop-cli] WARN: no runner configured for ${question.id}\n`);
    return { verdict: 'HEAL_EXHAUSTED', summary: 'no runner configured in healloop CLI' };
  };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function out(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  // Guard: env flag
  if (process.env.BRICKLAYER_HEAL_LOOP !== '1') {
    out({ ran: false, reason: 'env_not_set' });
    process.exit(0);
  }

  // Guard: verdict applicability
  const verdict = (args.verdict || '').toUpperCase();
  if (verdict !== 'FAILURE' && verdict !== 'DIAGNOSIS_COMPLETE') {
    out({ ran: false, reason: 'verdict_not_applicable' });
    process.exit(0);
  }

  // Load the engine. We require it lazily (after guards) so the module-level
  // side effects in config.js / findings.js don't fire on skip paths.
  let runHealLoop;
  try {
    const enginePath = path.resolve(__dirname, '..', 'healloop.js');
    ({ runHealLoop } = require(enginePath));
  } catch (err) {
    out({ error: `failed to load healloop engine: ${err.message}` });
    process.exit(1);
  }

  const questionId = args.questionId || 'unknown';
  const projectDir = args.projectDir || process.cwd();

  // Minimal synthetic question object — enough for the engine state machine
  // and writeFinding (which requires hypothesis, target, verdict_threshold).
  const syntheticQuestion = {
    id: questionId,
    title: `CLI heal loop for ${questionId}`,
    hypothesis: `Auto-heal triggered for ${questionId}`,
    target: projectDir,
    verdict_threshold: 'FIXED',
    question_type: 'behavioral',
    mode: 'agent',
    operational_mode: 'diagnose',
    session_context: '',
  };

  // Initial result seeded from the CLI verdict argument.
  const initialResult = {
    verdict,
    summary: `Initial verdict from CLI: ${verdict}`,
  };

  // Finding path — engine appends heal-cycle notes here.
  // If the file doesn't exist the engine catches the error silently.
  const findingPath = path.join(projectDir, 'findings', `${questionId}.md`);

  const runAgent = makeRunAgent(projectDir);

  // Override max_cycles via CLI arg (the engine also reads the env var, but
  // the CLI arg takes precedence for explicit invocations from Python).
  const savedEnv = process.env.BRICKLAYER_HEAL_MAX_CYCLES;
  process.env.BRICKLAYER_HEAL_MAX_CYCLES = String(args.maxCycles);

  let finalResult;
  let cycleCount = 0;

  try {
    // Wrap runAgent to count actual cycles.
    let agentCallPairs = 0;
    const countingRunAgent = function (question) {
      const result = runAgent(question);
      // Each diagnose+fix pair = 1 cycle. Count agent calls / 2 (rounded up).
      agentCallPairs++;
      cycleCount = Math.ceil(agentCallPairs / 2);
      return result;
    };

    finalResult = runHealLoop(syntheticQuestion, initialResult, findingPath, countingRunAgent);
  } catch (err) {
    out({ error: `heal loop threw: ${err.message}` });
    process.exit(1);
  } finally {
    // Restore env
    if (savedEnv === undefined) {
      delete process.env.BRICKLAYER_HEAL_MAX_CYCLES;
    } else {
      process.env.BRICKLAYER_HEAL_MAX_CYCLES = savedEnv;
    }
  }

  const finalVerdict = finalResult?.verdict || 'HEAL_EXHAUSTED';
  out({ ran: true, cycles: cycleCount, final_verdict: finalVerdict });
  process.exit(0);
}

try {
  main();
} catch (err) {
  process.stdout.write(JSON.stringify({ error: err.message }) + '\n');
  process.exit(1);
}
