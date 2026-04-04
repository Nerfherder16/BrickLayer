import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// ---- Mocks ----------------------------------------------------------------

vi.mock('../stores/artifactStore')

import * as artifactStoreModule from '../stores/artifactStore'

const mockAddArtifact = vi.fn()
const mockSetActiveArtifact = vi.fn()

function mockStore(overrides: Partial<ReturnType<typeof artifactStoreModule.useArtifactStore>> = {}): void {
  const state = {
    artifacts: [],
    activeArtifactId: null,
    addArtifact: mockAddArtifact,
    setActiveArtifact: mockSetActiveArtifact,
    getActiveArtifact: vi.fn().mockReturnValue(null),
    ...overrides,
  }
  vi.mocked(artifactStoreModule.useArtifactStore).mockImplementation((selector: unknown) => {
    if (typeof selector === 'function') return (selector as (s: typeof state) => unknown)(state)
    return state
  })
}

// ---- Import after mocks ---------------------------------------------------

import { ArtifactHistory } from '../components/Artifacts/ArtifactHistory'

// ---- Helpers --------------------------------------------------------------

const makeHistoryItem = (id: string, title: string, timestamp: string) => ({
  id,
  title,
  timestamp,
  metadata: {
    artifact_id: `art-${id}`,
    title,
    jsx: `<div>${title}</div>`,
    compiled: null,
  },
})

// ---- Tests ----------------------------------------------------------------

describe('ArtifactHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockStore()
    vi.stubGlobal('fetch', vi.fn())
  })

  it('renders with data-testid="artifact-history"', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response)

    render(<ArtifactHistory onSelect={vi.fn()} />)
    expect(screen.getByTestId('artifact-history')).toBeDefined()
  })

  it('shows "No saved artifacts" when history is empty', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response)

    render(<ArtifactHistory onSelect={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('No saved artifacts')).toBeDefined()
    })
  })

  it('renders artifact titles from history response', async () => {
    const items = [
      makeHistoryItem('m1', 'My Chart', '2024-02-01T00:00:00Z'),
      makeHistoryItem('m2', 'User Table', '2024-01-01T00:00:00Z'),
    ]
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => items,
    } as Response)

    render(<ArtifactHistory onSelect={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('My Chart')).toBeDefined()
      expect(screen.getByText('User Table')).toBeDefined()
    })
  })

  it('each history item has data-testid="artifact-history-item"', async () => {
    const items = [makeHistoryItem('m1', 'Chart A', '2024-01-01T00:00:00Z')]
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => items,
    } as Response)

    render(<ArtifactHistory onSelect={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getAllByTestId('artifact-history-item').length).toBeGreaterThan(0)
    })
  })

  it('calls onSelect when a history item is clicked', async () => {
    const onSelect = vi.fn()
    const item = makeHistoryItem('m1', 'Clickable', '2024-01-01T00:00:00Z')
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [item],
    } as Response)

    render(<ArtifactHistory onSelect={onSelect} />)

    await waitFor(() => {
      expect(screen.getByTestId('artifact-history-item')).toBeDefined()
    })

    await userEvent.click(screen.getByTestId('artifact-history-item'))
    expect(onSelect).toHaveBeenCalledWith(item)
  })

  it('shows empty state when fetch fails (Recall unavailable)', async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'))

    render(<ArtifactHistory onSelect={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('No saved artifacts')).toBeDefined()
    })
  })
})
