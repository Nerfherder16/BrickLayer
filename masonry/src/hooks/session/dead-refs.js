'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const DEAD_REFS = [
  { pattern: /oh-my-claudecode/i, label: 'oh-my-claudecode (uninstalled)' },
  { pattern: /DISABLE_OMC/i, label: 'DISABLE_OMC env var (removed)' },
  { pattern: /masonry-lint-check\.js/i, label: 'masonry-lint-check.js (merged into masonry-style-checker.js)' },
  { pattern: /masonry-design-token-enforcer\.js/i, label: 'masonry-design-token-enforcer.js (merged)' },
  { pattern: /masonry-config-protection\.js/i, label: 'masonry-config-protection.js (merged)' },
  { pattern: /masonry-secret-scanner\.js/i, label: 'masonry-secret-scanner.js (merged)' },
  { pattern: /masonry-session-lock\.js/i, label: 'masonry-session-lock.js (merged into masonry-pre-protect.js)' },
  { pattern: /masonry-pre-edit\.js/i, label: 'masonry-pre-edit.js (merged into masonry-pre-protect.js)' },
  { pattern: /claude-flow/i, label: 'claude-flow / Ruflo (replaced by Masonry)' },
];

function scanFile(filePath) {
  if (!fs.existsSync(filePath)) return [];
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return DEAD_REFS.filter(r => r.pattern.test(content)).map(r => ({ file: filePath, label: r.label }));
  } catch { return []; }
}

function scanAll(projectRoot, globalAgentsDir) {
  const findings = [];
  for (const dir of [path.join(projectRoot, '.claude', 'agents'), globalAgentsDir].filter(Boolean)) {
    if (!fs.existsSync(dir)) continue;
    try {
      fs.readdirSync(dir).filter(f => f.endsWith('.md')).forEach(f => findings.push(...scanFile(path.join(dir, f))));
    } catch {}
  }
  const hooksDir = path.join(projectRoot, 'masonry', 'src', 'hooks');
  if (fs.existsSync(hooksDir)) {
    try {
      fs.readdirSync(hooksDir).filter(f => f.endsWith('.js')).forEach(f => findings.push(...scanFile(path.join(hooksDir, f))));
    } catch {}
  }
  [path.join(projectRoot, '.claude', 'CLAUDE.md'), path.join(os.homedir(), '.claude', 'CLAUDE.md')]
    .forEach(f => findings.push(...scanFile(f)));
  return findings;
}

function formatWarnings(findings) {
  if (!findings.length) return '';
  return findings.map(f => `[Masonry] STALE_REF: ${f.label} — found in ${f.file}`).join('\n');
}

module.exports = { scanFile, scanAll, formatWarnings, DEAD_REFS };
