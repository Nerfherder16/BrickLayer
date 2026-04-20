// helper.js is a browser module inlined into HTML.
// We test the exported pure functions here (statusColor).
// DOM-dependent logic is integration-tested via server.test.cjs.

// Set up minimal browser globals before requiring helper.js
const mockElements = {};

function makeMockElement(id) {
  return {
    id,
    textContent: '',
    style: { backgroundColor: '' },
    innerHTML: '',
    className: '',
    dataset: {},
    children: [],
    addEventListener: vi.fn(),
    appendChild: vi.fn(function (child) { this.children.push(child); }),
    querySelectorAll: vi.fn(() => []),
    classList: { toggle: vi.fn() },
  };
}

global.document = {
  getElementById: vi.fn((id) => {
    if (!mockElements[id]) mockElements[id] = makeMockElement(id);
    return mockElements[id];
  }),
  querySelectorAll: vi.fn(() => []),
  createElement: vi.fn((tag) => makeMockElement('_' + tag + '_' + Math.random())),
  addEventListener: vi.fn(),
};

global.fetch = vi.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({ sections: [] }),
    body: {
      getReader: () => ({
        read: vi.fn(() => Promise.resolve({ done: true, value: null })),
      }),
    },
  })
);

// createRequire to load helper.js (CJS) from this vitest file
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const helper = require('./helper.js');

describe('statusColor', () => {
  it('returns green for approved', () => {
    expect(helper.statusColor('approved')).toBe('#3fb950');
  });

  it('returns red for flagged', () => {
    expect(helper.statusColor('flagged')).toBe('#f85149');
  });

  it('returns gray for draft', () => {
    expect(helper.statusColor('draft')).toBe('#8b949e');
  });

  it('returns gray for unknown/undefined status', () => {
    expect(helper.statusColor('unknown')).toBe('#8b949e');
    expect(helper.statusColor(undefined)).toBe('#8b949e');
  });
});

describe('helper exports', () => {
  it('exports statusColor as a function', () => {
    expect(typeof helper.statusColor).toBe('function');
  });
});
