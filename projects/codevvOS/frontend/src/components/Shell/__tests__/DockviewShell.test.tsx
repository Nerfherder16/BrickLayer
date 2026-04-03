import React from 'react'
import { describe, it, expect, vi, beforeAll, afterEach, afterAll, beforeEach } from 'vitest'
import { render, screen, act, waitFor, cleanup } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

// -------------------------------------------------------------------
// Shared mock state — must be declared before vi.mock() factory runs
// -------------------------------------------------------------------
const mockFromJSON = vi.fn()
const mockToJSON = vi.fn(() => ({ panels: {}, grid: {}, floatingGroups: [], popoutGroups: [] }))
const mockAddPanel = vi.fn()
let capturedLayoutChangeHandler: (() => void) | null = null

const mockDockviewApi = {
  fromJSON: mockFromJSON,
  toJSON: mockToJSON,
  addPanel: mockAddPanel,
  onDidLayoutChange: vi.fn().mockImplementation((cb: () => void) => {
    capturedLayoutChangeHandler = cb
    return { dispose: vi.fn() }
  }),
}

// -------------------------------------------------------------------
// Mock dockview-react — DockviewReact calls onReady with mockDockviewApi
// and renders the WelcomePanel component directly so assertions work
// -------------------------------------------------------------------
vi.mock('dockview-react', () => ({
  DockviewReact: ({
    onReady,
    components,
  }: {
    onReady: (api: unknown) => void
    components: Record<string, React.ComponentType>
  }) => {
    React.useEffect(() => {
      onReady(mockDockviewApi)
    }, [onReady])

    const WelcomePanel = components?.WelcomePanel
    return (
      <div data-testid="dockview-root">
        {WelcomePanel ? <WelcomePanel /> : null}
      </div>
    )
  },
}))

// -------------------------------------------------------------------
// Lazy import AFTER vi.mock() — prevents hoisting issues
// -------------------------------------------------------------------
const { LayoutContextProvider, LayoutContext } = await import('../../../contexts/LayoutContext')
const { default: DockviewShell } = await import('../DockviewShell')

// -------------------------------------------------------------------
// MSW server
// -------------------------------------------------------------------
const server = setupServer(
  http.get('/api/layout', () =>
    HttpResponse.json({ layout_version: null, layout: null }),
  ),
  http.put('/api/layout', () => HttpResponse.json({ ok: true })),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }))
afterEach(() => {
  cleanup()
  server.resetHandlers()
  vi.clearAllMocks()
  capturedLayoutChangeHandler = null
  // re-bind the mock implementation after clearAllMocks()
  mockDockviewApi.onDidLayoutChange.mockImplementation((cb: () => void) => {
    capturedLayoutChangeHandler = cb
    return { dispose: vi.fn() }
  })
  mockDockviewApi.toJSON.mockReturnValue({
    panels: {},
    grid: {},
    floatingGroups: [],
    popoutGroups: [],
  })
})
afterAll(() => server.close())

// -------------------------------------------------------------------
// Tests
// -------------------------------------------------------------------

describe('DockviewShell', () => {
  it('should render WelcomePanel text when layout is null', async () => {
    render(
      <LayoutContextProvider>
        <DockviewShell />
      </LayoutContextProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText(/Welcome to CodeVV OS/i)).toBeDefined()
    })
  })

  it('should not crash on corrupted layout data and still render WelcomePanel', async () => {
    server.use(
      http.get('/api/layout', () =>
        HttpResponse.json({ layout_version: 1, layout: 'not-a-valid-object' }),
      ),
    )

    expect(() =>
      render(
        <LayoutContextProvider>
          <DockviewShell />
        </LayoutContextProvider>,
      ),
    ).not.toThrow()

    await waitFor(() => {
      expect(screen.getByText(/Welcome to CodeVV OS/i)).toBeDefined()
    })
  })

  it('should debounce layout save and PUT /api/layout after 1000ms', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const putPayloads: unknown[] = []

    server.use(
      http.put('/api/layout', async ({ request }) => {
        putPayloads.push(await request.json())
        return HttpResponse.json({ ok: true })
      }),
    )

    render(
      <LayoutContextProvider>
        <DockviewShell />
      </LayoutContextProvider>,
    )

    // Wait for onReady to fire (capturedLayoutChangeHandler gets set in onDidLayoutChange mock)
    await waitFor(() => {
      expect(capturedLayoutChangeHandler).not.toBeNull()
    })

    // Trigger layout change
    act(() => {
      capturedLayoutChangeHandler!()
    })

    // PUT should NOT fire yet (debounce hasn't elapsed)
    expect(putPayloads).toHaveLength(0)

    // Advance clock by 1000ms and flush pending promises
    await act(async () => {
      vi.advanceTimersByTime(1000)
    })

    await waitFor(() => expect(putPayloads).toHaveLength(1))

    expect(putPayloads[0]).toMatchObject({ version: 1, layout: expect.anything() })

    vi.useRealTimers()
  })

  it('should store non-null dockviewApi in LayoutContext after onReady fires', async () => {
    let capturedContext: { dockviewApi: unknown } | null = null

    const ContextSpy = () => {
      capturedContext = React.useContext(LayoutContext) as { dockviewApi: unknown }
      return null
    }

    render(
      <LayoutContextProvider>
        <DockviewShell />
        <ContextSpy />
      </LayoutContextProvider>,
    )

    await waitFor(() => {
      expect(capturedContext?.dockviewApi).not.toBeNull()
    })
  })
})
