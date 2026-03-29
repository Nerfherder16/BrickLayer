"use strict";
/**
 * Extracted from masonry-tdd-enforcer.js.
 * Locates the test file corresponding to a given implementation file path.
 * Returns the absolute path of the test file, or null if not found.
 */

const { existsSync, readdirSync, statSync } = require("fs");
const path = require("path");

function findTestFile(filePath) {
  const ext = path.extname(filePath);
  const base = path.basename(filePath, ext);
  const dir = path.dirname(filePath);

  // Python files
  if (ext === ".py") {
    const candidates = [
      path.join(dir, `test_${base}.py`),
      path.join(dir, `${base}_test.py`),
    ];

    // Walk up to find all tests/ directories (do not break at first match —
    // a project may have masonry/tests/ and a root tests/; check both)
    let searchDir = dir;
    for (let i = 0; i < 10; i++) {
      const testsDir = path.join(searchDir, "tests");
      if (existsSync(testsDir)) {
        candidates.push(path.join(testsDir, `test_${base}.py`));
        try {
          const entries = readdirSync(testsDir);
          for (const entry of entries) {
            const full = path.join(testsDir, entry);
            if (statSync(full).isDirectory()) {
              candidates.push(path.join(full, `test_${base}.py`));
            }
          }
        } catch {}
      }
      const parent = path.dirname(searchDir);
      if (parent === searchDir) break;
      searchDir = parent;
    }

    return candidates.find((c) => existsSync(c)) || null;
  }

  // TypeScript/JavaScript files
  if (/\.(ts|tsx|js|jsx)$/.test(ext)) {
    const candidates = [
      path.join(dir, `${base}.test${ext}`),
      path.join(dir, `${base}.spec${ext}`),
      path.join(dir, "__tests__", `${base}.test${ext}`),
      path.join(dir, "__tests__", `${base}.spec${ext}`),
    ];

    let searchDir = dir;
    for (let i = 0; i < 10; i++) {
      const testsDir = path.join(searchDir, "tests");
      if (existsSync(testsDir)) {
        candidates.push(path.join(testsDir, `${base}.test${ext}`));
        candidates.push(path.join(testsDir, `${base}.spec${ext}`));
        candidates.push(path.join(testsDir, `test_${base}.js`));
        try {
          const entries = readdirSync(testsDir);
          for (const entry of entries) {
            const full = path.join(testsDir, entry);
            if (statSync(full).isDirectory()) {
              candidates.push(path.join(full, `${base}.test${ext}`));
              candidates.push(path.join(full, `${base}.spec${ext}`));
            }
          }
        } catch {}
      }

      const srcTestsDir = path.join(searchDir, "src", "__tests__");
      if (existsSync(srcTestsDir)) {
        candidates.push(path.join(srcTestsDir, `${base}.test${ext}`));
        candidates.push(path.join(srcTestsDir, `${base}.spec${ext}`));
        try {
          const entries = readdirSync(srcTestsDir);
          for (const entry of entries) {
            const full = path.join(srcTestsDir, entry);
            if (statSync(full).isDirectory()) {
              candidates.push(path.join(full, `${base}.test${ext}`));
              candidates.push(path.join(full, `${base}.spec${ext}`));
            }
          }
        } catch {}
      }

      const parent = path.dirname(searchDir);
      if (parent === searchDir) break;
      searchDir = parent;
    }

    return candidates.find((c) => existsSync(c)) || null;
  }

  return null;
}

module.exports = { findTestFile };
