'use strict';
// engine/runners/browser.js — Headless browser runner spec parser.
//
// Port of bl/runners/browser.py to Node.js.
// Exports the pure spec-parsing function. The full runner
// requires Playwright at runtime.

function _parseBrowserSpec(testField) {
  const spec = {
    url: null,
    action: 'navigate',
    action_selector: null,
    action_value: null,
    expect_title: null,
    expect_text: null,
    expect_not_text: null,
    expect_element: null,
    latency_threshold_ms: 5000,
    timeout: 15,
    screenshot: false,
    headless: true,
  };

  for (const line of testField.split('\n')) {
    const stripped = line.trim();
    if (!stripped) continue;

    const low = stripped.toLowerCase();

    if (low.startsWith('url:')) {
      spec.url = stripped.split(':').slice(1).join(':').trim();
      continue;
    }

    if (low.startsWith('action:')) {
      const actionStr = stripped.split(':').slice(1).join(':').trim();
      const parts = actionStr.split(/\s+/, 3);
      if (parts.length > 0) {
        spec.action = parts[0].toLowerCase();
        if (parts.length >= 2) spec.action_selector = parts[1];
        if (parts.length >= 3) spec.action_value = parts[2];
      }
      continue;
    }

    if (low.startsWith('expect_title:')) {
      spec.expect_title = stripped.split(':').slice(1).join(':').trim();
      continue;
    }

    if (low.startsWith('expect_text:')) {
      spec.expect_text = stripped.split(':').slice(1).join(':').trim();
      continue;
    }

    if (low.startsWith('expect_not_text:')) {
      spec.expect_not_text = stripped.split(':').slice(1).join(':').trim();
      continue;
    }

    if (low.startsWith('expect_element:')) {
      spec.expect_element = stripped.split(':').slice(1).join(':').trim();
      continue;
    }

    if (low.startsWith('latency_threshold_ms:')) {
      const val = parseInt(stripped.split(':').slice(1).join(':').trim(), 10);
      if (!isNaN(val)) spec.latency_threshold_ms = val;
      continue;
    }

    if (low.startsWith('timeout:')) {
      const val = parseInt(stripped.split(':').slice(1).join(':').trim(), 10);
      if (!isNaN(val)) spec.timeout = val;
      continue;
    }

    if (low.startsWith('screenshot:')) {
      const val = stripped.split(':').slice(1).join(':').trim().toLowerCase();
      spec.screenshot = ['true', 'yes', '1'].includes(val);
      continue;
    }

    if (low.startsWith('headless:')) {
      const val = stripped.split(':').slice(1).join(':').trim().toLowerCase();
      spec.headless = !['false', 'no', '0'].includes(val);
      continue;
    }
  }

  return spec;
}

module.exports = {
  _parseBrowserSpec,
};
