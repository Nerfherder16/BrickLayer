#!/usr/bin/env node
/**
 * extract-hooks-manifest.js — One-shot utility.
 *
 * Reads ~/.claude/settings.json and writes masonry/hooks-manifest.json —
 * a clean, documented JSON snapshot of every registered hook.
 *
 * Idempotent: running it twice produces identical output (modulo timestamps).
 * The manifest is documentation-only and is NOT used to generate settings.json.
 *
 * Usage: node masonry/scripts/extract-hooks-manifest.js
 */

'use strict';

const fs   = require('fs');
const path = require('path');
const os   = require('os');

const HOME         = os.homedir();
const SETTINGS     = path.join(HOME, '.claude', 'settings.json');
const MANIFEST_OUT = path.join(__dirname, '..', 'hooks-manifest.json');

// Runner scripts whose embedded BACKGROUND_HOOKS arrays we also expand
const RUNNER_SCRIPTS = {
  'masonry-stop-runner':
    '/home/nerfherder/Dev/Bricklayer2.0/masonry/src/hooks/masonry-stop-runner.js',
  'masonry-post-write-runner':
    '/home/nerfherder/Dev/Bricklayer2.0/masonry/src/hooks/masonry-post-write-runner.js',
};
const RUNNER_PATHS = new Set(Object.values(RUNNER_SCRIPTS));

// Known Claude Code event names — if an extracted "path" is one of these,
// it's an argument to the previous script (e.g. better-hook.sh EventName).
const EVENT_NAMES = new Set([
  'PreToolUse', 'PostToolUse', 'PostToolUseFailure', 'Stop', 'SessionStart',
  'SessionEnd', 'UserPromptSubmit', 'SubagentStart', 'SubagentStop',
  'TeammateIdle', 'TaskCompleted', 'PreCompact', 'PostCompact',
  'Notification', 'ExitPlanMode', 'Agent',
]);

// ─── Path helpers ─────────────────────────────────────────────────────────────
function expandPath(p) {
  if (!p) return p;
  if (p.startsWith('~/')) return path.join(HOME, p.slice(2));
  return p;
}

/**
 * Parse hook command string → { name, scriptPath, isBash }
 * Handles hook-timer.sh wrappers and direct `node <path>` / `bash <path>` forms.
 */
function parseHookCommand(cmd) {
  if (!cmd) return { name: '', scriptPath: null, isBash: false };

  const parts = cmd.trim().split(/\s+/);
  const timerIdx = parts.findIndex(p => p.includes('hook-timer.sh'));

  if (timerIdx !== -1) {
    const inner = parts.slice(timerIdx + 1);
    // inner[0] = label, inner[1] = cmd or script, inner[2] = path or event arg
    if (inner.length >= 3) {
      const label  = inner[0];
      const rawPath = inner[2];

      // If inner[2] is an event name, the script is inner[1] (e.g. better-hook.sh)
      if (EVENT_NAMES.has(rawPath)) {
        const scriptPath = expandPath(inner[1]);
        return { name: label, scriptPath, isBash: true };
      }

      const innerCmd   = inner[1];
      const scriptPath = expandPath(rawPath);
      const isBash     = innerCmd === 'bash' || scriptPath.endsWith('.sh');
      return { name: label, scriptPath, isBash };
    }
    return { name: '', scriptPath: null, isBash: false };
  }

  if (parts[0] === 'node' && parts.length >= 2) {
    const scriptPath = expandPath(parts[1]);
    const name = path.basename(scriptPath, '.js');
    return { name, scriptPath, isBash: false };
  }

  if (parts[0] === 'bash' || (parts[0] && parts[0].endsWith('.sh'))) {
    const scriptPath = expandPath(parts[0] === 'bash' ? parts[1] : parts[0]);
    const name = path.basename(scriptPath, '.sh');
    return { name, scriptPath, isBash: true };
  }

  return { name: cmd.slice(0, 40), scriptPath: null, isBash: false };
}

/**
 * Check if a script source contains process.exit(2) (can block).
 */
function canBlock(scriptPath) {
  if (!scriptPath) return false;
  try {
    const src = fs.readFileSync(scriptPath, 'utf8');
    return src.includes('process.exit(2)');
  } catch {
    return false;
  }
}

/**
 * Parse BACKGROUND_HOOKS array from a runner script.
 * Returns array of { label, scriptPath, isBash }
 *
 * Handles both:
 *   [`${HOME}/path/to/script.js`]
 *   [path.join(HOOKS_DIR, 'script.js')]
 */
function extractRunnerHooks(runnerPath) {
  let src;
  try { src = fs.readFileSync(runnerPath, 'utf8'); } catch { return []; }

  const hooksDir = path.dirname(runnerPath);
  const hooks    = [];
  const lineRe   = /\[\s*'([^']+)'\s*,\s*'(node|bash)'\s*,\s*\[([^\]]+)\]/g;
  let m;
  while ((m = lineRe.exec(src)) !== null) {
    const label   = m[1];
    const cmd     = m[2];
    const argsStr = m[3].trim();

    let scriptPath = null;

    // Form 1: template literal `${HOME}/...` or `${HOOKS_DIR}/...`
    const backtickMatch = argsStr.match(/`([^`]+)`/);
    if (backtickMatch) {
      const raw = backtickMatch[1]
        .replace(/\$\{HOME\}/g,     HOME)
        .replace(/\$\{HOOKS_DIR\}/g, hooksDir);
      scriptPath = expandPath(raw);
    }

    // Form 2: path.join(HOOKS_DIR, 'filename.js') or path.join(__dirname, ...)
    if (!scriptPath) {
      const joinMatch = argsStr.match(/path\.join\(\s*(?:HOOKS_DIR|__dirname)\s*,\s*['"]([^'"]+)['"]\s*\)/);
      if (joinMatch) {
        scriptPath = path.join(hooksDir, joinMatch[1]);
      }
    }

    // Form 3: bare string literal
    if (!scriptPath) {
      const strMatch = argsStr.match(/^['"]([^'"]+)['"]/);
      if (strMatch) {
        scriptPath = expandPath(strMatch[1]);
      }
    }

    if (!scriptPath) continue;

    hooks.push({
      label,
      scriptPath,
      isBash: cmd === 'bash' || scriptPath.endsWith('.sh'),
    });
  }
  return hooks;
}

// ─── Build manifest ────────────────────────────────────────────────────────────
function buildManifest(settings) {
  const hooks   = settings.hooks || {};
  const entries = [];

  for (const [eventType, eventEntries] of Object.entries(hooks)) {
    for (const entry of eventEntries) {
      const matcher = entry.matcher || '';
      for (const hook of (entry.hooks || [])) {
        const cmd       = hook.command || '';
        const isAsync   = !!(hook.async);
        const timeout   = hook.timeout || null;
        const { name, scriptPath, isBash } = parseHookCommand(cmd);
        const exists    = scriptPath ? fs.existsSync(scriptPath) : false;
        const blockable = !isBash && exists ? canBlock(scriptPath) : false;

        const record = {
          name:          name || path.basename(scriptPath || '', '.js'),
          label:         name || '',
          event:         eventType,
          matcher:       matcher,
          async:         isAsync,
          can_block:     blockable,
          timeout:       timeout,
          script:        scriptPath || null,
          script_exists: exists,
          inside_runner: null,
        };
        entries.push(record);

        // If this is a runner, expand its embedded hooks too
        if (scriptPath && RUNNER_PATHS.has(scriptPath)) {
          const runnerName = Object.entries(RUNNER_SCRIPTS).find(([, p]) => p === scriptPath)?.[0];
          const embedded   = extractRunnerHooks(scriptPath);
          for (const emb of embedded) {
            const embExists  = fs.existsSync(emb.scriptPath);
            const embBlock   = !emb.isBash && embExists ? canBlock(emb.scriptPath) : false;
            entries.push({
              name:          emb.label,
              label:         emb.label,
              event:         eventType,
              matcher:       matcher,
              async:         true,
              can_block:     embBlock,
              timeout:       null,
              script:        emb.scriptPath,
              script_exists: embExists,
              inside_runner: runnerName,
            });
          }
        }
      }
    }
  }

  return entries;
}

// ─── Main ─────────────────────────────────────────────────────────────────────
function main() {
  let settings;
  try {
    settings = JSON.parse(fs.readFileSync(SETTINGS, 'utf8'));
  } catch (err) {
    console.error(`Failed to read ${SETTINGS}: ${err.message}`);
    process.exit(1);
  }

  const manifest = buildManifest(settings);

  const output = {
    generated_at: new Date().toISOString(),
    settings_path: SETTINGS,
    total_hooks: manifest.length,
    hooks: manifest,
  };

  fs.writeFileSync(MANIFEST_OUT, JSON.stringify(output, null, 2) + '\n', 'utf8');

  console.log(`Wrote ${manifest.length} hooks to ${MANIFEST_OUT}`);

  // Summary
  const missing   = manifest.filter(h => !h.script_exists).length;
  const inRunner  = manifest.filter(h => h.inside_runner).length;
  const canBlock  = manifest.filter(h => h.can_block).length;
  const asyncHooks = manifest.filter(h => h.async).length;

  console.log(`  total: ${manifest.length}  missing: ${missing}  in-runner: ${inRunner}  can-block: ${canBlock}  async: ${asyncHooks}`);
}

main();
