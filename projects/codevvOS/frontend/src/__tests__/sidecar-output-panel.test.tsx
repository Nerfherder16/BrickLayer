import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import SidecarOutputPanel from '../components/Panels/SidecarOutputPanel'
import * as sidecarStoreModule from '../stores/sidecarStore'
import type { SidecarState, ConnectionState } from '../stores/sidecarStore'

vi.mock('../stores/sidecarStore')
vi.mock('ansi-to-html', () => {
  return {
    default: class MockAnsiToHtml {
      toHtml(input: string): string {
        return input
      }
    },
  }
})

const mockRunCommand = vi.fn()
const mockInterrupt = vi.fn()
const mockGetStatus = vi.fn()
const mockClearOutput = vi.fn()

function makeStoreReturn(overrides: Partial<SidecarState> = {}): SidecarState {
  return {
    output: [],
    isRunning: false,
    currentCommand: null,
    connectionState: 'idle' as ConnectionState,
    runCommand: mockRunCommand,
    interrupt: mockInterrupt,
    getStatus: mockGetStatus,
    clearOutput: mockClearOutput,
    ...overrides,
  }
}

// Minimal dockview panel props stub
const panelProps = {} as Parameters<typeof SidecarOutputPanel>[0]

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(sidecarStoreModule.useSidecarStore).mockReturnValue(makeStoreReturn())
})

describe('SidecarOutputPanel', () => {
  it('should render the panel container', () => {
    render(<SidecarOutputPanel {...panelProps} />)
    expect(screen.getByTestId('sidecar-output-panel')).toBeDefined()
  })

  it('should render output lines from store', () => {
    vi.mocked(sidecarStoreModule.useSidecarStore).mockReturnValue(
      makeStoreReturn({ output: ['hello world', 'second line'] }),
    )
    render(<SidecarOutputPanel {...panelProps} />)
    const ansiOutput = screen.getByTestId('ansi-output')
    expect(ansiOutput.textContent).toContain('hello world')
    expect(ansiOutput.textContent).toContain('second line')
  })

  it('should show sidecar-connecting indicator when connectionState is connecting', () => {
    vi.mocked(sidecarStoreModule.useSidecarStore).mockReturnValue(
      makeStoreReturn({ connectionState: 'connecting' }),
    )
    render(<SidecarOutputPanel {...panelProps} />)
    expect(screen.getByTestId('sidecar-connecting')).toBeDefined()
  })

  it('should not show sidecar-connecting when connectionState is idle', () => {
    render(<SidecarOutputPanel {...panelProps} />)
    expect(screen.queryByTestId('sidecar-connecting')).toBeNull()
  })

  it('should not show sidecar-connecting when connectionState is running', () => {
    vi.mocked(sidecarStoreModule.useSidecarStore).mockReturnValue(
      makeStoreReturn({ connectionState: 'running', isRunning: true }),
    )
    render(<SidecarOutputPanel {...panelProps} />)
    expect(screen.queryByTestId('sidecar-connecting')).toBeNull()
  })

  it('should render command toolbar', () => {
    render(<SidecarOutputPanel {...panelProps} />)
    expect(screen.getByTestId('command-toolbar')).toBeDefined()
  })

  it('should have stop button disabled when isRunning is false', () => {
    vi.mocked(sidecarStoreModule.useSidecarStore).mockReturnValue(
      makeStoreReturn({ isRunning: false }),
    )
    render(<SidecarOutputPanel {...panelProps} />)
    const stopBtn = screen.getByTestId('stop-button') as HTMLButtonElement
    expect(stopBtn.disabled).toBe(true)
  })

  it('should have stop button enabled when isRunning is true', () => {
    vi.mocked(sidecarStoreModule.useSidecarStore).mockReturnValue(
      makeStoreReturn({ isRunning: true }),
    )
    render(<SidecarOutputPanel {...panelProps} />)
    const stopBtn = screen.getByTestId('stop-button') as HTMLButtonElement
    expect(stopBtn.disabled).toBe(false)
  })

  it('should call interrupt when stop button is clicked while running', () => {
    vi.mocked(sidecarStoreModule.useSidecarStore).mockReturnValue(
      makeStoreReturn({ isRunning: true }),
    )
    render(<SidecarOutputPanel {...panelProps} />)
    fireEvent.click(screen.getByTestId('stop-button'))
    expect(mockInterrupt).toHaveBeenCalledTimes(1)
  })

  it('should render ansi-output container', () => {
    render(<SidecarOutputPanel {...panelProps} />)
    expect(screen.getByTestId('ansi-output')).toBeDefined()
  })
})
