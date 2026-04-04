import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

// engine/config.js uses require() — load it dynamically
let configModule;

function freshLoad() {
  // Clear module cache to get a fresh config singleton each time
  const configPath = path.resolve(process.cwd(), 'src', 'engine', 'config.js');
  const corePath = path.resolve(process.cwd(), 'src', 'core', 'config.js');
  delete require.cache[configPath];
  delete require.cache[corePath];
  return require(configPath);
}

describe('engine/config — defaults', () => {
  it('should export cfg, authHeaders, initProject', () => {
    configModule = freshLoad();
    expect(configModule.cfg).toBeDefined();
    expect(typeof configModule.authHeaders).toBe('function');
    expect(typeof configModule.initProject).toBe('function');
  });

  it('should have default paths relative to BrickLayer root', () => {
    configModule = freshLoad();
    const { cfg } = configModule;
    expect(cfg.blRoot).toBeTruthy();
    expect(cfg.findingsDir).toContain('findings');
    expect(cfg.resultsTsv).toContain('results.tsv');
    expect(cfg.questionsMd).toContain('questions.md');
    expect(cfg.historyDb).toContain('history.db');
  });

  it('should export API route constants', () => {
    configModule = freshLoad();
    expect(configModule.SEARCH_ROUTE).toBe('/search/query');
    expect(configModule.STORE_ROUTE).toBe('/memory/store');
    expect(configModule.HEALTH_ROUTE).toBe('/health');
    expect(configModule.CONSOLIDATE_ROUTE).toBe('/admin/consolidate');
  });

  it('authHeaders should return Authorization and Content-Type', () => {
    configModule = freshLoad();
    const headers = configModule.authHeaders();
    expect(headers['Content-Type']).toBe('application/json');
    expect(headers.Authorization).toMatch(/^Bearer /);
  });
});

describe('engine/config — initProject', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bl-config-test-'));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('should update cfg paths when project has project.json', () => {
    configModule = freshLoad();
    const { cfg, initProject } = configModule;

    // Create a fake project under blRoot/projects/
    const projectDir = path.join(cfg.blRoot, 'projects', 'test-config-proj');
    const existed = fs.existsSync(projectDir);

    try {
      fs.mkdirSync(projectDir, { recursive: true });
      fs.writeFileSync(
        path.join(projectDir, 'project.json'),
        JSON.stringify({ api_key: 'test-key-123' })
      );

      initProject('test-config-proj');

      expect(cfg.projectRoot).toBe(projectDir);
      expect(cfg.findingsDir).toBe(path.join(projectDir, 'findings'));
      expect(cfg.resultsTsv).toBe(path.join(projectDir, 'results.tsv'));
      expect(cfg.apiKey).toBe('test-key-123');
    } finally {
      // Clean up
      if (!existed) {
        fs.rmSync(projectDir, { recursive: true, force: true });
      }
    }
  });

  it('should exit with error for non-existent project', () => {
    configModule = freshLoad();
    const mockExit = process.exit;
    let exitCode = null;
    process.exit = (code) => { exitCode = code; throw new Error('exit'); };

    try {
      configModule.initProject('nonexistent-project-xyz-999');
    } catch (e) {
      // expected
    }

    process.exit = mockExit;
    expect(exitCode).toBe(1);
  });

  it('should use null project to set paths to blRoot', () => {
    configModule = freshLoad();
    const { cfg, initProject } = configModule;
    initProject(null);
    expect(cfg.projectRoot).toBe(cfg.blRoot);
    expect(cfg.findingsDir).toBe(path.join(cfg.blRoot, 'findings'));
  });
});
