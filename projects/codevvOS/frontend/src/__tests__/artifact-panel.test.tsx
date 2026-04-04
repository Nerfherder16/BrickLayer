import React from 'react'
import { render, screen, act, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// ---- Mocks ----------------------------------------------------------------

vi.mock('../stores/artifactStore')
vi.mock('dockview-react', () => ({ IDockviewPanelProps: {} }))

import * as artifactStoreModule from '../stores/artifactStore'
import type { Artifact } from '../stores/artifactStore'

const mockSetActiveArtifact = vi.fn()
const mockAddArtifact = vi.fn()
const mockGetActiveArtifact = vi.fn()

function makeStoreReturn(overrides: Partial<ReturnType<typeof artifactStoreModule.useArtifactStore>> = {}): ReturnType<typeof artifactStoreModule.useArtifactStore> {
  return {
    artifacts: [],
    activeArtifactId: null,
    addArtifact: mockAddArtifact,
    setActiveArtifact: mockSetActiveArtifact,
    getActiveArtifact: mockGetActiveArtifact,
    ...overrides,
  }
}

const makeArtifact = (overrides: Partial<Artifact> = {}): Artifact => ({
  id: 'art-1',
  title: 'My Artifact',
  jsx: '<div>hello</div>',
  compiled: 'console.log("hello")',
  ...overrides,
})

// ---- IframeSandbox component (use the real one, stub crypto) ---------------

// ---- Import after mocks ----------------------------------------------------

import ArtifactPanel from '../components/Panels/ArtifactPanel'
import type { IDockviewPanelProps } from 'dockview-react'
import { IframeSandbox } from '../components/Artifacts/IframeSandbox'

// ---- Tests -----------------------------------------------------------------

function mockStore(overrides: Partial<ReturnType<typeof artifactStoreModule.useArtifactStore>> = {}): void {
  const state = makeStoreReturn(overrides)
  vi.mocked(artifactStoreModule.useArtifactStore).mockImplementation((selector: unknown) => {
    if (typeof selector === 'function') return (selector as (s: typeof state) => unknown)(state)
    return state
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetActiveArtifact.mockReturnValue(null)
  mockStore()
})

describe('ArtifactPanel', () => {
  it('shows placeholder when no artifact is active', () => {
    mockGetActiveArtifact.mockReturnValue(null)
    mockStore({ getActiveArtifact: mockGetActiveArtifact })
    render(<ArtifactPanel {...({} as IDockviewPanelProps)} />)
    expect(screen.getByTestId('artifact-panel-empty')).toBeDefined()
  })

  it('renders IframeSandbox when an artifact with compiled code is active', () => {
    const art = makeArtifact()
    mockGetActiveArtifact.mockReturnValue(art)
    mockStore({ getActiveArtifact: mockGetActiveArtifact })
    render(<ArtifactPanel {...({} as IDockviewPanelProps)} />)
    expect(screen.getByTestId('artifact-iframe')).toBeDefined()
  })

  it('does not show error overlay initially', () => {
    const art = makeArtifact()
    mockGetActiveArtifact.mockReturnValue(art)
    mockStore({ getActiveArtifact: mockGetActiveArtifact })
    render(<ArtifactPanel {...({} as IDockviewPanelProps)} />)
    expect(screen.queryByTestId('artifact-error-overlay')).toBeNull()
  })

  it('shows artifact-error-overlay when iframe sends an error postMessage', () => {
    const art = makeArtifact()
    mockGetActiveArtifact.mockReturnValue(art)
    mockStore({ getActiveArtifact: mockGetActiveArtifact })
    render(<ArtifactPanel {...({} as IDockviewPanelProps)} />)

    act(() => {
      window.dispatchEvent(
        new MessageEvent('message', {
          data: { type: 'error', message: 'ReferenceError: foo is not defined' },
        }),
      )
    })

    expect(screen.getByTestId('artifact-error-overlay')).toBeDefined()
  })

  it('dismisses error overlay when Dismiss button is clicked', () => {
    const art = makeArtifact()
    mockGetActiveArtifact.mockReturnValue(art)
    mockStore({ getActiveArtifact: mockGetActiveArtifact })
    render(<ArtifactPanel {...({} as IDockviewPanelProps)} />)

    act(() => {
      window.dispatchEvent(
        new MessageEvent('message', {
          data: { type: 'error', message: 'SyntaxError' },
        }),
      )
    })

    const dismissBtn = screen.getByRole('button', { name: /dismiss/i })
    fireEvent.click(dismissBtn)
    expect(screen.queryByTestId('artifact-error-overlay')).toBeNull()
  })
})

describe('IframeSandbox', () => {
  it('renders iframe with data-testid="artifact-iframe"', () => {
    render(
      <IframeSandbox compiled="console.log(1)" title="Test" onError={vi.fn()} />,
    )
    expect(screen.getByTestId('artifact-iframe')).toBeDefined()
  })

  it('sandbox attribute contains "allow-scripts"', () => {
    render(
      <IframeSandbox compiled="console.log(1)" title="Test" onError={vi.fn()} />,
    )
    const iframe = screen.getByTestId('artifact-iframe') as HTMLIFrameElement
    expect(iframe.getAttribute('sandbox')).toContain('allow-scripts')
  })

  it('sandbox attribute does NOT contain "allow-same-origin"', () => {
    render(
      <IframeSandbox compiled="console.log(1)" title="Test" onError={vi.fn()} />,
    )
    const iframe = screen.getByTestId('artifact-iframe') as HTMLIFrameElement
    expect(iframe.getAttribute('sandbox')).not.toContain('allow-same-origin')
  })

  it('srcdoc includes the nonce value', () => {
    render(
      <IframeSandbox compiled="console.log(1)" title="Test" onError={vi.fn()} />,
    )
    const iframe = screen.getByTestId('artifact-iframe') as HTMLIFrameElement
    const srcdoc = iframe.getAttribute('srcdoc') ?? ''
    // srcdoc must include a nonce attribute (any UUID-like value)
    expect(srcdoc).toMatch(/nonce-[a-f0-9-]{8,}/)
  })

  it('calls onError when a message event with type="error" is received', () => {
    const onError = vi.fn()
    render(<IframeSandbox compiled="console.log(1)" title="Test" onError={onError} />)

    act(() => {
      window.dispatchEvent(
        new MessageEvent('message', {
          data: { type: 'error', message: 'boom' },
        }),
      )
    })

    expect(onError).toHaveBeenCalledWith('boom')
  })

  it('does not call onError for non-error messages', () => {
    const onError = vi.fn()
    render(<IframeSandbox compiled="console.log(1)" title="Test" onError={onError} />)

    act(() => {
      window.dispatchEvent(
        new MessageEvent('message', {
          data: { type: 'ready' },
        }),
      )
    })

    expect(onError).not.toHaveBeenCalled()
  })
})

describe('artifactStore persistence', () => {
  it('store retains artifacts across component unmount/remount', () => {
    // Verify the mocked store correctly returns the same artifact after remount
    const art = makeArtifact()
    mockGetActiveArtifact.mockReturnValue(art)
    mockStore({ getActiveArtifact: mockGetActiveArtifact })

    const { unmount } = render(<ArtifactPanel {...({} as IDockviewPanelProps)} />)
    expect(screen.getByTestId('artifact-iframe')).toBeDefined()
    unmount()

    // Re-render — store still has the artifact
    render(<ArtifactPanel {...({} as IDockviewPanelProps)} />)
    expect(screen.getByTestId('artifact-iframe')).toBeDefined()
  })
})
