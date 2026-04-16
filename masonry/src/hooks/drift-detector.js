'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * Parse file paths from a spec markdown string.
 * Looks in: fenced code blocks, bullet lists, and sections under
 * headings containing Files/Modified/Changed/Created.
 */
function parseSpecFiles(text) {
  const paths = new Set();
  const lines = text.split('\n');

  const pathLike = (s) => {
    const t = s.trim().replace(/^`+|`+$/g, '').trim();
    if (!t) return null;
    // Must contain / or have a known extension
    const knownExt = /\.(js|ts|py|md|json|sh|cjs|html|css|jsx|tsx|yml|yaml|txt)$/i.test(t);
    if (!t.includes('/') && !knownExt) return null;
    // Filter out URLs, markdown links, and very short tokens
    if (t.startsWith('http') || t.length < 4) return null;
    // Remove trailing punctuation
    return t.replace(/[,;)>]+$/, '').trim() || null;
  };

  let inCodeBlock = false;
  let inFilesSection = false;

  for (const line of lines) {
    // Toggle code block
    if (/^```/.test(line)) {
      inCodeBlock = !inCodeBlock;
      continue;
    }

    // Track headings with Files/Modified/Changed/Created
    if (!inCodeBlock && /^#{1,4}\s/.test(line)) {
      inFilesSection = /files|modified|changed|created/i.test(line);
      continue;
    }

    if (inCodeBlock) {
      const p = pathLike(line);
      if (p) paths.add(p);
      continue;
    }

    if (inFilesSection) {
      // Bullet list items
      const m = line.match(/^[\s]*[-*]\s+(.+)/);
      if (m) {
        const p = pathLike(m[1]);
        if (p) paths.add(p);
      }
      continue;
    }

    // Bullet lists anywhere — only if they look strongly like paths
    const m = line.match(/^[\s]*[-*]\s+`?([^\s`]+)`?/);
    if (m) {
      const p = pathLike(m[1]);
      if (p && p.includes('/')) paths.add(p);
    }
  }

  return [...paths];
}

/**
 * Compute drift between spec-claimed files and git-changed files.
 */
function computeDrift(claimedFiles, changedFiles) {
  const claimed = new Set(claimedFiles);
  const changed = new Set(changedFiles);

  const matched = [...claimed].filter((f) => changed.has(f));
  const onlyInSpec = [...claimed].filter((f) => !changed.has(f));
  const onlyInDiff = [...changed].filter((f) => !claimed.has(f));
  const verdict = onlyInSpec.length === 0 && onlyInDiff.length === 0 ? 'CLEAN' : 'DRIFT_DETECTED';

  return { matched, onlyInSpec, onlyInDiff, verdict };
}

async function main() {
  const cwd = process.cwd();

  // 1. Resolve spec file
  let specFile = process.argv[2] || null;
  if (!specFile) {
    const specPathFile = path.join(cwd, '.autopilot', 'spec-path');
    if (fs.existsSync(specPathFile)) {
      specFile = fs.readFileSync(specPathFile, 'utf8').trim();
    }
  }
  if (!specFile) {
    const specsDir = path.join(cwd, 'docs', 'specs');
    if (fs.existsSync(specsDir)) {
      const mdFiles = fs.readdirSync(specsDir)
        .filter((f) => f.endsWith('.md'))
        .map((f) => ({ f, mtime: fs.statSync(path.join(specsDir, f)).mtimeMs }))
        .sort((a, b) => b.mtime - a.mtime);
      if (mdFiles.length > 0) specFile = path.join(specsDir, mdFiles[0].f);
    }
  }
  if (!specFile) {
    console.log('No spec file found — skipping drift check');
    process.exit(0);
  }

  // 2. Read build-start SHA
  const shaFile = path.join(cwd, '.autopilot', 'build-start-sha');
  if (!fs.existsSync(shaFile)) {
    console.log('No build baseline — run /build first');
    process.exit(2);
  }
  const baseSha = fs.readFileSync(shaFile, 'utf8').trim();

  // 3. Parse spec
  let specText;
  try {
    specText = fs.readFileSync(specFile, 'utf8');
  } catch (e) {
    console.log(`Cannot read spec file ${specFile}: ${e.message}`);
    process.exit(2);
  }
  const claimedFiles = parseSpecFiles(specText);

  // 4. Git diff
  let changedFiles;
  try {
    const out = execSync(`git diff --name-only ${baseSha} HEAD`, {
      cwd,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    changedFiles = out.split('\n').filter(Boolean);
  } catch (e) {
    console.error(e.stderr || e.message);
    process.exit(2);
  }

  // 5. Compute drift
  const { matched, onlyInSpec, onlyInDiff, verdict } = computeDrift(claimedFiles, changedFiles);

  // 6. Write drift-report.md
  const reportLines = [
    '# Drift Report',
    `Generated: ${new Date().toISOString()}`,
    `Spec: ${specFile}`,
    `Verdict: ${verdict}`,
    '',
    `## Matched (${matched.length} files)`,
    ...matched.map((f) => `- ${f}`),
    '',
    `## Only in Spec — not touched (${onlyInSpec.length} files)`,
    ...onlyInSpec.map((f) => `- ${f}`),
    '',
    `## Only in Diff — not in spec (${onlyInDiff.length} files)`,
    ...onlyInDiff.map((f) => `- ${f}`),
  ];
  try {
    fs.writeFileSync(path.join(cwd, '.autopilot', 'drift-report.md'), reportLines.join('\n'));
  } catch (e) {
    console.error(`Warning: could not write drift-report.md: ${e.message}`);
  }

  // 7-9. Write summary and print
  const summary =
    verdict === 'CLEAN'
      ? `✓ CLEAN — ${matched.length} files matched, 0 drift`
      : `⚠ DRIFT: ${onlyInDiff.length} unspecced files changed, ${onlyInSpec.length} spec claims untouched`;

  try {
    fs.writeFileSync(path.join(cwd, '.autopilot', 'drift-summary.txt'), summary);
  } catch (e) {
    console.error(`Warning: could not write drift-summary.txt: ${e.message}`);
  }

  console.log(summary);
  process.exit(verdict === 'CLEAN' ? 0 : 1);
}

module.exports = { parseSpecFiles, computeDrift };

if (require.main === module) {
  main().catch((e) => {
    console.error(e.message);
    process.exit(2);
  });
}
