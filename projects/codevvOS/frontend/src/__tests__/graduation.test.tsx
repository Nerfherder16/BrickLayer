/**
 * Phase 2 Graduation Test — Full Shell Integration
 *
 * Tests the complete user-facing flow using MSW to mock all API calls.
 * dockview-react is mocked (same pattern as DockviewShell.test.tsx) because
 * it requires CSS layout capabilities that jsdom does not provide; the mock
 * calls onReady with a minimal stub API and renders WelcomePanel directly.
 * All other components (App, LoginScreen, DockviewShell, Dock) are real.
 *
 * Flow verified:
 *   1. App renders → LoginScreen visible ("CodeVV OS" in footer)
 *   2. GET /api/auth/users → Tim card renders
 *   3. Single user → auto-transitions to password phase
 *   4. Fill password "correct" → POST /auth/login → JWT stored → login()
 *   5. LoginScreen gone; dock visible
 *   6. DockviewShell mounts → GET /api/layout → null → WelcomePanel added
 *   7. WelcomePanel text "Welcome to CodeVV OS" visible
 *   8. Dock has at least one icon button
 *   9. Clicking the dock icon does not crash
 */
import React from 'react'
import { describe, it, expect, vi, beforeAll, afterEach, afterAll } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

// ---------------------------------------------------------------------------
// dockview-react mock — must be declared before vi.mock factory runs.
// Mirrors the pattern used in DockviewShell.test.tsx.
// ---------------------------------------------------------------------------
const mockDockviewApi = {
  fromJSON: vi.fn(),
  toJSON: vi.fn(() => ({ panels: {}, grid: {}, floatingGroups: [], popoutGroups: [] })),
  addPanel: vi.fn(),
  getPanel: vi.fn().mockReturnValue(null),
  panels: [],
  onDidLayoutChange: vi.fn().mockReturnValue({ dispose: vi.fn() }),
  onDidActivePanelChange: vi.fn().mockReturnValue({ dispose: vi.fn() }),
}

vi.mock('dockview-react', () => ({
  DockviewReact: ({
    onReady,
    components,
  }: {
    onReady: (event: { api: unknown }) => void
    components: Record<string, React.ComponentType>
  }) => {
    React.useEffect(() => {
      onReady({ api: mockDockviewApi })
    }, [onReady])
    const WelcomePanelComp = components?.WelcomePanel
    return (
      <div data-testid="dockview-root">
        {WelcomePanelComp ? <WelcomePanelComp /> : null}
      </div>
    )
  },
}))

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

// Static import AFTER vi.mock so App gets the mocked dockview-react
import App from '../App'

// ---------------------------------------------------------------------------
// MSW server — intercepts all real fetch calls in the components
// ---------------------------------------------------------------------------
const server = setupServer(
  http.get('/api/auth/users', () =>
    HttpResponse.json([{ id: 'u1', display_name: 'Tim', avatar_initials: 'T' }]),
  ),
  http.post('/auth/login', () =>
    HttpResponse.json({
      token: 'test.eyJleHAiOjk5OTk5OTk5OTl9.sig',
      user: { id: 'u1', display_name: 'Tim', avatar_initials: 'T' },
    }),
  ),
  http.get('/api/layout', () =>
    HttpResponse.json({ layout_version: null, layout: null }),
  ),
  http.put('/api/layout', () => HttpResponse.json({ status: 'ok' })),
)

beforeAll(() => {
  // jsdom defaults window.innerWidth to 0 → useBreakpoint returns isMobile:true.
  // Force desktop width so App renders DockviewShell + Dock.
  Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 1280 })
  server.listen({ onUnhandledRequest: 'bypass' })
})
afterEach(() => {
  server.resetHandlers()
  sessionStorage.clear()
  vi.clearAllMocks()
  mockDockviewApi.onDidLayoutChange.mockReturnValue({ dispose: vi.fn() })
  mockDockviewApi.onDidActivePanelChange.mockReturnValue({ dispose: vi.fn() })
  mockDockviewApi.getPanel.mockReturnValue(null)
  mockDockviewApi.toJSON.mockReturnValue({
    panels: {},
    grid: {},
    floatingGroups: [],
    popoutGroups: [],
  })
})
afterAll(() => server.close())

// ---------------------------------------------------------------------------
// Graduation test
// ---------------------------------------------------------------------------
describe('Phase 2 Graduation', () => {
  it('should complete the full shell login flow without crashing', async () => {
    const user = userEvent.setup()

    await act(async () => {
      render(<App />)
    })

    // Step 1: LoginScreen is visible — footer shows "CodeVV OS"
    expect(screen.getByText('CodeVV OS')).toBeDefined()

    // Step 2: Wait for Tim's user card (MSW serves GET /api/auth/users)
    // With exactly 1 user, LoginScreen auto-transitions to the password phase
    await waitFor(() => {
      expect(screen.getByText('Tim')).toBeDefined()
    })

    // Step 3: Single-user path — password input appears; fill and submit
    // (MSW serves POST /auth/login → JWT; useAuth.login() sets isAuthenticated: true)
    const passwordInput = await waitFor(() => screen.getByLabelText('Password'))
    await user.type(passwordInput, 'correct')
    const signInButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(signInButton)

    // Step 4: LoginScreen is gone; dock is visible
    await waitFor(() => {
      expect(screen.queryByTestId('login-screen')).toBeNull()
    })
    expect(screen.getByTestId('dock')).toBeDefined()

    // Step 5: DockviewShell mounts → onReady fires → GET /api/layout (null)
    //         → applyDefaultLayout → addPanel → WelcomePanel renders
    await waitFor(() => {
      expect(screen.getByText(/Welcome to CodeVV OS/)).toBeDefined()
    })

    // Step 6: Dock has at least one icon button
    const dock = screen.getByTestId('dock')
    const iconButtons = dock.querySelectorAll('button')
    expect(iconButtons.length).toBeGreaterThan(0)

    // Step 7: Click a dock icon — assert no crash (test passing = no unhandled errors)
    await user.click(iconButtons[0])
  })
})
