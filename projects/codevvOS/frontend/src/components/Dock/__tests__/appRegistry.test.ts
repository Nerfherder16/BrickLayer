import { describe, it, expect } from 'vitest'
import { APP_REGISTRY } from '../appRegistry'

describe('APP_REGISTRY', () => {
  it('is an array with exactly 8 entries', () => {
    expect(Array.isArray(APP_REGISTRY)).toBe(true)
    expect(APP_REGISTRY).toHaveLength(8)
  })

  it('each entry has id, label, icon, and componentKey', () => {
    for (const app of APP_REGISTRY) {
      expect(typeof app.id).toBe('string')
      expect(app.id.length).toBeGreaterThan(0)
      expect(typeof app.label).toBe('string')
      expect(app.label.length).toBeGreaterThan(0)
      expect(app.icon).not.toBeNull()
      expect(app.icon).not.toBeUndefined()
      expect(typeof app.componentKey).toBe('string')
      expect(app.componentKey.length).toBeGreaterThan(0)
    }
  })

  it('has no duplicate id values', () => {
    const ids = APP_REGISTRY.map((a) => a.id)
    const uniqueIds = new Set(ids)
    expect(uniqueIds.size).toBe(ids.length)
  })

  it('has the expected componentKey values', () => {
    const keys = APP_REGISTRY.map((a) => a.componentKey)
    expect(keys).toContain('TerminalPanel')
    expect(keys).toContain('FileTreePanel')
    expect(keys).toContain('AIChatPanel')
    expect(keys).toContain('SettingsPanel')
    expect(keys).toContain('LivePreviewPanel')
    expect(keys).toContain('SidecarOutputPanel')
    expect(keys).toContain('ArtifactPanel')
    expect(keys).toContain('KnowledgeGraphPanel')
  })
})
