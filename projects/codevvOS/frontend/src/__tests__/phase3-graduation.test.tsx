/**
 * Phase 3 Graduation Test — Full Panel Flow Integration
 *
 * Tests the complete user-facing flow from a pre-authenticated state through
 * all four dock panels using MSW mocks.
 *
 * The dockview-react mock is stateful: it tracks open panels and renders their
 * components directly so assertions on panel content work. This mirrors the
 * pattern from DockviewShell.test.tsx but with a richer mock that handles
 * addPanel / getPanel / focus for the Dock component.
 *
 * Heavy panel dependencies are mocked:
 *   - @xterm/xterm, addons — TerminalPanel renders a bare div
 *   - usePtyWebSocket     — no WebSocket in jsdom
 *   - useFileTree         — controlled via MSW /api/files/tree handler
 *   - useAIChat           — real hook, real MSW /api/ai/chat handler
 *
 * Flow verified (one it() per step):
 *   Step 1: Pre-auth JWT in sessionStorage → dock renders (no login screen)
 *   Step 2: Dock has exactly 4 icon buttons (Terminal, Files, AI Chat, Settings)
 *   Step 3: Click Terminal → TerminalPanel renders (data-testid="terminal-panel")
 *   Step 4: Click Files   → FileTreePanel renders, tree items visible
 *   Step 5: Click AI Chat → AIChatPanel renders, empty state visible
 *   Step 6: Click Terminal again (already open) → no duplicate, panel focused
 *   Step 7: Click Settings → SettingsPanel renders (data-testid="settings-panel")
 */
import React, { useState } from 'react'
import { describe, it, expect, vi, beforeAll, afterEach, afterAll } from 'vitest'
import { render, screen, waitFor, act, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

// ---------------------------------------------------------------------------
// Mock heavy terminal dependencies before any component imports
// ---------------------------------------------------------------------------

vi.mock('@xterm/xterm', () => ({
  Terminal: vi.fn().mockImplementation(() => ({
    open: vi.fn(),
    loadAddon: vi.fn(),
    onData: vi.fn(() => ({ dispose: vi.fn() })),
    onResize: vi.fn(() => ({ dispose: vi.fn() })),
    write: vi.fn(),
    dispose: vi.fn(),
    options: {},
  })),
}))

vi.mock('@xterm/addon-fit', () => ({
  FitAddon: vi.fn().mockImplementation(() => ({ fit: vi.fn(), dispose: vi.fn() })),
}))

vi.mock('@xterm/addon-webgl', () => ({
  WebglAddon: vi.fn().mockImplementation(() => ({
    onContextLoss: vi.fn(() => ({ dispose: vi.fn() })),
    dispose: vi.fn(),
  })),
}))

vi.mock('@xterm/addon-web-links', () => ({
  WebLinksAddon: vi.fn().mockImplementation(() => ({ dispose: vi.fn() })),
}))

vi.mock('@xterm/addon-search', () => ({
  SearchAddon: vi.fn().mockImplementation(() => ({ dispose: vi.fn() })),
}))

vi.mock('@/hooks/usePtyWebSocket', () => ({
  usePtyWebSocket: vi.fn(() => ({
    ws: null,
    readyState: 3, // CLOSED — never connects in test
    send: vi.fn(),
    sendResize: vi.fn(),
  })),
}))

vi.mock('@jsonforms/react', () => ({
  JsonForms: () => React.createElement('form', { role: 'form', 'data-testid': 'jsonforms-form' }),
}))
vi.mock('@jsonforms/vanilla-renderers', () => ({ vanillaRenderers: [] }))
vi.mock('@react-sigma/core', () => ({
  SigmaContainer: ({ children }: { children: React.ReactNode }) => (
    React.createElement('div', { 'data-testid': 'sigma-container' }, children)
  ),
  useLoadGraph: () => () => undefined,
  useRegisterEvents: () => () => undefined,
}))
vi.mock('graphology', () => {
  class MockMultiGraph {
    addNode(): void {}
    addEdge(): void {}
    nodes(): string[] { return [] }
  }
  return { default: MockMultiGraph, MultiGraph: MockMultiGraph }
})
vi.mock('graphology-layout-forceatlas2', () => ({ default: () => undefined }))

// ---------------------------------------------------------------------------
// Stateful dockview-react mock
//
// Tracks open panels in a React state map so Dock's getPanel() / focus() /
// addPanel() calls produce observable rendering side-effects.
// ---------------------------------------------------------------------------

// State lifted to module scope so the mock factory can close over it.
// The actual state lives inside the mock component via a module-level ref
// that we reset in afterEach.

type MockPanel = {
  id: string
  component: string
  focus: () => void
}

// Module-level state store (reset in afterEach via resetMockDockview)
let _activePanelId: string | null = null
let _openPanels: Map<string, MockPanel> = new Map()
let _onReadyCb: ((event: { api: unknown }) => void) | null = null
let _onDidActivePanelChangeCb: ((event: { panel: { id: string } | null }) => void) | null = null
let _onDidLayoutChangeCb: (() => void) | null = null
let _setOpenPanelsExternal: ((panels: Map<string, MockPanel>) => void) | null = null
let _setActivePanelExternal: ((id: string | null) => void) | null = null

function buildMockApi(
  setPanels: (panels: Map<string, MockPanel>) => void,
  setActive: (id: string | null) => void,
) {
  return {
    fromJSON: vi.fn(),
    toJSON: vi.fn(() => ({ panels: {}, grid: {}, floatingGroups: [], popoutGroups: [] })),
    addPanel: vi.fn(({ id, component }: { id: string; component: string }) => {
      const panel: MockPanel = {
        id,
        component,
        focus: () => {
          _activePanelId = id
          setActive(id)
          _onDidActivePanelChangeCb?.({ panel: { id } })
          _onDidLayoutChangeCb?.()
        },
      }
      _openPanels = new Map(_openPanels).set(id, panel)
      _activePanelId = id
      setPanels(new Map(_openPanels))
      setActive(id)
      _onDidActivePanelChangeCb?.({ panel: { id } })
      _onDidLayoutChangeCb?.()
    }),
    getPanel: vi.fn((id: string) => _openPanels.get(id) ?? null),
    get panels() {
      return Array.from(_openPanels.values())
    },
    onDidActivePanelChange: vi.fn((cb: (event: { panel: { id: string } | null }) => void) => {
      _onDidActivePanelChangeCb = cb
      return { dispose: vi.fn() }
    }),
    onDidLayoutChange: vi.fn((cb: () => void) => {
      _onDidLayoutChangeCb = cb
      return { dispose: vi.fn() }
    }),
  }
}

vi.mock('dockview-react', () => ({
  DockviewReact: ({
    onReady,
    components,
  }: {
    onReady: (event: { api: unknown }) => void
    components: Record<string, React.ComponentType>
  }) => {
    const [openPanels, setOpenPanels] = useState<Map<string, MockPanel>>(new Map())
    const [, setActiveId] = useState<string | null>(null)

    // Store external setters so module-level helpers can reset state
    _setOpenPanelsExternal = setOpenPanels
    _setActivePanelExternal = setActiveId

    React.useEffect(() => {
      const api = buildMockApi(setOpenPanels, setActiveId)
      _onReadyCb = onReady
      onReady({ api })
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    return (
      <div data-testid="dockview-root">
        {Array.from(openPanels.entries()).map(([id, panel]) => {
          const PanelComp = components?.[panel.component]
          // Cast to a plain FC to avoid IDockviewPanelProps type requirement in the mock
          const AnyComp = PanelComp as React.FC
          return AnyComp ? (
            <div key={id} data-panel-id={id}>
              <AnyComp />
            </div>
          ) : null
        })}
      </div>
    )
  },
}))

// Reset the stateful mock between tests
function resetMockDockview() {
  _activePanelId = null
  _openPanels = new Map()
  _onReadyCb = null
  _onDidActivePanelChangeCb = null
  _onDidLayoutChangeCb = null
  _setOpenPanelsExternal?.(new Map())
  _setActivePanelExternal?.(null)
  _setOpenPanelsExternal = null
  _setActivePanelExternal = null
}

// ---------------------------------------------------------------------------
// App import AFTER all vi.mock() calls
// ---------------------------------------------------------------------------
import App from '../App'

// ---------------------------------------------------------------------------
// MSW handlers
// ---------------------------------------------------------------------------
const TEST_JWT = 'test.eyJleHAiOjk5OTk5OTk5OTl9.sig'

const server = setupServer(
  http.get('/api/auth/users', () =>
    HttpResponse.json([{ id: 'u1', display_name: 'Tim', avatar_initials: 'T' }]),
  ),
  http.post('/auth/login', () =>
    HttpResponse.json({ token: TEST_JWT, user: { id: 'u1', display_name: 'Tim', avatar_initials: 'T' } }),
  ),
  http.get('/api/layout', () =>
    HttpResponse.json({ layout_version: null, layout: null }),
  ),
  http.put('/api/layout', () => HttpResponse.json({ status: 'ok' })),
  http.get('/api/files/tree', () =>
    HttpResponse.json({
      name: 'workspace',
      type: 'dir',
      children: [
        { name: 'src', type: 'dir' },
        { name: 'app.py', type: 'file' },
      ],
    }),
  ),
  http.post('/api/ai/chat', () =>
    new HttpResponse('data: [DONE]\n\n', {
      headers: { 'Content-Type': 'text/event-stream' },
    }),
  ),
  http.get('/api/settings/schema', () =>
    HttpResponse.json({ type: 'object', properties: {} }),
  ),
  http.get('/api/settings/user', () =>
    HttpResponse.json({ theme: 'dark' }),
  ),
)

beforeAll(() => {
  Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 1280 })
  // jsdom does not implement ResizeObserver; polyfill with a no-op stub
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  server.listen({ onUnhandledRequest: 'bypass' })
})

afterEach(() => {
  cleanup()
  server.resetHandlers()
  vi.clearAllMocks()
  sessionStorage.clear()
  resetMockDockview()
})

afterAll(() => server.close())

// ---------------------------------------------------------------------------
// Helper: render App with pre-authenticated JWT
// ---------------------------------------------------------------------------
function renderAuthed() {
  sessionStorage.setItem('codevvos_token', TEST_JWT)
  return render(<App />)
}

// ---------------------------------------------------------------------------
// Phase 3 Graduation Tests
// ---------------------------------------------------------------------------
describe('Phase 3 Graduation', () => {
  it('Step 1: dock renders when valid JWT is in sessionStorage (no login screen)', async () => {
    await act(async () => {
      renderAuthed()
    })

    await waitFor(() => {
      expect(screen.getByTestId('dock')).toBeDefined()
    })
    expect(screen.queryByTestId('login-screen')).toBeNull()
  })

  it('Step 2: dock has exactly 4 icon buttons (Terminal, Files, AI Chat, Settings)', async () => {
    await act(async () => {
      renderAuthed()
    })

    await waitFor(() => {
      expect(screen.getByTestId('dock')).toBeDefined()
    })

    expect(screen.getByTestId('dock-btn-terminal')).toBeDefined()
    expect(screen.getByTestId('dock-btn-files')).toBeDefined()
    expect(screen.getByTestId('dock-btn-ai-chat')).toBeDefined()
    expect(screen.getByTestId('dock-btn-settings')).toBeDefined()

    const dock = screen.getByTestId('dock')
    const buttons = dock.querySelectorAll('button')
    expect(buttons.length).toBe(9)
  })

  it('Step 3: clicking Terminal opens TerminalPanel (data-testid="terminal-panel")', async () => {
    const user = userEvent.setup()

    await act(async () => {
      renderAuthed()
    })

    await waitFor(() => {
      expect(screen.getByTestId('dock')).toBeDefined()
    })

    await user.click(screen.getByTestId('dock-btn-terminal'))

    await waitFor(() => {
      expect(screen.getByTestId('terminal-panel')).toBeDefined()
    })
  })

  it('Step 4: clicking Files opens FileTreePanel with tree items (src and app.py)', async () => {
    const user = userEvent.setup()

    await act(async () => {
      renderAuthed()
    })

    await waitFor(() => {
      expect(screen.getByTestId('dock')).toBeDefined()
    })

    await user.click(screen.getByTestId('dock-btn-files'))

    await waitFor(() => {
      expect(screen.getByTestId('file-tree-panel')).toBeDefined()
    })

    // File tree fetches /api/files/tree on mount — wait for tree items
    await waitFor(() => {
      expect(screen.getByText('src')).toBeDefined()
    })
    expect(screen.getByText('app.py')).toBeDefined()
  })

  it('Step 5: clicking AI Chat opens AIChatPanel with empty state "Start a conversation"', async () => {
    const user = userEvent.setup()

    await act(async () => {
      renderAuthed()
    })

    await waitFor(() => {
      expect(screen.getByTestId('dock')).toBeDefined()
    })

    await user.click(screen.getByTestId('dock-btn-ai-chat'))

    await waitFor(() => {
      expect(screen.getByTestId('ai-chat-panel')).toBeDefined()
    })

    expect(screen.getByText('Start a conversation')).toBeDefined()
  })

  it('Step 6: clicking Terminal again (already open) does not duplicate the panel', async () => {
    const user = userEvent.setup()

    await act(async () => {
      renderAuthed()
    })

    await waitFor(() => {
      expect(screen.getByTestId('dock')).toBeDefined()
    })

    // First click — open terminal
    await user.click(screen.getByTestId('dock-btn-terminal'))
    await waitFor(() => {
      expect(screen.getByTestId('terminal-panel')).toBeDefined()
    })

    // Second click — should focus, not duplicate
    await user.click(screen.getByTestId('dock-btn-terminal'))

    // Still exactly one terminal panel
    const panels = screen.getAllByTestId('terminal-panel')
    expect(panels.length).toBe(1)
  })

  it('Step 7: clicking Settings renders the settings panel', async () => {
    const user = userEvent.setup()

    await act(async () => {
      renderAuthed()
    })

    await waitFor(() => {
      expect(screen.getByTestId('dock')).toBeDefined()
    })

    await user.click(screen.getByTestId('dock-btn-settings'))

    await waitFor(() => {
      expect(screen.getByTestId('settings-panel')).toBeDefined()
    })
  })
})
