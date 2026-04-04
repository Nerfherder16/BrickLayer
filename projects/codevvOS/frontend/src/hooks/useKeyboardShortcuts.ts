export type ShortcutContext = 'global' | 'editor' | 'terminal'

export interface ShortcutEntry {
  id: string
  keybinding: string
  label?: string
  handler: () => void
  context: ShortcutContext
}

/** Module-level singleton — persists across re-renders and component mounts. */
const registry = new Map<string, ShortcutEntry>()

function parseEventToKeybinding(e: KeyboardEvent): string {
  const isMac = navigator.platform.includes('Mac')
  const parts: string[] = []

  // Primary modifier: metaKey on Mac, ctrlKey on Linux/Win → both normalize to "cmd"
  if (isMac ? e.metaKey : e.ctrlKey) parts.push('cmd')
  // On Mac, ctrlKey is its own modifier distinct from cmd
  if (isMac && e.ctrlKey) parts.push('ctrl')
  if (e.altKey) parts.push('alt')
  if (e.shiftKey) parts.push('shift')

  const key = e.key.toLowerCase()
  if (!['control', 'shift', 'alt', 'meta'].includes(key)) {
    parts.push(key)
  }

  return parts.join('+')
}

function isContextActive(context: ShortcutContext): boolean {
  if (context === 'global') return true

  const active = document.activeElement
  if (!active || active === document.body) return false

  if (context === 'editor') {
    return (
      active.closest('[data-panel-type="editor"]') !== null ||
      active.closest('.monaco-editor') !== null ||
      active.hasAttribute('data-editor')
    )
  }

  if (context === 'terminal') {
    return active.closest('[data-panel-type="terminal"]') !== null
  }

  return false
}

function handleKeydown(e: KeyboardEvent): void {
  const pressed = parseEventToKeybinding(e)
  if (!pressed) return

  for (const entry of registry.values()) {
    if (entry.keybinding === pressed && isContextActive(entry.context)) {
      entry.handler()
    }
  }
}

window.addEventListener('keydown', handleKeydown)

/** Register a keyboard shortcut. Warns (does not throw) on duplicate keybinding + context. */
export function registerShortcut(
  id: string,
  keybinding: string,
  handler: () => void,
  context: ShortcutContext = 'global',
): void {
  const normalized = keybinding.toLowerCase()

  for (const entry of registry.values()) {
    if (entry.keybinding === normalized && entry.context === context && entry.id !== id) {
      console.warn(
        `[useKeyboardShortcuts] Duplicate keybinding "${keybinding}" in context "${context}" ` +
          `(existing id: "${entry.id}", new id: "${id}")`,
      )
    }
  }

  registry.set(id, { id, keybinding: normalized, handler, context })
}

/** Remove a registered shortcut by id. */
export function unregisterShortcut(id: string): void {
  registry.delete(id)
}

/** Return all currently registered shortcuts (used by CommandPalette). */
export function getShortcuts(): ShortcutEntry[] {
  return Array.from(registry.values())
}
