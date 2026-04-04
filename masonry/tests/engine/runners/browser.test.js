import { describe, it, expect, beforeAll } from 'vitest';

describe('runners/browser', () => {
  let mod;

  beforeAll(() => {
    const modPath = require('path').resolve(
      process.cwd(), 'src', 'engine', 'runners', 'browser.js',
    );
    delete require.cache[modPath];
    mod = require(modPath);
  });

  describe('_parseBrowserSpec', () => {
    it('should parse url directive', () => {
      const spec = mod._parseBrowserSpec('url: http://localhost:3000\n');
      expect(spec.url).toBe('http://localhost:3000');
    });

    it('should parse action with selector and value', () => {
      const text = 'url: http://test\naction: fill #email user@test.com';
      const spec = mod._parseBrowserSpec(text);
      expect(spec.action).toBe('fill');
      expect(spec.action_selector).toBe('#email');
      expect(spec.action_value).toBe('user@test.com');
    });

    it('should parse click action', () => {
      const text = 'url: http://test\naction: click .submit-btn';
      const spec = mod._parseBrowserSpec(text);
      expect(spec.action).toBe('click');
      expect(spec.action_selector).toBe('.submit-btn');
      expect(spec.action_value).toBeNull();
    });

    it('should parse expect directives', () => {
      const text = [
        'url: http://test',
        'expect_title: My App',
        'expect_text: Welcome',
        'expect_not_text: Error',
        'expect_element: .hero-section',
      ].join('\n');
      const spec = mod._parseBrowserSpec(text);
      expect(spec.expect_title).toBe('My App');
      expect(spec.expect_text).toBe('Welcome');
      expect(spec.expect_not_text).toBe('Error');
      expect(spec.expect_element).toBe('.hero-section');
    });

    it('should parse numeric and boolean settings', () => {
      const text = [
        'url: http://test',
        'latency_threshold_ms: 3000',
        'timeout: 30',
        'screenshot: true',
        'headless: false',
      ].join('\n');
      const spec = mod._parseBrowserSpec(text);
      expect(spec.latency_threshold_ms).toBe(3000);
      expect(spec.timeout).toBe(30);
      expect(spec.screenshot).toBe(true);
      expect(spec.headless).toBe(false);
    });

    it('should use defaults for missing directives', () => {
      const spec = mod._parseBrowserSpec('url: http://test');
      expect(spec.action).toBe('navigate');
      expect(spec.latency_threshold_ms).toBe(5000);
      expect(spec.timeout).toBe(15);
      expect(spec.screenshot).toBe(false);
      expect(spec.headless).toBe(true);
    });

    it('should handle empty input', () => {
      const spec = mod._parseBrowserSpec('');
      expect(spec.url).toBeNull();
      expect(spec.action).toBe('navigate');
    });
  });
});
