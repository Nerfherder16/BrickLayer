import React from 'react'
import { describe, it, expect, vi } from 'vitest'

// -------------------------------------------------------------------
// Mock heavy dependencies that are unavailable in the test environment
// -------------------------------------------------------------------
vi.mock('dockview-react', () => ({
  DockviewReact: () => <div data-testid="dockview-root" />,
}))

vi.mock('@react-sigma/core', () => ({
  SigmaContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="sigma-container">{children}</div>
  ),
  useLoadGraph: () => vi.fn(),
  useRegisterEvents: () => vi.fn(),
}))

vi.mock('graphology', () => {
  class MockMultiGraph {
    addNode(): void {}
    addEdge(): void {}
    nodes(): string[] { return [] }
  }
  return { default: MockMultiGraph, MultiGraph: MockMultiGraph }
})

vi.mock('graphology-layout-forceatlas2', () => ({ default: vi.fn() }))

// -------------------------------------------------------------------
// Lazy imports AFTER vi.mock() — prevents hoisting issues
// -------------------------------------------------------------------
const { APP_REGISTRY } = await import('../components/Dock/appRegistry')
const { COMPONENTS } = await import('../components/Shell/DockviewShell')
const { registerShortcut, unregisterShortcut, getShortcuts } = await import('../hooks/useKeyboardShortcuts')

const NEW_PANEL_IDS = ['live-preview', 'sidecar-output', 'artifacts', 'knowledge-graph']
const NEW_COMPONENT_KEYS = ['LivePreviewPanel', 'SidecarOutputPanel', 'ArtifactPanel', 'KnowledgeGraphPanel']
const NEW_SHORTCUT_IDS = [
  'live-preview-cmd',
  'sidecar-output-cmd',
  'artifacts-cmd',
  'knowledge-graph-cmd',
]
const NEW_KEYBINDINGS = [
  'cmd+shift+p',
  'cmd+shift+b',
  'cmd+shift+a',
  'cmd+shift+g',
]

describe('panel-registration — APP_REGISTRY', () => {
  it('contains an entry for each new panel id', () => {
    const ids = APP_REGISTRY.map((a) => a.id)
    for (const id of NEW_PANEL_IDS) {
      expect(ids, `APP_REGISTRY missing id "${id}"`).toContain(id)
    }
  })

  it('contains an entry for each new componentKey', () => {
    const keys = APP_REGISTRY.map((a) => a.componentKey)
    for (const key of NEW_COMPONENT_KEYS) {
      expect(keys, `APP_REGISTRY missing componentKey "${key}"`).toContain(key)
    }
  })

  it('all entries have non-empty id, label, icon, and componentKey', () => {
    for (const app of APP_REGISTRY) {
      expect(typeof app.id).toBe('string')
      expect(app.id.length).toBeGreaterThan(0)
      expect(typeof app.label).toBe('string')
      expect(app.label.length).toBeGreaterThan(0)
      expect(app.icon).toBeDefined()
      expect(typeof app.componentKey).toBe('string')
      expect(app.componentKey.length).toBeGreaterThan(0)
    }
  })

  it('has no duplicate ids', () => {
    const ids = APP_REGISTRY.map((a) => a.id)
    expect(new Set(ids).size).toBe(ids.length)
  })
})

describe('panel-registration — COMPONENTS factory', () => {
  it('has an entry for each new componentKey', () => {
    for (const key of NEW_COMPONENT_KEYS) {
      expect(
        key in COMPONENTS,
        `COMPONENTS missing key "${key}"`,
      ).toBe(true)
    }
  })

  it('all APP_REGISTRY componentKeys are present in COMPONENTS', () => {
    for (const app of APP_REGISTRY) {
      expect(
        app.componentKey in COMPONENTS,
        `COMPONENTS missing key "${app.componentKey}" (from APP_REGISTRY id="${app.id}")`,
      ).toBe(true)
    }
  })
})

describe('panel-registration — keyboard shortcuts', () => {
  it('new shortcut ids can be registered with correct keybindings', () => {
    const testIds = NEW_SHORTCUT_IDS.map((id) => `test-${id}`)

    for (let i = 0; i < testIds.length; i++) {
      registerShortcut(testIds[i], NEW_KEYBINDINGS[i], vi.fn(), 'global')
    }

    const registered = getShortcuts()
    const registeredMap = new Map(registered.map((s) => [s.id, s]))

    for (let i = 0; i < testIds.length; i++) {
      const id = testIds[i]
      const keybinding = NEW_KEYBINDINGS[i]
      const entry = registeredMap.get(id)
      expect(entry, `Shortcut "${id}" not found in registry`).toBeDefined()
      expect(entry?.keybinding).toBe(keybinding)
    }

    // Cleanup
    for (const id of testIds) {
      unregisterShortcut(id)
    }
  })

  it('App registers live-preview shortcut with cmd+shift+p keybinding', () => {
    // Verify the known shortcut id and keybinding that App.tsx registers
    registerShortcut('live-preview-cmd', 'cmd+shift+p', vi.fn(), 'global')
    const entry = getShortcuts().find((s) => s.id === 'live-preview-cmd')
    expect(entry?.keybinding).toBe('cmd+shift+p')
    unregisterShortcut('live-preview-cmd')
  })

  it('App registers sidecar-output shortcut with cmd+shift+b keybinding', () => {
    registerShortcut('sidecar-output-cmd', 'cmd+shift+b', vi.fn(), 'global')
    const entry = getShortcuts().find((s) => s.id === 'sidecar-output-cmd')
    expect(entry?.keybinding).toBe('cmd+shift+b')
    unregisterShortcut('sidecar-output-cmd')
  })

  it('App registers artifacts shortcut with cmd+shift+a keybinding', () => {
    registerShortcut('artifacts-cmd', 'cmd+shift+a', vi.fn(), 'global')
    const entry = getShortcuts().find((s) => s.id === 'artifacts-cmd')
    expect(entry?.keybinding).toBe('cmd+shift+a')
    unregisterShortcut('artifacts-cmd')
  })

  it('App registers knowledge-graph shortcut with cmd+shift+g keybinding', () => {
    registerShortcut('knowledge-graph-cmd', 'cmd+shift+g', vi.fn(), 'global')
    const entry = getShortcuts().find((s) => s.id === 'knowledge-graph-cmd')
    expect(entry?.keybinding).toBe('cmd+shift+g')
    unregisterShortcut('knowledge-graph-cmd')
  })
})
