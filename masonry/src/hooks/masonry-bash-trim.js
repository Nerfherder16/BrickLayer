#!/usr/bin/env node
/**
 * PreToolUse Bash hook: advisory output limiter.
 *
 * Detects commands likely to produce large output and injects a systemMessage
 * suggesting truncation (| head, | tail, --quiet, etc.). Non-blocking — never
 * exits 2, so it only advises. Reduces cache token cost from Bash tool use.
 *
 * Patterns detected:
 * - cat/less on large files without head/tail
 * - find/ls -R without piping
 * - docker logs without --tail
 * - git log without -n/--oneline
 * - npm/pip list without --json or grep
 * - curl without -s or piping
 * - journalctl without --lines
 * - pytest/vitest without --quiet/--silent
 */

'use strict';

const VERBOSE_PATTERNS = [
  {
    // cat/less large file without head/tail/grep
    test: /\b(cat|less|bat)\s+\S+/,
    skip: /\|\s*(head|tail|grep|wc|awk|sed|cut|jq|python)/,
    hint: 'Pipe to | head -50 or | tail -20 to limit output',
  },
  {
    // find without piping or -maxdepth
    test: /\bfind\s+/,
    skip: /\|\s*(head|tail|grep|wc)|(-maxdepth\s+[12])|head\s+-/,
    hint: 'Add -maxdepth 2 or pipe to | head -30',
  },
  {
    // ls -R or ls -la on broad paths
    test: /\bls\s+(-\w*[Rl]\w*|\*\*)/,
    skip: /\|\s*(head|tail|grep|wc)/,
    hint: 'Pipe to | head -30 or use Glob tool instead',
  },
  {
    // docker logs without --tail
    test: /\bdocker\s+(logs|compose\s+logs)/,
    skip: /--tail|--since|\|\s*(head|tail|grep)/,
    hint: 'Add --tail 50 to limit log output',
  },
  {
    // git log without -n or --oneline
    test: /\bgit\s+log\b/,
    skip: /-\d+|--oneline|-n\s*\d+|\|\s*(head|tail)/,
    hint: 'Add --oneline -20 or -n 20 to limit output',
  },
  {
    // npm/pip list without filtering
    test: /\b(npm|pip|pip3)\s+list\b/,
    skip: /--json|\|\s*(grep|head|jq)/,
    hint: 'Pipe to | grep <pattern> or add --json | jq',
  },
  {
    // curl without -s (silent)
    test: /\bcurl\s+/,
    skip: /-s\b|--silent|\|\s*(head|tail|jq|python)/,
    hint: 'Add -s (silent) and pipe to | head or | jq',
  },
  {
    // pytest/vitest without quiet flags
    test: /\b(pytest|vitest|jest)\b/,
    skip: /--quiet|-q\b|--silent|--reporters=dot|--tb=no|--tb=short|--no-header/,
    hint: 'Add -q or --tb=short to reduce output',
  },
  {
    // journalctl without --lines
    test: /\bjournalctl\b/,
    skip: /--lines|-n\s*\d+|--since|\|\s*(head|tail|grep)/,
    hint: 'Add -n 50 or --lines=50',
  },
];

function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    const timer = setTimeout(() => resolve(data), 2000);
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (c) => { data += c; });
    process.stdin.on('end', () => { clearTimeout(timer); resolve(data); });
  });
}

async function main() {
  const raw = await readStdin();
  if (!raw.trim()) process.exit(0);

  let event;
  try { event = JSON.parse(raw.trim()); } catch { process.exit(0); }

  const cmd = event.tool_input?.command || '';
  if (!cmd) process.exit(0);

  const hints = [];
  for (const pattern of VERBOSE_PATTERNS) {
    if (pattern.test.test(cmd) && !pattern.skip.test(cmd)) {
      hints.push(pattern.hint);
    }
  }

  if (hints.length === 0) process.exit(0);

  // Advisory only — never block (exit 0)
  const msg = `[Token Trim] This command may produce large output:\n${hints.map(h => `  - ${h}`).join('\n')}`;
  process.stdout.write(JSON.stringify({ systemMessage: msg }) + '\n');
  process.exit(0);
}

main().catch(() => process.exit(0));
