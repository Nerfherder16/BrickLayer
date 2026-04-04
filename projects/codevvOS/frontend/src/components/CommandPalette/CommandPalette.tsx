import React, { useState, useCallback, useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { getShortcuts } from '@/hooks/useKeyboardShortcuts'
import { APP_REGISTRY } from '@/components/Dock/appRegistry'

interface CommandItem {
  id: string
  label: string
  keybinding?: string
  handler: () => void
}

function buildCommands(): CommandItem[] {
  const appCommands: CommandItem[] = APP_REGISTRY.map(app => ({
    id: `app-${app.id}`,
    label: `Open ${app.label}`,
    handler: () => {
      window.dispatchEvent(new CustomEvent('codevvos:open-app', { detail: { appId: app.id } }))
    },
  }))

  const shortcutCommands: CommandItem[] = getShortcuts()
    .filter(s => s.context === 'global' && s.label)
    .map(s => ({
      id: `shortcut-${s.id}`,
      label: s.label!,
      keybinding: s.keybinding,
      handler: s.handler,
    }))

  return [...appCommands, ...shortcutCommands]
}

function filterCommands(commands: CommandItem[], query: string): CommandItem[] {
  if (!query.trim()) return commands
  const q = query.toLowerCase()
  return commands.filter(cmd => cmd.label.toLowerCase().includes(q))
}

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
}

export default function CommandPalette({ isOpen, onClose }: CommandPaletteProps): JSX.Element {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)

  const commands = buildCommands()
  const filtered = filterCommands(commands, query)

  // Reset state when opening
  useEffect(() => {
    if (isOpen) {
      setQuery('')
      setSelectedIndex(-1)
    }
  }, [isOpen])

  const handleExecute = useCallback(
    (item: CommandItem) => {
      item.handler()
      onClose()
    },
    [onClose],
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
        return
      }

      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(prev => Math.min(prev + 1, filtered.length - 1))
        return
      }

      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(prev => Math.max(prev - 1, 0))
        return
      }

      if (e.key === 'Enter') {
        e.preventDefault()
        const idx = selectedIndex >= 0 ? selectedIndex : 0
        if (filtered[idx]) {
          handleExecute(filtered[idx])
        }
        return
      }
    },
    [filtered, selectedIndex, onClose, handleExecute],
  )

  const handleBackdropClick = useCallback(() => {
    onClose()
  }, [onClose])

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          key="command-palette-backdrop"
          data-testid="command-palette-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          onClick={handleBackdropClick}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            backdropFilter: 'blur(8px)',
            backgroundColor: 'color-mix(in srgb, var(--color-base) 70%, transparent)',
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'center',
            paddingTop: '10vh',
            zIndex: 1000,
          }}
        >
          <motion.div
            key="command-palette-modal"
            data-testid="command-palette-modal"
            initial={{ opacity: 0, scale: 0.95, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -8 }}
            transition={{ duration: 0.15 }}
            onClick={(e: React.MouseEvent) => e.stopPropagation()}
            style={{
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border-default)',
              borderRadius: 'var(--radius-lg)',
              boxShadow: 'var(--shadow-5)',
              width: '100%',
              maxWidth: '560px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                padding: 'var(--space-3) var(--space-4)',
                borderBottom: '1px solid var(--color-border-subtle)',
              }}
            >
              <input
                ref={inputRef}
                data-testid="command-palette-input"
                autoFocus
                value={query}
                onChange={e => {
                  setQuery(e.target.value)
                  setSelectedIndex(-1)
                }}
                onKeyDown={handleKeyDown}
                placeholder="Search commands..."
                style={{
                  width: '100%',
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: 'var(--color-text-primary)',
                  fontSize: 'var(--text-base)',
                  fontFamily: 'var(--font-sans)',
                }}
              />
            </div>

            <ul
              role="listbox"
              style={{
                listStyle: 'none',
                margin: 0,
                padding: 'var(--space-1) 0',
                maxHeight: '320px',
                overflowY: 'auto',
              }}
            >
              {filtered.length === 0 ? (
                <li
                  style={{
                    padding: 'var(--space-4)',
                    color: 'var(--color-text-tertiary)',
                    fontSize: 'var(--text-sm)',
                    textAlign: 'center',
                  }}
                >
                  No commands found
                </li>
              ) : (
                filtered.map((cmd, i) => (
                  <li
                    key={cmd.id}
                    role="option"
                    aria-selected={i === selectedIndex}
                    onClick={() => handleExecute(cmd)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: 'var(--space-2) var(--space-4)',
                      cursor: 'pointer',
                      background:
                        i === selectedIndex
                          ? 'var(--color-accent-muted)'
                          : 'transparent',
                      color: 'var(--color-text-primary)',
                      fontSize: 'var(--text-sm)',
                      transition: 'background var(--duration-fast)',
                    }}
                    onMouseEnter={() => setSelectedIndex(i)}
                  >
                    <span>{cmd.label}</span>
                    {cmd.keybinding && (
                      <kbd
                        style={{
                          fontSize: 'var(--text-xs)',
                          color: 'var(--color-text-tertiary)',
                          background: 'var(--color-surface-3)',
                          border: '1px solid var(--color-border-subtle)',
                          borderRadius: 'var(--radius-sm)',
                          padding: '0 var(--space-1)',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {cmd.keybinding}
                      </kbd>
                    )}
                  </li>
                ))
              )}
            </ul>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
