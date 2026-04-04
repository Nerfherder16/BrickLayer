import React from 'react'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import LivePreviewPanel from '../components/Panels/LivePreviewPanel'
import * as previewStoreModule from '../stores/previewStore'

// Mock the previewStore
vi.mock('../stores/previewStore')

const mockRefresh = vi.fn()

function makeStoreReturn(
  overrides: Partial<ReturnType<typeof previewStoreModule.usePreviewStore>> = {},
): ReturnType<typeof previewStoreModule.usePreviewStore> {
  return {
    previewPort: 5173,
    refreshCount: 0,
    previewUrl: 'http://localhost:5173?_r=0',
    setPort: vi.fn(),
    refresh: mockRefresh,
    ...overrides,
  }
}

// EventSource mock
class MockEventSource {
  static instance: MockEventSource | null = null
  url: string
  onmessage: ((ev: MessageEvent) => void) | null = null
  addEventListener: ReturnType<typeof vi.fn>
  removeEventListener: ReturnType<typeof vi.fn>
  close: ReturnType<typeof vi.fn>

  constructor(url: string) {
    this.url = url
    this.addEventListener = vi.fn()
    this.removeEventListener = vi.fn()
    this.close = vi.fn()
    MockEventSource.instance = this
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  MockEventSource.instance = null
  vi.stubGlobal('EventSource', MockEventSource)
  vi.mocked(previewStoreModule.usePreviewStore).mockReturnValue(makeStoreReturn())
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('LivePreviewPanel', () => {
  it('should render iframe with data-testid="live-preview-iframe"', () => {
    render(<LivePreviewPanel />)
    expect(screen.getByTestId('live-preview-iframe')).toBeDefined()
  })

  it('should render iframe with src matching url from store', () => {
    vi.mocked(previewStoreModule.usePreviewStore).mockReturnValue(
      makeStoreReturn({ previewUrl: 'http://localhost:5173?_r=0' }),
    )
    render(<LivePreviewPanel />)
    const iframe = screen.getByTestId('live-preview-iframe') as HTMLIFrameElement
    expect(iframe.src).toBe('http://localhost:5173/?_r=0')
  })

  it('should render iframe with sandbox attribute (no allow-same-origin)', () => {
    render(<LivePreviewPanel />)
    const iframe = screen.getByTestId('live-preview-iframe') as HTMLIFrameElement
    const sandbox = iframe.getAttribute('sandbox') ?? ''
    expect(sandbox).toContain('allow-scripts')
    expect(sandbox).not.toContain('allow-same-origin')
  })

  it('should change iframe container width to 1440px when desktop viewport selected', () => {
    render(<LivePreviewPanel />)
    const btn = screen.getByTestId('viewport-1440')
    fireEvent.click(btn)
    const container = screen.getByTestId('iframe-container')
    expect(container.style.width).toBe('1440px')
  })

  it('should change iframe container width to 768px when tablet viewport selected', () => {
    render(<LivePreviewPanel />)
    const btn = screen.getByTestId('viewport-768')
    fireEvent.click(btn)
    const container = screen.getByTestId('iframe-container')
    expect(container.style.width).toBe('768px')
  })

  it('should change iframe container width to 375px when mobile viewport selected', () => {
    render(<LivePreviewPanel />)
    const btn = screen.getByTestId('viewport-375')
    fireEvent.click(btn)
    const container = screen.getByTestId('iframe-container')
    expect(container.style.width).toBe('375px')
  })

  it('should call refresh() from store when refresh button is clicked', () => {
    render(<LivePreviewPanel />)
    const refreshBtn = screen.getByTestId('refresh-button')
    fireEvent.click(refreshBtn)
    expect(mockRefresh).toHaveBeenCalledTimes(1)
  })

  it('should show error overlay when iframe fires error', () => {
    render(<LivePreviewPanel />)
    const iframe = screen.getByTestId('live-preview-iframe')
    fireEvent.error(iframe)
    expect(screen.getByTestId('preview-error-overlay')).toBeDefined()
  })

  it('should not show error overlay initially', () => {
    render(<LivePreviewPanel />)
    expect(screen.queryByTestId('preview-error-overlay')).toBeNull()
  })

  it('should hide error overlay when retry button is clicked', () => {
    render(<LivePreviewPanel />)
    const iframe = screen.getByTestId('live-preview-iframe')
    fireEvent.error(iframe)
    const retryBtn = screen.getByTestId('error-retry-button')
    fireEvent.click(retryBtn)
    expect(screen.queryByTestId('preview-error-overlay')).toBeNull()
  })

  it('should set up EventSource on mount and close on unmount', () => {
    const { unmount } = render(<LivePreviewPanel />)
    expect(MockEventSource.instance).not.toBeNull()
    unmount()
    expect(MockEventSource.instance?.close).toHaveBeenCalled()
  })

  it('should call refresh() when preview-reload SSE event fires', () => {
    render(<LivePreviewPanel />)
    const es = MockEventSource.instance!
    // Find the preview-reload handler
    const addListenerCalls = es.addEventListener.mock.calls
    const reloadCall = addListenerCalls.find((c) => c[0] === 'preview-reload')
    expect(reloadCall).toBeDefined()
    // Simulate firing the event
    act(() => {
      reloadCall![1]({} as MessageEvent)
    })
    expect(mockRefresh).toHaveBeenCalled()
  })
})
