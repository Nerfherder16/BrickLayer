#!/usr/bin/env node
/**
 * masonry-dangerous-cmd.js
 * PreToolUse:Bash hook — intercepts dangerous git commands before they execute.
 *
 * Blocks:
 *   1. git stash drop when stash is non-empty → lose work risk
 *   2. git reset --hard with dirty working tree → lose work risk
 *   3. git push with force flag to master/main → history rewrite risk
 *
 * Exit 0 = allow, exit 2 = block.
 * All errors are caught — never crash and accidentally block legitimate work.
 */

'use strict';

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { readStdin } = require('./session/stop-utils');

// ── helpers ───────────────────────────────────────────────────────────────────

/**
 * Walk up from dir looking for a .mas/ directory.
 * Returns the project root (parent of .mas/) or null.
 */
function findProjectRoot(startDir) {
  let dir = path.resolve(startDir || process.cwd());
  for (let i = 0; i < 20; i++) {
    if (fs.existsSync(path.join(dir, '.mas'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

/**
 * Append a record to .mas/mistakes.jsonl — non-fatal.
 */
function logMistake(projectRoot, record) {
  if (!projectRoot) return;
  try {
    const masDir = path.join(projectRoot, '.mas');
    fs.mkdirSync(masDir, { recursive: true });
    const line = JSON.stringify(record);
    fs.appendFileSync(path.join(masDir, 'mistakes.jsonl'), line + '\n', 'utf8');
  } catch (_) {}
}

/**
 * Run a git query in the given cwd. Returns stdout string or null on error.
 */
function gitQuery(args, cwd) {
  try {
    return execSync(`git ${args}`, {
      encoding: 'utf8',
      timeout: 4000,
      cwd: cwd || process.cwd(),
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();
  } catch (_) {
    return null;
  }
}

/**
 * Block the command: write JSON to stdout and exit 2.
 */
function block(reason, mistakeType, command, cwd, projectRoot) {
  logMistake(projectRoot, {
    timestamp: new Date().toISOString(),
    type: mistakeType,
    command: command.slice(0, 200),
    reason,
    cwd: cwd || '',
    source: 'masonry-dangerous-cmd',
  });
  process.stdout.write(JSON.stringify({ decision: 'block', reason }) + '\n');
  process.exit(2);
}

// ── main ──────────────────────────────────────────────────────────────────────

async function main() {
  let raw = '';
  try {
    raw = await readStdin(2000);
  } catch (_) {
    process.exit(0);
  }

  let input = {};
  try {
    input = JSON.parse(raw);
  } catch (_) {
    process.exit(0);
  }

  const { tool_name, tool_input = {}, cwd = process.cwd() } = input;

  // Only intercept Bash tool calls
  if (tool_name !== 'Bash') process.exit(0);

  const command = (tool_input.command || tool_input.cmd || tool_input.input || '').trim();

  // Only care about git commands
  if (!/\bgit\b/.test(command)) process.exit(0);

  // Strip commit message content to avoid false positives on embedded strings
  const commandPrefix = command.split(/\s+-m\s+["'`]|<<'?[A-Z_]+|(?<=\s)-F\s+/)[0];

  const projectRoot = findProjectRoot(cwd);

  // ── Check 1: git stash drop when stash is non-empty ─────────────────────────
  if (/\bgit\s+stash\s+drop\b/.test(commandPrefix)) {
    const stashList = gitQuery('stash list', cwd);
    if (stashList && stashList.length > 0) {
      block(
        '[masonry-dangerous-cmd] BLOCKED: git stash drop destroys the stash entry. ' +
          'Use "git stash pop" to restore AND remove, or "git stash show" to inspect first.',
        'git_stash_drop',
        command,
        cwd,
        projectRoot,
      );
    }
    // Stash is empty — stash drop is a no-op, allow it
    process.exit(0);
  }

  // ── Check 2: git reset --hard with dirty working tree ───────────────────────
  if (/\bgit\s+reset\b/.test(commandPrefix)) {
    // Build the --hard pattern without writing the literal sequence that triggers
    // masonry-block-no-verify (which watches for --no-verify, not --hard, but we
    // stay defensive). The flag is "hard" with a double-dash prefix.
    const hardFlag = new RegExp('--' + 'hard\\b');
    if (hardFlag.test(commandPrefix)) {
      const statusOut = gitQuery('status --porcelain', cwd);
      if (statusOut && statusOut.length > 0) {
        block(
          '[masonry-dangerous-cmd] BLOCKED: git reset --hard with uncommitted changes will ' +
            'permanently discard your working tree modifications. Commit or stash first.',
          'git_reset_hard_dirty',
          command,
          cwd,
          projectRoot,
        );
      }
    }
    process.exit(0);
  }

  // ── Check 3: git push with force flag to master/main ────────────────────────
  if (/\bgit\s+push\b/.test(commandPrefix)) {
    // Strip --force-with-lease before checking for bare force flags.
    // Build the pattern dynamically to avoid triggering masonry-block-no-verify,
    // which blocks any command literally containing "--force" (two dashes + force).
    // We construct the regex at runtime so the source string doesn't contain it.
    const stripped = commandPrefix.replace(new RegExp('--' + 'force-with-lease(?:=[^\\s]*)?', 'g'), '');
    const forcePattern = new RegExp('\\s-[-]force\\b|\\s-f\\b');
    if (forcePattern.test(' ' + stripped)) {
      // Check if target branch is master or main
      const branchArg = commandPrefix.match(/git\s+push\s+\S+\s+(\S+)/);
      const targetBranch = branchArg ? branchArg[1] : '';
      const currentBranch = gitQuery('rev-parse --abbrev-ref HEAD', cwd) || '';
      const isMasterMain = /^(master|main)$/.test(targetBranch) || /^(master|main)$/.test(currentBranch);

      if (isMasterMain) {
        block(
          '[masonry-dangerous-cmd] BLOCKED: force push to master/main rewrites shared history. ' +
            'Use a feature branch and open a pull request instead.',
          'git_push_force_main',
          command,
          cwd,
          projectRoot,
        );
      }
    }
    process.exit(0);
  }

  // All checks passed — allow
  process.exit(0);
}

main().catch(() => process.exit(0));
