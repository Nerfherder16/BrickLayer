const { defineConfig } = require('vitest/config');

module.exports = defineConfig({
  test: {
    globals: true,
    // src/tools/*.test.js and most src/hooks/session/*.test.js are standalone
    // node-assert scripts (run with `node <file>.test.js`), not vitest suites.
    // Real vitest coverage lives in tests/, tests/tools/, and vitest-syntax session tests.
    exclude: [
      'src/tools/**',
      'src/hooks/session/dead-refs.test.js',
      'src/hooks/session/hotpaths.test.js',
      'node_modules/**',
    ],
  },
});
