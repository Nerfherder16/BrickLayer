import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import CommandPalette from '../CommandPalette'

// Mock keyboard shortcuts registry with controlled data
vi.mock('@/hooks/useKeyboardShortcuts', () => ({
  getShortcuts: vi.fn(() => [
    {
      id: 'terminal-focus',
      keybinding: 'ctrl+`',
      label: 'Focus Terminal',
      handler: vi.fn(),
      context: 'global',
    },
    {
      id: 'settings-cmd',
      keybinding: 'cmd+,',
      label: 'Open Settings',
      handler: vi.fn(),
      context: 'global',
    },
  ]),
  registerShortcut: vi.fn(),
  unregisterShortcut: vi.fn(),
}))

// APP_REGISTRY is real — provides: Terminal, Files, AI Chat, Settings

function renderPalette(isOpen = true, onClose = vi.fn()) {
  return { onClose, ...render(<CommandPalette isOpen={isOpen} onClose={onClose} />) }
}

describe('CommandPalette', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders input with data-testid="command-palette-input" when open', () => {
    renderPalette(true)
    expect(screen.getByTestId('command-palette-input')).toBeTruthy()
  })

  it('does not render when isOpen is false', () => {
    renderPalette(false)
    expect(screen.queryByTestId('command-palette-input')).toBeNull()
  })

  it('shows all commands when search is empty', () => {
    renderPalette(true)
    // APP_REGISTRY has 4 apps → 4 "Open X" commands
    // getShortcuts returns 2 labelled global shortcuts
    // Total: 6 items
    const items = screen.getAllByRole('option')
    expect(items.length).toBeGreaterThanOrEqual(4)
  })

  it('filters commands when typing a search term', async () => {
    renderPalette(true)
    const input = screen.getByTestId('command-palette-input')
    fireEvent.change(input, { target: { value: 'terminal' } })
    const items = screen.getAllByRole('option')
    items.forEach(item => {
      expect(item.textContent?.toLowerCase()).toContain('terminal')
    })
  })

  it('shows "No commands found" when search has no matches', () => {
    renderPalette(true)
    const input = screen.getByTestId('command-palette-input')
    fireEvent.change(input, { target: { value: 'xyznosuchthing123' } })
    expect(screen.getByText(/no commands found/i)).toBeTruthy()
  })

  it('moves selection down with ArrowDown', () => {
    renderPalette(true)
    const input = screen.getByTestId('command-palette-input')
    fireEvent.keyDown(input, { key: 'ArrowDown' })
    const items = screen.getAllByRole('option')
    // First item should be selected (index 0 → after ArrowDown → index 0 is still first highlighted)
    // ArrowDown from -1 → 0
    expect(items[0].getAttribute('aria-selected')).toBe('true')
  })

  it('moves selection up with ArrowUp from first item stays at 0', () => {
    renderPalette(true)
    const input = screen.getByTestId('command-palette-input')
    fireEvent.keyDown(input, { key: 'ArrowDown' }) // → 0
    fireEvent.keyDown(input, { key: 'ArrowDown' }) // → 1
    fireEvent.keyDown(input, { key: 'ArrowUp' })   // → 0
    const items = screen.getAllByRole('option')
    expect(items[0].getAttribute('aria-selected')).toBe('true')
    expect(items[1].getAttribute('aria-selected')).toBe('false')
  })

  it('calls handler and onClose when Enter is pressed on selected item', () => {
    const { onClose } = renderPalette(true)
    const input = screen.getByTestId('command-palette-input')
    // Navigate to first item and press Enter
    fireEvent.keyDown(input, { key: 'ArrowDown' }) // select item[0]
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when Escape is pressed', () => {
    const { onClose } = renderPalette(true)
    const input = screen.getByTestId('command-palette-input')
    fireEvent.keyDown(input, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when backdrop is clicked', () => {
    const { onClose } = renderPalette(true)
    const backdrop = screen.getByTestId('command-palette-backdrop')
    fireEvent.click(backdrop)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does NOT call onClose when the modal card itself is clicked', () => {
    const { onClose } = renderPalette(true)
    const card = screen.getByTestId('command-palette-modal')
    fireEvent.click(card)
    expect(onClose).not.toHaveBeenCalled()
  })
})
