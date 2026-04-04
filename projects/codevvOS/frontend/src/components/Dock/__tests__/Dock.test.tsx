import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import React from 'react'
import { LayoutContext } from '../../../contexts/LayoutContext'
import { APP_REGISTRY } from '../appRegistry'
import Dock from '../Dock'

function makeMockApi(overrides: Record<string, unknown> = {}) {
  return {
    addPanel: vi.fn(),
    getPanel: vi.fn().mockReturnValue(null),
    panels: [],
    onDidActivePanelChange: vi.fn().mockReturnValue({ dispose: vi.fn() }),
    onDidLayoutChange: vi.fn().mockReturnValue({ dispose: vi.fn() }),
    ...overrides,
  }
}

function renderDock(mockApi: ReturnType<typeof makeMockApi>) {
  return render(
    <LayoutContext.Provider value={{ dockviewApi: mockApi as unknown as import('dockview-react').DockviewApi, setDockviewApi: vi.fn() }}>
      <Dock />
    </LayoutContext.Provider>,
  )
}

describe('Dock', () => {
  let mockApi: ReturnType<typeof makeMockApi>

  beforeEach(() => {
    mockApi = makeMockApi()
  })

  it('renders one button per APP_REGISTRY entry', () => {
    renderDock(mockApi)
    for (const app of APP_REGISTRY) {
      expect(screen.getByTestId(`dock-btn-${app.id}`)).toBeTruthy()
    }
  })

  it('calls addPanel when clicking an icon for a panel that is not open', () => {
    mockApi.getPanel.mockReturnValue(null)
    renderDock(mockApi)
    fireEvent.click(screen.getByTestId('dock-btn-terminal'))
    expect(mockApi.addPanel).toHaveBeenCalledWith({
      id: 'terminal',
      component: 'TerminalPanel',
      title: 'Terminal',
    })
  })

  it('calls focus() and NOT addPanel when clicking an open but inactive panel', () => {
    const focusMock = vi.fn()
    mockApi.getPanel.mockImplementation((id: string) =>
      id === 'terminal' ? { id: 'terminal', focus: focusMock } : null,
    )
    // panels list has terminal, but activePanelId starts as null (no active panel set yet)
    mockApi.panels = [{ id: 'terminal' }] as unknown as typeof mockApi.panels

    renderDock(mockApi)
    fireEvent.click(screen.getByTestId('dock-btn-terminal'))
    expect(focusMock).toHaveBeenCalled()
    expect(mockApi.addPanel).not.toHaveBeenCalled()
  })

  it('is a no-op when clicking the already-active panel', () => {
    const focusMock = vi.fn()
    const fakePanel = { id: 'terminal', focus: focusMock }
    mockApi.getPanel.mockImplementation((id: string) =>
      id === 'terminal' ? fakePanel : null,
    )

    // Simulate active panel via the onDidActivePanelChange callback.
    // The real dockview API fires the panel object directly (IDockviewPanel | undefined).
    let activeCb: ((panel: { id: string } | undefined) => void) | null = null
    mockApi.onDidActivePanelChange.mockImplementation(
      (cb: (panel: { id: string } | undefined) => void) => {
        activeCb = cb
        return { dispose: vi.fn() }
      },
    )

    renderDock(mockApi)

    // Fire the active-panel-change event to make terminal the active panel
    act(() => {
      activeCb?.({ id: 'terminal' })
    })

    fireEvent.click(screen.getByTestId('dock-btn-terminal'))
    expect(mockApi.addPanel).not.toHaveBeenCalled()
    expect(focusMock).not.toHaveBeenCalled()
  })

  it('sets data-active="true" on the active panel button', () => {
    let activeCb: ((panel: { id: string } | undefined) => void) | null = null
    mockApi.onDidActivePanelChange.mockImplementation(
      (cb: (panel: { id: string } | undefined) => void) => {
        activeCb = cb
        return { dispose: vi.fn() }
      },
    )

    renderDock(mockApi)
    act(() => {
      activeCb?.({ id: 'terminal' })
    })

    const btn = screen.getByTestId('dock-btn-terminal')
    expect(btn.getAttribute('data-active')).toBe('true')
  })
})
