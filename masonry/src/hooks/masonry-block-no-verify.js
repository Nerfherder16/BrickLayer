#!/usr/bin/env node
/**
 * masonry-block-no-verify.js
 * PreToolUse hook — blocks git commands that bypass safety checks:
 *   1. git commit --no-verify / git commit -n
 *   2. git push --force / git push -f  (--force-with-lease is allowed)
 */

// Read hook input from stdin
let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    const { tool_name, tool_input } = hookData;

    // Only inspect Bash tool calls
    if (tool_name !== 'Bash') {
      process.exit(0);
    }

    const command = (tool_input && (tool_input.command || tool_input.cmd || tool_input.input)) || '';

    // Only care about git commands
    if (!/\bgit\b/.test(command)) {
      process.exit(0);
    }

    // Strip commit message content to avoid false positives on -m "...git push --force..."
    // Split at the first -m flag, heredoc delimiter, or -F flag and only inspect the prefix.
    const commandPrefix = command.split(/\s+-m\s+["'`]|<<'?[A-Z_]+|(?<=\s)-F\s+/)[0];

    // Block: git commit --no-verify or git commit -n
    if (/\bgit\s+commit\b/.test(commandPrefix)) {
      if (/--no-verify/.test(commandPrefix) || /\s-n\b/.test(commandPrefix)) {
        const reason =
          '[masonry-block-no-verify] BLOCKED: --no-verify bypasses safety hooks. ' +
          'Fix the underlying issue instead.';
        process.stdout.write(JSON.stringify({ decision: 'block', reason }) + '\n');
        process.exit(2);
      }
      // It's a git commit (not push) — no further checks needed
      process.exit(0);
    }

    // Block: git push --force or git push -f  (but NOT --force-with-lease)
    if (/\bgit\s+push\b/.test(commandPrefix)) {
      // Strip --force-with-lease occurrences before checking for --force / -f
      const stripped = commandPrefix.replace(/--force-with-lease(?:=[^\s]*)?/g, '');
      if (/--force\b/.test(stripped) || /\s-f\b/.test(stripped)) {
        const reason =
          '[masonry-block-no-verify] BLOCKED: git push --force can overwrite upstream work. ' +
          'Use --force-with-lease for safer force pushes.';
        process.stdout.write(JSON.stringify({ decision: 'block', reason }) + '\n');
        process.exit(2);
      }
    }

    // All checks passed — allow
    process.exit(0);
  } catch (_) {
    // stdin parse failure — allow rather than block
    process.exit(0);
  }
});
