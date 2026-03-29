'use strict';
/**
 * stop-checks.js — stop-time check functions for masonry-stop-guard.js
 * checkDocStaleness, checkOverseerTrigger, pruneOldBackups
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

const PROJECT_DOCS = ['CHANGELOG.md', 'ROADMAP.md', 'ARCHITECTURE.md', 'README.md', 'PROJECT_STATUS.md'];

const SOURCE_PATTERNS = [
  /^masonry\//,
  /^\.claude\//,
  /^template\//,
  /^adbp\//,
  /^kiln\//,
  /^bl\//,
  /^projects\//,
];

function checkDocStaleness(cwd, snapPath) {
  try {
    let since = '';
    try {
      const snapStat = fs.statSync(snapPath);
      since = `--after="${new Date(snapStat.mtimeMs).toISOString()}"`;
    } catch {
      since = '--after="midnight"';
    }

    const log = execSync(`git log --name-only --pretty=format:"" ${since}`, {
      encoding: 'utf8', timeout: 8000, cwd,
    }).trim();
    if (!log) return;

    const changedFiles = log.split('\n').map(l => l.trim()).filter(Boolean);
    const hasSourceChange = changedFiles.some(f => SOURCE_PATTERNS.some(p => p.test(f)));
    if (!hasSourceChange) return;

    const touchedDocs = changedFiles.filter(f => PROJECT_DOCS.includes(f));
    if (touchedDocs.length > 0) return;

    const missing = PROJECT_DOCS.filter(d => !touchedDocs.includes(d));
    process.stderr.write(
      `\n[Masonry] Doc staleness warning: code was committed this session but project docs were not updated.\n` +
      `  Stale: ${missing.join(', ')}\n` +
      `  Run karen or update docs before your next session.\n`
    );

    try {
      const autopilotDir = path.join(cwd, '.autopilot');
      const masDir = path.join(cwd, '.mas');
      const targetDir = fs.existsSync(autopilotDir) ? autopilotDir : masDir;
      fs.mkdirSync(targetDir, { recursive: true });
      fs.writeFileSync(
        path.join(targetDir, 'karen-needed.json'),
        JSON.stringify({
          reason: 'doc_staleness',
          stale_files: missing,
          source_files_changed: changedFiles.filter(
            f => /\.(py|js|ts|tsx|rs|go|md)$/.test(f) &&
                 !/(CHANGELOG|ARCHITECTURE|ROADMAP|synthesis|findings)/.test(f)
          ),
          timestamp: new Date().toISOString(),
        }, null, 2),
        'utf8'
      );
    } catch { /* non-fatal */ }
  } catch { /* git unavailable */ }
}

function checkOverseerTrigger(snapshotsDir, stderrFn) {
  stderrFn = stderrFn || ((s) => process.stderr.write(s));
  const flagPath = path.join(snapshotsDir, 'overseer_trigger.flag');
  if (!fs.existsSync(flagPath)) return;
  const agentsDir = path.join(os.homedir(), '.claude', 'agents');
  const overseerPath = path.join(agentsDir, 'overseer.md');
  stderrFn(
    '\n[overseer] 10 agent invocations since last health check.\n' +
    `Run: claude -p "Act as overseer agent in ${overseerPath}. agents_dir=${agentsDir}. Check all agents."\n`
  );
  fs.unlinkSync(flagPath);
}

function pruneOldBackups(autopilotDir) {
  const backupsRoot = path.join(autopilotDir, 'backups');
  if (!fs.existsSync(backupsRoot)) return;
  const cutoff = Date.now() - 7 * 24 * 60 * 60 * 1000;

  function pruneDir(dir) {
    let entries;
    try { entries = fs.readdirSync(dir); } catch { return; }
    for (const entry of entries) {
      const full = path.join(dir, entry);
      let stat;
      try { stat = fs.statSync(full); } catch { continue; }
      if (stat.isDirectory()) {
        pruneDir(full);
        try { if (!fs.readdirSync(full).length) fs.rmdirSync(full); } catch { /* ignore */ }
      } else if (stat.mtimeMs < cutoff) {
        try { fs.unlinkSync(full); } catch { /* ignore */ }
      }
    }
  }
  try { pruneDir(backupsRoot); } catch { /* ignore */ }
}

module.exports = { checkDocStaleness, checkOverseerTrigger, pruneOldBackups };
