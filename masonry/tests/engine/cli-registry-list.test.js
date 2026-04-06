import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execSync } from 'node:child_process';

const CLI = path.resolve(
  import.meta.dirname,
  '../../src/engine/cli/registry-list.js'
);

const REAL_REGISTRY = path.resolve(import.meta.dirname, '../../agent_registry.yml');

const SAMPLE_REGISTRY = `version: 1
agents:
- name: alpha-agent
  file: .claude/agents/alpha-agent.md
  model: sonnet
  description: Does alpha things
  modes:
  - build
  - research
  capabilities:
  - planning
  - analysis
  tier: trusted
- name: beta-agent
  file: .claude/agents/beta-agent.md
  model: haiku
  description: Does beta things
  modes:
  - audit
  capabilities:
  - review
  tier: candidate
- name: gamma-agent
  file: .claude/agents/gamma-agent.md
  model: sonnet
  description: Does gamma things
  modes:
  - build
  capabilities:
  - implementation
  tier: trusted
`;

function run(extraArgs = '', env = {}) {
  const cmd = `node ${CLI} ${extraArgs}`;
  try {
    const stdout = execSync(cmd, {
      env: { ...process.env, ...env },
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return { stdout, exitCode: 0 };
  } catch (err) {
    return { stdout: err.stdout ?? '', exitCode: err.status ?? 1 };
  }
}

function runWithProjectDir(projectDir, extraArgs = '') {
  return run(`--project-dir ${projectDir} ${extraArgs}`);
}

function makeRegistryDir(content = SAMPLE_REGISTRY) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'registry-test-'));
  const masonryDir = path.join(tmp, 'masonry');
  fs.mkdirSync(masonryDir);
  fs.writeFileSync(path.join(masonryDir, 'agent_registry.yml'), content, 'utf8');
  return tmp;
}

describe('registry-list CLI', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = makeRegistryDir();
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('no-args — outputs valid JSON array', () => {
    it('should output a JSON array when called against the real registry', () => {
      // Use the real registry via default path resolution
      const result = run();
      expect(result.exitCode).toBe(0);
      const parsed = JSON.parse(result.stdout.trim());
      expect(Array.isArray(parsed)).toBe(true);
      expect(parsed.length).toBeGreaterThan(0);
    });

    it('should include id, tier, mode, description, capabilities on each agent', () => {
      const result = runWithProjectDir(tmpDir);
      expect(result.exitCode).toBe(0);
      const agents = JSON.parse(result.stdout.trim());
      expect(agents.length).toBe(3);
      const agent = agents[0];
      expect(agent).toHaveProperty('id');
      expect(agent).toHaveProperty('tier');
      expect(agent).toHaveProperty('mode');
      expect(agent).toHaveProperty('description');
      expect(agent).toHaveProperty('capabilities');
    });
  });

  describe('--tier filter', () => {
    it('should return only tier:trusted agents when --tier trusted', () => {
      const result = runWithProjectDir(tmpDir, '--tier trusted');
      expect(result.exitCode).toBe(0);
      const agents = JSON.parse(result.stdout.trim());
      expect(agents.length).toBe(2);
      expect(agents.every((a) => a.tier === 'trusted')).toBe(true);
    });

    it('should return only tier:candidate agents when --tier candidate', () => {
      const result = runWithProjectDir(tmpDir, '--tier candidate');
      expect(result.exitCode).toBe(0);
      const agents = JSON.parse(result.stdout.trim());
      expect(agents.length).toBe(1);
      expect(agents[0].id).toBe('beta-agent');
    });

    it('should return empty array for a tier that does not exist', () => {
      const result = runWithProjectDir(tmpDir, '--tier nonexistent');
      expect(result.exitCode).toBe(0);
      const agents = JSON.parse(result.stdout.trim());
      expect(agents).toEqual([]);
    });
  });

  describe('--mode filter', () => {
    it('should return only agents whose modes include "build" when --mode build', () => {
      const result = runWithProjectDir(tmpDir, '--mode build');
      expect(result.exitCode).toBe(0);
      const agents = JSON.parse(result.stdout.trim());
      expect(agents.length).toBe(2);
      expect(agents.map((a) => a.id).sort()).toEqual(['alpha-agent', 'gamma-agent']);
    });

    it('should return only agents with mode "audit" when --mode audit', () => {
      const result = runWithProjectDir(tmpDir, '--mode audit');
      expect(result.exitCode).toBe(0);
      const agents = JSON.parse(result.stdout.trim());
      expect(agents.length).toBe(1);
      expect(agents[0].id).toBe('beta-agent');
    });

    it('should return empty array for a mode that does not exist', () => {
      const result = runWithProjectDir(tmpDir, '--mode nonexistent');
      expect(result.exitCode).toBe(0);
      const agents = JSON.parse(result.stdout.trim());
      expect(agents).toEqual([]);
    });
  });

  describe('--tier and --mode combined', () => {
    it('should apply both filters', () => {
      const result = runWithProjectDir(tmpDir, '--tier trusted --mode build');
      expect(result.exitCode).toBe(0);
      const agents = JSON.parse(result.stdout.trim());
      expect(agents.length).toBe(2);
      expect(agents.every((a) => a.tier === 'trusted')).toBe(true);
    });
  });

  describe('missing registry', () => {
    it('should exit 1 with JSON error object when registry file does not exist', () => {
      const missingDir = path.join(os.tmpdir(), 'no-such-project-xyz');
      const result = runWithProjectDir(missingDir);
      expect(result.exitCode).toBe(1);
      const parsed = JSON.parse(result.stdout.trim());
      expect(parsed).toHaveProperty('error');
      expect(parsed.error).toMatch(/registry not found at/);
    });
  });
});
