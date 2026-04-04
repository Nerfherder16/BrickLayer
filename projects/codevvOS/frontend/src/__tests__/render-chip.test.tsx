import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../stores/artifactStore')

import * as artifactStoreModule from '../stores/artifactStore'
import { RenderChip } from '../components/Artifacts/RenderChip'

const mockSetActiveArtifact = vi.fn()

function makeStoreReturn(
  overrides: Partial<ReturnType<typeof artifactStoreModule.useArtifactStore>> = {},
): ReturnType<typeof artifactStoreModule.useArtifactStore> {
  return {
    artifacts: [],
    activeArtifactId: null,
    addArtifact: vi.fn(),
    setActiveArtifact: mockSetActiveArtifact,
    getActiveArtifact: vi.fn().mockReturnValue(null),
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(artifactStoreModule.useArtifactStore).mockImplementation((selector: unknown) => {
    const state = makeStoreReturn()
    if (typeof selector === 'function') return (selector as (s: typeof state) => unknown)(state)
    return state
  })
})

describe('RenderChip', () => {
  it('renders with data-testid="render-chip"', () => {
    render(<RenderChip artifactId="art-1" title="My Widget" />)
    expect(screen.getByTestId('render-chip')).toBeDefined()
  })

  it('displays the artifact title', () => {
    render(<RenderChip artifactId="art-1" title="My Widget" />)
    expect(screen.getByTestId('render-chip').textContent).toContain('My Widget')
  })

  it('calls setActiveArtifact with the artifactId when clicked', () => {
    render(<RenderChip artifactId="art-42" title="Widget" />)
    fireEvent.click(screen.getByTestId('render-chip'))
    expect(mockSetActiveArtifact).toHaveBeenCalledWith('art-42')
  })

  it('calls setActiveArtifact once per click', () => {
    render(<RenderChip artifactId="art-1" title="Widget" />)
    fireEvent.click(screen.getByTestId('render-chip'))
    fireEvent.click(screen.getByTestId('render-chip'))
    expect(mockSetActiveArtifact).toHaveBeenCalledTimes(2)
  })

  it('is a button element for keyboard accessibility', () => {
    render(<RenderChip artifactId="art-1" title="Widget" />)
    const chip = screen.getByTestId('render-chip')
    expect(chip.tagName.toLowerCase()).toBe('button')
  })
})
