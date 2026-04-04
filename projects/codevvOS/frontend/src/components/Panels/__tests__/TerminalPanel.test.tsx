import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import TerminalPanel from '../TerminalPanel'
import type { IDockviewPanelProps } from 'dockview-react'

// Track addon load and open order
const callOrder: string[] = []

const mockTerminalInstance = {
  open: vi.fn((_el: HTMLElement) => {
    callOrder.push('open')
  }),
  loadAddon: vi.fn(() => {
    callOrder.push('loadAddon')
  }),
  onData: vi.fn(() => ({ dispose: vi.fn() })),
  onResize: vi.fn(() => ({ dispose: vi.fn() })),
  write: vi.fn(),
  dispose: vi.fn(),
  options: {},
}

const mockFitAddon = {
  fit: vi.fn(),
  dispose: vi.fn(),
}

const mockWebglAddon = {
  onContextLoss: vi.fn((_cb: () => void) => ({ dispose: vi.fn() })),
  dispose: vi.fn(),
}

const mockWebLinksAddon = {
  dispose: vi.fn(),
}

const mockSearchAddon = {
  dispose: vi.fn(),
}

vi.mock('@xterm/xterm', () => ({
  Terminal: vi.fn(() => mockTerminalInstance),
}))

vi.mock('@xterm/addon-fit', () => ({
  FitAddon: vi.fn(() => mockFitAddon),
}))

vi.mock('@xterm/addon-webgl', () => ({
  WebglAddon: vi.fn(() => mockWebglAddon),
}))

vi.mock('@xterm/addon-web-links', () => ({
  WebLinksAddon: vi.fn(() => mockWebLinksAddon),
}))

vi.mock('@xterm/addon-search', () => ({
  SearchAddon: vi.fn(() => mockSearchAddon),
}))

// Mock the usePtyWebSocket hook
vi.mock('@/hooks/usePtyWebSocket', () => ({
  usePtyWebSocket: vi.fn(() => ({
    ws: null,
    readyState: 3,
    send: vi.fn(),
    sendResize: vi.fn(),
  })),
}))

// Mock ResizeObserver
class MockResizeObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

const mockDockviewProps = {
  params: {},
  api: {} as IDockviewPanelProps['api'],
  containerApi: {} as IDockviewPanelProps['containerApi'],
} as IDockviewPanelProps

describe('TerminalPanel', () => {
  beforeEach(() => {
    callOrder.length = 0
    vi.clearAllMocks()
    vi.stubGlobal('ResizeObserver', MockResizeObserver)
    // Stub crypto.randomUUID
    vi.stubGlobal('crypto', {
      randomUUID: vi.fn(() => 'test-uuid-1234'),
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('should render container div with data-testid="terminal-panel"', () => {
    render(<TerminalPanel {...mockDockviewProps} />)
    expect(screen.getByTestId('terminal-panel')).toBeDefined()
  })

  it('should call Terminal constructor', async () => {
    const { Terminal } = await import('@xterm/xterm')
    render(<TerminalPanel {...mockDockviewProps} />)
    expect(Terminal).toHaveBeenCalled()
  })

  it('should call terminal.open() with a DOM element', () => {
    render(<TerminalPanel {...mockDockviewProps} />)
    expect(mockTerminalInstance.open).toHaveBeenCalledWith(expect.any(HTMLElement))
  })

  it('should call terminal.loadAddon() at least 2 times', () => {
    render(<TerminalPanel {...mockDockviewProps} />)
    expect(mockTerminalInstance.loadAddon.mock.calls.length).toBeGreaterThanOrEqual(2)
  })

  it('should call open() before any loadAddon() calls', () => {
    render(<TerminalPanel {...mockDockviewProps} />)

    const openIndex = callOrder.indexOf('open')
    const firstLoadAddonIndex = callOrder.indexOf('loadAddon')

    expect(openIndex).toBeGreaterThanOrEqual(0)
    expect(firstLoadAddonIndex).toBeGreaterThanOrEqual(0)
    expect(openIndex).toBeLessThan(firstLoadAddonIndex)
  })

  it('should call terminal.dispose() on unmount', () => {
    const { unmount } = render(<TerminalPanel {...mockDockviewProps} />)
    unmount()
    expect(mockTerminalInstance.dispose).toHaveBeenCalled()
  })
})
