const { defineConfig } = require('vitest/config');

module.exports = defineConfig({
  test: {
    globals: true,
    // src/tools/*.test.js and src/hooks/session/*.test.js are standalone
    // node-assert scripts (run with `node <file>.test.js`), not vitest suites.
    // Real vitest coverage lives in tests/ and tests/tools/.
    exclude: ['src/tools/**', 'src/hooks/session/*.test.js', 'node_modules/**'],
  },
});
