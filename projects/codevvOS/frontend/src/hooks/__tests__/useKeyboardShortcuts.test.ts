import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { registerShortcut, unregisterShortcut, getShortcuts } from '../useKeyboardShortcuts'

describe('useKeyboardShortcuts', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should call handler when registered global shortcut keydown is dispatched', () => {
    const handler = vi.fn()
    // jsdom: navigator.platform="" (not Mac), so ctrlKey → "cmd" in parser
    registerShortcut('test-global', 'cmd+shift+g', handler, 'global')

    window.dispatchEvent(
      new KeyboardEvent('keydown', { ctrlKey: true, shiftKey: true, key: 'g', bubbles: true }),
    )

    expect(handler).toHaveBeenCalledOnce()
    unregisterShortcut('test-global')
  })

  it('should not call handler after unregister', () => {
    const handler = vi.fn()
    registerShortcut('test-unreg', 'cmd+shift+u', handler, 'global')
    unregisterShortcut('test-unreg')

    window.dispatchEvent(
      new KeyboardEvent('keydown', { ctrlKey: true, shiftKey: true, key: 'u', bubbles: true }),
    )

    expect(handler).not.toHaveBeenCalled()
  })

  it('should warn on duplicate keybinding in same context without throwing', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined)
    const handler1 = vi.fn()
    const handler2 = vi.fn()

    registerShortcut('test-dup-1', 'shift+d', handler1, 'global')

    expect(() => {
      registerShortcut('test-dup-2', 'shift+d', handler2, 'global')
    }).not.toThrow()

    expect(warnSpy).toHaveBeenCalled()

    unregisterShortcut('test-dup-1')
    unregisterShortcut('test-dup-2')
  })

  it('should not fire editor context shortcut when document.body has focus', () => {
    const handler = vi.fn()
    registerShortcut('test-editor', 'shift+e', handler, 'editor')

    document.body.focus()

    window.dispatchEvent(
      new KeyboardEvent('keydown', { shiftKey: true, key: 'e', bubbles: true }),
    )

    expect(handler).not.toHaveBeenCalled()
    unregisterShortcut('test-editor')
  })

  it('getShortcuts returns all registered entries', () => {
    const handler = vi.fn()
    registerShortcut('test-list-1', 'shift+l', handler, 'global')
    registerShortcut('test-list-2', 'shift+m', handler, 'editor')

    const shortcuts = getShortcuts()
    const ids = shortcuts.map((s) => s.id)
    expect(ids).toContain('test-list-1')
    expect(ids).toContain('test-list-2')

    unregisterShortcut('test-list-1')
    unregisterShortcut('test-list-2')
  })
})
